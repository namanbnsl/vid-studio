"""Publishing: each platform's client against a fake that follows the platform's documented protocol."""
import contextlib
import http.client
import io
import json
import os
import re
import sys
import tempfile
import threading
import unittest
import urllib.parse
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "vid-studio" / "scripts"))
import narration as tts  # noqa: E402
import publish as pub  # noqa: E402
import studio  # noqa: E402
from support import idea_script  # noqa: E402


class FakePlatforms:
    """Routes pub.request to in-memory YouTube, Instagram and TikTok APIs, and records every call."""

    def __init__(self):
        self.calls, self.youtube_uploads, self.ig_polls, self.fail_after_chunk = [], {}, 0, None
        self.tiktok_privacy = ["SELF_ONLY", "PUBLIC_TO_EVERYONE"]
        self.extra_scopes = []  # what the user consented to beyond the basics

    def __call__(self, method, url, headers=None, body=None, timeout=120):
        headers = headers or {}
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
        parts = urllib.parse.urlsplit(url)
        query = dict(urllib.parse.parse_qsl(parts.query))
        self.calls.append({"method": method, "url": url, "headers": headers, "body": body, "query": query})
        host, path = parts.hostname, parts.path
        ok = lambda data, status=200, extra=None: (status, {"content-type": "application/json", **(extra or {})}, json.dumps(data).encode())
        form = dict(urllib.parse.parse_qsl(body.decode())) if body and headers.get("Content-Type", "").startswith("application/x-www-form") else {}
        # ---- Google
        if url == "https://oauth2.googleapis.com/token":
            if form["grant_type"] == "authorization_code":
                assert form["code"] == "good-code" and form["code_verifier"], form
                return ok({"access_token": "ya29.a", "refresh_token": "1//r", "expires_in": 3599, "scope": " ".join(pub.YouTube.SCOPES + self.extra_scopes)})
            return ok({"access_token": "ya29.b", "expires_in": 3599})
        if host == "oauth2.googleapis.com" and path == "/revoke":
            return ok({})
        if url.startswith("https://www.googleapis.com/youtube/v3/channels"):
            assert headers["Authorization"].startswith("Bearer ya29")
            return ok({"items": [{"id": "UC1", "snippet": {"title": "Pipe Gyaan", "customUrl": "@pipegyaan"}}]})
        if url.startswith("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable") and method == "POST":
            meta = json.loads(body)
            session = f"https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&upload_id=s{len(self.youtube_uploads)}"
            self.youtube_uploads[session] = {"size": int(headers["X-Upload-Content-Length"]), "data": b"", "meta": meta}
            return ok({}, 200, {"location": session})
        if url in self.youtube_uploads and method == "PUT":
            upload = self.youtube_uploads[url]
            total = re.match(r"bytes (\*|(\d+)-(\d+))/(\d+)", headers["Content-Range"])
            if total[1] != "*":
                assert int(total[2]) == len(upload["data"]), "chunks must continue from the confirmed byte"
                upload["data"] += body
                if self.fail_after_chunk is not None and len(upload["data"]) >= self.fail_after_chunk:
                    self.fail_after_chunk = None
                    raise pub.PublishError("Couldn't reach www.googleapis.com: connection reset")
            if len(upload["data"]) == upload["size"]:
                return ok({"id": "vid123", "status": {"privacyStatus": upload["meta"]["status"]["privacyStatus"]}}, 201)
            return 308, {"range": f"bytes=0-{len(upload['data']) - 1}"} if upload["data"] else {}, b""
        if url.startswith("https://www.googleapis.com/upload/youtube/v3/thumbnails/set"):
            return ok({"items": [{}]})
        if url.startswith("https://www.googleapis.com/upload/youtube/v3/captions"):
            assert b"-->" in body
            return ok({"id": "cap1"})
        if url.startswith("https://www.googleapis.com/youtube/v3/videos?part=statistics"):
            return ok({"items": [{"statistics": {"viewCount": "1234", "likeCount": "56", "commentCount": "7"}, "status": {"privacyStatus": "public"}}]})
        # ---- Instagram
        if host == "graph.instagram.com" and path == "/refresh_access_token":
            return ok({"access_token": "IGQ-refreshed-token-0123456789", "expires_in": 5183944})
        if host == "graph.instagram.com" and path.endswith("/me"):
            return ok({"user_id": "1784", "username": "pipegyaan", "account_type": "MEDIA_CREATOR"})
        if host == "graph.instagram.com" and path.endswith("/1784/media") and method == "POST":
            assert (form["media_type"], form["upload_type"]) == ("REELS", "resumable"), form
            self.ig_caption = form["caption"]
            return ok({"id": "c1", "uri": "https://rupload.facebook.com/ig-api-upload/c1"})
        if host == "rupload.facebook.com":
            assert headers["Authorization"].startswith("OAuth ") and headers["offset"] == "0" and int(headers["file_size"]) == len(body)
            return ok({"success": True})
        if host == "graph.instagram.com" and path.endswith("/c1"):
            self.ig_polls += 1
            return ok({"status_code": "FINISHED" if self.ig_polls > 1 else "IN_PROGRESS", "status": ""})
        if host == "graph.instagram.com" and path.endswith("/media_publish"):
            assert form["creation_id"] == "c1"
            return ok({"id": "m1"})
        if host == "graph.instagram.com" and path.endswith("/m1"):
            return ok({"permalink": "https://www.instagram.com/reel/ABC/", "like_count": 9, "comments_count": 2})
        # ---- TikTok
        if url == "https://open.tiktokapis.com/v2/oauth/token/":
            return ok({"access_token": "act.tok", "refresh_token": "rft.tok", "expires_in": 86400, "scope": "user.info.basic,video.publish,video.upload"})
        if url.startswith("https://open.tiktokapis.com/v2/user/info/"):
            return ok({"data": {"user": {"open_id": "o1", "display_name": "Pipe Gyaan", "username": "pipegyaan"}}, "error": {"code": "ok"}})
        if url == "https://open.tiktokapis.com/v2/post/publish/creator_info/query/":
            return ok({"data": {"privacy_level_options": self.tiktok_privacy}, "error": {"code": "ok"}})
        if url in ("https://open.tiktokapis.com/v2/post/publish/video/init/", "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/"):
            info = json.loads(body)["source_info"]
            assert info["source"] == "FILE_UPLOAD" and info["total_chunk_count"] >= 1
            self.tiktok_init = json.loads(body)
            return ok({"data": {"publish_id": "p1", "upload_url": "https://open-upload.tiktokapis.com/upload/?token=x"}, "error": {"code": "ok"}})
        if host == "open-upload.tiktokapis.com":
            self.tiktok_bytes = getattr(self, "tiktok_bytes", 0) + len(body)
            return 201, {}, b""
        if url == "https://open.tiktokapis.com/v2/post/publish/status/fetch/":
            inbox = "inbox" in self.calls[-3]["url"] or "inbox" in json.dumps(getattr(self, "tiktok_init", {}))
            status = "SEND_TO_USER_INBOX" if "post_info" not in self.tiktok_init else "PUBLISH_COMPLETE"
            return ok({"data": {"status": status, "publicaly_available_post_id": [7300000000000000001]}, "error": {"code": "ok"}})
        raise AssertionError(f"Unexpected call: {method} {url}")


class MetaTest(unittest.TestCase):
    def test_post_details_are_validated(self):
        meta = pub.clean_meta({"title": " Hi ", "hashtags": ["#upi", "money"], "publish_at": "2026-10-20T18:30:00+05:30"})
        self.assertEqual((meta["title"], meta["hashtags"], meta["publish_at"]), ("Hi", ["upi", "money"], "2026-10-20T13:00:00Z"))
        for bad in ({"title": "x" * 101}, {"title": "<b>"}, {"tags": ["a" * 101]}, {"tags": ["x" * 90] * 6}, {"publish_at": "soon"},
                    {"made_for_kids": "no"}, {"category": "news"}, {"colour": 1}):
            with self.assertRaises(ValueError, msg=bad):
                pub.clean_meta(bad)

    def test_credits_sources_and_hashtags_are_appended_once(self):
        text = pub.with_credits("About UPI. #upi", ["Photo: A / Flickr, CC BY 2.0"], ["https://rbi.org.in/x"], ["upi", "money"], 5000)
        self.assertEqual(text, "About UPI. #upi\n\nSources:\nhttps://rbi.org.in/x\n\nPhoto: A / Flickr, CC BY 2.0\n\n#money")
        self.assertEqual(len(pub.with_credits("x" * 50, [], [], ["tag"], 20)), 20)

    def test_pkce_and_token_names(self):
        verifier, b64, hexed = pub.pkce()
        self.assertTrue(43 <= len(verifier) <= 128)
        self.assertEqual(len(hexed), 64)
        self.assertNotIn("=", b64)
        self.assertEqual(pub.token_name("pipe-gyaan"), "PUBLISH_PIPE_GYAAN")

    def test_http_statuses_are_returned_and_errors_explained(self):
        error = urllib_error(403, b'{"error": {"message": "Quota exceeded", "errors": [{"reason": "quotaExceeded"}]}}')
        with mock.patch.object(pub._OPENER, "open", side_effect=error):
            status, _, body = pub.request("GET", "https://www.googleapis.com/x")
        self.assertEqual(status, 403)
        with self.assertRaisesRegex(pub.PublishError, r"HTTP 403: Quota exceeded \(quotaExceeded\) \(daily upload quota"):
            pub.check("YouTube", status, body)
        with self.assertRaises(pub.Reconnect):
            pub.check("YouTube", 401, b"{}")


def urllib_error(code, body):
    import urllib.error
    return urllib.error.HTTPError("https://x", code, "err", {}, io.BytesIO(body))


class PublishFlowTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.fake = FakePlatforms()
        self.patches = [mock.patch.object(pub, "request", self.fake), mock.patch.object(pub, "CHUNK", 256 * 1024),
                        mock.patch.dict(os.environ, {k: "" for k in ("GOOGLE_OAUTH_CLIENT_ID", "GOOGLE_OAUTH_CLIENT_SECRET", "TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET")}),
                        mock.patch("time.sleep", lambda s: None)]
        for patch in self.patches:
            patch.start()
        with contextlib.redirect_stdout(io.StringIO()):
            studio.main(["--workspace", str(self.home), "new-project", "--name", "Pub"])
        studio.add_channel(self.home, {"name": "Shorts", "platform": "YouTube Shorts", "language": "Hindi"})
        studio.add_channel(self.home, {"name": "Reels", "platform": "Instagram Reels"})
        studio.add_channel(self.home, {"name": "Tok", "platform": "TikTok"})
        studio.add_channel(self.home, {"name": "WA", "kind": "post"})
        self.project = studio.Studio(self.home / "projects" / "pub", self.home)
        self.text = "## Hook\nUPI Lite की limit बढ़ी.\nVisual: stat | ₹5,000 | Limit\nImage: media/a.jpg | Photo: A / Flickr, CC BY 2.0\n## End\nVisual: end | Bye | Follow"
        self.scripts = {}
        for channel in ("shorts", "reels", "tok"):
            sid = idea_script(self.project, channel, "UPI Lite")["id"]
            self.project.path("scripts", sid, "facts.md").write_text("## Facts\n- x [1]\n\n## Sources\n[1] NPCI, circular, https://www.npci.org.in/c1.\n[2] RBI, https://rbi.org.in/x\n")
            self.project.update_script(sid, {"text": self.text})
            self.render(sid)
            self.scripts[channel] = sid

    def tearDown(self):
        for patch in reversed(self.patches):
            patch.stop()
        self.tmp.cleanup()

    def render(self, sid, size=700_000):
        folder = self.project.path("scripts", sid, "render")
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "video.mp4").write_bytes(bytes(range(256)) * (size // 256) + b"x" * (size % 256))
        (folder / "poster.jpg").write_bytes(b"\xff\xd8\xff fake jpeg")

    def connect_youtube(self, captions=False):
        tts.set_secret(self.home, "GOOGLE_OAUTH_CLIENT_ID", "123.apps.googleusercontent.com")
        tts.set_secret(self.home, "GOOGLE_OAUTH_CLIENT_SECRET", "GOCSPX-secret")
        url = studio.start_oauth(self.home, "shorts", "youtube", "http://localhost:8765/oauth/callback", captions)
        query = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query))
        self.assertEqual((query["code_challenge_method"], query["access_type"], query["redirect_uri"]), ("S256", "offline", "http://localhost:8765/oauth/callback"))
        self.assertEqual(captions, pub.YouTube.CAPTION_SCOPE in query["scope"])
        self.fake.extra_scopes = [pub.YouTube.CAPTION_SCOPE] if captions else []
        return studio.finish_oauth(self.home, query["state"], "good-code")

    def test_youtube_connects_uploads_resumes_and_marks_the_script_published(self):
        self.assertEqual(studio.channel_publishing(self.home, "shorts")["platform"], "youtube")  # guessed from "YouTube Shorts"
        with self.assertRaisesRegex(RuntimeError, "Add your YouTube app's client ID and client secret"):
            studio.start_oauth(self.home, "shorts", "youtube", "http://localhost:8765/oauth/callback")
        info = self.connect_youtube(captions=True)
        self.assertEqual((info["connected"], info["account"]["name"], info["account"]["url"]), (True, "Pipe Gyaan", "https://www.youtube.com/@pipegyaan"))
        with self.assertRaisesRegex(ValueError, "expired or was already used"):
            studio.finish_oauth(self.home, "reused", "good-code")
        self.assertNotIn("1//r", json.dumps(studio.channel_publishing(self.home, "shorts")))
        self.assertEqual(pub.read_tokens(self.home, "shorts")["refresh_token"], "1//r")

        sid = self.scripts["shorts"]
        self.project.save_publish_details(sid, {"title": "UPI Lite की नई limit", "description": "What changed.", "hashtags": ["upi"],
                                                "publish_at": "2026-10-20T18:30:00+05:30", "tags": ["upi lite"]})
        self.fake.fail_after_chunk = 300_000  # the connection drops after the second chunk
        with self.assertRaisesRegex(pub.PublishError, "connection reset"):
            self.project.publish_script(sid)
        status = self.project.publish_status(sid)
        self.assertEqual(status["status"], "failed")
        session = json.loads(self.project.path("scripts", sid, "publish", "state.json").read_text())["session"]
        result = self.project.publish_script(sid)  # resumes the same session from YouTube's confirmed byte
        self.assertEqual(len(self.fake.youtube_uploads), 1)
        upload = self.fake.youtube_uploads[session]
        self.assertEqual(upload["data"], self.project.path("scripts", sid, "render", "video.mp4").read_bytes())
        snippet, state = upload["meta"]["snippet"], upload["meta"]["status"]
        self.assertEqual((snippet["title"], snippet["categoryId"], snippet["defaultAudioLanguage"], snippet["tags"]), ("UPI Lite की नई limit", "27", "hi", ["upi lite"]))
        self.assertIn("https://www.npci.org.in/c1", snippet["description"])  # sources from the fact sheet
        self.assertIn("Photo: A / Flickr, CC BY 2.0", snippet["description"])  # CC BY credit
        self.assertTrue(snippet["description"].endswith("#upi"))
        self.assertEqual((state["privacyStatus"], state["publishAt"], state["selfDeclaredMadeForKids"]), ("private", "2026-10-20T13:00:00Z", False))
        self.assertEqual(result, {"id": "vid123", "url": "https://www.youtube.com/shorts/vid123", "status": "scheduled", "notes": [], "privacy": "private"})
        self.assertTrue(any("thumbnails/set?videoId=vid123" in c["url"] for c in self.fake.calls))
        self.assertTrue(any("/captions?" in c["url"] for c in self.fake.calls))
        script = self.project.script(sid)
        self.assertEqual((script["stage"], script["published_url"], script["publish"]["status"]), ("published", "https://www.youtube.com/shorts/vid123", "scheduled"))
        self.assertNotIn("session", json.loads(self.project.path("scripts", sid, "publish", "state.json").read_text()))
        self.assertEqual(self.project.refresh_stats(sid)["views"], 1234)
        listed = next(x for x in self.project.scripts() if x["id"] == sid)
        self.assertEqual(listed["publish"]["stats"]["views"], 1234)

    def test_publishing_needs_a_current_render_and_a_connection(self):
        sid = self.scripts["shorts"]
        with self.assertRaisesRegex(RuntimeError, "Connect Shorts to its YouTube account"):
            self.project.publish_script(sid)
        self.connect_youtube()
        (self.project.path("scripts", sid, "render", "video.mp4")).unlink()
        with self.assertRaisesRegex(RuntimeError, "Render the video first"):
            self.project.publish_script(sid)
        post = idea_script(self.project, "wa", "UPI Lite")["id"]
        with self.assertRaisesRegex(ValueError, "shared by hand"):
            self.project.publish_script(post)
        self.assertIsNone(self.project.script(post)["publish"])

    def test_instagram_reel_with_a_pasted_token(self):
        info = studio.connect_token(self.home, "reels", "instagram", "IGQWRPasted0123456789token")
        self.assertEqual(info["account"], {"id": "1784", "name": "@pipegyaan", "handle": "pipegyaan", "url": "https://www.instagram.com/pipegyaan/"})
        with self.assertRaisesRegex(pub.PublishError, "doesn't look like"):
            studio.connect_token(self.home, "reels", "instagram", "short")
        sid = self.scripts["reels"]
        self.project.save_publish_details(sid, {"caption": "UPI Lite की limit अब ₹5,000.", "hashtags": ["upi"]})
        self.project.save_publish_details(sid, {"publish_at": "2026-10-20T18:30:00+05:30"})
        with self.assertRaisesRegex(ValueError, "can't schedule"):
            self.project.publish_script(sid)
        self.project.save_publish_details(sid, {"publish_at": ""})
        result = self.project.publish_script(sid)
        self.assertEqual((result["url"], result["status"]), ("https://www.instagram.com/reel/ABC/", "published"))
        self.assertEqual(self.fake.ig_caption, "UPI Lite की limit अब ₹5,000.\n\nPhoto: A / Flickr, CC BY 2.0\n\n#upi")
        self.assertEqual(self.fake.ig_polls, 2)
        self.assertEqual(self.project.refresh_stats(sid), self.project.publish_status(sid)["stats"])

    def test_tiktok_drafts_by_default_and_respects_creator_privacy(self):
        tts.set_secret(self.home, "TIKTOK_CLIENT_KEY", "awkey")
        tts.set_secret(self.home, "TIKTOK_CLIENT_SECRET", "secret")
        url = studio.start_oauth(self.home, "tok", "tiktok", "http://localhost:8765/oauth/callback")
        query = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query))
        self.assertEqual(len(query["code_challenge"]), 64)  # TikTok's desktop flow: hex SHA-256
        studio.finish_oauth(self.home, query["state"], "good-code")
        sid = self.scripts["tok"]
        result = self.project.publish_script(sid)
        self.assertEqual(result["status"], "draft")
        self.assertNotIn("post_info", self.fake.tiktok_init)
        self.assertEqual(self.fake.tiktok_bytes, 700_000)
        self.project.save_publish_details(sid, {"privacy": "MUTUAL_FOLLOW_FRIENDS"})
        with self.assertRaisesRegex(pub.PublishError, "allows only SELF_ONLY, PUBLIC_TO_EVERYONE"):
            self.project.publish_script(sid)
        self.project.save_publish_details(sid, {"privacy": "SELF_ONLY", "synthetic": True})
        result = self.project.publish_script(sid)
        self.assertEqual((result["status"], result["url"]), ("published", "https://www.tiktok.com/@pipegyaan/video/7300000000000000001"))
        self.assertEqual((self.fake.tiktok_init["post_info"]["privacy_level"], self.fake.tiktok_init["post_info"]["is_aigc"]), ("SELF_ONLY", True))

    def test_defaults_switching_and_disconnecting(self):
        self.connect_youtube()
        saved = studio.save_publishing(self.home, "shorts", {"defaults": {"privacy": "unlisted", "hashtags": ["#money"], "category": "25"}})
        self.assertEqual((saved["defaults"]["privacy"], saved["defaults"]["hashtags"]), ("unlisted", ["money"]))
        self.assertEqual(self.project.publish_details(self.scripts["shorts"])["privacy"], "unlisted")
        with self.assertRaises(ValueError):
            studio.save_publishing(self.home, "shorts", {"defaults": {"privacy": "SELF_ONLY"}})
        with self.assertRaises(ValueError):
            studio.save_publishing(self.home, "wa", {"platform": "youtube"})
        studio.save_publishing(self.home, "shorts", {"platform": "instagram"})  # switching platforms disconnects
        self.assertFalse(studio.channel_publishing(self.home, "shorts")["connected"])
        self.assertEqual(pub.read_tokens(self.home, "shorts"), {})
        self.assertTrue(any("oauth2.googleapis.com/revoke" in c["url"] for c in self.fake.calls))

    def test_cli_requires_confirmation(self):
        self.connect_youtube()
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit) as stop:
            studio.main(["--workspace", str(self.home), "publish", "--script", self.scripts["shorts"]])
        self.assertIn("Re-run with --yes", str(stop.exception))
        self.assertIn("to YouTube · Pipe Gyaan · private", out.getvalue())
        with contextlib.redirect_stdout(out):
            studio.main(["--workspace", str(self.home), "publish", "--script", self.scripts["shorts"], "--yes"])
            studio.main(["--workspace", str(self.home), "platforms"])
        self.assertIn("Published: https://www.youtube.com/shorts/vid123", out.getvalue())
        self.assertIn("shorts → YouTube: Pipe Gyaan", out.getvalue())

    def test_http_oauth_round_trip_and_publish(self):
        tts.set_secret(self.home, "GOOGLE_OAUTH_CLIENT_ID", "123.apps.googleusercontent.com")
        tts.set_secret(self.home, "GOOGLE_OAUTH_CLIENT_SECRET", "GOCSPX-secret")
        server = studio.ThreadingHTTPServer(("127.0.0.1", 0), studio.make_handler(self.home))
        threading.Thread(target=server.serve_forever, daemon=True).start()

        def call(method, path, body=None):
            connection = http.client.HTTPConnection("127.0.0.1", server.server_port)
            try:
                headers = {"Host": f"localhost:{server.server_port}", "X-Vid-Studio": "1", "Content-Type": "application/json"}
                connection.request(method, path, json.dumps(body) if body is not None else None, headers)
                response = connection.getresponse()
                data = response.read()
                return response.status, response, (json.loads(data) if response.getheader("Content-Type", "").startswith("application/json") else data)
            finally:
                connection.close()
        try:
            code, response, _ = call("GET", "/oauth/start?channel=shorts&platform=youtube")
            self.assertEqual(code, 302)
            target = response.getheader("Location")
            self.assertTrue(target.startswith("https://accounts.google.com/o/oauth2/v2/auth?"))
            query = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(target).query))
            self.assertEqual(query["redirect_uri"], f"http://localhost:{server.server_port}/oauth/callback")
            code, _, page = call("GET", f"/oauth/callback?state=forged&code=good-code")
            self.assertEqual(code, 400)
            code, _, page = call("GET", f"/oauth/callback?state={query['state']}&code=good-code")
            self.assertEqual(code, 200)
            self.assertIn(b"Connected", page)
            self.assertTrue(call("GET", "/api/channels/shorts/publishing")[2]["connected"])
            self.assertEqual(call("GET", "/oauth/start?channel=wa&platform=youtube")[0], 400)
            sid = self.scripts["shorts"]
            self.assertEqual(call("PUT", f"/api/p/pub/scripts/{sid}/publish-details", {"title": "Hello"})[2]["title"], "Hello")
            self.assertEqual(call("POST", f"/api/p/pub/scripts/{sid}/publish", {})[0], 400)  # needs confirm
            code, _, state = call("POST", f"/api/p/pub/scripts/{sid}/publish", {"confirm": True})
            self.assertEqual(code, 200)
            studio.PUBLISHES[f"{self.project.ws}:{sid}"].join(10)
            script = call("GET", f"/api/p/pub/scripts/{sid}")[2]
            self.assertEqual((script["publish"]["status"], script["stage"]), ("published", "published"))
            self.assertEqual(call("POST", f"/api/p/pub/scripts/{sid}/stats", {})[2]["views"], 1234)
            self.assertEqual(call("PUT", "/api/platforms/youtube/app", {"EVIL": "x"})[0], 400)
            listed = call("PUT", "/api/platforms/tiktok/app", {"TIKTOK_CLIENT_KEY": "k"})[2]
            self.assertTrue(next(p for p in listed if p["id"] == "tiktok")["app_keys"][0]["set"])
            self.assertNotIn("GOCSPX-secret", json.dumps(call("GET", "/api/platforms")[2]))
            self.assertFalse(call("DELETE", "/api/channels/shorts/connection")[2]["connected"])
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()

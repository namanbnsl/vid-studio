"""Publish rendered videos to the platforms a channel is connected to: YouTube, Instagram Reels, TikTok.

Standard library only, against each platform's official API. A channel connects to one account:
  youtube    OAuth with the user's own Google Cloud "Desktop app" client (loopback redirect, PKCE)
  tiktok     OAuth with the user's own TikTok app (Login Kit for Desktop, PKCE), or a pasted access token
  instagram  a pasted Instagram API (Instagram Login) access token from the Meta app dashboard
Tokens live in <studio>/.secrets.json (mode 600) and refresh on their own. Uploads stream the MP4 from disk
and report progress; a YouTube upload that stops midway resumes from the last byte YouTube confirmed.
"""

from __future__ import annotations

import base64
import datetime as dt
import hashlib
import json
import os
import re
import secrets as random
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import narration as tts  # the studio's secrets store

USER_AGENT = "vid-studio/1.0"
CHUNK = 8 * 1024 * 1024  # a multiple of 256 KiB, as YouTube's resumable upload requires
IG_VERSION = "v23.0"


class PublishError(RuntimeError):
    """The platform refused, or something it needs is missing. The message says what to do."""


class Reconnect(PublishError):
    """The account's authorisation expired or was revoked: connect the channel again."""


# ---------------------------------------------------------------- HTTP: every status comes back, nothing is followed

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None  # YouTube answers 308 "Resume Incomplete", which is not a redirect


_OPENER = urllib.request.build_opener(_NoRedirect)


def request(method: str, url: str, headers: dict | None = None, body=None, timeout: int = 120) -> tuple[int, dict, bytes]:
    """(status, lower-cased headers, body). Network failures raise PublishError; HTTP errors are returned."""
    if isinstance(body, (dict, list)):
        data, headers = json.dumps(body).encode(), {"Content-Type": "application/json; charset=UTF-8", **(headers or {})}
    else:
        data = body
    req = urllib.request.Request(url, data=data, method=method, headers={"User-Agent": USER_AGENT, **(headers or {})})
    try:
        with _OPENER.open(req, timeout=timeout) as response:
            return response.status, {k.lower(): v for k, v in response.headers.items()}, response.read()
    except urllib.error.HTTPError as error:
        return error.code, {k.lower(): v for k, v in (error.headers or {}).items()}, error.read()
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise PublishError(f"Couldn't reach {urllib.parse.urlsplit(url).hostname}: {getattr(error, 'reason', error)}")


def as_json(body: bytes) -> dict:
    try:
        data = json.loads(body or b"{}")
        return data if isinstance(data, dict) else {"data": data}
    except json.JSONDecodeError:
        return {}


def explain(platform: str, status: int, body: bytes) -> str:
    data = as_json(body)
    error = data.get("error")
    if isinstance(error, dict):
        message = error.get("message") or error.get("error_user_msg") or error.get("code") or ""
        reasons = [e.get("reason") for e in error.get("errors", []) if isinstance(e, dict) and e.get("reason")]
        message = f"{message} ({', '.join(reasons)})" if reasons else message
    else:
        message = data.get("error_description") or error or data.get("message") or body[:300].decode("utf-8", "replace")
    return f"{platform} said HTTP {status}: {str(message).strip()[:400]}"


def check(platform: str, status: int, body: bytes, ok=(200, 201)) -> dict:
    if status in (401,) or (status == 400 and b"invalid_grant" in body):
        raise Reconnect(f"{explain(platform, status, body)}. Connect the channel again.")
    if status not in ok:
        hint = " (daily upload quota or rate limit; try again later)" if status in (403, 429) and re.search(rb"quota|rate", body, re.I) else ""
        raise PublishError(explain(platform, status, body) + hint)
    return as_json(body)


def form(data: dict) -> tuple[dict, bytes]:
    return {"Content-Type": "application/x-www-form-urlencoded"}, urllib.parse.urlencode(data).encode()


# ---------------------------------------------------------------- connections and tokens

def token_name(channel_id: str) -> str:
    return "PUBLISH_" + re.sub(r"[^A-Z0-9]", "_", channel_id.upper())[:50]


def read_tokens(root: Path, channel_id: str) -> dict:
    raw = tts.read_secrets(root).get(token_name(channel_id)) or ""
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def save_tokens(root: Path, channel_id: str, tokens: dict | None) -> None:
    tts.set_secret(root, token_name(channel_id), json.dumps(tokens, separators=(",", ":")) if tokens else "")


def pkce() -> tuple[str, str, str]:
    """(verifier, S256 base64url challenge, S256 hex challenge: TikTok's desktop flow wants hex)."""
    verifier = random.token_urlsafe(48)
    digest = hashlib.sha256(verifier.encode()).digest()
    return verifier, base64.urlsafe_b64encode(digest).rstrip(b"=").decode(), digest.hex()


def expires_at(seconds) -> float:
    try:
        return time.time() + float(seconds) - 60
    except (TypeError, ValueError):
        return 0.0


def now_iso() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


# ---------------------------------------------------------------- platforms

class Platform:
    id = ""
    name = ""
    oauth = False                 # connects in the browser (needs the user's own app credentials)
    app_keys: list = []           # [(secret name, label)] for the user's own app
    app_url = ""                  # where to create the app
    token_help = ""               # how to get a token to paste, when that's the way in
    kinds = ("video",)
    privacy_options: list = []    # [(value, label)]
    default_privacy = ""
    caption_limit = 2200

    # connecting

    def app_problem(self, root: Path) -> str:
        missing = [label for name, label in self.app_keys if not tts.secret(root, name)]
        return f"Add your {self.name} app's {' and '.join(missing)}" if missing else ""

    def auth_url(self, root: Path, redirect: str, state: str, challenge: tuple[str, str]) -> str:
        raise PublishError(f"{self.name} connects with a pasted access token")

    def exchange(self, root: Path, code: str, redirect: str, verifier: str) -> dict:
        raise NotImplementedError

    def from_token(self, root: Path, token: str) -> dict:
        raise PublishError(f"{self.name} connects in the browser; use Connect")

    def refresh(self, root: Path, tokens: dict) -> dict:
        return tokens

    def account(self, root: Path, tokens: dict) -> dict:
        """{"id", "name", "url"} for the connected account."""
        raise NotImplementedError

    def revoke(self, root: Path, tokens: dict) -> None:
        pass

    # publishing

    def publish(self, root: Path, tokens: dict, account: dict, video: Path, meta: dict, extras: dict, state: dict, progress) -> dict:
        """Upload and publish; returns {"id", "url", "status"}. `state` persists across retries (resumable sessions)."""
        raise NotImplementedError

    def stats(self, root: Path, tokens: dict, remote_id: str) -> dict:
        return {}

    def describe(self, root: Path) -> dict:
        return {"id": self.id, "name": self.name, "oauth": self.oauth, "app_problem": self.app_problem(root),
                "app_keys": [{"name": n, "label": label, "set": bool(tts.secret(root, n))} for n, label in self.app_keys],
                "app_url": self.app_url, "token_help": self.token_help, "privacy": [{"id": v, "label": label} for v, label in self.privacy_options],
                "default_privacy": self.default_privacy, "caption_limit": self.caption_limit}


class YouTube(Platform):
    id, name, oauth = "youtube", "YouTube", True
    app_keys = [("GOOGLE_OAUTH_CLIENT_ID", "client ID"), ("GOOGLE_OAUTH_CLIENT_SECRET", "client secret")]
    app_url = "https://console.cloud.google.com/apis/credentials"
    privacy_options = [("private", "Private"), ("unlisted", "Unlisted"), ("public", "Public")]
    default_privacy = "private"
    caption_limit = 5000
    SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.readonly"]
    CAPTION_SCOPE = "https://www.googleapis.com/auth/youtube.force-ssl"
    TOKEN = "https://oauth2.googleapis.com/token"
    API = "https://www.googleapis.com/youtube/v3"
    UPLOAD = "https://www.googleapis.com/upload/youtube/v3"

    def auth_url(self, root, redirect, state, challenge, captions: bool = False):
        params = {"client_id": tts.secret(root, "GOOGLE_OAUTH_CLIENT_ID"), "redirect_uri": redirect, "response_type": "code",
                  "scope": " ".join(self.SCOPES + ([self.CAPTION_SCOPE] if captions else [])), "state": state,
                  "access_type": "offline", "prompt": "consent", "code_challenge": challenge[0], "code_challenge_method": "S256"}
        return "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)

    def exchange(self, root, code, redirect, verifier):
        headers, body = form({"code": code, "client_id": tts.secret(root, "GOOGLE_OAUTH_CLIENT_ID"),
                              "client_secret": tts.secret(root, "GOOGLE_OAUTH_CLIENT_SECRET"), "redirect_uri": redirect,
                              "grant_type": "authorization_code", "code_verifier": verifier})
        data = check("Google", *request("POST", self.TOKEN, headers, body)[::2])
        if not data.get("refresh_token"):
            raise PublishError("Google didn't return a refresh token; remove the app's access at myaccount.google.com/permissions and connect again")
        return {"access_token": data["access_token"], "refresh_token": data["refresh_token"], "expires_at": expires_at(data.get("expires_in")),
                "scope": data.get("scope", "")}

    def refresh(self, root, tokens):
        if tokens.get("access_token") and tokens.get("expires_at", 0) > time.time():
            return tokens
        headers, body = form({"client_id": tts.secret(root, "GOOGLE_OAUTH_CLIENT_ID"), "client_secret": tts.secret(root, "GOOGLE_OAUTH_CLIENT_SECRET"),
                              "refresh_token": tokens.get("refresh_token", ""), "grant_type": "refresh_token"})
        data = check("Google", *request("POST", self.TOKEN, headers, body)[::2])
        return tokens | {"access_token": data["access_token"], "expires_at": expires_at(data.get("expires_in"))}

    def auth(self, tokens):
        return {"Authorization": f"Bearer {tokens['access_token']}"}

    def account(self, root, tokens):
        data = check("YouTube", *request("GET", f"{self.API}/channels?part=snippet&mine=true", self.auth(tokens))[::2])
        items = data.get("items") or []
        if not items:
            raise PublishError("This Google account has no YouTube channel yet; create one at youtube.com first")
        snippet = items[0].get("snippet", {})
        handle = snippet.get("customUrl", "")
        return {"id": items[0]["id"], "name": snippet.get("title", ""), "handle": handle,
                "url": f"https://www.youtube.com/{handle}" if handle else f"https://www.youtube.com/channel/{items[0]['id']}"}

    def revoke(self, root, tokens):
        if tokens.get("refresh_token"):
            request("POST", "https://oauth2.googleapis.com/revoke?" + urllib.parse.urlencode({"token": tokens["refresh_token"]}), *form({}))

    def metadata(self, meta: dict) -> dict:
        snippet = {"title": meta["title"][:100], "description": meta["description"][:5000], "categoryId": meta.get("category") or "27"}
        if meta.get("tags"):
            snippet["tags"] = meta["tags"]
        if meta.get("language"):
            snippet["defaultLanguage"] = snippet["defaultAudioLanguage"] = meta["language"]
        status = {"privacyStatus": meta.get("privacy") or self.default_privacy, "selfDeclaredMadeForKids": bool(meta.get("made_for_kids")),
                  "containsSyntheticMedia": bool(meta.get("synthetic")), "embeddable": True}
        if meta.get("publish_at"):
            status["privacyStatus"], status["publishAt"] = "private", meta["publish_at"]  # YouTube makes it public then
        return {"snippet": snippet, "status": status}

    def publish(self, root, tokens, account, video, meta, extras, state, progress):
        size = video.stat().st_size
        session = state.get("session") if state.get("session_size") == size and state.get("session_file") == str(video) else None
        offset = 0
        if session:  # ask how far the last attempt got
            status, headers, body = request("PUT", session, self.auth(tokens) | {"Content-Range": f"bytes */{size}", "Content-Length": "0"}, b"")
            if status in (200, 201):
                return self.finish(root, tokens, as_json(body), meta, extras, state)
            if status == 308:
                confirmed = re.match(r"bytes=0-(\d+)", headers.get("range", ""))
                offset = int(confirmed.group(1)) + 1 if confirmed else 0
            else:
                session = None  # expired (a session lasts about a week) or gone: start over
        if not session:
            url = f"{self.UPLOAD}/videos?uploadType=resumable&part=snippet,status"
            status, headers, body = request("POST", url, self.auth(tokens) | {"X-Upload-Content-Length": str(size), "X-Upload-Content-Type": "video/mp4"},
                                            self.metadata(meta))
            check("YouTube", status, body)
            session = headers.get("location", "")
            if not session.startswith(f"{self.UPLOAD}/videos"):
                raise PublishError("YouTube didn't return an upload session")
            state.update(session=session, session_size=size, session_file=str(video), session_started=now_iso())
            state["save"]()
        with video.open("rb") as handle:
            while True:
                handle.seek(offset)
                chunk = handle.read(CHUNK)
                end = offset + len(chunk) - 1
                status, headers, body = request("PUT", session, self.auth(tokens) | {"Content-Length": str(len(chunk)),
                                                "Content-Range": f"bytes {offset}-{end}/{size}", "Content-Type": "video/mp4"}, chunk, timeout=600)
                if status in (200, 201):
                    progress(size, size)
                    return self.finish(root, tokens, as_json(body), meta, extras, state)
                if status != 308:
                    check("YouTube", status, body)
                confirmed = re.match(r"bytes=0-(\d+)", headers.get("range", ""))
                offset = int(confirmed.group(1)) + 1 if confirmed else 0
                progress(offset, size)

    def finish(self, root, tokens, video, meta, extras, state):
        video_id = video.get("id")
        if not video_id:
            raise PublishError("YouTube finished the upload but returned no video id")
        state.pop("session", None)
        notes = []
        if extras.get("thumbnail") and Path(extras["thumbnail"]).is_file():
            status, _, body = request("POST", f"{self.UPLOAD}/thumbnails/set?videoId={video_id}", self.auth(tokens) | {"Content-Type": "image/jpeg"},
                                      Path(extras["thumbnail"]).read_bytes())
            if status not in (200, 201):
                notes.append("Thumbnail not set (custom thumbnails need a verified channel): " + explain("YouTube", status, body))
        if extras.get("captions") and self.CAPTION_SCOPE in tokens.get("scope", ""):
            boundary = "vidstudio" + random.token_hex(8)
            snippet = json.dumps({"snippet": {"videoId": video_id, "language": meta.get("language") or "en", "name": "", "isDraft": False}})
            body = (f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{snippet}\r\n"
                    f"--{boundary}\r\nContent-Type: application/x-subrip\r\n\r\n{extras['captions']}\r\n--{boundary}--\r\n").encode()
            status, _, reply = request("POST", f"{self.UPLOAD}/captions?uploadType=multipart&part=snippet",
                                       self.auth(tokens) | {"Content-Type": f"multipart/related; boundary={boundary}"}, body)
            if status not in (200, 201):
                notes.append("Captions not uploaded: " + explain("YouTube", status, reply))
        elif extras.get("captions"):
            notes.append("Captions not uploaded: reconnect with captions allowed to upload them")
        short = extras.get("vertical") and extras.get("duration", 999) <= 180
        url = f"https://www.youtube.com/shorts/{video_id}" if short else f"https://youtu.be/{video_id}"
        return {"id": video_id, "url": url, "status": "scheduled" if meta.get("publish_at") else "published", "notes": notes,
                "privacy": video.get("status", {}).get("privacyStatus") or meta.get("privacy")}

    def stats(self, root, tokens, remote_id):
        data = check("YouTube", *request("GET", f"{self.API}/videos?part=statistics,status&id={urllib.parse.quote(remote_id)}", self.auth(tokens))[::2])
        items = data.get("items") or []
        if not items:
            return {"missing": True}
        counts = items[0].get("statistics", {})
        return {"views": int(counts.get("viewCount", 0)), "likes": int(counts.get("likeCount", 0)), "comments": int(counts.get("commentCount", 0)),
                "privacy": items[0].get("status", {}).get("privacyStatus", "")}


class Instagram(Platform):
    id, name = "instagram", "Instagram"
    token_help = ("In your Meta app (developers.facebook.com → your app → Instagram → API setup with Instagram login), add the account "
                  "as a tester, click Generate token, and paste it here. It needs instagram_business_basic and "
                  "instagram_business_content_publish, and the account must be a professional (Business or Creator) account.")
    app_url = "https://developers.facebook.com/apps/"
    privacy_options = [("public", "Public (Instagram has no private posts)")]
    default_privacy = "public"
    BASE = f"https://graph.instagram.com/{IG_VERSION}"

    def from_token(self, root, token):
        token = token.strip()
        if not re.fullmatch(r"[A-Za-z0-9_\-.|]{20,1000}", token):
            raise PublishError("That doesn't look like an Instagram access token")
        return self.refresh(root, {"access_token": token, "refreshed": 0})

    def refresh(self, root, tokens):
        # Long-lived tokens last 60 days; refreshing (allowed once a token is a day old) restarts the clock.
        if time.time() - tokens.get("refreshed", 0) < 86400 * 7:
            return tokens
        status, _, body = request("GET", "https://graph.instagram.com/refresh_access_token?" + urllib.parse.urlencode(
            {"grant_type": "ig_refresh_token", "access_token": tokens["access_token"]}))
        if status == 200 and as_json(body).get("access_token"):
            return tokens | {"access_token": as_json(body)["access_token"], "refreshed": time.time()}
        if status in (400, 401) and b"expired" in body.lower():
            raise Reconnect("The Instagram token has expired; generate a new one and connect again")
        return tokens | {"refreshed": time.time() - 86400 * 6}  # a fresh short token can't refresh yet; try again tomorrow

    def get(self, path, tokens, **params):
        return check("Instagram", *request("GET", f"{self.BASE}/{path}?" + urllib.parse.urlencode(params | {"access_token": tokens["access_token"]}))[::2])

    def account(self, root, tokens):
        data = self.get("me", tokens, fields="user_id,username,account_type")
        if data.get("account_type") not in (None, "BUSINESS", "MEDIA_CREATOR", "CREATOR"):
            raise PublishError("Publishing needs a professional (Business or Creator) Instagram account")
        return {"id": str(data.get("user_id") or data.get("id")), "name": "@" + data.get("username", ""), "handle": data.get("username", ""),
                "url": f"https://www.instagram.com/{data.get('username', '')}/"}

    def publish(self, root, tokens, account, video, meta, extras, state, progress):
        auth = {"access_token": tokens["access_token"]}
        container = state.get("container")
        if not container:
            fields = {"media_type": "REELS", "upload_type": "resumable", "caption": meta["caption"][:2200],
                      "share_to_feed": "true", "thumb_offset": str(int(extras.get("cover_ms", 1600)))}
            headers, body = form(fields | auth)
            created = check("Instagram", *request("POST", f"{self.BASE}/{account['id']}/media", headers, body)[::2])
            container = created.get("id")
            if not container:
                raise PublishError("Instagram didn't create a media container")
            state.update(container=container, uploaded=False)
            state["save"]()
        if not state.get("uploaded"):
            size = video.stat().st_size
            status, _, body = request("POST", f"https://rupload.facebook.com/ig-api-upload/{IG_VERSION}/{container}",
                                      {"Authorization": f"OAuth {tokens['access_token']}", "offset": "0", "file_size": str(size),
                                       "Content-Type": "application/octet-stream"}, video.read_bytes(), timeout=900)
            check("Instagram", status, body)
            state["uploaded"] = True
            state["save"]()
            progress(size, size)
        for _ in range(120):  # Instagram processes the video before it can be published: up to ten minutes
            info = self.get(container, tokens, fields="status_code,status")
            code = info.get("status_code")
            if code == "FINISHED":
                break
            if code in ("ERROR", "EXPIRED"):
                state.pop("container", None)
                raise PublishError(f"Instagram couldn't process the video: {info.get('status') or code}")
            time.sleep(state.get("poll", 5))
        else:
            raise PublishError("Instagram is still processing the video; publish again in a few minutes to finish")
        headers, body = form({"creation_id": container} | auth)
        published = check("Instagram", *request("POST", f"{self.BASE}/{account['id']}/media_publish", headers, body)[::2])
        media_id = published.get("id")
        state.pop("container", None)
        link = self.get(media_id, tokens, fields="permalink").get("permalink") or account.get("url", "")
        return {"id": media_id, "url": link, "status": "published", "notes": []}

    def stats(self, root, tokens, remote_id):
        data = self.get(remote_id, tokens, fields="like_count,comments_count")
        return {"likes": int(data.get("like_count", 0)), "comments": int(data.get("comments_count", 0))}


class TikTok(Platform):
    id, name, oauth = "tiktok", "TikTok", True
    app_keys = [("TIKTOK_CLIENT_KEY", "client key"), ("TIKTOK_CLIENT_SECRET", "client secret")]
    app_url = "https://developers.tiktok.com/apps/"
    token_help = "Or paste a user access token with the video.publish (and video.upload) scopes from your TikTok app."
    privacy_options = [("draft", "Draft in the TikTok app (you finish posting there)"), ("SELF_ONLY", "Only me"),
                       ("MUTUAL_FOLLOW_FRIENDS", "Friends"), ("FOLLOWER_OF_CREATOR", "Followers"), ("PUBLIC_TO_EVERYONE", "Everyone")]
    default_privacy = "draft"
    BASE = "https://open.tiktokapis.com/v2"

    def auth_url(self, root, redirect, state, challenge, captions: bool = False):
        params = {"client_key": tts.secret(root, "TIKTOK_CLIENT_KEY"), "scope": "user.info.basic,video.publish,video.upload",
                  "response_type": "code", "redirect_uri": redirect, "state": state,
                  "code_challenge": challenge[1], "code_challenge_method": "S256"}  # TikTok's desktop PKCE: hex SHA-256
        return "https://www.tiktok.com/v2/auth/authorize/?" + urllib.parse.urlencode(params)

    def token_call(self, root, fields):
        headers, body = form({"client_key": tts.secret(root, "TIKTOK_CLIENT_KEY"), "client_secret": tts.secret(root, "TIKTOK_CLIENT_SECRET")} | fields)
        data = check("TikTok", *request("POST", f"{self.BASE}/oauth/token/", headers, body)[::2])
        if data.get("error") or not data.get("access_token"):
            raise Reconnect(f"TikTok refused the sign-in: {data.get('error_description') or data.get('error') or 'no token'}")
        return {"access_token": data["access_token"], "refresh_token": data.get("refresh_token", ""), "expires_at": expires_at(data.get("expires_in")),
                "scope": data.get("scope", "")}

    def exchange(self, root, code, redirect, verifier):
        return self.token_call(root, {"code": code, "grant_type": "authorization_code", "redirect_uri": redirect, "code_verifier": verifier})

    def from_token(self, root, token):
        token = token.strip()
        if not re.fullmatch(r"[A-Za-z0-9_\-.!*]{20,1000}", token):
            raise PublishError("That doesn't look like a TikTok access token")
        return {"access_token": token, "refresh_token": "", "expires_at": time.time() + 86400 - 60}

    def refresh(self, root, tokens):
        if tokens.get("expires_at", 0) > time.time():
            return tokens
        if not tokens.get("refresh_token") or self.app_problem(root):
            raise Reconnect("The TikTok token has expired; connect again")
        return tokens | self.token_call(root, {"grant_type": "refresh_token", "refresh_token": tokens["refresh_token"]})

    def call(self, method, path, tokens, body=None):
        status, _, reply = request(method, f"{self.BASE}/{path}", {"Authorization": f"Bearer {tokens['access_token']}"}, body)
        data = check("TikTok", status, reply)
        error = data.get("error") or {}
        if isinstance(error, dict) and error.get("code") not in (None, "", "ok"):
            if error.get("code") in ("access_token_invalid", "scope_not_authorized"):
                raise Reconnect(f"TikTok: {error.get('message') or error['code']}. Connect again.")
            raise PublishError(f"TikTok: {error.get('message') or error.get('code')}")
        return data.get("data") or {}

    def account(self, root, tokens):
        user = self.call("GET", "user/info/?fields=open_id,display_name,username", tokens).get("user", {})
        handle = user.get("username", "")
        return {"id": user.get("open_id", ""), "name": user.get("display_name") or handle, "handle": handle,
                "url": f"https://www.tiktok.com/@{handle}" if handle else ""}

    def revoke(self, root, tokens):
        if not self.app_problem(root):
            request("POST", f"{self.BASE}/oauth/revoke/", *form({"client_key": tts.secret(root, "TIKTOK_CLIENT_KEY"),
                                                                 "client_secret": tts.secret(root, "TIKTOK_CLIENT_SECRET"), "token": tokens.get("access_token", "")}))

    def publish(self, root, tokens, account, video, meta, extras, state, progress):
        size = video.stat().st_size
        privacy = meta.get("privacy") or self.default_privacy
        # Up to 64 MB goes in one chunk; above that, 10 MB chunks with the remainder folded into the last one.
        chunk = size if size <= 64 * 1024 * 1024 else 10 * 1024 * 1024
        count = max(1, size // chunk)
        source = {"source": "FILE_UPLOAD", "video_size": size, "chunk_size": chunk, "total_chunk_count": count}
        if privacy == "draft":
            init = self.call("POST", "post/publish/inbox/video/init/", tokens, {"source_info": source})
        else:
            creator = self.call("POST", "post/publish/creator_info/query/", tokens, {})
            allowed = creator.get("privacy_level_options") or []
            if allowed and privacy not in allowed:
                raise PublishError(f"TikTok allows only {', '.join(allowed)} for this account"
                                   + (" (apps TikTok hasn't audited can only post privately)" if allowed == ["SELF_ONLY"] else ""))
            post = {"title": meta["caption"][:2200], "privacy_level": privacy, "disable_comment": False, "disable_duet": False,
                    "disable_stitch": False, "video_cover_timestamp_ms": int(extras.get("cover_ms", 1600)), "is_aigc": bool(meta.get("synthetic"))}
            init = self.call("POST", "post/publish/video/init/", tokens, {"post_info": post, "source_info": source})
        publish_id, upload = init.get("publish_id"), init.get("upload_url", "")
        if not publish_id or not upload.startswith("https://"):
            raise PublishError("TikTok didn't return an upload address")
        with video.open("rb") as handle:
            for i in range(count):
                start = i * chunk
                data = handle.read(chunk if i < count - 1 else size - start)
                end = start + len(data) - 1
                status, _, body = request("PUT", upload, {"Content-Type": "video/mp4", "Content-Length": str(len(data)),
                                                          "Content-Range": f"bytes {start}-{end}/{size}"}, data, timeout=600)
                if status not in (200, 201, 206):
                    raise PublishError(explain("TikTok", status, body))
                progress(end + 1, size)
        for _ in range(120):
            info = self.call("POST", "post/publish/status/fetch/", tokens, {"publish_id": publish_id})
            stage = info.get("status")
            if stage == "PUBLISH_COMPLETE" or (privacy == "draft" and stage in ("SEND_TO_USER_INBOX", "PUBLISH_COMPLETE")):
                posted = (info.get("publicaly_available_post_id") or info.get("publicly_available_post_id") or [None])[0]
                url = f"https://www.tiktok.com/@{account.get('handle')}/video/{posted}" if posted and account.get("handle") else account.get("url", "")
                return {"id": str(posted or publish_id), "url": url, "status": "draft" if privacy == "draft" else "published",
                        "notes": ["Sent to your TikTok inbox: open the TikTok app to finish posting"] if privacy == "draft" else []}
            if stage == "FAILED":
                raise PublishError(f"TikTok couldn't publish the video: {info.get('fail_reason') or 'unknown reason'}")
            time.sleep(state.get("poll", 5))
        raise PublishError("TikTok is still processing the video; check the TikTok app")


PLATFORMS: dict[str, Platform] = {p.id: p for p in (YouTube(), Instagram(), TikTok())}


def platform(platform_id: str) -> Platform:
    if platform_id not in PLATFORMS:
        raise KeyError(f"Unknown platform {platform_id!r}. Platforms: {', '.join(PLATFORMS)}")
    return PLATFORMS[platform_id]


def guess_platform(text: str) -> str:
    low = (text or "").casefold()
    return "youtube" if "youtube" in low else "instagram" if "instagram" in low or "reel" in low else "tiktok" if "tiktok" in low else ""


# ---------------------------------------------------------------- what gets posted

DEFAULT_META = {"title": "", "description": "", "caption": "", "tags": [], "hashtags": [], "privacy": "", "publish_at": "",
                "made_for_kids": False, "synthetic": False, "category": "27", "captions": True, "thumbnail": True}


def clean_meta(meta: dict, limit: int = 2200) -> dict:
    if not isinstance(meta, dict):
        raise ValueError("publish details must be a JSON object")
    unknown = set(meta) - set(DEFAULT_META)
    if unknown:
        raise ValueError(f"Unknown publish key: {', '.join(sorted(unknown))}. Allowed: {', '.join(sorted(DEFAULT_META))}")
    result = json.loads(json.dumps(DEFAULT_META)) | meta
    for key, most in (("title", 100), ("description", 5000), ("caption", limit), ("privacy", 40), ("category", 4)):
        if not isinstance(result[key], str) or len(result[key].strip()) > most:
            raise ValueError(f"publish.{key} must be text of at most {most} characters")
        result[key] = result[key].strip()
    if re.search(r"[<>]", result["title"]):
        raise ValueError("publish.title can't contain < or > (YouTube rejects them)")
    for key in ("tags", "hashtags"):
        if not isinstance(result[key], list) or len(result[key]) > 60 or not all(isinstance(t, str) and 0 < len(t.strip()) <= 100 for t in result[key]):
            raise ValueError(f"publish.{key} must be a list of short strings")
        result[key] = [t.strip().lstrip("#") if key == "hashtags" else t.strip() for t in result[key]]
    if sum(len(t) + 1 for t in result["tags"]) > 500:
        raise ValueError("publish.tags add up to more than YouTube's 500 characters")
    if result["publish_at"]:
        try:
            when = dt.datetime.fromisoformat(result["publish_at"].replace("Z", "+00:00"))
        except ValueError:
            raise ValueError("publish.publish_at must be a date and time like 2026-10-20T18:30:00+05:30")
        if when.tzinfo is None:
            when = when.astimezone()
        result["publish_at"] = when.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if not re.fullmatch(r"\d{1,3}", result["category"]):
        raise ValueError("publish.category must be a YouTube category number (27 is Education, 25 News & Politics)")
    for key in ("made_for_kids", "synthetic", "captions", "thumbnail"):
        if not isinstance(result[key], bool):
            raise ValueError(f"publish.{key} must be true or false")
    return result


def with_credits(text: str, credits: list[str], sources: list[str], hashtags: list[str], limit: int) -> str:
    """The text as posted: the user's words, then sources and photo credits (CC BY requires them), then hashtags."""
    parts = [text.strip()]
    missing_sources = [s for s in sources if s not in text]
    if missing_sources:
        parts.append("Sources:\n" + "\n".join(missing_sources))
    missing_credits = [c for c in credits if c not in text]
    if missing_credits:
        parts.append("\n".join(missing_credits))
    tags = " ".join("#" + re.sub(r"\s+", "", h) for h in hashtags if ("#" + re.sub(r"\s+", "", h)) not in text)
    if tags:
        parts.append(tags)
    out = "\n\n".join(p for p in parts if p)
    return out if len(out) <= limit else out[: limit - 1].rstrip() + "…"

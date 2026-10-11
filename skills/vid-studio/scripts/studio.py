#!/usr/bin/env python3
"""Vid Studio helper: one channel's topics, sources, findings, scripts, and the local web UI.

Standard library only. The workspace is --workspace, else $VID_STUDIO_HOME, else ~/vid-studio.
Every command prints what it did so the calling agent can continue from the output.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
ASSETS = SKILL_DIR / "assets"
USER_AGENT = "Mozilla/5.0 (compatible; vid-studio/1.0)"
FEED_PATHS = ["/feed", "/rss", "/feed.xml", "/rss.xml", "/atom.xml", "/index.xml", "/feeds/posts/default"]
FIRST_RUN_LOOKBACK = dt.timedelta(days=7)
RUN_OVERLAP = dt.timedelta(hours=6)
MAX_FINDING_TITLE = 110
MAX_FINDING_SUMMARY = 240
SCRIPT_TEXTS = {"script": "script.md", "post": "post.md", "notes": "notes.md"}


# ---------------------------------------------------------------- basics

def now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def parse_time(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value)
    return parsed if parsed.tzinfo else parsed.astimezone()


def workspace_path(value: str | None) -> Path:
    return Path(value or os.environ.get("VID_STUDIO_HOME") or "~/vid-studio").expanduser().resolve()


def load(path: Path, default=None):
    if not path.exists():
        if default is not None:
            return default
        raise SystemExit(f"Missing {path}. Run: studio.py init")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise SystemExit(f"Invalid JSON in {path}: {error}")


def save(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def write_text(path: Path, text: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def slugify(text: str, limit: int = 48) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:limit].rstrip("-") or "item"


def unique_id(base: str, existing) -> str:
    candidate, counter = base, 2
    while candidate in existing:
        candidate, counter = f"{base}-{counter}", counter + 1
    return candidate


def domain(url: str) -> str:
    host = urllib.parse.urlsplit(url).hostname or ""
    return host[4:] if host.startswith("www.") else host


def clean_text(value: str, limit: int | None = None) -> str:
    text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value or ""))).strip()
    return text if limit is None or len(text) <= limit else text[: limit - 1].rstrip() + "…"


def fetch(url: str, timeout: int = 25) -> tuple[bytes, str, str]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read(), response.headers.get("Content-Type", "") or "", response.geturl()


def decode(data: bytes, content_type: str) -> str:
    match = re.search(r"charset=([\w-]+)", content_type)
    try:
        return data.decode(match.group(1) if match else "utf-8", errors="replace")
    except LookupError:
        return data.decode("utf-8", errors="replace")


def normalize_url(value: str) -> str:
    original = value = (value or "").strip()
    if re.match(r"[a-zA-Z][\w+.-]*:(?!\d)", value) and not re.match(r"https?://", value, re.I):
        raise ValueError(f"Not a web address: {original!r}")  # javascript:, mailto:, file: …
    if value and "://" not in value:
        value = "https://" + value
    parts = urllib.parse.urlsplit(value)
    try:
        parts.port
    except ValueError:
        raise ValueError(f"Not a web address: {original!r}")
    host = parts.hostname or ""
    if parts.scheme not in ("http", "https") or not ("." in host or host == "localhost"):
        raise ValueError(f"Not a web address: {original!r}")
    return value


# ---------------------------------------------------------------- feeds

def local_name(tag) -> str:
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def child_text(element, *names: str) -> str:
    for child in element:
        if local_name(child.tag) in names and (child.text or "").strip():
            return child.text.strip()
    return ""


def parse_feed(data: bytes) -> list[dict]:
    """Parse RSS, Atom, Google Alerts, Google News, and Google Trends feeds."""
    root = ET.fromstring(data)
    if local_name(root.tag) not in ("rss", "feed", "RDF"):
        raise ValueError("Not an RSS or Atom feed")
    items = []
    for element in root.iter():
        if local_name(element.tag) not in ("item", "entry"):
            continue
        link = ""
        for child in element:
            if local_name(child.tag) == "link":
                candidate = child.get("href") or (child.text or "").strip()
                if candidate and child.get("rel") in (None, "alternate"):
                    link = candidate
                    break
                link = link or candidate
        # Google Trends items link to the feed itself; the real story is in news_item_url.
        news_urls = [
            (grandchild.text or "").strip()
            for child in element if local_name(child.tag) == "news_item"
            for grandchild in child if local_name(grandchild.tag) == "news_item_url"
        ]
        if "trends.google." in link and news_urls:
            link = news_urls[0]
        # Google Alerts wraps targets in a google.com/url?url= redirect.
        parsed = urllib.parse.urlsplit(link)
        if parsed.netloc.endswith("google.com") and parsed.path == "/url":
            link = urllib.parse.parse_qs(parsed.query).get("url", [link])[0]
        title = clean_text(child_text(element, "title")) or "(untitled)"
        summary = clean_text(child_text(element, "description", "summary", "content"), 280)
        if summary and re.sub(r"\W+", "", summary.lower()).startswith(re.sub(r"\W+", "", title.lower())[:40]):
            summary = ""
        traffic = child_text(element, "approx_traffic")
        if traffic:
            summary = f"Searches: {traffic}. {summary}".strip()
        items.append({
            "title": title,
            "url": link,
            "published": child_text(element, "pubDate", "published", "updated", "date"),
            "summary": summary,
        })
    return items


def url_key(url: str) -> str:
    if not url:
        return ""
    parts = urllib.parse.urlsplit(url)
    query = [(k, v) for k, v in urllib.parse.parse_qsl(parts.query) if not re.match(r"utm_|fbclid|gclid|ref$", k)]
    return "u:" + urllib.parse.urlunsplit((parts.scheme, parts.netloc.lower(), parts.path.rstrip("/"), urllib.parse.urlencode(query), ""))


def title_key(title: str) -> str:
    # Google News appends " - Publisher"; drop it so the same headline dedupes across feeds.
    normalized = re.sub(r"[^\w]+", " ", re.sub(r"\s+-\s+[^-]+$", "", title).lower()).strip()
    return "t:" + normalized if len(normalized) > 12 else ""


class LinkFinder(HTMLParser):
    def __init__(self):
        super().__init__()
        self.feeds, self.hints = [], []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        href = attributes.get("href") or ""
        kind = (attributes.get("type") or "").lower()
        if tag == "link" and "alternate" in (attributes.get("rel") or "").lower() and ("rss" in kind or "atom" in kind):
            if href:
                self.feeds.append(href)
        elif tag == "a" and re.search(r"rss|atom|feed", href, re.I):
            self.hints.append(href)


def try_feed(url: str) -> bool:
    try:
        return bool(parse_feed(fetch(url)[0]))
    except Exception:
        return False


def discover_feed(url: str) -> tuple[str | None, str]:
    """Return (feed URL, explanation). Without a feed, the explanation tells the agent what to try next."""
    try:
        data, content_type, final_url = fetch(url)
    except Exception as error:
        return None, (f"page could not be fetched ({type(error).__name__}: {error}); "
                      "search for the site's RSS feed and rerun with --feed, or keep it as a manual page")
    try:
        if parse_feed(data):
            return url, "the URL is itself a feed"
    except Exception:
        pass
    finder = LinkFinder()
    finder.feed(decode(data, content_type))
    candidates = [urllib.parse.urljoin(final_url, href) for href in finder.feeds + finder.hints]
    parts = urllib.parse.urlsplit(final_url)
    candidates += [f"{parts.scheme}://{parts.netloc}{path}" for path in FEED_PATHS]
    for candidate in list(dict.fromkeys(candidates))[:15]:
        if try_feed(candidate):
            return candidate, f"feed found: {candidate}"
    hints = list(dict.fromkeys(urllib.parse.urljoin(final_url, h) for h in finder.hints))[:5]
    if hints:
        return None, ("no feed found; these links may list feeds, open them and rerun with --feed: " + ", ".join(hints))
    return None, "no feed found; the agent checks this page during scans"


# ---------------------------------------------------------------- studio model (shared by CLI and web UI)

SETTING_KEYS = {"name", "description", "audience", "language", "timezone", "research_notes",
                "script_format", "post_format", "schedule"}


class Studio:
    """All reads and writes of the workspace files. Raises ValueError for bad input."""

    def __init__(self, ws: Path, root: Path | None = None):
        self.ws = ws  # this channel's folder
        self.root = root or ws.parent.parent

    def path(self, *parts: str) -> Path:
        return self.ws.joinpath(*parts)

    # settings

    def settings(self) -> dict:
        return load(self.path("studio.json"))

    def update_settings(self, changes: dict) -> dict:
        settings = self.settings()
        for key, value in changes.items():
            if key not in SETTING_KEYS:
                raise ValueError(f"Unknown setting: {key}")
            if key == "schedule":
                times = sorted({str(t).strip() for t in (value or {}).get("times", []) if str(t).strip()})
                for t in times:
                    if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", t):
                        raise ValueError(f"Times must look like 07:30, not {t!r}")
                value = {**settings.get("schedule", {}), "times": times}
            elif not isinstance(value, str):
                raise ValueError(f"{key} must be text")
            settings[key] = value
        if not settings.get("name", "").strip():
            raise ValueError("The channel needs a name")
        save(self.path("studio.json"), settings)
        return settings

    # topics

    def topics(self) -> list[dict]:
        return load(self.path("topics.json"))["topics"]

    def add_topic(self, name: str, description: str = "") -> dict:
        name, data = (name or "").strip(), load(self.path("topics.json"))
        if not name:
            raise ValueError("A topic needs a name")
        if any(t["name"].lower() == name.lower() for t in data["topics"]):
            raise ValueError(f"Topic already exists: {name}")
        topic = {"id": unique_id(slugify(name, 40), {t["id"] for t in data["topics"]}),
                 "name": name, "description": (description or "").strip(), "created": now()}
        data["topics"].append(topic)
        save(self.path("topics.json"), data)
        return topic

    def update_topic(self, topic_id: str, changes: dict) -> dict:
        data = load(self.path("topics.json"))
        topic = self._find(data["topics"], topic_id, "topic")
        if "name" in changes:
            name = str(changes["name"]).strip()
            if not name:
                raise ValueError("A topic needs a name")
            if any(t["name"].lower() == name.lower() and t["id"] != topic_id for t in data["topics"]):
                raise ValueError(f"Topic already exists: {name}")
            topic["name"] = name
        if "description" in changes:
            topic["description"] = str(changes["description"]).strip()
        save(self.path("topics.json"), data)
        return topic

    def delete_topic(self, topic_id: str) -> None:
        data = load(self.path("topics.json"))
        self._find(data["topics"], topic_id, "topic")
        data["topics"] = [t for t in data["topics"] if t["id"] != topic_id]
        save(self.path("topics.json"), data)
        findings = load(self.path("findings.json"))
        for finding in findings["findings"]:
            finding["topics"] = [t for t in finding.get("topics", []) if t != topic_id]
        save(self.path("findings.json"), findings)
        for script_id in self.script_ids():
            meta_path = self.path("scripts", script_id, "script.json")
            meta = load(meta_path)
            if topic_id in meta.get("topics", []):
                meta["topics"] = [t for t in meta["topics"] if t != topic_id]
                save(meta_path, meta)

    # sources: "approved" ones are checked on every run; "suggested" ones wait for the user

    def sources(self) -> list[dict]:
        return [s | {"status": s.get("status", "approved")} for s in load(self.path("sources.json"))["sources"]]

    def approved_sources(self) -> list[dict]:
        return [s for s in self.sources() if s["status"] == "approved"]

    def add_source(self, url: str, note: str = "", suggested_reason: str | None = None, run_id: str | None = None) -> dict:
        url, data = normalize_url(url), load(self.path("sources.json"))
        for existing in data["sources"]:
            if url_key(existing["url"]) == url_key(url):
                state = existing.get("status", "approved")
                if suggested_reason is not None:
                    raise ValueError(f"Already {'dismissed by the user' if state == 'dismissed' else state}: {url}")
                if state == "approved":
                    raise ValueError(f"Already a source: {url}")
                existing.update(status="approved", note=(note or existing.get("note", "")).strip())  # user adds a suggested/dismissed one
                save(self.path("sources.json"), data)
                return existing
        source = {"id": unique_id(slugify(domain(url) + urllib.parse.urlsplit(url).path, 40), {s["id"] for s in data["sources"]}),
                  "url": url, "note": (note or "").strip(), "status": "approved", "feed": None, "feed_checked": False,
                  "created": now()}
        if suggested_reason is not None:
            if not suggested_reason.strip():
                raise ValueError("A suggested source needs a reason")
            source.update(status="suggested", reason=suggested_reason.strip(), suggested_by=run_id)
        data["sources"].append(source)
        save(self.path("sources.json"), data)
        return source

    def update_source(self, source_id: str, changes: dict) -> dict:
        data = load(self.path("sources.json"))
        source = self._find(data["sources"], source_id, "source")
        if "note" in changes:
            source["note"] = str(changes["note"]).strip()
        if "status" in changes:
            if changes["status"] not in ("approved", "dismissed"):
                raise ValueError("Status must be approved or dismissed")
            source["status"] = changes["status"]
            source["decided"] = now()
        save(self.path("sources.json"), data)
        return source

    def delete_source(self, source_id: str) -> None:
        data = load(self.path("sources.json"))
        self._find(data["sources"], source_id, "source")
        data["sources"] = [s for s in data["sources"] if s["id"] != source_id]
        save(self.path("sources.json"), data)

    def source_for_url(self, url: str) -> dict | None:
        """The approved source a page belongs to: same site, and inside the source's path if it has one."""
        parts = urllib.parse.urlsplit(url)
        for source in self.approved_sources():
            base = urllib.parse.urlsplit(source["url"])
            if domain(url) == domain(source["url"]) and parts.path.startswith(base.path.rstrip("/")):
                return source
        return None

    # research runs and findings

    def findings(self) -> list[dict]:
        return sorted(load(self.path("findings.json"))["findings"], key=lambda f: f.get("found_at", ""), reverse=True)

    def runs(self) -> list[dict]:
        return load(self.path("runs.json"))["runs"]

    def research_since(self) -> dt.datetime:
        completed = [r for r in self.runs() if r.get("status") == "completed"]
        if not completed:
            return dt.datetime.now().astimezone() - FIRST_RUN_LOOKBACK
        return parse_time(completed[-1]["started"]) - RUN_OVERLAP

    def start_run(self, trigger: str = "manual") -> tuple[dict, dt.datetime, list[str]]:
        since = self.research_since()
        data = load(self.path("runs.json"))
        abandoned = []
        for run in data["runs"]:
            if run.get("status") == "running":
                run.update(status="abandoned", finished=now())
                abandoned.append(run["id"])
        run = {"id": unique_id("run-" + dt.datetime.now().strftime("%Y%m%d-%H%M"), {r["id"] for r in data["runs"]}),
               "trigger": trigger, "status": "running", "started": now(), "since": since.isoformat(timespec="seconds"),
               "sources": [s["id"] for s in self.approved_sources()], "checked": {}}
        data["runs"].append(run)
        save(self.path("runs.json"), data)
        return run, since, abandoned

    def mark_checked(self, run_id: str, source_ids: list[str], note: str = "") -> dict:
        data = load(self.path("runs.json"))
        run = self._find(data["runs"], run_id, "run")
        if run.get("status") != "running":
            raise ValueError(f"Run {run_id} is not running")
        for source_id in source_ids:
            if source_id not in run.get("sources", []):
                raise KeyError(f"Source {source_id} is not part of run {run_id}")
            run.setdefault("checked", {})[source_id] = {"at": now(), "note": note}
        save(self.path("runs.json"), data)
        return run

    def unchecked_sources(self, run: dict) -> list[str]:
        return [s for s in run.get("sources", []) if s not in run.get("checked", {})]

    def finish_run(self, run_id: str, failed: str | None = None, note: str = "") -> dict:
        data = load(self.path("runs.json"))
        run = self._find(data["runs"], run_id, "run")
        missing = self.unchecked_sources(run)
        if missing and not failed:
            raise ValueError("Check every source before finishing. Not checked yet: " + ", ".join(missing)
                             + ". Mark each with `studio.py checked --run RUN --source ID --note \"…\"` (note why if a site was unreachable).")
        run.update(status="failed" if failed else "completed", finished=now(),
                   findings=sum(1 for f in self.findings() if run_id in f.get("runs", [])),
                   suggested_sources=sum(1 for s in self.sources() if s.get("suggested_by") == run_id),
                   note=failed or note or "")
        save(self.path("runs.json"), data)
        return run

    def add_findings(self, run_id: str, items: list) -> tuple[list[str], list[str]]:
        self._find(self.runs(), run_id, "run")
        topics = self.topics()
        by_name = {t["name"].lower(): t["id"] for t in topics} | {t["id"]: t["id"] for t in topics}
        data = load(self.path("findings.json"))
        owner = {url_key(s["url"]): f for f in data["findings"] for s in f.get("sources", [])}
        added, merged = [], []
        if not isinstance(items, list):
            raise ValueError("Expected a JSON list of findings")
        for number, item in enumerate(items, 1):
            label = f"Finding {number}"
            if not isinstance(item, dict) or not str(item.get("title", "")).strip():
                raise ValueError(f"{label}: needs a title")
            # Findings are scanned in a feed: keep them short. Depth belongs in the script's research notes.
            if len(clean_text(item["title"])) > MAX_FINDING_TITLE:
                raise ValueError(f"{label}: title is longer than {MAX_FINDING_TITLE} characters; shorten it to a headline")
            if len(str(item.get("summary") or "").strip()) > MAX_FINDING_SUMMARY:
                raise ValueError(f"{label}: summary is longer than {MAX_FINDING_SUMMARY} characters; keep it to one or two short sentences")
            topic_ids = []
            for topic in item.get("topics") or []:
                if str(topic).lower() not in by_name:
                    raise ValueError(f"{label}: unknown topic {topic!r}; topics are {', '.join(t['name'] for t in topics)}")
                topic_ids.append(by_name[str(topic).lower()])
            if not topic_ids:
                raise ValueError(f"{label}: needs at least one topic")
            sources = []
            for source in item.get("sources") or []:
                source = source if isinstance(source, dict) else {"url": source}
                url = normalize_url(str(source.get("url", "")))
                mine = self.source_for_url(url)
                sources.append({"url": url, "title": str(source.get("title") or "").strip(),
                                "publisher": str(source.get("publisher") or domain(url)).strip(),
                                "published": str(source.get("published") or "").strip(),
                                "source_id": mine["id"] if mine else None})
            if not sources:
                raise ValueError(f"{label}: needs at least one source URL")
            existing = next((owner[url_key(s["url"])] for s in sources if url_key(s["url"]) in owner), None)
            if existing:
                known = {url_key(s["url"]) for s in existing["sources"]}
                existing["sources"] += [s for s in sources if url_key(s["url"]) not in known]
                existing["topics"] = list(dict.fromkeys(existing.get("topics", []) + topic_ids))
                existing["runs"] = list(dict.fromkeys(existing.get("runs", []) + [run_id]))
                existing["updated_at"] = now()
                merged.append(existing["id"])
                target = existing
            else:
                target = {"id": "f-" + hashlib.sha1(url_key(sources[0]["url"]).encode()).hexdigest()[:10],
                          "title": clean_text(item["title"]), "summary": str(item.get("summary") or "").strip(),
                          "topics": list(dict.fromkeys(topic_ids)), "sources": sources,
                          "found_at": now(), "runs": [run_id]}
                data["findings"].append(target)
                added.append(target["id"])
            for source in target["sources"]:
                owner[url_key(source["url"])] = target
        save(self.path("findings.json"), data)
        return added, merged

    def set_dismissed(self, finding_id: str, dismissed: bool) -> dict:
        data = load(self.path("findings.json"))
        finding = self._find(data["findings"], finding_id, "finding")
        if dismissed:
            finding["dismissed_at"] = now()
        else:
            finding.pop("dismissed_at", None)
        save(self.path("findings.json"), data)
        return finding

    # scripts: linked to findings (news), topics (explainers), or both

    def script_ids(self) -> list[str]:
        return sorted(p.parent.name for p in self.path("scripts").glob("*/script.json"))

    def script(self, script_id: str) -> dict:
        folder = self.path("scripts", script_id)
        if not re.fullmatch(r"[a-z0-9-]+", script_id or "") or not (folder / "script.json").is_file():
            raise KeyError(f"Unknown script: {script_id}")
        meta = {"findings": [], "topics": []} | load(folder / "script.json")
        texts = {key: (folder / name).read_text(encoding="utf-8") if (folder / name).is_file() else ""
                 for key, name in SCRIPT_TEXTS.items()}
        version = hashlib.sha1(json.dumps([meta, texts], sort_keys=True).encode()).hexdigest()[:16]
        return {**meta, **texts, "version": version}

    def scripts(self) -> list[dict]:
        listed = []
        for script_id in self.script_ids():
            item = self.script(script_id)
            listed.append({key: item[key] for key in ("id", "title", "findings", "topics", "created", "updated", "version")}
                          | {"drafted": bool(item["script"].strip()), "has_post": bool(item["post"].strip())})
        return sorted(listed, key=lambda s: s.get("updated", ""), reverse=True)

    def create_script(self, title: str, finding_ids: list[str] | None = None, topic_ids: list[str] | None = None) -> dict:
        title = (title or "").strip() or "Untitled script"
        finding_ids, topic_ids = self._check_findings(finding_ids or []), self._check_topics(topic_ids or [])
        script_id = unique_id(dt.date.today().isoformat() + "-" + slugify(title, 40), set(self.script_ids()))
        folder = self.path("scripts", script_id)
        folder.mkdir(parents=True)
        save(folder / "script.json", {"id": script_id, "title": title, "findings": finding_ids, "topics": topic_ids,
                                      "created": now(), "updated": now()})
        for name in SCRIPT_TEXTS.values():
            (folder / name).write_text("", encoding="utf-8")
        return self.script(script_id)

    def update_script(self, script_id: str, changes: dict, version: str | None = None) -> dict:
        current = self.script(script_id)
        if version is not None and version != current["version"]:
            raise RuntimeError("This script changed since you opened it (probably your agent wrote a draft). Reload to see it.")
        folder = self.path("scripts", script_id)
        meta = {"findings": [], "topics": []} | load(folder / "script.json")
        if "title" in changes:
            meta["title"] = str(changes["title"]).strip() or "Untitled script"
        if "findings" in changes:
            meta["findings"] = self._check_findings(changes["findings"])
        if "add_findings" in changes:
            meta["findings"] = list(dict.fromkeys(meta["findings"] + self._check_findings(changes["add_findings"])))
        if "topics" in changes:
            meta["topics"] = self._check_topics(changes["topics"])
        for key, name in SCRIPT_TEXTS.items():
            if key in changes:
                write_text(folder / name, str(changes[key]))
        meta["updated"] = now()
        save(folder / "script.json", meta)
        return self.script(script_id)

    def delete_script(self, script_id: str) -> None:
        self.script(script_id)
        trash = self.path("scripts", ".trash")
        trash.mkdir(exist_ok=True)
        self.path("scripts", script_id).rename(trash / f"{script_id}-{int(time.time())}")

    # whole state for the UI

    def state(self) -> dict:
        runs = self.runs()
        return {"workspace": str(self.root), "default_workspace": self.root == workspace_path(None) and not os.environ.get("VID_STUDIO_HOME"),
                "channel": self.ws.name, "settings": self.settings(), "topics": self.topics(), "sources": self.sources(),
                "findings": self.findings(), "runs": runs[-20:], "scripts": self.scripts()}

    # helpers

    def _find(self, records: list, record_id: str, label: str) -> dict:
        for record in records:
            if record.get("id") == record_id:
                return record
        raise KeyError(f"Unknown {label}: {record_id}")

    def _check_findings(self, finding_ids) -> list[str]:
        known = {f["id"] for f in self.findings()}
        finding_ids = [str(f) for f in finding_ids or []]
        unknown = [f for f in finding_ids if f not in known]
        if unknown:
            raise ValueError(f"Unknown findings: {', '.join(unknown)}")
        return list(dict.fromkeys(finding_ids))

    def _check_topics(self, topic_ids) -> list[str]:
        known = {t["id"] for t in self.topics()}
        topic_ids = [str(t) for t in topic_ids or []]
        unknown = [t for t in topic_ids if t not in known]
        if unknown:
            raise ValueError(f"Unknown topics: {', '.join(unknown)}")
        return list(dict.fromkeys(topic_ids))


# ---------------------------------------------------------------- channels: <root>/channels/<id>/

CHANNEL_FILES = ["studio.json", "topics.json", "sources.json", "findings.json", "runs.json", "scripts", ".cache"]


def channel_dirs(root: Path) -> list[Path]:
    return sorted(p.parent for p in (root / "channels").glob("*/studio.json"))


def channels_overview(root: Path) -> list[dict]:
    listed = []
    for folder in channel_dirs(root):
        studio = Studio(folder, root)
        settings = studio.settings()
        listed.append({"id": folder.name, "name": settings.get("name") or folder.name,
                       "description": settings.get("description", ""), "language": settings.get("language", ""),
                       "findings": sum(1 for f in studio.findings() if not f.get("dismissed_at")),
                       "suggested_sources": sum(1 for x in studio.sources() if x["status"] == "suggested")})
    return listed


def find_channel(root: Path, value: str | None) -> Path:
    """A channel by ID or name; with no value, the only channel there is."""
    value = value or os.environ.get("VID_STUDIO_CHANNEL")
    folders = channel_dirs(root)
    if not folders:
        raise KeyError("No channels yet. Create one with `studio.py new-channel --name NAME`.")
    if value:
        wanted = value.strip().casefold()
        for folder in folders:
            if wanted in (folder.name, str(load(folder / "studio.json").get("name", "")).strip().casefold()):
                return folder
        raise KeyError(f"No channel {value!r}. Channels: {', '.join(c['name'] for c in channels_overview(root))}")
    if len(folders) == 1:
        return folders[0]
    raise KeyError("Several channels exist; pass --channel with one of: " + ", ".join(c["name"] for c in channels_overview(root)))


def fill_templates(folder: Path) -> None:
    templates = ASSETS / "channel"
    for source in sorted(templates.iterdir()):
        target = folder / source.name
        if source.is_file() and not target.exists():
            shutil.copyfile(source, target)
    (folder / "scripts").mkdir(parents=True, exist_ok=True)


def create_channel(root: Path, name: str, description: str = "", language: str = "") -> Path:
    name = (name or "").strip()
    if not name:
        raise ValueError("A channel needs a name")
    if any(c["name"].casefold() == name.casefold() for c in channels_overview(root)):
        raise ValueError(f"A channel called {name!r} already exists")
    existing = {p.name for p in (root / "channels").glob("*")}
    folder = root / "channels" / unique_id(slugify(name, 40), existing)
    folder.mkdir(parents=True)
    fill_templates(folder)
    settings = load(folder / "studio.json")
    settings.update(name=name, description=(description or "").strip())
    if language:
        settings["language"] = language
    save(folder / "studio.json", settings)
    return folder


def migrate_single_channel(root: Path) -> None:
    """Move a workspace from the one-channel layout (files at the root) into channels/<id>/."""
    if not (root / "studio.json").is_file():
        return
    name = str(load(root / "studio.json").get("name") or "").strip() or "Main"
    existing = {p.name for p in (root / "channels").glob("*")}
    folder = root / "channels" / unique_id(slugify(name, 40), existing)
    folder.mkdir(parents=True)
    (root / "studio.db").unlink(missing_ok=True)  # an old derived query index; the JSON files are the data
    for item in CHANNEL_FILES:
        if item == ".cache":
            seen = root / ".cache" / "seen.json"
            if seen.is_file():
                (folder / ".cache").mkdir(exist_ok=True)
                seen.rename(folder / ".cache" / "seen.json")
        elif (root / item).exists():
            (root / item).rename(folder / item)
    fill_templates(folder)
    readme = root / "README.md"
    if readme.is_file() and readme.read_text(encoding="utf-8").startswith("# Vid Studio workspace"):
        shutil.copyfile(ASSETS / "README.md", readme)  # the old one-channel README no longer applies
    print(f"Moved your channel into {folder} (the studio now supports several channels).", file=sys.stderr)


# ---------------------------------------------------------------- commands

def cmd_init(root: Path, args) -> None:
    (root / "channels").mkdir(parents=True, exist_ok=True)
    if not (root / "README.md").exists():
        shutil.copyfile(ASSETS / "README.md", root / "README.md")
    print(f"Studio: {root}")
    channels = channels_overview(root)
    print(f"Channels: {', '.join(c['name'] for c in channels) or 'none yet (studio.py new-channel --name NAME)'}")


def cmd_channels(root: Path, args) -> None:
    channels = channels_overview(root)
    if not channels:
        print("No channels yet. Create one with `studio.py new-channel --name NAME`.")
    for channel in channels:
        extra = f", {channel['suggested_sources']} suggested sources" if channel["suggested_sources"] else ""
        print(f"{channel['id']} · {channel['name']} · {channel['findings']} findings{extra}")


def cmd_new_channel(root: Path, args) -> None:
    folder = create_channel(root, args.name, args.description or "", args.language or "")
    print(f"Channel {folder.name}: {folder}")


def cmd_status(root: Path, args) -> None:
    if not channel_dirs(root):
        print(f"No channels in {root}. Run `studio.py init`, then set up a channel (references/setup.md).")
        return
    try:
        ws = find_channel(root, args.channel)
    except KeyError as error:
        print(error.args[0])
        print(f"UI: {(running_server(root) or {}).get('url') or 'not running (studio.py serve --background)'}")
        return
    studio = Studio(ws, root)
    settings, topics, sources, scripts = studio.settings(), studio.topics(), studio.sources(), studio.scripts()
    runs = studio.runs()
    last = next((r for r in reversed(runs) if r.get("status") in ("completed", "failed")), None)
    others = [c["name"] for c in channels_overview(root) if c["id"] != ws.name]
    print(f"Channel: {settings.get('name') or '(unnamed)'} ({ws.name}) · studio {root}" + (f" · other channels: {', '.join(others)}" if others else ""))
    print(f"Topics: {', '.join(t['name'] for t in topics) or 'none'}")
    approved = [s for s in sources if s["status"] == "approved"]
    suggested = [s for s in sources if s["status"] == "suggested"]
    print(f"Sources: {', '.join(domain(s['url']) + urllib.parse.urlsplit(s['url']).path.rstrip('/') for s in approved) or 'none'}"
          + (f" · {len(suggested)} suggested, waiting for the user" if suggested else ""))
    print(f"Findings: {sum(1 for f in studio.findings() if not f.get('dismissed_at'))} · last research: "
          + (f"{last['finished']} ({last['status']}, {last.get('findings', 0)} findings)" if last else "never"))
    print(f"Schedule: {', '.join(settings.get('schedule', {}).get('times', [])) or 'manual only'}")
    print("Scripts:" + ("" if scripts else " none"))
    for script in scripts:
        state = "drafted" if script["drafted"] else "not drafted"
        links = [f"{len(script['findings'])} findings"] + [f"topic {t}" for t in script["topics"]]
        print(f"  {script['id']} · {script['title']} · {', '.join(links)} · {state}")
    server = running_server(root)
    print(f"UI: {server['url'] + '#/' + ws.name if server else 'not running (studio.py serve --background)'}")
    hints = []
    if not settings.get("name") or not topics:
        hints.append("Set up the channel: name, topics, sources (references/setup.md).")
    elif not last:
        hints.append("Run research (references/research.md).")
    running = next((r for r in reversed(runs) if r.get("status") == "running"), None)
    if running:
        hints.append(f"Run {running['id']} is unfinished; sources not checked yet: {', '.join(studio.unchecked_sources(running)) or 'none'}.")
    hints += [f"Script '{s['title']}' has material but no draft (references/write.md)." for s in scripts
              if (s["findings"] or s["topics"]) and not s["drafted"]]
    if hints:
        print("Suggestions:\n" + "\n".join(f"- {h}" for h in hints))


def cmd_add_topic(ws: Path, args) -> None:
    topic = Studio(ws).add_topic(args.name, args.description or "")
    print(f"Added topic {topic['id']}: {topic['name']}")


def cmd_add_source(ws: Path, args) -> None:
    source = Studio(ws).add_source(args.url, args.note or "")
    print(f"Added source {source['id']}: {source['url']}")


def cmd_suggest_source(ws: Path, args) -> None:
    source = Studio(ws).add_source(args.url, args.note or "", suggested_reason=args.reason, run_id=args.run)
    print(f"Suggested {source['url']}; it waits in the Sources tab for the user to approve")


def cmd_checked(ws: Path, args) -> None:
    studio = Studio(ws)
    run = studio.mark_checked(args.run, args.source, args.note or "")
    left = studio.unchecked_sources(run)
    print(f"Checked {', '.join(args.source)}. " + (f"Still to check: {', '.join(left)}" if left else "All sources checked."))


def cmd_scan(ws: Path, args) -> None:
    """Pull new items from source feeds. Read-only apart from the feed cache."""
    studio = Studio(ws)
    data = load(ws / "sources.json")
    seen_path = ws / ".cache" / "seen.json"
    seen = load(seen_path, {"keys": {}})["keys"]
    cutoff = (dt.date.today() - dt.timedelta(days=120)).isoformat()
    seen = {key: day for key, day in seen.items() if day >= cutoff}
    today = dt.date.today().isoformat()
    without_feed = []
    for source in data["sources"]:
        if source.get("status", "approved") != "approved":
            continue
        if not source.get("feed") and not source.get("feed_checked"):
            source["feed"], _ = discover_feed(source["url"])
            source["feed_checked"] = True
        if not source.get("feed"):
            without_feed.append(source)
            continue
        try:
            items = parse_feed(fetch(source["feed"])[0])
        except Exception as error:
            print(f"\n## {source['id']}: {source['url']}\nFeed failed ({type(error).__name__}: {error}); search this site directly.")
            continue
        fresh = []
        for item in items:
            keys = [key for key in (url_key(item["url"]), title_key(item["title"])) if key]
            if keys and not any(key in seen for key in keys):
                fresh.append(item)
                for key in keys:
                    seen[key] = today
            if len(fresh) >= args.limit:
                break
        print(f"\n## {source['id']}: {source['url']} ({len(fresh)} new)")
        for item in fresh:
            print(f"- {item['title']} | {item['url']} | {item['published']}" + (f"\n  {item['summary']}" if item["summary"] else ""))
    save(ws / "sources.json", data)
    save(seen_path, {"keys": seen})
    if without_feed:
        print("\nNo feed; search these sites directly (for example `site:` queries):")
        for source in without_feed:
            print(f"- {source['id']}: {source['url']}" + (f" ({source['note']})" if source.get("note") else ""))
    print(f"\nTopics: {', '.join(t['name'] for t in studio.topics())}")


def cmd_start_run(ws: Path, args) -> None:
    run, since, abandoned = Studio(ws).start_run(args.trigger)
    if abandoned:
        print(f"Marked unfinished runs abandoned: {', '.join(abandoned)}")
    print(f"Run: {run['id']}")
    print(f"Look for developments since: {since.isoformat(timespec='minutes')}")
    sources = {s["id"]: s for s in Studio(ws).sources()}
    if run["sources"]:
        print("Check every one of these sources, then mark it with `studio.py checked`:")
        for source_id in run["sources"]:
            print(f"- {source_id}: {sources[source_id]['url']}")


def cmd_add_findings(ws: Path, args) -> None:
    raw = sys.stdin.read() if args.file == "-" else Path(args.file).expanduser().read_text(encoding="utf-8")
    try:
        items = json.loads(raw)
    except json.JSONDecodeError as error:
        raise SystemExit(f"Invalid JSON: {error}")
    added, merged = Studio(ws).add_findings(args.run, items)
    print(f"Added {len(added)} findings" + (f", merged {len(merged)} into existing ones (same sources)" if merged else ""))


def cmd_finish_run(ws: Path, args) -> None:
    run = Studio(ws).finish_run(args.run, args.failed, args.note or "")
    print(f"{run['id']}: {run['status']}, {run['findings']} findings, {len(run.get('checked', {}))}/{len(run.get('sources', []))} sources checked"
          + (f", {run['suggested_sources']} sources suggested" if run.get("suggested_sources") else ""))


def cmd_new_script(ws: Path, args) -> None:
    script = Studio(ws).create_script(args.title, args.finding or [], args.topic or [])
    print(f"Script: {ws / 'scripts' / script['id']}")


# ---------------------------------------------------------------- web UI server

def running_server(ws: Path) -> dict | None:
    info = load(ws / ".cache" / "server.json", {})
    if not info.get("url"):
        return None
    try:
        with urllib.request.urlopen(info["url"] + "api/health", timeout=2) as response:
            return info if response.read().decode() == str(ws) else None
    except Exception:
        return None


def make_handler(ws: Path):
    import threading
    lock = threading.Lock()
    page = ASSETS / "ui" / "index.html"

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, code: int, body, content_type: str = "application/json; charset=utf-8") -> None:
            if not isinstance(body, bytes):
                body = json.dumps(body, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def allowed(self, write: bool) -> bool:
            # Only this machine may talk to the server (blocks DNS rebinding). Writes also need a custom
            # header and a JSON body, which browsers will not send cross-site without a CORS preflight.
            hostname = (self.headers.get("Host") or "").rsplit(":", 1)[0].strip("[]")
            if hostname not in ("localhost", "127.0.0.1", "::1"):
                return False
            return not write or (self.headers.get("X-Vid-Studio") == "1"
                                 and (self.headers.get("Content-Type") or "").startswith("application/json"))

        def route(self, method: str):
            if not self.allowed(method != "GET"):
                return self.reply(403, {"error": "Forbidden"})
            path = urllib.parse.urlsplit(self.path).path.rstrip("/") or "/"
            parts = [urllib.parse.unquote(p) for p in path.strip("/").split("/")] if path != "/" else []
            body = {}
            if method in ("POST", "PUT"):
                length = int(self.headers.get("Content-Length") or 0)
                try:
                    body = json.loads(self.rfile.read(length) or b"{}")
                except json.JSONDecodeError:
                    return self.reply(400, {"error": "Invalid JSON"})
                if not isinstance(body, dict):
                    return self.reply(400, {"error": "Expected a JSON object"})
            try:
                if method == "GET" and not parts:
                    return self.reply(200, page.read_bytes(), "text/html; charset=utf-8")
                if method == "GET" and len(parts) == 2 and parts[0] == "fonts" and re.fullmatch(r"[a-z0-9-]+\.woff2", parts[1]):
                    font = page.parent / "fonts" / parts[1]
                    if font.is_file():
                        return self.reply(200, font.read_bytes(), "font/woff2")
                if parts == ["api", "health"]:
                    return self.reply(200, str(ws).encode(), "text/plain; charset=utf-8")
                with lock:
                    if parts == ["api", "channels"] and method == "GET":
                        result = {"workspace": str(ws), "default_workspace": ws == workspace_path(None) and not os.environ.get("VID_STUDIO_HOME"),
                                  "channels": channels_overview(ws)}
                    elif parts == ["api", "channels"] and method == "POST":
                        folder = create_channel(ws, body.get("name", ""), body.get("description", ""), body.get("language", ""))
                        result = {"id": folder.name}
                    elif parts[:2] == ["api", "c"] and len(parts) >= 3:
                        result = self.api(method, parts[3:], body, Studio(find_channel(ws, parts[2]), ws))
                    else:
                        return self.reply(404, {"error": "Not found"})
                return self.reply(200, result)
            except KeyError as error:
                return self.reply(404, {"error": str(error.args[0] if error.args else error)})
            except ValueError as error:
                return self.reply(400, {"error": str(error)})
            except RuntimeError as error:
                return self.reply(409, {"error": str(error)})
            except (SystemExit, OSError) as error:
                return self.reply(500, {"error": str(error)})

        def api(self, method: str, parts: list[str], body: dict, studio: Studio):
            resource, item = (parts + [None, None])[:2]
            if method == "GET" and resource == "state":
                return studio.state()
            if resource == "settings" and method == "PUT":
                return studio.update_settings(body)
            if resource == "topics":
                if method == "POST":
                    return studio.add_topic(body.get("name", ""), body.get("description", ""))
                if method == "PUT" and item:
                    return studio.update_topic(item, body)
                if method == "DELETE" and item:
                    return studio.delete_topic(item) or {"ok": True}
            if resource == "sources":
                if method == "POST":
                    return studio.add_source(body.get("url", ""), body.get("note", ""))
                if method == "PUT" and item:
                    return studio.update_source(item, body)
                if method == "DELETE" and item:
                    return studio.delete_source(item) or {"ok": True}
            if resource == "findings" and method == "PUT" and item and "dismissed" in body:
                return studio.set_dismissed(item, bool(body["dismissed"]))
            if resource == "scripts":
                if method == "GET" and item:
                    return studio.script(item)
                if method == "POST":
                    return studio.create_script(body.get("title", ""), body.get("findings", []), body.get("topics", []))
                if method == "PUT" and item:
                    version = body.pop("version", None)
                    return studio.update_script(item, body, version)
                if method == "DELETE" and item:
                    return studio.delete_script(item) or {"ok": True}
            raise KeyError("Not found")

        def do_GET(self):
            self.route("GET")

        def do_POST(self):
            self.route("POST")

        def do_PUT(self):
            self.route("PUT")

        def do_DELETE(self):
            self.route("DELETE")

    return Handler


def cmd_serve(ws: Path, args) -> None:
    info_path = ws / ".cache" / "server.json"
    server_info = running_server(ws)
    if args.stop:
        if server_info:
            os.kill(server_info["pid"], signal.SIGTERM)
            print(f"Stopped {server_info['url']}")
        else:
            print("No server running")
        info_path.unlink(missing_ok=True)
        return
    if server_info:
        print(f"Studio: {server_info['url']}")
        return
    if args.background:
        detach = {"creationflags": 0x00000008} if os.name == "nt" else {"start_new_session": True}
        process = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "--workspace", str(ws), "serve", "--port", str(args.port)],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **detach)
        for _ in range(60):
            time.sleep(0.1)
            server_info = running_server(ws)
            if server_info:
                print(f"Studio: {server_info['url']}")
                return
            if process.poll() is not None:
                break
        raise SystemExit("The studio server did not start. Run `studio.py serve` in the foreground to see why.")

    for port in range(args.port, args.port + 20):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(ws))
            break
        except OSError:
            continue
    else:
        raise SystemExit(f"No free port between {args.port} and {args.port + 19}")
    url = f"http://localhost:{server.server_port}/"
    save(info_path, {"pid": os.getpid(), "port": server.server_port, "url": url, "started": now()})
    print(f"Studio: {url} (Ctrl+C to stop)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        if load(info_path, {}).get("pid") == os.getpid():
            info_path.unlink(missing_ok=True)


# ---------------------------------------------------------------- cli

def main(argv=None) -> None:
    workspace_help = "Workspace directory (default: $VID_STUDIO_HOME or ~/vid-studio)"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", help=workspace_help)
    parser.add_argument("--channel", help="Channel ID or name (default: $VID_STUDIO_CHANNEL, or the only channel)")
    # Accept --workspace after the subcommand too, without clobbering one given before it.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--workspace", default=argparse.SUPPRESS, help=workspace_help)
    common.add_argument("--channel", default=argparse.SUPPRESS,
                        help="Channel ID or name (default: $VID_STUDIO_CHANNEL, or the only channel)")
    commands = parser.add_subparsers(dest="command", required=True)

    def command(name, handler, help_text):
        sub = commands.add_parser(name, parents=[common], help=help_text)
        sub.set_defaults(handler=handler)
        return sub

    command("init", cmd_init, "Create the studio folder; never overwrites files")
    command("channels", cmd_channels, "List channels")
    sub = command("new-channel", cmd_new_channel, "Create a channel")
    sub.add_argument("--name", required=True)
    sub.add_argument("--description")
    sub.add_argument("--language", choices=["English", "Hindi", "Hinglish"])
    command("status", cmd_status, "Show the channel, research runs, scripts, and suggestions")

    sub = command("serve", cmd_serve, "Run the studio web UI at http://localhost")
    sub.add_argument("--port", type=int, default=8765)
    sub.add_argument("--background", action="store_true", help="Start detached and print the URL")
    sub.add_argument("--stop", action="store_true")

    sub = command("add-topic", cmd_add_topic, "Add a topic")
    sub.add_argument("--name", required=True)
    sub.add_argument("--description")

    sub = command("add-source", cmd_add_source, "Add a website to check on every research run")
    sub.add_argument("--url", required=True)
    sub.add_argument("--note")

    sub = command("suggest-source", cmd_suggest_source, "Suggest a source; the user approves it in the Sources tab")
    sub.add_argument("--url", required=True)
    sub.add_argument("--reason", required=True, help="Why this source is worth checking on every run")
    sub.add_argument("--note")
    sub.add_argument("--run", help="Run that found it")

    sub = command("checked", cmd_checked, "Mark sources as checked in a research run")
    sub.add_argument("--run", required=True)
    sub.add_argument("--source", action="append", required=True, help="Source ID; repeatable")
    sub.add_argument("--note", help="What you found, or why the site could not be checked")

    sub = command("scan", cmd_scan, "List new items from source feeds (helper for research runs)")
    sub.add_argument("--limit", type=int, default=20, help="Max new items per source")

    sub = command("start-run", cmd_start_run, "Start a research run; prints the run ID and the since-time")
    sub.add_argument("--trigger", choices=["manual", "scheduled"], default="manual")

    sub = command("add-findings", cmd_add_findings, "Save findings from a JSON file (or - for stdin)")
    sub.add_argument("--run", required=True)
    sub.add_argument("file")

    sub = command("finish-run", cmd_finish_run, "Finish a research run")
    sub.add_argument("--run", required=True)
    sub.add_argument("--note")
    sub.add_argument("--failed", metavar="REASON")

    sub = command("new-script", cmd_new_script, "Create a script, optionally with findings attached")
    sub.add_argument("--title", required=True)
    sub.add_argument("--finding", action="append", help="Finding ID; repeatable")
    sub.add_argument("--topic", action="append", help="Topic ID, for explainers; repeatable")

    args = parser.parse_args(argv)
    root = workspace_path(args.workspace)
    try:
        migrate_single_channel(root)
        if args.command in ("init", "channels", "new-channel", "status", "serve"):
            args.handler(root, args)
        else:
            args.handler(find_channel(root, args.channel), args)
    except (ValueError, KeyError, RuntimeError) as error:
        raise SystemExit(f"Error: {error.args[0] if error.args else error}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()

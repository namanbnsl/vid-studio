#!/usr/bin/env python3
"""Vid Studio helper: one project's topics, sources, findings, scripts, and the local web UI.

Standard library only. The workspace is --workspace, else $VID_STUDIO_HOME, else ~/vid-studio.
Every command prints what it did so the calling agent can continue from the output.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import html
import json
import math
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import narration as tts  # noqa: E402
import publish as pub  # noqa: E402

SKILL_DIR = Path(__file__).resolve().parents[1]
ASSETS = SKILL_DIR / "assets"
SCENES_DIR = ASSETS / "scenes"
PRESETS_DIR = SCENES_DIR / "presets"
FONT_CATALOG = SCENES_DIR / "fonts.json"
VOICE_DEFAULT_PATH = ASSETS / "voice-default.json"
USER_AGENT = "Mozilla/5.0 (compatible; vid-studio/1.0)"
FEED_PATHS = ["/feed", "/rss", "/feed.xml", "/rss.xml", "/atom.xml", "/index.xml", "/feeds/posts/default"]
FIRST_RUN_LOOKBACK = dt.timedelta(days=7)
RUN_OVERLAP = dt.timedelta(hours=6)
MAX_FINDING_TITLE = 110
MAX_FINDING_SUMMARY = 240
STAGES = ["script", "ready", "published"]

DEFAULT_PRESET = "bold-explainer"
DEFAULT_DESIGN = {
    "preset": DEFAULT_PRESET, "aspect": "9:16",
    "colors": {"background": "#121212", "surface": "#1E1E1E", "text": "#F7F3EA", "muted": "#9C978D",
               "accent": "#FFC233", "accent2": "#FF7A45", "negative": "#FF5D5D"},
    "fonts": {"display": "Bricolage Grotesque", "body": "Mukta", "mono": "JetBrains Mono"},
    "type": {"scale": 1.0, "display_case": "none", "display_weight": 800, "tracking": -0.03},
    "motion": {"energy": "high", "easing": "snappy", "transition": "slide"},
    "captions": {"style": "highlight", "position": "lower", "highlight": "accent", "max_words": 4, "size": "medium"},
    "background": {"style": "grain", "pattern": "none"}, "cards": {"style": "glass"}, "images": {"treatment": "dim", "layout": "auto"},
    "sources": {"show": True}, "progress": {"show": True}, "radius": 28,
    "logo": {"text": "", "position": "top-left"}, "custom_css": "",
}
HOOK_STYLES = ["question", "surprising-stat", "myth-bust", "story", "moment", "stakes", "contrast"]
DEFAULT_VOICE = {
    "length_seconds": 60, "words_per_minute": 160, "persona": "",
    "tone": {"playful": 50, "casual": 60, "intensity": 55}, "hook_styles": HOOK_STYLES,
    "do": [], "dont": [], "open": "", "close": "", "cta": "", "examples": [],
}


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

SETTING_KEYS = {"name", "description", "audience", "timezone", "research_notes", "schedule"}


DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def clean_schedule(schedule: dict) -> dict:
    """Times as sorted HH:MM; days as weekday keys in week order, where all seven means every day."""
    times = sorted({str(t).strip() for t in schedule.get("times", []) if str(t).strip()})
    for t in times:
        if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", t):
            raise ValueError(f"Times must look like 07:30, not {t!r}")
    days = {str(d).strip().lower()[:3] for d in schedule.get("days") or DAYS}
    if days - set(DAYS):
        raise ValueError(f"Days must be from {', '.join(DAYS)}")
    return {"days": [d for d in DAYS if d in days], "times": times}


def describe_schedule(schedule: dict) -> str:
    times, days = schedule.get("times", []), schedule.get("days") or DAYS
    if not times:
        return "manual only"
    when = ("every day" if len(days) == 7 else "weekdays" if days == DAYS[:5] else "weekends" if days == DAYS[5:]
            else ", ".join(d.title() for d in days))
    return f"{when} at {' and '.join(times)}"


class Studio:
    """All reads and writes of the workspace files. Raises ValueError for bad input."""

    def __init__(self, ws: Path, root: Path | None = None):
        self.ws = ws  # this project's folder
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
                value = clean_schedule(value or {})
            elif not isinstance(value, str):
                raise ValueError(f"{key} must be text")
            settings[key] = value
        if not settings.get("name", "").strip():
            raise ValueError("The project needs a name")
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
        for story_id in self.story_ids():
            meta_path = self.path("stories", story_id, "story.json")
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

    # stories (research): an angle built from findings (news), topics (explainers), or both, with research notes

    def story_ids(self) -> list[str]:
        return sorted(p.parent.name for p in self.path("stories").glob("*/story.json"))

    def story(self, story_id: str) -> dict:
        folder = self.path("stories", story_id)
        if not re.fullmatch(r"[a-z0-9-]+", story_id or "") or not (folder / "story.json").is_file():
            raise KeyError(f"Unknown story: {story_id}")
        meta = {"findings": [], "topics": []} | load(folder / "story.json")
        notes = (folder / "notes.md").read_text(encoding="utf-8") if (folder / "notes.md").is_file() else ""
        version = hashlib.sha1(json.dumps([meta, notes], sort_keys=True).encode()).hexdigest()[:16]
        return {**meta, "notes": notes, "version": version}

    def stories(self) -> list[dict]:
        listed = []
        for story_id in self.story_ids():
            item = self.story(story_id)
            listed.append({key: item[key] for key in ("id", "title", "findings", "topics", "created", "updated", "version")}
                          | {"researched": bool(item["notes"].strip())})
        return sorted(listed, key=lambda s: s.get("updated", ""), reverse=True)

    def create_story(self, title: str, finding_ids: list[str] | None = None, topic_ids: list[str] | None = None) -> dict:
        title = (title or "").strip() or "Untitled story"
        finding_ids, topic_ids = self._check_findings(finding_ids or []), self._check_topics(topic_ids or [])
        story_id = unique_id(dt.date.today().isoformat() + "-" + slugify(title, 40), set(self.story_ids()))
        folder = self.path("stories", story_id)
        folder.mkdir(parents=True)
        save(folder / "story.json", {"id": story_id, "title": title, "findings": finding_ids, "topics": topic_ids,
                                     "created": now(), "updated": now()})
        (folder / "notes.md").write_text("", encoding="utf-8")
        return self.story(story_id)

    def update_story(self, story_id: str, changes: dict, version: str | None = None) -> dict:
        current = self.story(story_id)
        if version is not None and version != current["version"]:
            raise RuntimeError("This story changed since you opened it (probably your agent wrote notes). Reload to see it.")
        folder = self.path("stories", story_id)
        meta = {"findings": [], "topics": []} | load(folder / "story.json")
        if "title" in changes:
            meta["title"] = str(changes["title"]).strip() or "Untitled story"
        if "findings" in changes:
            meta["findings"] = self._check_findings(changes["findings"])
        if "add_findings" in changes:
            meta["findings"] = list(dict.fromkeys(meta["findings"] + self._check_findings(changes["add_findings"])))
        if "topics" in changes:
            meta["topics"] = self._check_topics(changes["topics"])
        if "notes" in changes:
            write_text(folder / "notes.md", str(changes["notes"]))
        meta["updated"] = now()
        save(folder / "story.json", meta)
        return self.story(story_id)

    def delete_story(self, story_id: str) -> None:
        self.story(story_id)
        self._trash("stories", story_id)

    # scripts (production): one per story and channel; the text follows the channel's language and format

    def script_ids(self) -> list[str]:
        return sorted(p.parent.name for p in self.path("scripts").glob("*/script.json"))

    def script(self, script_id: str) -> dict:
        folder = self.path("scripts", script_id)
        if not re.fullmatch(r"[a-z0-9-]+", script_id or "") or not (folder / "script.json").is_file():
            raise KeyError(f"Unknown script: {script_id}")
        meta = {"stage": "script", "published_url": ""} | load(folder / "script.json")
        text = (folder / "script.md").read_text(encoding="utf-8") if (folder / "script.md").is_file() else ""
        # Comments are not part of the version, so adding or resolving one never looks like a conflicting edit.
        version = hashlib.sha1(json.dumps([meta, text], sort_keys=True).encode()).hexdigest()[:16]
        channel = find_channel(self.root, meta["channel"])
        scenes = parse_scenes(text, channel_voice(self.root, channel["id"])["words_per_minute"]) if channel["kind"] == "video" else []
        voiceover = self.narration_status(script_id, scenes, channel) if channel["kind"] == "video" else None
        return {**meta, "text": text, "comments": self.comments(script_id, text), "version": version,
                "scenes": scenes, "duration": total_duration(scenes), "media": self.media(script_id), "narration": voiceover,
                "video": self.video_status(script_id, scenes, channel) if channel["kind"] == "video" else None,
                "angles": load(folder / "angles.json", {"angles": []})["angles"],
                "publish": self.publish_status(script_id) if channel["kind"] == "video" else None,
                "review": load(folder / "review.json") if (folder / "review.json").is_file() else None}

    def scripts(self) -> list[dict]:
        listed = []
        for script_id in self.script_ids():
            item = self.script(script_id)
            listed.append({key: item[key] for key in ("id", "title", "story", "channel", "stage", "published_url", "created", "updated", "version", "duration")}
                          | {"drafted": bool(item["text"].strip()), "open_comments": sum(1 for c in item["comments"] if not c.get("resolved_at")),
                             "video": item["video"] and {k: item["video"][k] for k in ("status", "ready", "stale")},
                             "narration": item["narration"] and {k: item["narration"][k] for k in ("provider", "status", "done", "missing")},
                             "publish": item["publish"] and {k: item["publish"][k] for k in ("platform", "status", "url", "stats")}})
        return sorted(listed, key=lambda s: s.get("updated", ""), reverse=True)

    def create_script(self, story_id: str, channel_id: str, title: str = "") -> dict:
        story, channel = self.story(story_id), find_channel(self.root, channel_id)
        channel_folder(self.root, channel["id"])
        if any(s["story"] == story_id and s["channel"] == channel["id"] for s in self.scripts()):
            raise ValueError(f"The story already has a script for {channel['name']}")
        title = (title or "").strip() or story["title"]
        script_id = unique_id(slugify(story_id, 48) + "-" + channel["id"], set(self.script_ids()))
        folder = self.path("scripts", script_id)
        folder.mkdir(parents=True)
        save(folder / "script.json", {"id": script_id, "title": title, "story": story_id, "channel": channel["id"],
                                      "stage": "script", "published_url": "", "created": now(), "updated": now()})
        (folder / "script.md").write_text("", encoding="utf-8")
        return self.script(script_id)

    def update_script(self, script_id: str, changes: dict, version: str | None = None) -> dict:
        current = self.script(script_id)
        if version is not None and version != current["version"]:
            raise RuntimeError("This script changed since you opened it (probably your agent wrote a draft). Reload to see it.")
        folder = self.path("scripts", script_id)
        angles = None
        if "chosen_angle" in changes:
            angles = current["angles"]
            self._find(angles, changes["chosen_angle"], "angle")
            for angle in angles:
                angle["chosen"] = angle["id"] == changes["chosen_angle"]
        if not (set(changes) - {"chosen_angle"}):
            if angles is not None:
                save(folder / "angles.json", {"angles": angles})
            return self.script(script_id)
        meta = {"stage": "script", "published_url": ""} | load(folder / "script.json")
        if "title" in changes:
            meta["title"] = str(changes["title"]).strip() or "Untitled script"
        if "stage" in changes:
            if changes["stage"] not in STAGES:
                raise ValueError(f"Stage must be one of: {', '.join(STAGES)}")
            meta["stage"] = changes["stage"]
        if "published_url" in changes:
            url = str(changes["published_url"] or "").strip()
            meta["published_url"] = normalize_url(url) if url else ""
        if "text" in changes:
            write_text(folder / "script.md", str(changes["text"]))
        meta["updated"] = now()
        save(folder / "script.json", meta)
        if angles is not None:
            save(folder / "angles.json", {"angles": angles})
        return self.script(script_id)

    def save_angles(self, script_id: str, angles) -> list[dict]:
        self.script(script_id)
        if isinstance(angles, dict):
            check_keys(angles, {"angles"}, "angles file")
            angles = angles.get("angles")
        if not isinstance(angles, list) or not 2 <= len(angles) <= 6:
            raise ValueError("angles must be a list of 2–6 hook options")
        cleaned, ids = [], set()
        for i, angle in enumerate(angles, 1):
            check_keys(angle, {"id", "hook", "angle", "why", "chosen"}, f"angles[{i}]")
            item = {"id": angle.get("id", f"a{i}"), "chosen": angle.get("chosen", False)}
            for key in ("id", "hook", "angle", "why"):
                item[key] = check_text(item[key] if key == "id" else angle.get(key), f"angles[{i}].{key}", 100 if key == "id" else 4000)
            if not item["id"].strip() or item["id"] in ids:
                raise ValueError(f"angles[{i}].id must be non-empty and unique")
            if not isinstance(item["chosen"], bool):
                raise ValueError(f"angles[{i}].chosen must be true or false")
            ids.add(item["id"])
            cleaned.append(item)
        if sum(a["chosen"] for a in cleaned) > 1:
            raise ValueError("Choose at most one angle")
        if not any(a["chosen"] for a in cleaned):
            cleaned[0]["chosen"] = True
        save(self.path("scripts", script_id, "angles.json"), {"angles": cleaned})
        return cleaned

    def save_review(self, script_id: str, review: dict) -> dict:
        self.script(script_id)
        check_keys(review, {"scores", "summary", "notes", "at"}, "review")
        scores = review.get("scores")
        keys = {"hook", "clarity", "retention", "specificity", "voice", "human", "natural", "value", "accuracy"}
        check_keys(scores, keys, "review.scores")
        for key in sorted(keys):
            check_number(scores.get(key), f"review.scores.{key}", 1, 10, integer=True)
        result = {"scores": dict(scores), "summary": check_text(review.get("summary"), "review.summary", 10000),
                  "notes": check_strings(review.get("notes"), "review.notes"), "at": now()}
        save(self.path("scripts", script_id, "review.json"), result)
        return result

    def export_script(self, script_id: str, out_dir: str | Path | None = None) -> Path:
        script = self.script(script_id)
        channel = find_channel(self.root, script["channel"])
        if channel["kind"] != "video":
            raise ValueError("Export requires a video channel; text posts have no scenes")
        for name in ("engine.js", "engine.css", "composition.html"):
            if not (SCENES_DIR / name).is_file():
                raise RuntimeError(f"Missing scene asset {SCENES_DIR / name}; add the scene engine before exporting")
        design = channel_design(self.root, channel["id"])
        template = (SCENES_DIR / "composition.html").read_text(encoding="utf-8")
        replacements = {"__VID_DESIGN_JSON__": script_json(design),
                        "__VID_SCENES_JSON__": script_json(script["scenes"]), "__VID_TITLE__": html.escape(script["title"])}
        # Substitute once: user text containing a token must remain literal.
        template = re.sub("|".join(replacements), lambda match: replacements[match.group()], template)
        # HyperFrames reads the canvas size and length from the root's attributes, before any script runs.
        width, height = ASPECT_SIZES[design["aspect"]]
        template = template.replace('data-width="1080" data-height="1920"',
                                    f'data-width="{width}" data-height="{height}" data-duration="{total_duration(script["scenes"])}"', 1)
        folder = Path(out_dir).expanduser().resolve() if out_dir is not None else self.path("scripts", script_id, "render")
        folder.mkdir(parents=True, exist_ok=True)
        for name in ("engine.js", "engine.css"):
            target = folder / name
            if target.resolve() != (SCENES_DIR / name).resolve():
                shutil.copyfile(SCENES_DIR / name, target)
        # Photos travel with the composition, at the same relative paths the script uses (media/…).
        media = self.path("scripts", script_id, "media")
        if (folder / "media").is_dir() and (folder / "media").resolve() != media.resolve():
            for old in (folder / "media").iterdir():
                if old.is_file() and re.fullmatch(r"[a-z0-9-]+\.(jpg|png|webp)", old.name) and not (media / old.name).is_file():
                    old.unlink()
        if media.is_dir() and (folder / "media").resolve() != media.resolve():
            shutil.copytree(media, folder / "media", dirs_exist_ok=True)
        # The voiceover travels too: one <audio> clip per beat, which HyperFrames places on its own track.
        clips, start = [], 0.0
        if (folder / "narration").is_dir():
            shutil.rmtree(folder / "narration")
        for i, scene in enumerate(script["scenes"]):
            audio = scene.get("audio")
            if audio:
                (folder / "narration").mkdir(exist_ok=True)
                shutil.copyfile(self.path("scripts", script_id, audio["src"]), folder / audio["src"])
                clips.append(f'<audio id="vo-{i}" class="clip" src="{html.escape(audio["src"])}" data-start="{start:.3f}" '
                             f'data-duration="{audio["duration"]:.3f}" data-track-index="3"></audio>')
            start += scene["duration"]
        if clips:
            template = template.replace("</body>", "\n".join(clips) + "\n</body>", 1)
        write_text(folder / "index.html", template)
        return folder

    # media: photos for a script's beats, in scripts/<id>/media, listed with their credits in media.json

    def media(self, script_id: str) -> list[dict]:
        folder = self.path("scripts", script_id, "media")
        listed = load(self.path("scripts", script_id, "media.json"), {"media": []})["media"]
        return [item for item in listed if (folder / item.get("file", "")).is_file()]

    def add_media(self, script_id: str, data: bytes, name: str = "", credit: str = "", source: str = "", license: str = "") -> dict:
        self.script(script_id)
        kind = image_kind(data)
        if not kind:
            raise ValueError("Not a JPEG, PNG, or WebP image")
        if len(data) > MAX_MEDIA_BYTES:
            raise ValueError(f"Images must be under {MAX_MEDIA_BYTES // 1_000_000} MB")
        folder = self.path("scripts", script_id, "media")
        folder.mkdir(parents=True, exist_ok=True)
        existing = {p.name for p in folder.iterdir()}
        stem = slugify(Path(name).stem if name else "image", 40) or "image"
        file = unique_id(stem, {Path(n).stem for n in existing}) + "." + kind
        (folder / file).write_bytes(data)
        item = {"file": file, "path": f"media/{file}", "credit": clean_text(credit, 200), "source": source.strip(),
                "license": clean_text(license, 80), "added": now()}
        listed = [m for m in self.media(script_id) if m["file"] != file] + [item]
        save(self.path("scripts", script_id, "media.json"), {"media": listed})
        return item

    def delete_media(self, script_id: str, file: str) -> None:
        self.script(script_id)
        if not re.fullmatch(r"[a-z0-9-]+\.(jpg|png|webp)", file or ""):
            raise KeyError(f"Unknown media file: {file}")
        target = self.path("scripts", script_id, "media", file)
        if not target.is_file():
            raise KeyError(f"Unknown media file: {file}")
        target.unlink()
        save(self.path("scripts", script_id, "media.json"), {"media": [m for m in self.media(script_id) if m["file"] != file]})

    # voiceover: scripts/<id>/narration holds one WAV per beat, named by what was said and how, and narration.json

    def narration_settings(self, channel: dict) -> dict:
        return narration_style(self.root, channel["id"], channel_narration(self.root, channel["id"]))

    def narration_status(self, script_id: str, scenes: list, channel: dict) -> dict:
        """Give each beat that has a current clip its audio and its real length; report what's missing."""
        settings = self.narration_settings(channel)
        folder = self.path("scripts", script_id, "narration")
        manifest = load(folder / "narration.json", {})
        clips, language = manifest.get("clips", {}), channel["language"]
        state = manifest.get("status") or "none"
        if state == "narrating" and manifest.get("pid") not in (None, os.getpid()) and not pid_alive(manifest.get("pid")):
            state, manifest["error"] = "failed", "The voiceover stopped before it finished"
        takes = manifest.get("recordings", {})
        synthetic = settings["provider"] not in ("", "recorded")
        result = {"provider": settings["provider"], "voice": settings["voice"], "pause": settings["pause"],
                  "settings": tts.settings_key(settings, language) if synthetic else "", "status": state,
                  "progress": manifest.get("progress", 0), "error": manifest.get("error", ""), "finished": manifest.get("finished", ""),
                  "done": 0, "missing": 0, "recorded": 0, "clips": {},
                  "takes": {key: {k: take.get(k) for k in ("file", "text", "duration", "source", "created")} for key, take in takes.items()
                            if (folder / take.get("file", "")).is_file()}}
        for scene in scenes:
            text = scene.get("say") or scene["vo"]
            if not text:
                continue
            # Your own take always wins; then the narrator's clip for these words and settings.
            take = result["takes"].get(tts.recording_key(text))
            clip = take or (clips.get(tts.clip_key(settings, language, text)) if synthetic else None)
            if not clip or not (folder / clip.get("file", "")).is_file():
                result["missing"] += 1 if settings["provider"] else 0
                continue
            result["done"] += 1
            result["recorded"] += 1 if take else 0
            result["clips"][text] = {k: clip.get(k) for k in ("file", "duration", "words", "caption")} | ({"recorded": True} if take else {})
            scene["audio"] = {"src": "narration/" + clip["file"], "duration": clip["duration"]} | ({"recorded": True} if take else {})
            if clip.get("words") and clip.get("caption") == scene["vo"]:
                scene["audio"]["words"] = clip["words"]
            if not scene.get("fixed"):
                scene["duration"] = beat_seconds(clip["duration"], settings["pause"])
        return result

    def narrate_script(self, script_id: str, force: bool = False, progress=None) -> dict:
        """Synthesize every beat without a current clip (all of them with force), then drop clips nothing uses."""
        script = self.script(script_id)
        channel = find_channel(self.root, script["channel"])
        if channel["kind"] != "video":
            raise ValueError("Only video scripts have a voiceover")
        settings = self.narration_settings(channel)
        if not settings["provider"]:
            raise ValueError(f"Choose a voice for {channel['name']} first (Channels → {channel['name']} → Narration, or `studio.py narration --channel`)")
        if settings["provider"] == "recorded":
            waiting = [s["beat"] for s in script["scenes"] if (s.get("say") or s["vo"]) and not s.get("audio")]
            if waiting:
                raise ValueError(f"{channel['name']} uses your own voice; record or upload a take for: {', '.join(waiting)}")
            return {"made": 0, "beats": sum(1 for s in script["scenes"] if s.get("say") or s["vo"]), "provider": "recorded"}
        problem = tts.provider(settings["provider"]).problem(self.root)
        if problem:
            raise RuntimeError(problem)
        folder = self.path("scripts", script_id, "narration")
        folder.mkdir(parents=True, exist_ok=True)
        path, language = folder / "narration.json", channel["language"]
        manifest = load(path, {})
        clips, takes = manifest.get("clips", {}), manifest.get("recordings", {})
        wanted = {}
        for scene in script["scenes"]:
            text = scene.get("say") or scene["vo"]
            if text and tts.recording_key(text) not in takes:
                wanted.setdefault(tts.clip_key(settings, language, text), (text, scene["vo"]))
        todo = [key for key in wanted if force or key not in clips or not (folder / clips[key].get("file", "")).is_file()]
        status = {"pid": os.getpid(), "started": now(), "provider": settings["provider"], "voice": settings["voice"]}
        save(path, {"clips": clips, "recordings": takes, "status": "narrating", "progress": 0} | status)
        try:
            for n, key in enumerate(todo, 1):
                text, caption = wanted[key]
                audio = tts.speak(self.root, text, settings, language)
                (folder / f"{key}.wav").write_bytes(audio.wav())
                clips[key] = {"file": f"{key}.wav", "text": text, "caption": caption, "duration": round(audio.duration, 3),
                              "words": tts.word_times(audio, caption) if text == caption else None,
                              "settings": tts.settings_key(settings, language), "created": now()}
                save(path, {"clips": clips, "recordings": takes, "status": "narrating", "progress": round(n / len(todo), 3)} | status)
                if progress:
                    progress(n, len(todo))
        except BaseException as error:
            save(path, {"clips": clips, "recordings": takes, "status": "failed", "error": str(error) or type(error).__name__, "finished": now()} | status)
            raise
        for key in [k for k in clips if k not in wanted]:
            (folder / clips.pop(key).get("file", "")).unlink(missing_ok=True)
        save(path, {"clips": clips, "recordings": takes, "status": "done", "progress": 1, "finished": now(), "made": len(todo)} | status)
        return {"made": len(todo), "beats": len(wanted) + sum(1 for s in script["scenes"] if (s.get("say") or s["vo"]) and tts.recording_key(s.get("say") or s["vo"]) in takes),
                "provider": settings["provider"]}

    def add_take(self, script_id: str, text: str, data: bytes, name: str = "", source: str = "recorded") -> dict:
        """Your own recording of a beat's words (recorded in the studio, or an uploaded file)."""
        script = self.script(script_id)
        if find_channel(self.root, script["channel"])["kind"] != "video":
            raise ValueError("Only video scripts have a voiceover")
        lines = {scene.get("say") or scene["vo"]: scene["beat"] for scene in script["scenes"] if scene.get("say") or scene["vo"]}
        if text not in lines:
            raise ValueError("That line isn't in the script any more; reload and record the current one")
        audio = tts.prepare_take(data, name)
        folder = self.path("scripts", script_id, "narration")
        folder.mkdir(parents=True, exist_ok=True)
        key = tts.recording_key(text)
        (folder / f"rec-{key}.wav").write_bytes(audio.wav())
        path = folder / "narration.json"
        manifest = load(path, {})
        manifest.setdefault("recordings", {})[key] = {"file": f"rec-{key}.wav", "text": text, "beat": lines[text], "duration": round(audio.duration, 3),
                                                      "source": "uploaded" if source == "uploaded" else "recorded", "name": clean_text(name, 120), "created": now()}
        save(path, manifest)
        return self.script(script_id)["narration"]

    def delete_take(self, script_id: str, key: str) -> dict:
        self.script(script_id)
        if not re.fullmatch(r"[0-9a-f]{12}", key or ""):
            raise KeyError(f"Unknown take: {key}")
        path = self.path("scripts", script_id, "narration", "narration.json")
        manifest = load(path, {})
        take = manifest.get("recordings", {}).pop(key, None)
        if not take:
            raise KeyError(f"Unknown take: {key}")
        self.path("scripts", script_id, "narration", take["file"]).unlink(missing_ok=True)
        save(path, manifest)
        return self.script(script_id)["narration"]

    def captions_srt(self, script_id: str) -> str:
        """The voiceover as SubRip captions: word-timed where the provider gave timings, else by beat."""
        script = self.script(script_id)
        cues, start = [], 0.0
        for scene in script["scenes"]:
            words, timed = scene["vo"].split(), (scene.get("audio") or {}).get("words")
            if words:
                if not timed or len(timed) != len(words):
                    span = (scene.get("audio") or {}).get("duration") or scene["duration"]
                    weights = [1 + 0.09 * len(re.sub(r"\W", "", w)) for w in words]
                    total, acc, timed = sum(weights), 0.0, []
                    for weight in weights:
                        timed.append([span * acc / total, span * (acc + weight) / total])
                        acc += weight
                for i in range(0, len(words), 7):
                    chunk = list(range(i, min(i + 7, len(words))))
                    cues.append((start + timed[chunk[0]][0], start + timed[chunk[-1]][1], " ".join(words[j] for j in chunk)))
            start += scene["duration"]
        return tts.srt(cues)

    # publishing: scripts/<id>/publish.json holds the post's details; publish/state.json the upload and its result

    def publish_details(self, script_id: str) -> dict:
        script = self.script(script_id)
        channel = find_channel(self.root, script["channel"])
        saved = load(self.path("scripts", script_id, "publish.json"), {})
        defaults = channel_publishing(self.root, channel["id"])["defaults"] if channel["kind"] == "video" else {}
        details = pub.clean_meta({**{k: v for k, v in defaults.items() if k in pub.DEFAULT_META}, **saved})
        details["title"] = details["title"] or script["title"][:100]
        return details | {"sources": self.story_sources(script["story"]), "credits": self.used_credits(script)}

    def save_publish_details(self, script_id: str, details: dict) -> dict:
        self.script(script_id)
        details = {k: v for k, v in details.items() if k not in ("sources", "credits")}
        saved = load(self.path("scripts", script_id, "publish.json"), {})
        cleaned = pub.clean_meta(saved | details)
        save(self.path("scripts", script_id, "publish.json"), {k: cleaned[k] for k in saved | details})
        return self.publish_details(script_id)

    def story_sources(self, story_id: str) -> list[str]:
        """Source URLs from the story notes' Sources section, for the description."""
        try:
            notes = self.story(story_id)["notes"]
        except KeyError:
            return []
        section = re.split(r"(?im)^#+\s*sources\s*$", notes)
        urls = re.findall(r"https?://[^\s)>\]]+", section[-1] if len(section) > 1 else "")
        return list(dict.fromkeys(u.rstrip(".,;") for u in urls))[:10]

    def used_credits(self, script: dict) -> list[str]:
        credits = []
        for scene in script["scenes"]:
            credit = (scene.get("image") or {}).get("credit") or (scene["data"].get("credit") if scene["type"] == "image" else "")
            if credit:
                credits.append(credit)
        return list(dict.fromkeys(credits))

    def publish_status(self, script_id: str) -> dict:
        state = load(self.path("scripts", script_id, "publish", "state.json"), {})
        status = state.get("status") or "none"
        if status == "uploading" and state.get("pid") not in (None, os.getpid()) and not pid_alive(state.get("pid")):
            status, state["error"] = "failed", "The upload stopped before it finished; publish again to resume"
        return {key: state.get(key) for key in ("platform", "progress", "url", "id", "started", "finished", "notes", "account", "stats", "privacy",
                                               "publish_at")} | {"status": status, "error": state.get("error", "") if status == "failed" else ""}

    def publish_script(self, script_id: str, progress=None) -> dict:
        """Upload the rendered MP4 to the channel's account with the post's details; mark the script published."""
        script = self.script(script_id)
        channel = find_channel(self.root, script["channel"])
        if channel["kind"] != "video":
            raise ValueError("Text posts are shared by hand: copy the post, then paste its link under Published")
        video = script["video"] or {}
        if not video.get("ready"):
            raise RuntimeError("Render the video first (studio.py render --script, or Render MP4)")
        if video.get("stale"):
            raise RuntimeError("The script, images, voice or look changed since the last render; render again before publishing")
        chosen, tokens, account = channel_tokens(self.root, channel["id"])
        details = self.publish_details(script_id)
        if chosen.id == "instagram" and details["publish_at"]:
            raise ValueError("Instagram can't schedule posts through its API; clear the time to publish now")
        if chosen.id == "tiktok" and details["publish_at"]:
            raise ValueError("TikTok can't schedule posts through its API; clear the time to publish now")
        limit = chosen.caption_limit
        description = pub.with_credits(details["description"] or details["caption"] or script["title"], details["credits"], details["sources"],
                                       details["hashtags"], 5000)
        caption = pub.with_credits(details["caption"] or (details["title"] + "\n\n" + details["description"]).strip(), details["credits"], [],
                                   details["hashtags"], limit)
        language = {"english": "en", "hindi": "hi", "hinglish": "hi"}.get(channel["language"].casefold(), "")
        meta = details | {"description": description, "caption": caption, "language": language}
        folder = self.path("scripts", script_id, "render")
        design = channel_design(self.root, channel["id"])
        extras = {"thumbnail": str(folder / "poster.jpg") if details["thumbnail"] else "", "vertical": design["aspect"] in ("9:16", "4:5"),
                  "duration": script["duration"], "cover_ms": 1600,
                  "captions": self.captions_srt(script_id) if details["captions"] and any(s["vo"] for s in script["scenes"]) else ""}
        path = self.path("scripts", script_id, "publish", "state.json")
        state = load(path, {})
        if state.get("platform") not in (None, chosen.id) or state.get("status") in ("published", "scheduled", "draft"):
            state = {}  # a new post: never resume another platform's (or a finished) upload
        state |= {"platform": chosen.id, "status": "uploading", "progress": 0, "pid": os.getpid(), "started": now(), "error": "",
                  "account": account, "privacy": meta["privacy"] or chosen.default_privacy, "publish_at": meta["publish_at"]}
        live = {k: v for k, v in state.items()}
        live["save"] = lambda: save(path, {k: v for k, v in live.items() if k != "save"})
        live["save"]()
        last = [0.0]

        def report(done, total):
            live["progress"] = round(done / total, 3) if total else 1
            if progress:
                progress(done, total)
            if time.monotonic() - last[0] > 0.5 or done == total:
                last[0] = time.monotonic()
                live["save"]()

        try:
            result = chosen.publish(self.root, tokens, account, folder / "video.mp4", meta, extras, live, report)
        except BaseException as error:
            live.update(status="failed", error=str(error) or type(error).__name__, finished=now())
            live["save"]()
            raise
        for key in ("session", "session_size", "session_file", "session_started", "container", "uploaded"):
            live.pop(key, None)
        live.update(status=result["status"], progress=1, url=result["url"], id=result["id"], notes=result.get("notes", []), finished=now())
        live["save"]()
        self.update_script(script_id, {"stage": "published", "published_url": result["url"]} if result["url"] else {"stage": "published"})
        return result

    def refresh_stats(self, script_id: str) -> dict:
        state_path = self.path("scripts", script_id, "publish", "state.json")
        state = load(state_path, {})
        if state.get("status") not in ("published", "scheduled") or not state.get("id"):
            raise ValueError("This script hasn't been published from the studio yet")
        script = self.script(script_id)
        chosen, tokens, _ = channel_tokens(self.root, script["channel"])
        if chosen.id != state.get("platform"):
            raise RuntimeError("The channel is now connected to a different platform than this post")
        stats = chosen.stats(self.root, tokens, state["id"]) | {"at": now()}
        save(state_path, load(state_path, {}) | {"stats": stats})
        return stats

    # rendering: scripts/<id>/render holds the exported composition, video.mp4, poster.jpg and render.json

    def video_status(self, script_id: str, scenes: list, channel: dict) -> dict:
        folder = self.path("scripts", script_id, "render")
        status = load(folder / "render.json", {})
        video = folder / "video.mp4"
        state = status.get("status") or ("done" if video.is_file() else "none")
        if state == "rendering" and status.get("pid") not in (None, os.getpid()) and not pid_alive(status.get("pid")):
            state = "failed"
            status["error"] = "The render stopped before it finished"
        result = {"status": state, "progress": status.get("progress", 0), "error": status.get("error", ""),
                  "finished": status.get("finished", ""), "seconds": status.get("seconds"),
                  "ready": video.is_file(), "size": video.stat().st_size if video.is_file() else 0,
                  "stale": False, "placeholders": []}
        for scene in scenes:
            src = (scene["data"].get("url") if scene["type"] == "image" else "") or (scene.get("image") or {}).get("src")
            if (scene["type"] == "image" and not src) or (src and src.startswith("media/") and not self.path("scripts", script_id, src).is_file()):
                result["placeholders"].append(scene["beat"])
        if video.is_file() and status.get("fingerprint"):
            result["stale"] = status["fingerprint"] != media_fingerprint(self.path("scripts", script_id), scenes, channel_design(self.root, channel["id"]))
        return result

    def render_script(self, script_id: str, quality: str = "high", progress=None) -> dict:
        import render as renderer
        script = self.script(script_id)
        channel = find_channel(self.root, script["channel"])
        if channel["kind"] != "video":
            raise ValueError("Only video scripts render to MP4")
        if not script["scenes"]:
            raise ValueError("The script has no beats yet")
        problems = renderer.missing_tools()
        if problems:
            raise RuntimeError("Rendering needs: " + "; ".join(problems))
        folder = self.path("scripts", script_id, "render")
        status_path = folder / "render.json"
        fingerprint = media_fingerprint(self.path("scripts", script_id), script["scenes"], channel_design(self.root, channel["id"]))
        # The previous video stays downloadable while this one renders, so keep what it was rendered from.
        status = {"status": "rendering", "progress": 0, "pid": os.getpid(), "started": now(), "quality": quality,
                  "fingerprint": load(status_path, {}).get("fingerprint")}
        save(status_path, status)
        last = [0.0]

        def report(done, total):
            if progress:
                progress(done, total)
            if time.monotonic() - last[0] > 0.5 or done == total:
                last[0] = time.monotonic()
                save(status_path, status | {"progress": round(done / total, 3)})

        try:
            narration = script["narration"] or {}
            if narration.get("provider") not in (None, "", "recorded") and narration.get("missing"):
                save(status_path, status | {"phase": "voiceover"})
                self.narrate_script(script_id)
                script = self.script(script_id)
                fingerprint = media_fingerprint(self.path("scripts", script_id), script["scenes"], channel_design(self.root, channel["id"]))
                save(status_path, status)
            self.export_script(script_id)
            track, clips, start = None, [], 0.0
            for scene in script["scenes"]:
                if scene.get("audio"):
                    clips.append((start, folder / scene["audio"]["src"]))
                start += scene["duration"]
            if clips:
                track = renderer.mix_voiceover(clips, total_duration(script["scenes"]), folder / "voiceover.wav")
            result = renderer.render(folder, folder / "video.mp4", quality=quality, progress=report, poster=folder / "poster.jpg", audio=track)
        except BaseException as error:
            save(status_path, status | {"status": "failed", "error": str(error) or type(error).__name__, "finished": now()})
            raise
        save(status_path, status | {"status": "done", "progress": 1, "finished": now(), "seconds": result["seconds"],
                                    "fingerprint": fingerprint, "duration": result["duration"]})
        credits = [m for m in self.media(script_id) if m.get("credit")]
        if credits:
            write_text(folder / "credits.txt", "".join(f"{m['credit']}{' – ' + m['source'] if m.get('source') else ''}\n" for m in credits))
        if any(scene.get("vo") for scene in script["scenes"]):
            write_text(folder / "captions.srt", self.captions_srt(script_id))
        return result | {"credits": [m["credit"] for m in credits]}

    def delete_script(self, script_id: str) -> None:
        self.script(script_id)
        self._trash("scripts", script_id)

    # comments: anchored to a quote in the script text; open ones are read in the order they appear

    def comments(self, script_id: str, text: str | None = None) -> list[dict]:
        listed = load(self.path("scripts", script_id, "comments.json"), {"comments": []})["comments"]
        text = self.path("scripts", script_id, "script.md").read_text(encoding="utf-8") if text is None else text
        for comment in listed:
            comment["position"] = comment_position(text, comment)
        # Comments on the whole script (no quote) and ones whose quote was rewritten away come last.
        return sorted(listed, key=lambda c: (c["position"] < 0, c["position"] if c["position"] >= 0 else 0, c.get("created", "")))

    def add_comment(self, script_id: str, body: str, quote: str = "", offset: int | None = None) -> dict:
        self.script(script_id)
        body, quote = (body or "").strip(), (quote or "").strip()
        if not body:
            raise ValueError("A comment needs some text")
        path = self.path("scripts", script_id, "comments.json")
        data = load(path, {"comments": []})
        comment = {"id": unique_id("c-" + dt.datetime.now().strftime("%m%d%H%M%S"), {c["id"] for c in data["comments"]}),
                   "quote": quote, "offset": offset if isinstance(offset, int) and offset >= 0 else None,
                   "body": body, "created": now()}
        data["comments"].append(comment)
        save(path, data)
        return comment

    def update_comment(self, script_id: str, comment_id: str, changes: dict) -> dict:
        path = self.path("scripts", script_id, "comments.json")
        data = load(path, {"comments": []})
        comment = self._find(data["comments"], comment_id, "comment")
        if "body" in changes:
            if not str(changes["body"]).strip():
                raise ValueError("A comment needs some text")
            comment["body"] = str(changes["body"]).strip()
        if "resolved" in changes:
            if changes["resolved"]:
                comment["resolved_at"] = now()
                if changes.get("reply"):
                    comment["reply"] = str(changes["reply"]).strip()
            else:
                comment.pop("resolved_at", None)
                comment.pop("reply", None)
        save(path, data)
        return comment

    def delete_comment(self, script_id: str, comment_id: str) -> None:
        path = self.path("scripts", script_id, "comments.json")
        data = load(path, {"comments": []})
        self._find(data["comments"], comment_id, "comment")
        data["comments"] = [c for c in data["comments"] if c["id"] != comment_id]
        save(path, data)

    # whole state for the UI

    def state(self) -> dict:
        runs = self.runs()
        return {"workspace": str(self.root), "default_workspace": self.root == workspace_path(None) and not os.environ.get("VID_STUDIO_HOME"),
                "project": self.ws.name, "settings": self.settings(), "topics": self.topics(), "sources": self.sources(),
                "findings": self.findings(), "runs": runs[-20:], "stories": self.stories(), "scripts": self.scripts(),
                "channels": channels(self.root)}

    # helpers

    def _find(self, records: list, record_id: str, label: str) -> dict:
        for record in records:
            if record.get("id") == record_id:
                return record
        raise KeyError(f"Unknown {label}: {record_id}")

    def _trash(self, kind: str, item_id: str) -> None:
        trash = self.path(kind, ".trash")
        trash.mkdir(exist_ok=True)
        self.path(kind, item_id).rename(trash / f"{item_id}-{int(time.time())}")

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


def beat_seconds(audio_seconds: float, pause: float) -> float:
    """A narrated beat lasts as long as its voiceover plus a pause, in tenths, never under 1.5 s (as in the UI)."""
    return min(60.0, max(1.5, math.floor((audio_seconds + pause) * 10 + 0.5) / 10))


ASPECT_SIZES = {"9:16": (1080, 1920), "16:9": (1920, 1080), "1:1": (1080, 1080), "4:5": (1080, 1350)}


# ---------------------------------------------------------------- channels: <root>/channels.json, shared by every project

LANGUAGES = ["English", "Hindi", "Hinglish"]
CHANNEL_KINDS = ["video", "post"]
CHANNEL_KEYS = {"name", "platform", "kind", "language", "audience", "format"}
DEFAULT_FORMATS = load(ASSETS / "channel-formats.json")  # a new channel starts with the format for its kind


def channels(root: Path) -> list[dict]:
    return load(root / "channels.json", {"channels": []})["channels"]


def find_channel(root: Path, value: str) -> dict:
    wanted = str(value or "").strip().casefold()
    for channel in channels(root):
        if wanted in (channel["id"], channel["name"].casefold()):
            return channel
    raise KeyError(f"No channel {value!r}. Channels: {', '.join(c['name'] for c in channels(root)) or 'none yet'}")


def clean_channel(channel: dict, changes: dict) -> dict:
    for key, value in changes.items():
        if key not in CHANNEL_KEYS:
            raise ValueError(f"Unknown channel setting: {key}")
        channel[key] = str(value or "").strip()
    if not channel.get("name"):
        raise ValueError("A channel needs a name")
    if channel.get("kind") not in CHANNEL_KINDS:
        raise ValueError("Kind must be video (a script for a video) or post (a text post, like WhatsApp)")
    return channel


def add_channel(root: Path, changes: dict) -> dict:
    data = load(root / "channels.json", {"channels": []})
    kind = changes.get("kind") or "video"
    changes = {key: value for key, value in changes.items() if key != "format" or str(value or "").strip()}  # empty: the default
    channel = clean_channel({"platform": "", "language": "English", "audience": "", "format": DEFAULT_FORMATS.get(kind, "")},
                            {"kind": kind} | changes)
    if any(c["name"].casefold() == channel["name"].casefold() for c in data["channels"]):
        raise ValueError(f"A channel called {channel['name']!r} already exists")
    channel = {"id": unique_id(slugify(channel["name"], 40), {c["id"] for c in data["channels"]})} | channel | {"created": now()}
    data["channels"].append(channel)
    save(root / "channels.json", data)
    channel_folder(root, channel["id"]).mkdir(parents=True, exist_ok=True)
    return channel


def update_channel(root: Path, channel_id: str, changes: dict) -> dict:
    data = load(root / "channels.json", {"channels": []})
    channel = next((c for c in data["channels"] if c["id"] == channel_id), None)
    if not channel:
        raise KeyError(f"Unknown channel: {channel_id}")
    clean_channel(channel, changes)
    if any(c["name"].casefold() == channel["name"].casefold() and c["id"] != channel_id for c in data["channels"]):
        raise ValueError(f"A channel called {channel['name']!r} already exists")
    save(root / "channels.json", data)
    return channel


def delete_channel(root: Path, channel_id: str) -> None:
    folder = channel_folder(root, channel_id)
    used = [f"{Studio(folder, root).settings().get('name')}: {s['title']}" for folder in project_dirs(root)
            for s in Studio(folder, root).scripts() if s["channel"] == channel_id]
    if used:
        raise ValueError("Scripts still use this channel (" + "; ".join(used[:3]) + ("…" if len(used) > 3 else "") + "). Delete them first.")
    disconnect_channel(root, channel_id)
    data = load(root / "channels.json", {"channels": []})
    data["channels"] = [c for c in data["channels"] if c["id"] != channel_id]
    save(root / "channels.json", data)
    if folder.is_dir():
        shutil.rmtree(folder)


# ---------------------------------------------------------------- channel looks and script-writing voice

def deep_merge(base: dict, changes: dict) -> dict:
    result = json.loads(json.dumps(base))
    for key, value in changes.items():
        result[key] = deep_merge(result[key], value) if isinstance(result.get(key), dict) and isinstance(value, dict) else value
    return result


def check_keys(value, allowed, label: str) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    unknown = set(value) - set(allowed)
    if unknown:
        raise ValueError(f"Unknown {label} key: {', '.join(sorted(unknown))}. Allowed: {', '.join(sorted(allowed))}")


def check_text(value, label: str, limit: int = 4000) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be text")
    if len(value) > limit:
        raise ValueError(f"{label} must be at most {limit} characters")
    return value


def check_number(value, label: str, low, high, integer: bool = False) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or (integer and not isinstance(value, int)):
        raise ValueError(f"{label} must be {'an integer' if integer else 'a number'} from {low} to {high}")
    if not low <= value <= high or not math.isfinite(value):
        raise ValueError(f"{label} must be from {low} to {high}")


def check_strings(value, label: str, limit: int = 4000, count: int = 100) -> list[str]:
    if not isinstance(value, list) or len(value) > count:
        raise ValueError(f"{label} must be a list of at most {count} strings")
    return [check_text(item, f"{label}[{i}]", limit) for i, item in enumerate(value, 1)]


def channel_folder(root: Path, channel_id: str) -> Path:
    if not isinstance(channel_id, str) or not re.fullmatch(r"[a-z0-9-]+", channel_id):
        raise KeyError(f"Invalid channel id: {channel_id!r}; use a channel id containing lowercase letters, numbers, and hyphens")
    channel = find_channel(root, channel_id)
    if channel["id"] != channel_id:
        raise KeyError(f"Unknown channel id: {channel_id}")
    base = (root / "channels").resolve()
    folder = base / channel_id
    if not folder.resolve().is_relative_to(base):
        raise ValueError(f"Channel folder must stay inside {base}")
    return folder


def presets() -> list[dict]:
    listed = [load(path) for path in PRESETS_DIR.glob("*.json") if path.is_file()]
    if not any(p["id"] == DEFAULT_PRESET for p in listed):
        listed.append({"id": DEFAULT_PRESET, "name": "Bold Explainer", "description": "Bold numbers, energetic motion, and clear captions.",
                       "design": {k: v for k, v in deep_merge(DEFAULT_DESIGN, {}).items() if k != "preset"}})
    return sorted(listed, key=lambda p: (p["name"].casefold(), p["id"]))


def fonts() -> dict:
    return load(FONT_CATALOG, {"fonts": []})


def merged_design(design: dict) -> dict:
    named = next((p for p in presets() if p["id"] == design.get("preset", DEFAULT_PRESET)), None)
    if named is None:
        named = next(p for p in presets() if p["id"] == DEFAULT_PRESET)
        design = design | {"preset": DEFAULT_PRESET}
    return deep_merge(deep_merge(DEFAULT_DESIGN, named["design"] | {"preset": named["id"]}), design)


HINDI_PRESET = "neon-finance"  # the default look must use Devanagari fonts when the channel writes in Hindi or Hinglish


def language_design(root: Path, channel_id: str, design: dict) -> dict:
    if not design.get("preset") and find_channel(root, channel_id).get("language", "").casefold() in ("hindi", "hinglish") \
            and any(p["id"] == HINDI_PRESET for p in presets()):
        design = design | {"preset": HINDI_PRESET}
    return merged_design(design)


def channel_design(root: Path, channel_id: str) -> dict:
    return language_design(root, channel_id, load(channel_folder(root, channel_id) / "design.json", {}))


def save_design(root: Path, channel_id: str, design: dict) -> dict:
    folder = channel_folder(root, channel_id)
    check_keys(design, DEFAULT_DESIGN, "design")
    if "preset" in design and (not isinstance(design["preset"], str) or design["preset"] not in {p["id"] for p in presets()}):
        raise ValueError("design.preset must be a preset id from studio.py presets")
    design = language_design(root, channel_id, design)
    for key, default in DEFAULT_DESIGN.items():
        if isinstance(default, dict):
            check_keys(design[key], default, f"design.{key}")
    enums = {
        "aspect": ["9:16", "16:9", "1:1", "4:5"], "type.display_case": ["upper", "title", "none"],
        "motion.energy": ["calm", "medium", "high"], "motion.easing": ["smooth", "snappy", "bouncy"],
        "motion.transition": ["cut", "fade", "slide", "zoom", "wipe"],
        "captions.style": ["none", "plain", "boxed", "karaoke", "highlight", "underline", "pop"], "captions.position": ["lower", "middle", "upper"],
        "captions.highlight": ["accent", "accent2", "text"], "background.style": ["solid", "gradient", "grain", "paper"],
        "cards.style": ["glass", "solid", "flat"],
        "images.layout": ["auto", "full"],
        "background.pattern": ["none", "grid", "dots", "lines"], "logo.position": ["top-left", "top-right", "bottom-left", "bottom-right"],
        "captions.size": ["small", "medium", "large"], "images.treatment": ["natural", "dim", "mono", "duotone"],
    }
    def value_at(key):
        group, dot, sub = key.partition(".")
        return design[group][sub] if dot else design[group]
    for key, allowed in enums.items():
        if value_at(key) not in allowed:
            raise ValueError(f"design.{key} must be one of: {', '.join(allowed)}")
    for key, low, high, integer in (("type.scale", 0.8, 1.3, False), ("type.display_weight", 400, 900, True),
                                    ("type.tracking", -0.05, 0.1, False), ("captions.max_words", 1, 8, True), ("radius", 0, 48, False)):
        check_number(value_at(key), f"design.{key}", low, high, integer)
    for key, value in design["colors"].items():
        if not isinstance(value, str) or not re.fullmatch(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})", value):
            raise ValueError(f"design.colors.{key} must be a hex color like #FC3 or #FFD23F")
    catalog = {f["family"]: f for f in fonts()["fonts"]} if FONT_CATALOG.exists() else None
    language = find_channel(root, channel_id)["language"].casefold()
    for key, value in design["fonts"].items():
        check_text(value, f"design.fonts.{key}", 200)
        if catalog is not None:
            if value not in catalog:
                raise ValueError(f"design.fonts.{key}: unknown family {value!r}; choose a family from studio.py fonts")
            if key in ("display", "body") and language in ("hindi", "hinglish") and not catalog[value]["devanagari"]:
                raise ValueError(f"design.fonts.{key}: {value!r} does not support Devanagari; choose a family from studio.py fonts --devanagari for {language.title()}")
    for group in ("sources", "progress"):
        if not isinstance(design[group]["show"], bool):
            raise ValueError(f"design.{group}.show must be true or false")
    check_text(design["logo"]["text"], "design.logo.text", 200)
    css = check_text(design["custom_css"], "design.custom_css", 20000)
    if re.search(r"</style|<script", css, re.I):
        raise ValueError("design.custom_css cannot contain </style or <script; provide CSS only")
    save(folder / "design.json", design)
    return design


def voice_defaults() -> dict:
    return deep_merge(DEFAULT_VOICE, load(VOICE_DEFAULT_PATH, {}))


def channel_voice(root: Path, channel_id: str) -> dict:
    return deep_merge(voice_defaults(), load(channel_folder(root, channel_id) / "voice.json", {}))


def save_voice(root: Path, channel_id: str, voice: dict) -> dict:
    folder = channel_folder(root, channel_id)
    check_keys(voice, DEFAULT_VOICE, "voice")
    voice = deep_merge(voice_defaults(), voice)
    check_number(voice["length_seconds"], "voice.length_seconds", 10, 600)
    check_number(voice["words_per_minute"], "voice.words_per_minute", 80, 260)
    check_keys(voice["tone"], DEFAULT_VOICE["tone"], "voice.tone")
    for key, value in voice["tone"].items():
        check_number(value, f"voice.tone.{key}", 0, 100)
    for key in ("persona", "open", "close", "cta"):
        check_text(voice[key], f"voice.{key}", 4000)
    for key in ("hook_styles", "do", "dont"):
        check_strings(voice[key], f"voice.{key}")
    if any(style not in HOOK_STYLES for style in voice["hook_styles"]):
        raise ValueError(f"voice.hook_styles must contain only: {', '.join(HOOK_STYLES)}")
    if not isinstance(voice["examples"], list) or len(voice["examples"]) > 30:
        raise ValueError("voice.examples must be a list of at most 30 examples")
    for i, example in enumerate(voice["examples"], 1):
        check_keys(example, {"title", "text", "why"}, f"voice.examples[{i}]")
        for key in ("title", "text", "why"):
            check_text(example.get(key), f"voice.examples[{i}].{key}", 20000 if key == "text" else 4000)
    save(folder / "voice.json", voice)
    return voice


def channel_narration(root: Path, channel_id: str) -> dict:
    """The channel's text-to-speech settings; an empty provider means videos render without a voiceover."""
    return tts.clean_settings(load(channel_folder(root, channel_id) / "narration.json", {}))


def save_narration(root: Path, channel_id: str, settings: dict) -> dict:
    folder = channel_folder(root, channel_id)
    if find_channel(root, channel_id)["kind"] != "video":
        raise ValueError("Only video channels have a voiceover")
    settings = tts.clean_settings(deep_merge(load(folder / "narration.json", {}), settings) if isinstance(settings, dict) else settings)
    save(folder / "narration.json", settings)
    return settings


def narration_style(root: Path, channel_id: str, settings: dict) -> dict:
    """Without a style line of its own, a voice that takes instructions reads in the channel's persona."""
    if settings.get("style"):
        return settings
    persona = channel_voice(root, channel_id).get("persona", "").strip()
    return settings | ({"style": f"Speak as this person, to one listener, naturally and not like an announcer: {persona}"} if persona else {})


def clone_channel_voice(root: Path, channel_id: str, name: str, samples: list[tuple[str, bytes]], consent: bool, remove_noise: bool = True) -> dict:
    """Make an ElevenLabs voice from the user's own recordings, keep the samples, and make it the channel's narrator."""
    channel = find_channel(root, channel_id)
    folder = channel_folder(root, channel["id"])
    if channel["kind"] != "video":
        raise ValueError("Only video channels have a voiceover")
    if consent is not True:
        raise ValueError("Confirm that the recordings are your own voice, or that you have the speaker's permission")
    made = tts.clone_voice(root, name, samples, f"{channel['name']} narrator, recorded in Vid Studio", remove_noise)
    kept = folder / "voice-samples"
    kept.mkdir(parents=True, exist_ok=True)
    for i, (filename, data) in enumerate(samples, 1):
        suffix = re.sub(r"[^a-z0-9.]", "", Path(filename or "sample.webm").suffix.lower())[:8] or ".webm"
        (kept / f"{dt.date.today().isoformat()}-{made['voice_id'][:8]}-{i}{suffix}").write_bytes(data)
    settings = save_narration(root, channel["id"], {"provider": "elevenlabs", "voice": made["voice_id"],
                                                     "model": channel_narration(root, channel["id"]).get("model") if channel_narration(root, channel["id"])["provider"] == "elevenlabs" else ""})
    return made | {"narration": settings, "name": name}


def speak_sample(root: Path, channel_id: str, text: str = "", changes: dict | None = None) -> bytes:
    """A short WAV in the channel's voice (with unsaved changes applied), for trying voices."""
    channel = find_channel(root, channel_id)
    settings = tts.clean_settings(deep_merge(channel_narration(root, channel["id"]), changes or {}))
    text = (text or "").strip()[:600] or tts.SAMPLE_TEXT.get(channel["language"], tts.SAMPLE_TEXT["English"])
    return tts.speak(root, text, narration_style(root, channel["id"], settings), channel["language"]).wav()


# ---------------------------------------------------------------- publishing: channels/<id>/publish.json, tokens in .secrets.json

PUBLISH_DEFAULT_KEYS = {"privacy", "category", "made_for_kids", "synthetic", "hashtags", "captions", "thumbnail"}
OAUTH_PENDING: dict[str, dict] = {}  # state → the sign-in it belongs to, for ten minutes


def channel_publishing(root: Path, channel_id: str) -> dict:
    """Where the channel publishes: its platform, the connected account, and defaults for new posts."""
    channel = find_channel(root, channel_id)
    data = load(channel_folder(root, channel["id"]) / "publish.json", {})
    chosen = data.get("platform") or pub.guess_platform(channel.get("platform", ""))
    connected = bool(data.get("account")) and bool(pub.read_tokens(root, channel["id"]))
    info = pub.platform(chosen).describe(root) if chosen in pub.PLATFORMS else None
    defaults = {"privacy": info["default_privacy"] if info else "", "category": "27", "made_for_kids": False, "synthetic": False,
                "hashtags": [], "captions": True, "thumbnail": True} | data.get("defaults", {})
    problem = ("" if connected else f"Connect {channel['name']} to its {info['name']} account" if info
               else "Posts are shared by hand" if channel["kind"] == "post" else "Choose where this channel publishes")
    return {"platform": chosen if info else "", "account": data.get("account") if connected else None, "connected": connected,
            "connected_at": data.get("connected_at", "") if connected else "", "defaults": defaults, "problem": problem, "info": info,
            "kind": channel["kind"]}


def save_publishing(root: Path, channel_id: str, changes: dict) -> dict:
    folder = channel_folder(root, channel_id)
    channel = find_channel(root, channel_id)
    check_keys(changes, {"platform", "defaults"}, "publishing")
    data = load(folder / "publish.json", {})
    if "platform" in changes:
        if changes["platform"] not in ("", *pub.PLATFORMS):
            raise ValueError(f"publishing.platform must be one of: {', '.join(pub.PLATFORMS)}")
        if channel["kind"] != "video" and changes["platform"]:
            raise ValueError("Text-post channels are shared by hand; only video channels publish to a platform")
        if changes["platform"] != data.get("platform"):
            disconnect_channel(root, channel_id)
            data = load(folder / "publish.json", {})
        data["platform"] = changes["platform"]
    if "defaults" in changes:
        check_keys(changes["defaults"], PUBLISH_DEFAULT_KEYS, "publishing.defaults")
        merged = data.get("defaults", {}) | changes["defaults"]
        cleaned = pub.clean_meta({k: v for k, v in merged.items()})
        chosen = data.get("platform") or pub.guess_platform(channel.get("platform", ""))
        allowed = {v for v, _ in pub.platform(chosen).privacy_options} if chosen in pub.PLATFORMS else set()
        if cleaned["privacy"] and allowed and cleaned["privacy"] not in allowed:
            raise ValueError(f"publishing.defaults.privacy must be one of: {', '.join(sorted(allowed))}")
        data["defaults"] = {k: cleaned[k] for k in merged}
    save(folder / "publish.json", data)
    return channel_publishing(root, channel_id)


def connect_token(root: Path, channel_id: str, platform_id: str, token: str) -> dict:
    """Connect with an access token the user pasted (Instagram; TikTok without an app of their own)."""
    channel = find_channel(root, channel_id)
    chosen = pub.platform(platform_id)
    tokens = chosen.from_token(root, token)
    account = chosen.account(root, tokens)
    return finish_connect(root, channel["id"], chosen.id, tokens, account)


def finish_connect(root: Path, channel_id: str, platform_id: str, tokens: dict, account: dict) -> dict:
    folder = channel_folder(root, channel_id)
    if find_channel(root, channel_id)["kind"] != "video":
        raise ValueError("Only video channels publish to a platform")
    pub.save_tokens(root, channel_id, tokens)
    data = load(folder / "publish.json", {})
    folder.mkdir(parents=True, exist_ok=True)
    save(folder / "publish.json", data | {"platform": platform_id, "account": account, "connected_at": now()})
    return channel_publishing(root, channel_id)


def start_oauth(root: Path, channel_id: str, platform_id: str, redirect: str, captions: bool = False) -> str:
    """The provider's sign-in URL; its callback (finish_oauth) connects the channel."""
    channel = find_channel(root, channel_id)
    if channel["kind"] != "video":
        raise ValueError("Only video channels publish to a platform")
    chosen = pub.platform(platform_id)
    if not chosen.oauth:
        raise ValueError(f"{chosen.name} connects with a pasted access token")
    problem = chosen.app_problem(root)
    if problem:
        raise RuntimeError(problem)
    for state in [k for k, v in OAUTH_PENDING.items() if v["created"] < time.time() - 600]:
        OAUTH_PENDING.pop(state, None)
    state = pub.random.token_urlsafe(24)
    verifier, b64, hexed = pub.pkce()
    OAUTH_PENDING[state] = {"root": str(root), "channel": channel["id"], "platform": chosen.id, "verifier": verifier,
                            "redirect": redirect, "created": time.time()}
    return chosen.auth_url(root, redirect, state, (b64, hexed), captions=captions)


def finish_oauth(root: Path, state: str, code: str) -> dict:
    pending = OAUTH_PENDING.pop(state or "", None)
    if not pending or pending["root"] != str(root) or pending["created"] < time.time() - 600:
        raise ValueError("This sign-in link expired or was already used; start again from the channel page")
    chosen = pub.platform(pending["platform"])
    tokens = chosen.exchange(root, code, pending["redirect"], pending["verifier"])
    return finish_connect(root, pending["channel"], chosen.id, tokens, chosen.account(root, tokens)) | {"channel": pending["channel"]}


def disconnect_channel(root: Path, channel_id: str) -> None:
    folder = channel_folder(root, channel_id)
    data = load(folder / "publish.json", {})
    tokens = pub.read_tokens(root, channel_id)
    if tokens and data.get("platform") in pub.PLATFORMS:
        try:
            pub.platform(data["platform"]).revoke(root, tokens)
        except pub.PublishError:
            pass  # offline: forgetting the token locally still disconnects the studio
    pub.save_tokens(root, channel_id, None)
    if data:
        data.pop("account", None)
        data.pop("connected_at", None)
        save(folder / "publish.json", data)


def channel_tokens(root: Path, channel_id: str) -> tuple:
    """(platform, fresh tokens, account) for a connected channel, refreshing and saving tokens as needed."""
    info = channel_publishing(root, channel_id)
    if not info["connected"]:
        raise RuntimeError(info["problem"])
    chosen = pub.platform(info["platform"])
    tokens = pub.read_tokens(root, channel_id)
    fresh = chosen.refresh(root, tokens)
    if fresh != tokens:
        pub.save_tokens(root, channel_id, fresh)
    return chosen, fresh, info["account"]


# ---------------------------------------------------------------- media and rendering

MAX_MEDIA_BYTES = 15_000_000


def image_kind(data: bytes) -> str | None:
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def media_fingerprint(script_folder: Path, scenes: list, design: dict) -> str:
    digest = hashlib.sha1(json.dumps([scenes, design], sort_keys=True).encode())
    media = script_folder / "media"
    for path in sorted(media.glob("*")) if media.is_dir() else []:
        stat = path.stat()
        digest.update(f"{path.name}:{stat.st_size}:{int(stat.st_mtime)}".encode())
    return digest.hexdigest()[:16]


def pid_alive(pid) -> bool:
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError, TypeError):
        return False


def fetch_image(url: str) -> tuple[bytes, str]:
    """Download an image URL; returns (bytes, a file name to keep)."""
    if not re.match(r"^https?://", url or ""):
        raise ValueError("Image URLs must start with http:// or https://")
    data, _, final = fetch(url, timeout=40)
    name = Path(urllib.parse.urlsplit(final).path).name or "image"
    return data, urllib.parse.unquote(name)


# ---------------------------------------------------------------- script beats and scenes

def spoken_text(text: str) -> str:
    text = re.sub(r"!?\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[(\d+(?:\s*[,–—-]\s*\d+)*)\]", "", text)
    text = re.sub(r"[*_`]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def word_count(text: str) -> int:
    return sum(any(char.isalnum() for char in word) for word in spoken_text(text).split())


def total_duration(scenes: list[dict]) -> float:
    return round(sum(scene["duration"] for scene in scenes), 1)


UNIT_HINT = re.compile(r"[\d%₹$€£]|index|score|points|rank|rating|lakh|crore|litre|liter|kg|km|hour|minute|day|month|year|"
                       r"रुपये|लाख|करोड़|लीटर|साल|महीने|घंटे|मिनट|दिन", re.I)


MACHINE_PHRASES = [
    "here's why", "here's the catch", "here's the thing", "the kicker", "plot twist", "let's dive", "let's get into",
    "without further ado", "let that sink in", "read that again", "this changes everything", "game-changer", "game changer",
    "until it doesn't", "let's check", "buckle up", "stay tuned", "but wait", "the answer might surprise", "in today's",
    "it's important to note", "it's worth mentioning", "plays a crucial role", "a testament to", "delve",
    "seamless", "in conclusion", "to sum up", "smash that", "like, share and subscribe", "have you ever wondered",
    "follow for more", "follow to keep up", "imagine a world", "picture this", "ever wondered", "let's break it down",
    "let's break this down", "everything you need to know", "here's what you need to know", "you won't believe",
    "nobody talks about", "no one talks about", "shocked everyone", "mind-blowing", "mind blowing", "at the end of the day",
    "in a nutshell", "revolutionize", "revolutionise", "cutting-edge", "ever-evolving", "tapestry", "hey guys", "hi guys",
    "दोस्तों", "आपको बता दें", "गौरतलब है", "तो चलिए", "आज की इस वीडियो", "अंत तक ज़रूर",
]


# First-person stories are only true if the channel's persona lived them (script-craft.md §3).
ANECDOTE_PHRASES = ["my friend", "my uncle", "my aunt", "my cousin", "my neighbour", "my neighbor", "i remember when",
                    "when i was", "i tried this", "मेरे दोस्त", "मेरे एक दोस्त", "मेरे चाचा", "मेरे मामा", "मेरी दोस्त"]
NOT_X_ITS_Y = re.compile(r"\b(?:it|this|that)(?:'s| is| isn't) not\b[^.?!]{0,40}[.,;—–-]\s*(?:it|this|that)(?:'s| is)\b|"
                         r"\b(?:it|this|that) isn't\b[^.?!]{0,40}[.;—–-]\s*(?:it|this|that)(?:'s| is)\b")


def voice_warnings(scene: dict) -> list[str]:
    """Spoken patterns that make a script sound generated (script-craft.md §3, §6 and §10)."""
    spoken = spoken_text(scene["vo"])
    low = spoken.casefold().replace("’", "'")
    found = [p for p in MACHINE_PHRASES if p in low]
    warnings = [f"{scene['beat']}: \"{p}\" sounds machine-made; say the fact itself" for p in found]
    named = re.search(r"\b[Mm]eet ([A-Z][a-z]+)\b", spoken)
    if named:
        warnings.append(f"{scene['beat']}: \"Meet {named[1]}\" reads as an invented character; use a sourced case, \"you\", or \"say your…\"")
    if re.search(r"\bguys\b", low):
        warnings.append(f"{scene['beat']}: \"guys\" talks to a crowd; talk to one person (\"you\")")
    told = [p for p in ANECDOTE_PHRASES if p in low]
    if told:
        warnings.append(f"{scene['beat']}: \"{told[0]}\" is a personal story; keep it only if it really happened to the persona, "
                        "otherwise use a sourced case or \"say you…\"")
    if NOT_X_ITS_Y.search(low):
        warnings.append(f"{scene['beat']}: a \"not X, it's Y\" reframe; just say what it is and why it matters")
    if spoken.count("—") >= 2:
        warnings.append(f"{scene['beat']}: {spoken.count('—')} em dashes; that's written rhythm, so split or join the sentences the way you'd say them")
    sentences = [x for x in re.split(r"(?<=[.!?।])\s+", spoken) if x.strip()]
    run = best = 0
    for sentence in sentences:
        run = run + 1 if word_count(sentence) <= 3 else 0
        best = max(best, run)
    if best >= 3:
        warnings.append(f"{scene['beat']}: {best} fragment sentences in a row; join them into one sentence that explains")
    return warnings


def scene_warnings(scenes: list[dict]) -> list[str]:
    """On-screen problems that make a video look generated: repeated lines, slogan runs, charts without meaning."""
    warnings, seen = [], {}
    for scene in scenes:
        if scene["duration"] > 12:
            warnings.append(f"{scene['beat']} runs over 12s ({scene['duration']:.1f}s); split it into smaller beats")
        if scene.get("audio") and scene["audio"]["duration"] > scene["duration"] + 0.05:
            warnings.append(f"{scene['beat']}: the voiceover runs {scene['audio']['duration']:.1f}s but Duration: holds the beat to "
                            f"{scene['duration']:.1f}s, so it gets cut off; remove the Duration: line or shorten the line")
        warnings += voice_warnings(scene)
        data, kind = scene["data"], scene["type"]
        if word_count(scene["text"]) > 8 or (kind == "text" and word_count(data.get("text", "")) > 8):
            warnings.append(f"{scene['beat']} has more than 8 words of on-screen text; shorten it")
        # chart titles may repeat across a deliberate series; headline lines may not
        headline = data.get("title", "") if kind in ("title", "end") else data.get("text", "") if kind == "text" else ""
        for line in (scene["text"], headline):
            key = re.sub(r"[^\w\s]", "", line.replace("*", "")).casefold().split()
            if key:
                first = seen.setdefault(" ".join(key), scene["beat"])
                if first != scene["beat"]:
                    warnings.append(f"{scene['beat']} repeats on-screen text from {first} (\"{clean_text(line.replace('*', ''), 40)}\"); show something new")
        if kind in ("bars", "compare"):
            values = [str(item.get("value", "")) for item in data.get("items", []) if isinstance(item, dict)]
            numeric = [v for v in values if re.search(r"[\d\u0966-\u096F]", v)]
            if kind == "bars" and len(numeric) < len(values):
                warnings.append(f"{scene['beat']}: every bar needs a number; use a list for words")
            elif kind == "compare" and 0 < len(numeric) < len(values):
                warnings.append(f"{scene['beat']}: compare either two numbers or two short phrases, not one of each")
            elif numeric and all(re.fullmatch(r"[\d.,\s]+", v) for v in values) and not UNIT_HINT.search(data.get("title", "")):
                warnings.append(f"{scene['beat']}: the values have no unit; say what is measured (₹, %, litres, a named index) "
                                "in the values or the title. Never chart a claim as invented numbers")
        # direction.md: numbers the scenes can animate, words the screen can carry
        if kind == "stat":
            digits = len(re.findall(r"[\d\u0966-\u096F]", str(data.get("value", ""))))
            if digits > 5:
                warnings.append(f"{scene['beat']}: the stat value \"{data.get('value', '')}\" is too long to read at a glance; "
                                "write lakh or crore and round (₹29.6 lakh, 42%)")
        if kind == "compare":
            values = [str(item.get("value", "")) for item in data.get("items", []) if isinstance(item, dict)]
            if len(values) == 2 and all(re.search(r"\d", v) for v in values) and ("%" in values[0]) != ("%" in values[1]):
                warnings.append(f"{scene['beat']}: one value is a percentage and the other isn't, so the difference means nothing; "
                                "compare like with like")
        if kind == "text" and len(re.findall(r"\*[^*]+\*", data.get("text", ""))) > 1:
            warnings.append(f"{scene['beat']}: more than one *emphasis*; keep one, so it stands out")
        if kind == "list":
            items = [str(x) for x in data.get("items", [])]
            if len(items) > 5:
                warnings.append(f"{scene['beat']}: {len(items)} list items; keep 3 to 5")
            long = [x for x in items if word_count(x) > 6]
            if long:
                warnings.append(f"{scene['beat']}: list items over 6 words (\"{clean_text(long[0], 40)}\"); keep each to 2–5 words")
        if kind == "message" and not scene["text"].strip() and not scene.get("source"):
            warnings.append(f"{scene['beat']}: label the message: \"Text: Example\" for a reconstruction, or a Source: line for a real one")
    sentences = [x for scene in scenes for x in re.split(r"(?<=[.!?।])\s+", spoken_text(scene["vo"])) if word_count(x)]
    if len(sentences) >= 8:
        lengths = [word_count(x) for x in sentences]
        mean = sum(lengths) / len(lengths)
        spread = (sum((n - mean) ** 2 for n in lengths) / len(lengths)) ** 0.5
        if spread < 0.22 * mean:
            warnings.append(f"every sentence is about {round(mean)} words long; vary the rhythm: a longer explaining sentence, then a short one")
    if total_duration(scenes) >= 30 and not any(s.get("image") or s["type"] == "image" for s in scenes):
        warnings.append("no photos: give the 2–4 beats about real things, places or people an Image: line (images.md); "
                        "a video with none looks templated")
    labelled = [s for s in scenes if s["text"].strip()]
    if len(scenes) >= 4 and len(labelled) > len(scenes) / 2:
        warnings.append(f"{len(labelled)} of {len(scenes)} beats have a Text: label; keep them for naming what's on screen "
                        "or flagging an example (direction.md)")
    for i in range(2, len(scenes)):
        run = {scenes[j]["type"] for j in (i - 2, i - 1, i)}
        titles = [str(scenes[j]["data"].get("title", "")).strip().casefold() for j in (i - 2, i - 1, i)]
        series = len({t for t in titles if t}) < len([t for t in titles if t])   # a deliberate series shares a title
        if len(run) == 1 and scenes[i]["type"] != "stat" and not series:
            warnings.append(f"{scenes[i - 2]['beat']} to {scenes[i]['beat']}: three {scenes[i]['type']} scenes in a row; "
                            "change the scene type every one or two beats")
    texts = [s["beat"] for s in scenes if s["type"] == "text"]
    if len(texts) > 2:
        warnings.append(f"{len(texts)} text scenes ({', '.join(texts)}): slogans on screen read as generated; "
                        "keep at most two, and show a number, chart, list, or photo instead")
    if not scenes or scenes[-1]["type"] != "end":
        warnings.append("the last beat is missing an end scene")
    return warnings


def script_json(value) -> str:
    text = json.dumps(value, ensure_ascii=False, allow_nan=False)
    for char, escape in (("<", "\\u003c"), (">", "\\u003e"), ("&", "\\u0026"), ("\u2028", "\\u2028"), ("\u2029", "\\u2029")):
        text = text.replace(char, escape)
    return text


def parse_scenes(text: str, words_per_minute=160) -> list[dict]:
    if isinstance(words_per_minute, bool) or not isinstance(words_per_minute, (int, float)) or not math.isfinite(words_per_minute) or words_per_minute <= 0:
        raise ValueError("words_per_minute must be a positive number")
    beats, current = [], None
    for line in text.splitlines():
        line = line.strip()
        heading = re.match(r"^##\s+(.*)$", line)
        if heading:
            current = {"beat": re.sub(r"[#*_]", "", heading[1]).strip(), "lines": []}
            beats.append(current)
        elif current is not None and line and not line.startswith("#"):
            cue = re.sub(r"^[-*]\s+", "", line)
            match = re.match(r"^[*_]{0,2}(visual|text|note|image|source|duration|say)[*_]{0,2}\s*:[*_]{0,2}\s*(.*)$", cue, re.I)
            if match:
                current[match[1].lower()] = match[2].strip()
            elif line:
                current["lines"].append(line)
    scenes = []
    fields = {"title": ("title", "subtitle", "kicker"), "stat": ("value", "label", "context"),
              "quote": ("quote", "source"), "text": ("text",), "image": ("description", "url", "credit"), "end": ("title", "cta")}
    for beat in beats:
        vo = spoken_text(" ".join(beat["lines"]))
        visual = beat.get("visual")
        parts = [part.strip() for part in visual.split("|")] if visual else ["text", vo]
        kind, values = parts[0].lower(), parts[1:]
        if kind in fields:
            data = {key: values[i] if i < len(values) else "" for i, key in enumerate(fields[kind])}
            if kind == "text" and not data["text"]:
                data["text"] = vo
        elif kind in ("bars", "compare", "timeline", "list", "message"):
            items = []
            for value in values[1:]:
                if kind in ("list", "message"):
                    items.append(value)
                else:
                    left, separator, right = value.partition(":") if kind == "timeline" else value.rpartition(":")
                    if not separator or not left or not right.strip():
                        left, right = value, ""
                    keys = ("date", "label") if kind == "timeline" else ("label", "value")
                    items.append(dict(zip(keys, (left.strip(), right.strip()))))
            data = {"title": values[0] if values else "", "items": items}
        else:
            kind, data = "image", {"description": visual or "", "url": "", "credit": ""}
        duration = max(1.5, math.floor(word_count(vo) * 600 / words_per_minute + 0.5) / 10)  # halves round up, like the UI
        fixed = re.fullmatch(r"(\d+(?:\.\d+)?)\s*s?", beat.get("duration", ""), re.I)
        if fixed:
            duration = min(60.0, max(1.0, math.floor(float(fixed[1]) * 10 + 0.5) / 10))
        scene = {"beat": beat["beat"], "type": kind, "duration": duration, "vo": vo, "text": beat.get("text", ""), "data": data}
        if beat.get("image"):
            src, _, credit = beat["image"].partition("|")
            # an optional last field places the photo: "top" (across the top of the frame) or "full" (behind the scene)
            layout = re.match(r"^(?:(.*?)\s*\|)?\s*(top|full)\s*$", credit, re.I)
            credit, layout = (layout[1] or "", layout[2].lower()) if layout else (credit, "")
            scene["image"] = {"src": src.strip(), "credit": credit.strip()}
            if layout:
                scene["image"]["layout"] = layout
        if beat.get("source"):
            scene["source"] = beat["source"]
        if beat.get("note"):
            scene["note"] = beat["note"]
        if fixed:
            scene["fixed"] = True
        # Say: is what the voiceover speaks when it differs from the captions ("₹12,000" → "twelve thousand rupees")
        if spoken_text(beat.get("say", "")):
            scene["say"] = spoken_text(beat["say"])
        scenes.append(scene)
    return scenes


def comment_position(text: str, comment: dict) -> int:
    """Where a comment's quote is in the text: the occurrence nearest its saved offset, or -1."""
    quote = comment.get("quote") or ""
    if not quote:
        return -1
    found, start = [], text.find(quote)
    while start >= 0:
        found.append(start)
        start = text.find(quote, start + 1)
    if not found:
        return -1
    offset = comment.get("offset")
    return min(found, key=lambda i: abs(i - offset)) if isinstance(offset, int) else found[0]


# ---------------------------------------------------------------- projects: <root>/projects/<id>/

def project_dirs(root: Path) -> list[Path]:
    return sorted(p.parent for p in (root / "projects").glob("*/studio.json"))


def projects_overview(root: Path) -> list[dict]:
    listed = []
    for folder in project_dirs(root):
        studio = Studio(folder, root)
        settings = studio.settings()
        listed.append({"id": folder.name, "name": settings.get("name") or folder.name,
                       "description": settings.get("description", ""),
                       "findings": sum(1 for f in studio.findings() if not f.get("dismissed_at")),
                       "suggested_sources": sum(1 for x in studio.sources() if x["status"] == "suggested")})
    return listed


def channel_looks(root: Path) -> dict:
    """What each channel looks and sounds like at a glance, for lists."""
    names = {p["id"]: p["name"] for p in presets()}
    looks = {}
    for channel in channels(root):
        voice = channel_voice(root, channel["id"])
        look = {"length_seconds": voice["length_seconds"]}
        if channel["kind"] == "video":
            design = channel_design(root, channel["id"])
            look |= {"preset": names.get(design.get("preset"), ""), "aspect": design["aspect"], "colors": design["colors"],
                     "display_font": design["fonts"]["display"]}
        looks[channel["id"]] = look
    return looks


def production_overview(root: Path) -> dict:
    """Production spans all research projects; IDs remain scoped to their owner."""
    projects = projects_overview(root)
    scripts, stories = [], []
    for project in projects:
        studio = Studio(root / "projects" / project["id"], root)
        origin = {"project": project["id"], "project_name": project["name"]}
        project_stories = studio.stories()
        titles = {story["id"]: story["title"] for story in project_stories}
        stories.extend(story | origin for story in project_stories)
        scripts.extend(script | origin | {"story_title": titles.get(script["story"], "")}
                       for script in studio.scripts())
    return {"workspace": str(root),
            "default_workspace": root == workspace_path(None) and not os.environ.get("VID_STUDIO_HOME"),
            "projects": projects, "channels": channels(root), "looks": channel_looks(root),
            "scripts": sorted(scripts, key=lambda script: script.get("updated", ""), reverse=True),
            "stories": stories}


def find_project(root: Path, value: str | None) -> Path:
    """A project by ID or name; with no value, the only project there is."""
    value = value or os.environ.get("VID_STUDIO_PROJECT")
    folders = project_dirs(root)
    if not folders:
        raise KeyError("No projects yet. Create one with `studio.py new-project --name NAME`.")
    if value:
        wanted = value.strip().casefold()
        for folder in folders:
            if wanted in (folder.name, str(load(folder / "studio.json").get("name", "")).strip().casefold()):
                return folder
        raise KeyError(f"No project {value!r}. Projects: {', '.join(c['name'] for c in projects_overview(root))}")
    if len(folders) == 1:
        return folders[0]
    raise KeyError("Several projects exist; pass --project with one of: " + ", ".join(c["name"] for c in projects_overview(root)))


def fill_templates(folder: Path) -> None:
    templates = ASSETS / "project"
    for source in sorted(templates.iterdir()):
        target = folder / source.name
        if source.is_file() and not target.exists():
            shutil.copyfile(source, target)
    for kind in ("stories", "scripts"):
        (folder / kind).mkdir(parents=True, exist_ok=True)


def create_project(root: Path, name: str, description: str = "") -> Path:
    name = (name or "").strip()
    if not name:
        raise ValueError("A project needs a name")
    if any(c["name"].casefold() == name.casefold() for c in projects_overview(root)):
        raise ValueError(f"A project called {name!r} already exists")
    existing = {p.name for p in (root / "projects").glob("*")}
    folder = root / "projects" / unique_id(slugify(name, 40), existing)
    folder.mkdir(parents=True)
    fill_templates(folder)
    settings = load(folder / "studio.json")
    settings.update(name=name, description=(description or "").strip())
    save(folder / "studio.json", settings)
    return folder


# ---------------------------------------------------------------- commands

def cmd_init(root: Path, args) -> None:
    (root / "projects").mkdir(parents=True, exist_ok=True)
    if not (root / "README.md").exists():
        shutil.copyfile(ASSETS / "README.md", root / "README.md")
    print(f"Studio: {root}")
    projects = projects_overview(root)
    print(f"Projects: {', '.join(c['name'] for c in projects) or 'none yet (studio.py new-project --name NAME)'}")


def cmd_projects(root: Path, args) -> None:
    projects = projects_overview(root)
    if not projects:
        print("No projects yet. Create one with `studio.py new-project --name NAME`.")
    for project in projects:
        extra = f", {project['suggested_sources']} suggested sources" if project["suggested_sources"] else ""
        print(f"{project['id']} · {project['name']} · {project['findings']} findings{extra}")


def cmd_new_project(root: Path, args) -> None:
    folder = create_project(root, args.name, args.description or "")
    print(f"Project {folder.name}: {folder}")


def cmd_status(root: Path, args) -> None:
    listed_channels = channels(root)
    print("Channels:" + ("" if listed_channels else " none"))
    for channel in listed_channels:
        look = f" · look {channel_design(root, channel['id'])['preset']}" if channel["kind"] == "video" else ""
        if channel["kind"] == "video":
            voiced = channel_narration(root, channel["id"])
            look += f" · voiceover {voiced['provider']}{'/' + voiced['voice'] if voiced['voice'] else ''}" if voiced["provider"] else " · no voiceover"
        print(f"  {channel['id']} · {channel['name']} · {channel['language']} · {channel['kind']}{look}")
    if not project_dirs(root):
        print(f"No projects in {root}. Run `studio.py init`, then set up a project (references/setup.md).")
        return
    try:
        ws = find_project(root, args.project)
    except KeyError as error:
        print(error.args[0])
        print(f"UI: {(running_server(root) or {}).get('url') or 'not running (studio.py serve --background)'}")
        return
    studio = Studio(ws, root)
    settings, topics, sources, stories, scripts = studio.settings(), studio.topics(), studio.sources(), studio.stories(), studio.scripts()
    runs = studio.runs()
    last = next((r for r in reversed(runs) if r.get("status") in ("completed", "failed")), None)
    others = [c["name"] for c in projects_overview(root) if c["id"] != ws.name]
    print(f"Project: {settings.get('name') or '(unnamed)'} ({ws.name}) · studio {root}" + (f" · other projects: {', '.join(others)}" if others else ""))
    print(f"Topics: {', '.join(t['name'] for t in topics) or 'none'}")
    approved = [s for s in sources if s["status"] == "approved"]
    suggested = [s for s in sources if s["status"] == "suggested"]
    print(f"Sources: {', '.join(domain(s['url']) + urllib.parse.urlsplit(s['url']).path.rstrip('/') for s in approved) or 'none'}"
          + (f" · {len(suggested)} suggested, waiting for the user" if suggested else ""))
    print(f"Findings: {sum(1 for f in studio.findings() if not f.get('dismissed_at'))} · last research: "
          + (f"{last['finished']} ({last['status']}, {last.get('findings', 0)} findings)" if last else "never"))
    print(f"Schedule: {describe_schedule(settings.get('schedule', {}))}"
          + (f" ({settings['timezone']})" if settings.get("timezone") and settings.get("schedule", {}).get("times") else ""))
    print("Stories:" + ("" if stories else " none"))
    for story in stories:
        links = [f"{len(story['findings'])} findings"] + [f"topic {t}" for t in story["topics"]]
        print(f"  {story['id']} · {story['title']} · {', '.join(links)} · {'researched' if story['researched'] else 'not researched'}")
    names = {c["id"]: c["name"] for c in channels(root)}
    print("Scripts:" + ("" if scripts else " none"))
    for script in scripts:
        state = (script["stage"] if script["drafted"] else "not drafted") + (f", {script['open_comments']} open comment{'s' * (script['open_comments'] != 1)}" if script["open_comments"] else "")
        if find_channel(root, script["channel"])["kind"] == "video":
            state += f" · {script['duration']:.1f}s"
        print(f"  {script['id']} · {script['title']} · for {names.get(script['channel'], script['channel'])} · story {script['story']} · {state}")
    server = running_server(root)
    print(f"UI: {server['url'] + '#/' + ws.name if server else 'not running (studio.py serve --background)'}")
    hints = []
    if not settings.get("name") or not topics:
        hints.append("Set up the project: name, topics, sources (references/setup.md).")
    elif not last:
        hints.append("Run research (references/research.md).")
    running = next((r for r in reversed(runs) if r.get("status") == "running"), None)
    if running:
        hints.append(f"Run {running['id']} is unfinished; sources not checked yet: {', '.join(studio.unchecked_sources(running)) or 'none'}.")
    hints += [f"Script '{s['title']}' has no draft yet (references/write.md)." for s in scripts if not s["drafted"]]
    hints += [f"Script '{s['title']}' has {s['open_comments']} open comment{'s' * (s['open_comments'] != 1)} to address (references/write.md)." for s in scripts
              if s["drafted"] and s["open_comments"]]
    if hints:
        print("Suggestions:\n" + "\n".join(f"- {h}" for h in hints))


def cmd_set_schedule(ws: Path, args) -> None:
    changes = {"schedule": {"times": [] if args.off else args.time or [], "days": args.day or DAYS}}
    if args.timezone:
        changes["timezone"] = args.timezone
    settings = Studio(ws).update_settings(changes)
    print(f"Schedule: {describe_schedule(settings['schedule'])}" + (f" ({settings['timezone']})" if settings.get("timezone") else ""))


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


def cmd_new_story(ws: Path, args) -> None:
    story = Studio(ws).create_story(args.title, args.finding or [], args.topic or [])
    print(f"Story: {ws / 'stories' / story['id']}")


def cmd_new_script(ws: Path, args) -> None:
    script = Studio(ws).create_script(args.story, args.channel, args.title or "")
    print(f"Script: {ws / 'scripts' / script['id']}")


def cmd_channels(root: Path, args) -> None:
    listed = channels(root)
    if not listed:
        print("No channels yet. Create one with `studio.py add-channel --name NAME --kind video --language English`.")
    for channel in listed:
        print(f"{channel['id']} · {channel['name']} · {channel['platform'] or 'no platform'} · {channel['kind']} · {channel['language']}")


def cmd_add_channel(root: Path, args) -> None:
    changes = {key: value for key, value in vars(args).items() if key in CHANNEL_KEYS and value is not None}
    channel = add_channel(root, changes)
    print(f"Channel {channel['id']}: {channel['name']} ({channel['kind']}, {channel['language']})")


def read_json_file(value: str):
    try:
        return json.loads(sys.stdin.read() if value == "-" else Path(value).expanduser().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot read JSON from {value!r}: {error}")


def cmd_channel_settings(root: Path, args) -> None:
    channel = find_channel(root, args.channel)
    reader, writer = (channel_design, save_design) if args.command == "design" else (channel_voice, save_voice)
    before = reader(root, channel["id"])
    if args.file is None:
        print(json.dumps(before, indent=2, ensure_ascii=False))
        return
    after = writer(root, channel["id"], read_json_file(args.file))
    changed = [key for key in after if before.get(key) != after[key]]
    print(f"Saved {args.command} for {channel['name']}: changed {', '.join(changed) or 'no keys'}")


def cmd_presets(root: Path, args) -> None:
    for preset in presets():
        print(f"{preset['id']} · {preset['name']} · {preset['description']}")


def cmd_fonts(root: Path, args) -> None:
    for font in fonts()["fonts"]:
        if not args.devanagari or font["devanagari"]:
            print(f"{font['family']} · {font['category']} · devanagari {'yes' if font['devanagari'] else 'no'}")


def cmd_scenes(ws: Path, args) -> None:
    studio = Studio(ws)
    script = studio.script(args.script)
    scenes = script["scenes"]
    if args.json:
        print(json.dumps(scenes, indent=2, ensure_ascii=False))
        return
    voice = channel_voice(studio.root, script["channel"])
    for i, scene in enumerate(scenes, 1):
        voiced = " (voiced)" if scene.get("audio") else ""
        print(f"{i}. {scene['beat']} · {scene['type']} · {scene['duration']:.1f}s{voiced} · {clean_text(scene['vo'], 60)}")
    target = voice["length_seconds"]
    print(f"Total {script['duration']:.1f}s (target {target:g}s)")
    narration = script.get("narration") or {}
    if narration.get("provider") and narration.get("missing"):
        print(f"Voiceover: {narration['missing']} beat{'s' * (narration['missing'] != 1)} not voiced yet, so timed by the speaking pace (studio.py narrate --script {args.script})")
    for warning in scene_warnings(scenes):
        print(f"Warning: {warning}")
    if abs(script["duration"] - target) > target * 0.10:
        print("Warning: total duration is more than 10% off the channel's target")


def cmd_angles(ws: Path, args) -> None:
    angles = Studio(ws).save_angles(args.script, read_json_file(args.file))
    chosen = next(a["id"] for a in angles if a["chosen"])
    print(f"Saved {len(angles)} angles for {args.script}; chosen {chosen}")


def cmd_review(ws: Path, args) -> None:
    review = Studio(ws).save_review(args.script, read_json_file(args.file))
    scores = ', '.join(f"{key} {value}/10" for key, value in review["scores"].items())
    print(f"Saved review for {args.script}: {scores}")


def cmd_export(ws: Path, args) -> None:
    folder = Studio(ws).export_script(args.script, args.out)
    print(f"Exported: {folder}")
    print("Next: run `npx hyperframes preview` or `npx hyperframes render` in that folder")


OPEN_LICENSES = re.compile(r"^(cc0|pdm|public domain|pd\b|cc[ -]by(-sa)?([ -][\d.]+)?$|by(-sa)?$)", re.I)


def search_openverse(query: str, limit: int, orientation: str) -> list[dict]:
    params = {"q": query, "page_size": str(min(20, limit * 2)), "license_type": "commercial,modification", "mature": "false"}
    if orientation in ("tall", "wide", "square"):
        params["aspect_ratio"] = orientation
    data, _, _ = fetch("https://api.openverse.org/v1/images/?" + urllib.parse.urlencode(params))
    results = []
    for item in json.loads(data).get("results", []):
        license_name = ("CC0" if item.get("license") == "cc0" else "Public domain" if item.get("license") == "pdm"
                        else f"CC {str(item.get('license', '')).upper()} {item.get('license_version') or ''}".strip())
        creator = clean_text(item.get("creator") or "Unknown", 60)
        provider = str(item.get("source") or item.get("provider") or "").replace("_", " ").title()
        results.append({"title": clean_text(item.get("title") or "Untitled", 80), "url": item.get("url"),
                        "thumbnail": item.get("thumbnail") or item.get("url"), "page": item.get("foreign_landing_url") or "",
                        "width": item.get("width"), "height": item.get("height"), "license": license_name,
                        "credit": f"Photo: {creator} / {provider}, {license_name}" if license_name not in ("CC0", "Public domain") else f"Photo: {creator} / {provider}"})
    return results


def search_commons(query: str, limit: int, orientation: str) -> list[dict]:
    params = {"action": "query", "format": "json", "generator": "search", "gsrsearch": f"filetype:bitmap {query}", "gsrnamespace": "6",
              "gsrlimit": str(min(30, limit * 3)), "prop": "imageinfo", "iiprop": "url|extmetadata|size", "iiurlwidth": "1600"}
    data, _, _ = fetch("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params))
    pages = sorted(json.loads(data).get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
    results = []
    for page in pages:
        info = (page.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata") or {}
        value = lambda key: re.sub(r"<[^>]+>", "", html.unescape(str((meta.get(key) or {}).get("value", "")))).strip()
        license_name = value("LicenseShortName")
        if not OPEN_LICENSES.match(license_name) or info.get("width", 0) < 900:
            continue
        width, height = info.get("width") or 0, info.get("height") or 0
        if orientation == "tall" and width > height or orientation == "wide" and height > width:
            continue
        creator = clean_text(value("Artist") or "Unknown", 60)
        clean = lambda url: re.sub(r"\?utm_[^#]*$", "", url or "")
        results.append({"title": clean_text(page.get("title", "").removeprefix("File:"), 80), "url": clean(info.get("thumburl") or info.get("url")),
                        "thumbnail": info.get("thumburl") or info.get("url"), "page": info.get("descriptionurl") or "",
                        "width": width, "height": height, "license": license_name,
                        "credit": f"Photo: {creator} / Wikimedia Commons" + ("" if re.match(r"(?i)cc0|public domain|pd", license_name) else f", {license_name}")})
    return results


def cmd_images(ws: Path, args) -> None:
    found, errors = [], []
    for name, search in (("Wikimedia Commons", search_commons), ("Openverse", search_openverse)):
        if args.provider not in ("all", name.split()[0].lower()):
            continue
        try:
            found += search(args.query, args.limit, args.orientation)[: args.limit]
        except Exception as error:  # one provider being down shouldn't hide the other
            errors.append(f"{name}: {error}")
    for error in errors:
        print(f"Search failed on {error}")
    if not found:
        print("No openly licensed images found. Try a broader or more literal query (objects and places, not ideas).")
        return
    preview = Path(args.preview).expanduser() if args.preview else None
    if preview:
        preview.mkdir(parents=True, exist_ok=True)
    for i, item in enumerate(found, 1):
        print(f"{i}. {item['title']} · {item['width']}×{item['height']} · {item['license']}")
        print(f"   credit: {item['credit']}")
        print(f"   url: {item['url']}")
        print(f"   page: {item['page']}")
        if preview:
            try:
                data, _, _ = fetch(item["thumbnail"], timeout=20)
                if image_kind(data):
                    target = preview / f"{i:02d}.{image_kind(data)}"
                    target.write_bytes(data)
                    print(f"   preview: {target}")
            except Exception:
                pass
    print('Next: look at the candidates, then `studio.py media --script ID --add URL --credit "…" --source PAGE`')


def cmd_media(ws: Path, args) -> None:
    studio = Studio(ws)
    if args.remove:
        studio.delete_media(args.script, args.remove)
        print(f"Removed media/{args.remove}")
        return
    if args.add:
        if re.match(r"^https?://", args.add):
            data, name = fetch_image(args.add)
            source = args.source or args.add
        else:
            path = Path(args.add).expanduser()
            if not path.is_file():
                raise ValueError(f"No such file: {path}")
            data, name, source = path.read_bytes(), path.name, args.source or ""
        item = studio.add_media(args.script, data, args.name or name, args.credit or "", source, args.license or "")
        print(f"Saved {item['path']}")
        cue = f"Image: {item['path']}" + (f" | {item['credit']}" if item["credit"] else "")
        print(f"Use it on a beat with `{cue}`, or as `Visual: image | <what it shows> | {item['path']}`")
        return
    listed = studio.media(args.script)
    print(f"{len(listed)} image{'s' * (len(listed) != 1)} for {args.script}" + (":" if listed else "."))
    for item in listed:
        print(f"- {item['path']}" + (f" · {item['credit']}" if item.get("credit") else "") + (f" · {item['source']}" if item.get("source") else ""))


def cmd_render(ws: Path, args) -> None:
    studio = Studio(ws)
    script = studio.script(args.script)
    for beat in (script.get("video") or {}).get("placeholders", []):
        print(f"Warning: {beat} has no image yet; it renders as an 'Image needed' card")

    def progress(done, total):
        print(f"\rRendering {done}/{total} frames", end="", flush=True)

    result = studio.render_script(args.script, "draft" if args.draft else "high", progress)
    print()
    target = Path(result["output"])
    if args.out:
        out = Path(args.out).expanduser()
        if out.is_dir():
            out = out / (slugify(script["title"], 60) + ".mp4")
        shutil.copyfile(target, out)
        target = out
    print(f"Rendered {result['duration']:.1f}s at {result['width']}×{result['height']}, {result['fps']} fps in {result['seconds']:.0f}s: {target}")
    if result.get("fonts") != "loaded":
        print("Warning: web fonts didn't load (offline?), so system fonts were used")
    if result["credits"]:
        print("Image credits for the video description:")
        for credit in result["credits"]:
            print(f"- {credit}")


def cmd_voices_providers(root: Path, args) -> None:
    for item in tts.providers(root):
        state = "ready" if item["ready"] else item["problem"]
        timing = " · word-timed captions" if item["word_timings"] else ""
        print(f"{item['id']} · {item['name']} · {item['kind']} · {state}{timing}")
    print("Pick one for a channel with `studio.py narration --channel C --file -` ({\"provider\": \"…\", \"voice\": \"…\"}).")


def cmd_voices(root: Path, args) -> None:
    chosen = tts.provider(args.provider)
    problem = chosen.problem(root)
    if problem:
        raise RuntimeError(problem)
    listed = chosen.voices(root, args.language)
    for voice in listed:
        extra = " · ".join(x for x in (voice.get("language"), voice.get("gender"), voice.get("category")) if x)
        print(f"{voice['id']} · {voice.get('name') or voice['id']}" + (f" · {extra}" if extra else ""))
    if not listed:
        print("No voice list for this provider; pass any voice id it accepts.")
    print(f"Default for {args.language}: {chosen.default_voice(args.language)}")


def cmd_voice_key(root: Path, args) -> None:
    chosen = tts.provider(args.provider)
    if not chosen.key:
        raise ValueError(f"{chosen.name} runs on this computer and needs no key")
    value = "" if args.remove else (sys.stdin.readline() if args.key == "-" else args.key or "")
    if not args.remove and not value.strip():
        raise ValueError("Pass the key with --key KEY, or --key - to read it from stdin")
    tts.set_secret(root, chosen.key, value)
    print(f"{'Removed' if args.remove else 'Saved'} the {chosen.name} key in {tts.secrets_path(root)}" +
          (f" (note: ${chosen.key} is also set in the environment and wins)" if os.environ.get(chosen.key) else ""))


def cmd_narration(root: Path, args) -> None:
    channel = find_channel(root, args.channel)
    if args.file is None:
        print(json.dumps(channel_narration(root, channel["id"]), indent=2, ensure_ascii=False))
        return
    settings = save_narration(root, channel["id"], read_json_file(args.file))
    print(f"Saved narration for {channel['name']}: " + (f"{settings['provider']} · {settings['voice'] or 'default voice'}" if settings["provider"] else "no voiceover"))


def cmd_say(root: Path, args) -> None:
    channel = find_channel(root, args.channel)
    out = Path(args.out).expanduser()
    out.write_bytes(speak_sample(root, channel["id"], args.text or ""))
    print(f"Saved a sample of {channel['name']}'s voice: {out}")


def cmd_narrate(ws: Path, args) -> None:
    studio = Studio(ws)
    result = studio.narrate_script(args.script, args.force, lambda done, total: print(f"\rVoiceover {done}/{total} beats", end="", flush=True))
    print()
    script = studio.script(args.script)
    print(f"{result['made']} of {result['beats']} beats voiced with {result['provider']}; the script now runs {script['duration']:.1f}s")
    for warning in scene_warnings(script["scenes"]):
        if "voiceover" in warning:
            print(f"Warning: {warning}")


def cmd_take(ws: Path, args) -> None:
    studio = Studio(ws)
    script = studio.script(args.script)
    lines = [scene for scene in script["scenes"] if scene.get("say") or scene["vo"]]
    if not 1 <= args.beat <= len(lines):
        raise ValueError(f"--beat is the number of a beat with words, 1 to {len(lines)}: " + ", ".join(f"{i} {s['beat']}" for i, s in enumerate(lines, 1)))
    scene = lines[args.beat - 1]
    text = scene.get("say") or scene["vo"]
    if args.remove:
        studio.delete_take(args.script, tts.recording_key(text))
        print(f"Removed your take of {scene['beat']}")
        return
    path = Path(args.file or "").expanduser()
    if not path.is_file():
        raise ValueError("Pass the recording with --file PATH (WAV, MP3, M4A, WebM…)")
    narration = studio.add_take(args.script, text, path.read_bytes(), path.name, "uploaded")
    take = narration["takes"][tts.recording_key(text)]
    print(f"Saved your take of {scene['beat']} ({take['duration']:.1f}s); {narration['recorded']} of {narration['done'] + narration['missing']} beats are in your voice")


def cmd_captions(ws: Path, args) -> None:
    text = Studio(ws).captions_srt(args.script)
    if args.out:
        Path(args.out).expanduser().write_text(text, encoding="utf-8")
        print(f"Saved captions: {args.out}")
    else:
        print(text, end="")


def cmd_platforms(root: Path, args) -> None:
    for chosen in pub.PLATFORMS.values():
        info = chosen.describe(root)
        how = "connects in the browser" if chosen.oauth else "connects with a pasted token"
        print(f"{chosen.id} · {chosen.name} · {how}" + (f" · {info['app_problem']}" if chosen.oauth and info["app_problem"] else " · app ready" if chosen.oauth else ""))
    for channel in channels(root):
        if channel["kind"] == "video":
            info = channel_publishing(root, channel["id"])
            where = f"{info['info']['name']}: {info['account']['name']}" if info["connected"] else info["problem"]
            print(f"  {channel['id']} → {where}")


def cmd_platform_app(root: Path, args) -> None:
    chosen = pub.platform(args.platform)
    if not chosen.app_keys:
        raise ValueError(f"{chosen.name} needs no app keys; connect with a token: studio.py connect --channel C --platform {chosen.id} --token -")
    values = [sys.stdin.readline() if v == "-" else v for v in (args.id, args.secret)]
    for (name, label), value in zip(chosen.app_keys, values):
        if value is not None:
            tts.set_secret(root, name, value)
            print(f"{'Saved' if value.strip() else 'Removed'} the {chosen.name} app's {label}")


def cmd_connect(root: Path, args) -> None:
    channel = find_channel(root, args.channel)
    chosen = pub.platform(args.platform or channel_publishing(root, channel["id"])["platform"] or "youtube")
    if args.token:
        token = sys.stdin.readline() if args.token == "-" else args.token
        info = connect_token(root, channel["id"], chosen.id, token)
        print(f"Connected {channel['name']} to {info['account']['name']} on {chosen.name}")
        return
    if not chosen.oauth:
        raise ValueError(f"{chosen.name} connects with a token: {chosen.token_help}\nThen: studio.py connect --channel C --platform {chosen.id} --token -")
    problem = chosen.app_problem(root)
    if problem:
        raise RuntimeError(f"{problem}: studio.py platform-app --platform {chosen.id} --id … --secret -")
    server = running_server(root)
    if not server:
        raise RuntimeError("Signing in goes through the studio: run `studio.py serve --background` first")
    query = urllib.parse.urlencode({"channel": channel["id"], "platform": chosen.id} | ({"captions": "1"} if args.captions else {}))
    print(f"Open this link in the browser and sign in; the channel connects when you're done:\n{server['url']}oauth/start?{query}")


def cmd_disconnect(root: Path, args) -> None:
    channel = find_channel(root, args.channel)
    disconnect_channel(root, channel["id"])
    print(f"Disconnected {channel['name']}")


def cmd_publishing(root: Path, args) -> None:
    channel = find_channel(root, args.channel)
    info = channel_publishing(root, channel["id"]) if args.file is None else save_publishing(root, channel["id"], read_json_file(args.file))
    print(json.dumps({k: v for k, v in info.items() if k != "info"}, indent=2, ensure_ascii=False))


def cmd_publish_details(ws: Path, args) -> None:
    studio = Studio(ws)
    details = studio.publish_details(args.script) if args.file is None else studio.save_publish_details(args.script, read_json_file(args.file))
    print(json.dumps(details, indent=2, ensure_ascii=False))


def cmd_publish(ws: Path, args) -> None:
    studio = Studio(ws)
    script = studio.script(args.script)
    channel = find_channel(studio.root, script["channel"])
    info = channel_publishing(studio.root, channel["id"])
    details = studio.publish_details(args.script)
    where = f"{info['info']['name']} · {info['account']['name']}" if info["connected"] else info["problem"]
    print(f"Publishing \"{details['title']}\" to {where} · {details['privacy'] or 'default privacy'}"
          + (f" · scheduled {details['publish_at']}" if details["publish_at"] else ""))
    if not args.yes:
        raise ValueError("This posts to a real account. Re-run with --yes once the user has confirmed")
    result = studio.publish_script(args.script, lambda done, total: print(f"\rUploading {done * 100 // max(1, total)}%", end="", flush=True))
    print()
    print(f"{result['status'].title()}: {result['url']}")
    for note in result.get("notes", []):
        print(f"Note: {note}")


def cmd_stats(ws: Path, args) -> None:
    stats = Studio(ws).refresh_stats(args.script)
    print(", ".join(f"{k} {v:,}" if isinstance(v, int) else f"{k} {v}" for k, v in stats.items() if k != "at"))


def cmd_comments(ws: Path, args) -> None:
    studio = Studio(ws)
    script = studio.script(args.script)
    open_comments = [c for c in script["comments"] if not c.get("resolved_at")]
    print(f"{len(open_comments)} open comment{'s' * (len(open_comments) != 1)} on {script['title']}, in the order they appear in the text:" if open_comments else "No open comments.")
    for comment in open_comments:
        where = f'on "{comment["quote"]}"' if comment["position"] >= 0 else (f'on "{comment["quote"]}" (no longer in the text)' if comment["quote"] else "on the whole script")
        print(f"- {comment['id']} {where}: {comment['body']}")


def cmd_resolve(ws: Path, args) -> None:
    comment = Studio(ws).update_comment(args.script, args.comment, {"resolved": True, "reply": args.reply or ""})
    print(f"Resolved {comment['id']}")


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


class Raw:
    """A binary reply (an image or video) from the API, optionally as a download."""

    def __init__(self, path: Path, content_type: str, filename: str = ""):
        self.path, self.content_type, self.filename = path, content_type, filename


RENDERS: dict[str, threading.Thread] = {}


def start_render(studio: "Studio", script_id: str, quality: str = "high") -> dict:
    key = f"{studio.ws}:{script_id}"
    running = RENDERS.get(key)
    if not (running and running.is_alive()):
        script = studio.script(script_id)
        if not script["scenes"]:
            raise ValueError("Write the script's beats before rendering")
        import render as renderer
        problems = renderer.missing_tools()
        if problems:
            raise RuntimeError("Rendering needs " + "; ".join(problems))
        status_path = studio.path("scripts", script_id, "render", "render.json")
        save(status_path, {"status": "rendering", "progress": 0, "pid": os.getpid(), "started": now(),
                           "fingerprint": load(status_path, {}).get("fingerprint")})

        def run():
            try:
                Studio(studio.ws, studio.root).render_script(script_id, quality)
            except BaseException as error:
                # Setup may fail before render_script reaches its status handler.
                status = load(status_path, {})
                save(status_path, status | {"status": "failed", "error": str(error) or type(error).__name__, "finished": now()})

        RENDERS[key] = threading.Thread(target=run, daemon=True)
        RENDERS[key].start()
    return studio.script(script_id)["video"]


NARRATIONS: dict[str, threading.Thread] = {}
PUBLISHES: dict[str, threading.Thread] = {}


def start_publish(studio: "Studio", script_id: str) -> dict:
    """Publish in the background; the script's publish status reports progress and the result."""
    key = f"{studio.ws}:{script_id}"
    running = PUBLISHES.get(key)
    if not (running and running.is_alive()):
        script = studio.script(script_id)
        channel = find_channel(studio.root, script["channel"])
        if channel["kind"] != "video":
            raise ValueError("Text posts are shared by hand")
        if not (script["video"] or {}).get("ready") or (script["video"] or {}).get("stale"):
            raise RuntimeError("Render the latest version of the video before publishing")
        channel_tokens(studio.root, channel["id"])  # fails fast when the channel isn't connected
        path = studio.path("scripts", script_id, "publish", "state.json")
        save(path, load(path, {}) | {"status": "uploading", "progress": 0, "pid": os.getpid(), "error": ""})

        def run():
            try:
                Studio(studio.ws, studio.root).publish_script(script_id)
            except BaseException as error:
                save(path, load(path, {}) | {"status": "failed", "error": str(error) or type(error).__name__, "finished": now()})

        PUBLISHES[key] = threading.Thread(target=run, daemon=True)
        PUBLISHES[key].start()
    return studio.publish_status(script_id)


def oauth_page(title: str, message: str, ok: bool) -> bytes:
    """The small page the browser lands on after signing in to a platform."""
    return f"""<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} · Vid Studio</title>
<style>body{{font:15px/1.5 system-ui,sans-serif;background:#fafaf8;color:#111110;display:grid;place-items:center;min-height:100vh;margin:0}}
main{{max-width:440px;padding:32px;border:1px solid #e6e5e1;border-radius:14px;background:#fff}}h1{{font-size:20px;margin:0 0 8px}}p{{margin:0;color:#5a5853}}
b{{color:{'#17663a' if ok else '#b42318'}}}</style>
<main><h1><b>{'✓' if ok else '✕'}</b> {html.escape(title)}</h1><p>{html.escape(message)}</p></main>
<script>try {{ window.opener && window.opener.postMessage({{type: "vid-connected", ok: {str(ok).lower()}}}, location.origin.replace("127.0.0.1", "localhost")); }} catch (e) {{}}
{"setTimeout(function(){ window.close(); }, 1500);" if ok else ""}</script>""".encode()


def start_narration(studio: "Studio", script_id: str, force: bool = False) -> dict:
    key = f"{studio.ws}:{script_id}"
    if RENDERS.get(key) and RENDERS[key].is_alive():
        raise RuntimeError("This script is rendering; its voiceover is made as part of the render")
    running = NARRATIONS.get(key)
    if not (running and running.is_alive()):
        script = studio.script(script_id)
        if not script["scenes"]:
            raise ValueError("Write the script's beats before making the voiceover")
        channel = find_channel(studio.root, script["channel"])
        settings = studio.narration_settings(channel)
        if not settings["provider"]:
            raise ValueError(f"Choose a voice for {channel['name']} first (Channels → {channel['name']} → Narration)")
        problem = tts.provider(settings["provider"]).problem(studio.root)
        if problem:
            raise RuntimeError(problem)
        path = studio.path("scripts", script_id, "narration", "narration.json")
        save(path, load(path, {}) | {"status": "narrating", "progress": 0, "pid": os.getpid(), "error": ""})

        def run():
            try:
                Studio(studio.ws, studio.root).narrate_script(script_id, force)
            except BaseException as error:
                save(path, load(path, {}) | {"status": "failed", "error": str(error) or type(error).__name__, "finished": now()})

        NARRATIONS[key] = threading.Thread(target=run, daemon=True)
        NARRATIONS[key].start()
    return studio.script(script_id)["narration"]


def make_handler(ws: Path):
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

        def send_file(self, raw: Raw) -> None:
            if not raw.path.is_file():
                return self.reply(404, {"error": "Not found"})
            size = raw.path.stat().st_size
            # One byte range (what <audio> and <video> ask for to seek); anything else gets the whole file.
            start, end = 0, size - 1
            ranged = re.fullmatch(r"bytes=(\d*)-(\d*)", self.headers.get("Range") or "")
            if ranged and (ranged[1] or ranged[2]) and size:
                if ranged[1]:
                    start, end = int(ranged[1]), min(size - 1, int(ranged[2])) if ranged[2] else size - 1
                else:
                    start = max(0, size - int(ranged[2]))
                if start > end:
                    self.send_response(416)
                    self.send_header("Content-Range", f"bytes */{size}")
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
            self.send_response(206 if ranged and (start, end) != (0, size - 1) else 200)
            self.send_header("Content-Type", raw.content_type)
            self.send_header("Content-Length", str(end - start + 1 if size else 0))
            self.send_header("Accept-Ranges", "bytes")
            if ranged and (start, end) != (0, size - 1):
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            if raw.filename:
                ascii_name = re.sub(r"[^A-Za-z0-9._-]+", "-", raw.filename).strip("-") or "video.mp4"
                self.send_header("Content-Disposition", f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{urllib.parse.quote(raw.filename)}")
            self.end_headers()
            with raw.path.open("rb") as handle:
                handle.seek(start)
                remaining = end - start + 1 if size else 0
                while remaining > 0:
                    chunk = handle.read(min(1 << 20, remaining))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    remaining -= len(chunk)

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
            query = {k: v[-1] for k, v in urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query).items()}
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
                if method == "GET" and parts[0:1] == ["scenes"]:
                    relative = urllib.parse.unquote(path[len("/scenes/"):]) if path.startswith("/scenes/") else ""
                    if not relative or "\\" in relative or relative.startswith("/") or any(p.startswith(".") or not p for p in relative.split("/")):
                        raise KeyError("Invalid scene asset path")
                    base = SCENES_DIR.resolve()
                    asset = (base / relative).resolve()
                    if not asset.is_relative_to(base) or not asset.is_file():
                        raise KeyError("Scene asset not found")
                    if any(p.startswith(".") for p in asset.relative_to(base).parts):
                        raise KeyError("Hidden scene assets are not served")
                    content_types = {".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
                                     ".html": "text/html; charset=utf-8", ".json": "application/json; charset=utf-8",
                                     ".svg": "image/svg+xml", ".woff2": "font/woff2", ".png": "image/png",
                                     ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
                    return self.reply(200, asset.read_bytes(), content_types.get(asset.suffix.lower(), "application/octet-stream"))
                if method == "GET" and len(parts) == 2 and parts[0] == "fonts" and re.fullmatch(r"[a-z0-9-]+\.woff2", parts[1]):
                    font = page.parent / "fonts" / parts[1]
                    if font.is_file():
                        return self.reply(200, font.read_bytes(), "font/woff2")
                if parts == ["api", "health"]:
                    return self.reply(200, str(ws).encode(), "text/plain; charset=utf-8")
                if method == "GET" and parts == ["oauth", "start"]:
                    # Opened in a new tab by the UI or the CLI: remember who's signing in, then go to the platform.
                    redirect = f"http://localhost:{self.server.server_port}/oauth/callback"
                    try:
                        with lock:
                            target = start_oauth(ws, query.get("channel", ""), query.get("platform", ""), redirect, query.get("captions") == "1")
                    except (KeyError, ValueError, RuntimeError) as error:
                        return self.reply(400, oauth_page("Couldn't start connecting", str(error.args[0] if error.args else error), False), "text/html; charset=utf-8")
                    self.send_response(302)
                    self.send_header("Location", target)
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                if method == "GET" and parts == ["oauth", "callback"]:
                    if query.get("error"):
                        message = query.get("error_description") or query["error"]
                        OAUTH_PENDING.pop(query.get("state", ""), None)
                        return self.reply(400, oauth_page("Not connected", f"The platform said: {message}", False), "text/html; charset=utf-8")
                    try:
                        with lock:
                            done = finish_oauth(ws, query.get("state", ""), query.get("code", ""))
                    except (KeyError, ValueError, RuntimeError) as error:
                        return self.reply(400, oauth_page("Not connected", str(error.args[0] if error.args else error), False), "text/html; charset=utf-8")
                    who = (done.get("account") or {}).get("name") or "the account"
                    return self.reply(200, oauth_page("Connected", f"{find_channel(ws, done['channel'])['name']} now publishes to {who} on "
                                                      f"{done['info']['name']}. You can close this tab.", True), "text/html; charset=utf-8")
                with lock:
                    if parts == ["api", "projects"] and method == "GET":
                        result = {"workspace": str(ws), "default_workspace": ws == workspace_path(None) and not os.environ.get("VID_STUDIO_HOME"),
                                  "projects": projects_overview(ws)}
                    elif parts == ["api", "production"] and method == "GET":
                        result = production_overview(ws)
                    elif parts == ["api", "projects"] and method == "POST":
                        folder = create_project(ws, body.get("name", ""), body.get("description", ""))
                        result = {"id": folder.name}
                    elif parts == ["api", "channels"] and method == "POST":
                        result = add_channel(ws, body)
                    elif parts == ["api", "channels"] and method == "GET":
                        result = channels(ws)
                    elif parts == ["api", "presets"] and method == "GET":
                        result = presets()
                    elif parts == ["api", "fonts"] and method == "GET":
                        result = fonts()
                    elif parts[:2] == ["api", "channels"] and len(parts) == 4 and parts[3] in ("design", "voice") and method in ("GET", "PUT"):
                        reader, writer = (channel_design, save_design) if parts[3] == "design" else (channel_voice, save_voice)
                        result = reader(ws, parts[2]) if method == "GET" else writer(ws, parts[2], body)
                    elif parts == ["api", "voice-providers"] and method == "GET":
                        result = tts.providers(ws)
                    elif parts[:2] == ["api", "voice-providers"] and len(parts) == 4 and parts[3] == "key" and method == "PUT":
                        chosen = tts.provider(parts[2])
                        if not chosen.key:
                            raise ValueError(f"{chosen.name} needs no key")
                        tts.set_secret(ws, chosen.key, str(body.get("key") or ""))
                        result = tts.providers(ws)
                    elif parts[:2] == ["api", "voice-providers"] and len(parts) == 4 and parts[3] == "voices" and method == "GET":
                        chosen = tts.provider(parts[2])
                        problem = chosen.problem(ws)
                        if problem:
                            raise RuntimeError(problem)
                        language = query.get("language") or "English"
                        result = {"voices": chosen.voices(ws, language), "default": chosen.default_voice(language)}
                    elif parts == ["api", "platforms"] and method == "GET":
                        result = [p.describe(ws) for p in pub.PLATFORMS.values()]
                    elif parts[:2] == ["api", "platforms"] and parts[3:] == ["app"] and method == "PUT":
                        chosen = pub.platform(parts[2])
                        allowed = {name for name, _ in chosen.app_keys}
                        if not allowed or set(body) - allowed:
                            raise ValueError(f"{chosen.name} app keys are: {', '.join(sorted(allowed)) or 'none'}")
                        for name, value in body.items():
                            tts.set_secret(ws, name, str(value or ""))
                        result = [p.describe(ws) for p in pub.PLATFORMS.values()]
                    elif parts[:2] == ["api", "channels"] and len(parts) == 4 and parts[3] == "publishing" and method in ("GET", "PUT"):
                        result = channel_publishing(ws, parts[2]) if method == "GET" else save_publishing(ws, parts[2], body)
                    elif parts[:2] == ["api", "channels"] and len(parts) == 4 and parts[3] == "connection" and method == "PUT":
                        result = connect_token(ws, parts[2], str(body.get("platform") or ""), str(body.get("token") or ""))
                    elif parts[:2] == ["api", "channels"] and len(parts) == 4 and parts[3] == "connection" and method == "DELETE":
                        disconnect_channel(ws, parts[2])
                        result = channel_publishing(ws, parts[2])
                    elif parts[:2] == ["api", "channels"] and len(parts) == 4 and parts[3] == "narration" and method in ("GET", "PUT"):
                        result = channel_narration(ws, parts[2]) if method == "GET" else save_narration(ws, parts[2], body)
                    elif parts[:2] == ["api", "channels"] and parts[3:] == ["voice-clone"] and method == "POST":
                        samples = []
                        for i, sample in enumerate(body.get("samples") or [], 1):
                            try:
                                samples.append((str(sample.get("name") or f"sample-{i}.webm"), base64.b64decode(str(sample.get("data", "")).split(",")[-1], validate=True)))
                            except (ValueError, AttributeError):
                                raise ValueError(f"Sample {i} was not valid base64")
                        result = clone_channel_voice(ws, parts[2], str(body.get("name") or ""), samples, body.get("consent") is True, body.get("remove_noise") is not False)
                    elif parts[:2] == ["api", "channels"] and parts[3:] == ["narration", "sample"] and method == "POST":
                        audio = speak_sample(ws, parts[2], str(body.get("text") or ""), body.get("settings") or {})
                        result = {"audio": "data:audio/wav;base64," + base64.b64encode(audio).decode()}
                    elif parts[:2] == ["api", "channels"] and len(parts) == 3 and method == "PUT":
                        result = update_channel(ws, parts[2], body)
                    elif parts[:2] == ["api", "channels"] and len(parts) == 3 and method == "DELETE":
                        result = delete_channel(ws, parts[2]) or {"ok": True}
                    elif parts[:2] == ["api", "p"] and len(parts) >= 3:
                        result = self.api(method, parts[3:], body, Studio(find_project(ws, parts[2]), ws))
                    else:
                        return self.reply(404, {"error": "Not found"})
                if isinstance(result, Raw):
                    return self.send_file(result)
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
            if resource == "stories":
                if method == "GET" and item:
                    return studio.story(item)
                if method == "POST":
                    return studio.create_story(body.get("title", ""), body.get("findings", []), body.get("topics", []))
                if method == "PUT" and item:
                    version = body.pop("version", None)
                    return studio.update_story(item, body, version)
                if method == "DELETE" and item:
                    return studio.delete_story(item) or {"ok": True}
            if resource == "scripts" and item and len(parts) == 3 and parts[2] in ("publish", "publish-details", "stats"):
                if parts[2] == "publish-details" and method == "GET":
                    return studio.publish_details(item)
                if parts[2] == "publish-details" and method == "PUT":
                    return studio.save_publish_details(item, body)
                if parts[2] == "publish" and method == "POST":
                    if body.get("confirm") is not True:
                        raise ValueError("Publishing needs {\"confirm\": true}")
                    return start_publish(studio, item)
                if parts[2] == "stats" and method == "POST":
                    return studio.refresh_stats(item)
            if resource == "scripts" and item and len(parts) >= 3 and parts[2] == "takes":
                if method == "POST" and len(parts) == 3:
                    try:
                        data = base64.b64decode(str(body.get("data", "")).split(",")[-1], validate=True)
                    except ValueError:
                        raise ValueError("The recording was not valid base64")
                    return studio.add_take(item, str(body.get("text") or ""), data, str(body.get("name") or ""), str(body.get("source") or "recorded"))
                if method == "DELETE" and len(parts) == 4:
                    return studio.delete_take(item, parts[3])
            if resource == "scripts" and item and len(parts) >= 3 and parts[2] in ("narrate", "narration", "captions.srt"):
                studio.script(item)
                if parts[2] == "narrate" and method == "POST":
                    return start_narration(studio, item, bool(body.get("force")))
                if parts[2] == "narration" and method == "GET" and len(parts) == 4:
                    if not re.fullmatch(r"(rec-)?[0-9a-f]{12}\.wav", parts[3]):
                        raise KeyError("Unknown voiceover clip")
                    return Raw(studio.path("scripts", item, "narration", parts[3]), "audio/wav")
                if parts[2] == "captions.srt" and method == "GET":
                    title = studio.script(item)["title"]
                    target = studio.path("scripts", item, "render", "captions.srt")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    write_text(target, studio.captions_srt(item))
                    return Raw(target, "application/x-subrip; charset=utf-8", (slugify(title, 60) or item) + ".srt")
            if resource == "scripts" and item and len(parts) >= 3 and parts[2] in ("media", "render", "video", "poster.jpg"):
                folder = studio.path("scripts", item)
                studio.script(item)
                if parts[2] == "media" and method == "GET" and len(parts) == 4:
                    if not re.fullmatch(r"[a-z0-9-]+\.(jpg|png|webp)", parts[3]):
                        raise KeyError("Unknown media file")
                    kinds = {"jpg": "image/jpeg", "png": "image/png", "webp": "image/webp"}
                    return Raw(folder / "media" / parts[3], kinds[parts[3].rsplit(".", 1)[1]])
                if parts[2] == "media" and method == "POST" and len(parts) == 3:
                    try:
                        data = base64.b64decode(str(body.get("data", "")).split(",")[-1], validate=True)
                    except ValueError:
                        raise ValueError("The upload was not valid base64")
                    return studio.add_media(item, data, body.get("name", ""), body.get("credit", ""), body.get("source", ""))
                if parts[2] == "media" and method == "DELETE" and len(parts) == 4:
                    return studio.delete_media(item, parts[3]) or {"ok": True}
                if parts[2] == "render" and method == "POST":
                    return start_render(studio, item, "draft" if body.get("draft") else "high")
                if parts[2] == "video" and method == "GET":
                    title = studio.script(item)["title"]
                    return Raw(folder / "render" / "video.mp4", "video/mp4", (slugify(title, 60) or item) + ".mp4")
                if parts[2] == "poster.jpg" and method == "GET":
                    return Raw(folder / "render" / "poster.jpg", "image/jpeg")
            if resource == "scripts" and len(parts) >= 3 and parts[2] == "comments":
                comment = parts[3] if len(parts) > 3 else None
                if method == "POST" and not comment:
                    return studio.add_comment(item, body.get("body", ""), body.get("quote", ""), body.get("offset"))
                if method == "PUT" and comment:
                    return studio.update_comment(item, comment, body)
                if method == "DELETE" and comment:
                    return studio.delete_comment(item, comment) or {"ok": True}
            elif resource == "scripts":
                if method == "GET" and item:
                    return studio.script(item)
                if method == "POST":
                    return studio.create_script(body.get("story", ""), body.get("channel", ""), body.get("title", ""))
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
    parser.add_argument("--project", help="Project ID or name (default: $VID_STUDIO_PROJECT, or the only project)")
    # Accept --workspace after the subcommand too, without clobbering one given before it.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--workspace", default=argparse.SUPPRESS, help=workspace_help)
    common.add_argument("--project", default=argparse.SUPPRESS,
                        help="Project ID or name (default: $VID_STUDIO_PROJECT, or the only project)")
    commands = parser.add_subparsers(dest="command", required=True)

    def command(name, handler, help_text):
        sub = commands.add_parser(name, parents=[common], help=help_text)
        sub.set_defaults(handler=handler)
        return sub

    command("init", cmd_init, "Create the studio folder; never overwrites files")
    command("projects", cmd_projects, "List projects")
    sub = command("new-project", cmd_new_project, "Create a project")
    sub.add_argument("--name", required=True)
    sub.add_argument("--description")
    command("status", cmd_status, "Show the project, research runs, scripts, and suggestions")

    sub = command("serve", cmd_serve, "Run the studio web UI at http://localhost")
    sub.add_argument("--port", type=int, default=8765)
    sub.add_argument("--background", action="store_true", help="Start detached and print the URL")
    sub.add_argument("--stop", action="store_true")

    sub = command("set-schedule", cmd_set_schedule, "Save the research schedule (the scheduled task itself is created in the agent app)")
    sub.add_argument("--time", action="append", help="HH:MM; repeatable")
    sub.add_argument("--day", action="append", choices=DAYS, help="Weekday; repeatable (default: every day)")
    sub.add_argument("--timezone")
    sub.add_argument("--off", action="store_true", help="Clear the schedule")

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

    sub = command("new-story", cmd_new_story, "Create a story, optionally with findings or topics attached")
    sub.add_argument("--title", required=True)
    sub.add_argument("--finding", action="append", help="Finding ID; repeatable")
    sub.add_argument("--topic", action="append", help="Topic ID, for explainers; repeatable")

    sub = command("new-script", cmd_new_script, "Send a story to production: a script for one channel")
    sub.add_argument("--story", required=True, help="Story ID")
    sub.add_argument("--channel", required=True, help="Channel ID or name")
    sub.add_argument("--title", help="Defaults to the story's title")

    command("channels", cmd_channels, "List channels (shared by every project)")
    sub = command("add-channel", cmd_add_channel, "Add a channel: where scripts get published")
    sub.add_argument("--name", required=True)
    sub.add_argument("--kind", choices=CHANNEL_KINDS, default="video", help="video (a video script) or post (a text post, like WhatsApp)")
    sub.add_argument("--platform", help="e.g. YouTube Shorts, Instagram Reels, WhatsApp channel")
    sub.add_argument("--language", choices=LANGUAGES)
    sub.add_argument("--audience")
    sub.add_argument("--format", help="Length, structure, tone; defaults to a format for the kind")

    for name in ("design", "voice"):
        sub = command(name, cmd_channel_settings, f"Read or save a channel's {name}")
        sub.add_argument("--channel", required=True, help="Channel ID or name")
        sub.add_argument("--file", help="JSON file, or - for stdin; omitted to read")
    command("presets", cmd_presets, "List channel look presets")
    sub = command("fonts", cmd_fonts, "List scene font families")
    sub.add_argument("--devanagari", action="store_true")
    sub = command("scenes", cmd_scenes, "Inspect script beats, timing, and production warnings")
    sub.add_argument("--script", required=True)
    sub.add_argument("--json", action="store_true")
    for name, handler in (("angles", cmd_angles), ("review", cmd_review)):
        sub = command(name, handler, f"Validate and save a script's {name}")
        sub.add_argument("--script", required=True)
        sub.add_argument("--file", required=True, help="JSON file, or - for stdin")
    sub = command("export", cmd_export, "Export a video script for HyperFrames")
    sub.add_argument("--script", required=True)
    sub.add_argument("--out", help="Output folder (default: the script's render folder)")

    sub = command("render", cmd_render, "Render a video script to MP4 on this machine (needs Chrome and ffmpeg)")
    sub.add_argument("--script", required=True)
    sub.add_argument("--out", help="Also copy the MP4 here (a file or folder)")
    sub.add_argument("--draft", action="store_true", help="Faster, smaller, lower quality")

    sub = command("images", cmd_images, "Search openly licensed photos (Wikimedia Commons, Openverse) for a beat")
    sub.add_argument("query", help="What should be in the photo: concrete objects, places, people's roles")
    sub.add_argument("--limit", type=int, default=6, help="Results per provider")
    sub.add_argument("--orientation", choices=["any", "tall", "wide", "square"], default="any")
    sub.add_argument("--provider", choices=["all", "wikimedia", "openverse"], default="all")
    sub.add_argument("--preview", metavar="DIR", help="Download small previews here so you can look at them")

    sub = command("media", cmd_media, "List, add, or remove a script's images")
    sub.add_argument("--script", required=True)
    sub.add_argument("--add", metavar="FILE_OR_URL", help="An image file you made or downloaded, or an image URL")
    sub.add_argument("--name", help="File name to keep (default: from the file or URL)")
    sub.add_argument("--credit", help='On-screen credit, e.g. "Photo: Jane Doe / Wikimedia Commons, CC BY-SA 4.0"')
    sub.add_argument("--source", help="Page the image came from")
    sub.add_argument("--license")
    sub.add_argument("--remove", metavar="FILE", help="File name in media/ to remove")

    command("voice-providers", cmd_voices_providers, "List text-to-speech providers and whether each is ready")
    sub = command("voices", cmd_voices, "List a provider's voices")
    sub.add_argument("--provider", required=True, choices=list(tts.PROVIDERS))
    sub.add_argument("--language", default="English", help="English, Hindi, Hinglish, or a code like hi-IN")
    sub = command("voice-key", cmd_voice_key, "Save (or remove) a provider's API key in the studio's .secrets.json")
    sub.add_argument("--provider", required=True, choices=[p for p, x in tts.PROVIDERS.items() if x.key])
    sub.add_argument("--key", help="The key, or - to read it from stdin")
    sub.add_argument("--remove", action="store_true")
    sub = command("narration", cmd_narration, "Read or save a video channel's voiceover settings")
    sub.add_argument("--channel", required=True, help="Channel ID or name")
    sub.add_argument("--file", help="JSON file, or - for stdin; omitted to read")
    sub = command("say", cmd_say, "Speak a line in a channel's voiceover, to try the voice")
    sub.add_argument("--channel", required=True)
    sub.add_argument("--text", help="Defaults to a sample line in the channel's language")
    sub.add_argument("--out", default="sample.wav")
    sub = command("narrate", cmd_narrate, "Make the voiceover for a video script (beats without a current clip)")
    sub.add_argument("--script", required=True)
    sub.add_argument("--force", action="store_true", help="Redo every beat")
    sub = command("take", cmd_take, "Use your own recording for a beat's voiceover (or remove it)")
    sub.add_argument("--script", required=True)
    sub.add_argument("--beat", type=int, required=True, help="Number of the beat, counting beats with words from 1")
    sub.add_argument("--file", help="The audio file: WAV, MP3, M4A, WebM, …")
    sub.add_argument("--remove", action="store_true")
    sub = command("captions", cmd_captions, "Write the voiceover as SRT captions")
    sub.add_argument("--script", required=True)
    sub.add_argument("--out", help="File to write (default: print)")

    command("platforms", cmd_platforms, "List publishing platforms and where each channel publishes")
    sub = command("platform-app", cmd_platform_app, "Save your own YouTube or TikTok app's credentials (for connecting accounts)")
    sub.add_argument("--platform", required=True, choices=[p for p, x in pub.PLATFORMS.items() if x.app_keys])
    sub.add_argument("--id", help="Client ID (YouTube) or client key (TikTok); - reads stdin")
    sub.add_argument("--secret", help="Client secret; - reads stdin")
    sub = command("connect", cmd_connect, "Connect a video channel to its YouTube, Instagram or TikTok account")
    sub.add_argument("--channel", required=True)
    sub.add_argument("--platform", choices=list(pub.PLATFORMS))
    sub.add_argument("--token", help="An access token to connect with (Instagram, or TikTok); - reads stdin")
    sub.add_argument("--captions", action="store_true", help="YouTube: also allow uploading captions (asks for broader access)")
    sub = command("disconnect", cmd_disconnect, "Disconnect a channel's account and forget its token")
    sub.add_argument("--channel", required=True)
    sub = command("publishing", cmd_publishing, "Read or save where a channel publishes and its post defaults")
    sub.add_argument("--channel", required=True)
    sub.add_argument("--file", help="JSON file, or - for stdin; omitted to read")
    sub = command("publish-details", cmd_publish_details, "Read or save a script's post: title, description, caption, tags, privacy, time")
    sub.add_argument("--script", required=True)
    sub.add_argument("--file", help="JSON file, or - for stdin; omitted to read")
    sub = command("publish", cmd_publish, "Upload a rendered video to its channel's account (only when the user asks)")
    sub.add_argument("--script", required=True)
    sub.add_argument("--yes", action="store_true", help="Confirm: this posts to a real account")
    sub = command("stats", cmd_stats, "Fetch a published video's views, likes and comments")
    sub.add_argument("--script", required=True)

    sub = command("comments", cmd_comments, "List a script's open comments in the order they appear")
    sub.add_argument("--script", required=True)

    sub = command("resolve", cmd_resolve, "Resolve a comment after addressing it")
    sub.add_argument("--script", required=True)
    sub.add_argument("--comment", required=True)
    sub.add_argument("--reply", help="One line on what you changed")

    args = parser.parse_args(argv)
    root = workspace_path(args.workspace)
    try:
        if args.command in ("init", "projects", "new-project", "status", "serve", "channels", "add-channel", "design", "voice", "presets", "fonts", "images",
                            "voice-providers", "voices", "voice-key", "narration", "say",
                            "platforms", "platform-app", "connect", "disconnect", "publishing"):
            args.handler(root, args)
        else:
            args.handler(find_project(root, args.project), args)
    except (ValueError, KeyError, RuntimeError) as error:
        raise SystemExit(f"Error: {error.args[0] if error.args else error}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()

#!/usr/bin/env python3
"""Vid Studio workspace helper: state, monitoring, evidence capture, and checks.

Standard library only. The workspace is --workspace, else $VID_STUDIO_HOME, else ~/vid-studio.
Every command prints what it did so the calling agent can continue from the output.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import html
import json
import mimetypes
import os
import re
import shutil
import signal
import sqlite3
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
STAGES = ["planning", "researching", "brief-review", "writing", "script-review", "approved", "dropped"]
CLAIM_STATUSES = {"verified", "single-source", "disputed", "unverified"}
STRONG_SOURCE_TYPES = {"primary", "data"}
REFRESH_AFTER = {"init", "add-source", "add-topic", "lead", "scan", "checked", "triaged",
                 "new-project", "no-news", "snapshot", "stage"}
FEED_PATHS = ["/feed", "/rss", "/feed.xml", "/rss.xml", "/atom.xml", "/index.xml", "/feeds/posts/default"]


# ---------------------------------------------------------------- basics

def today() -> str:
    return dt.date.today().isoformat()


def now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


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


def project_dir(ws: Path, project_id: str) -> Path:
    path = ws / "projects" / project_id
    if not (path / "project.json").exists():
        raise SystemExit(f"Unknown project: {project_id} (expected {path}/project.json)")
    return path


def find(records: list, record_id: str, label: str) -> dict:
    for record in records:
        if record.get("id") == record_id:
            return record
    raise SystemExit(f"Unknown {label}: {record_id}")


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


def locale(ws: Path) -> tuple[str, str]:
    settings = load(ws / "studio.json", {}).get("locale", {})
    return settings.get("language") or "en", (settings.get("country") or "US").upper()


# ---------------------------------------------------------------- html → text

class TextExtractor(HTMLParser):
    SKIP = {"script", "style", "noscript", "svg", "template", "iframe", "nav", "footer", "aside", "form", "button"}
    BLOCK = {"p", "div", "br", "li", "tr", "section", "article", "main", "blockquote", "pre", "table",
             "ul", "ol", "dd", "dt", "figcaption", "h1", "h2", "h3", "h4", "h5", "h6"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.meta, self.title, self.skip, self.in_title = [], {}, "", 0, False

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "meta":
            key = (attributes.get("property") or attributes.get("name") or attributes.get("itemprop") or "").lower()
            if key and attributes.get("content"):
                self.meta.setdefault(key, attributes["content"].strip())
        elif tag == "title":
            self.in_title = True
        elif tag in self.SKIP:
            self.skip += 1
        elif tag in self.BLOCK:
            self.parts.append("\n")
            if tag in ("h1", "h2", "h3"):
                self.parts.append("## ")
            elif tag == "li":
                self.parts.append("- ")

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        elif tag in self.SKIP:
            self.skip = max(0, self.skip - 1)
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        elif not self.skip:
            self.parts.append(data)

    def text(self) -> str:
        lines = [re.sub(r"[ \t\r\f\v]+", " ", line).strip() for line in "".join(self.parts).split("\n")]
        lines = [line for line in lines if line and line not in ("##", "-")]
        return "\n".join(lines)


def extract_html(raw: str) -> dict:
    parser = TextExtractor()
    parser.feed(raw)
    meta = parser.meta
    published = next((meta[k] for k in ("article:published_time", "datepublished", "date", "dc.date", "pubdate") if k in meta), "")
    return {
        "title": clean_text(meta.get("og:title") or parser.title),
        "publisher": clean_text(meta.get("og:site_name", "")),
        "published": published,
        "text": parser.text(),
    }


# ---------------------------------------------------------------- commands

def cmd_init(ws: Path, args) -> None:
    created, kept = [], []
    templates = ASSETS / "workspace"
    for source in sorted(templates.rglob("*")):
        if not source.is_file():
            continue
        target = ws / source.relative_to(templates)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            kept.append(str(target.relative_to(ws)))
        else:
            shutil.copyfile(source, target)
            created.append(str(target.relative_to(ws)))
    for folder in ("inbox", "projects", "digests"):
        (ws / folder).mkdir(parents=True, exist_ok=True)
    print(f"Workspace: {ws}")
    print(f"Created: {', '.join(created) or 'nothing'}")
    if kept:
        print(f"Kept existing: {', '.join(kept)}")


def setup_gaps(studio: dict) -> list[str]:
    gaps = [key for key in ("owner", "audience", "language", "timezone") if not studio.get(key)]
    if not studio.get("interests"):
        gaps.append("interests")
    return gaps


def status_report(ws: Path) -> tuple[list[str], list[str]]:
    """Summary lines and next actions, shared by `status` and the UI."""
    lines: list[str] = []
    if not (ws / "studio.json").exists():
        return [f"Workspace: {ws} (not created)"], ["Run `studio.py init`, then onboard the user (references/setup.md)."]
    studio = load(ws / "studio.json")
    sources = load(ws / "sources.json")["sources"]
    topics = load(ws / "topics.json")["topics"]
    state = load(ws / "state.json")
    projects = []
    for path in sorted((ws / "projects").glob("*/project.json")):
        projects.append(load(path))

    gaps = setup_gaps(studio)
    enabled = [s for s in sources if s.get("enabled", True)]
    feeds = [s for s in enabled if s.get("feed")]
    failing = [s["id"] for s in enabled if state.get("sources", {}).get(s["id"], {}).get("last_error")]
    active = [t for t in topics if t.get("status") == "active"]
    proposed = [t for t in topics if t.get("status") == "proposed"]
    due = [t for t in active if t.get("mode") == "daily" and t.get("last_run") != today()]
    pending_once = [t for t in active if t.get("mode") == "once" and not t.get("projects")]
    untriaged = state.get("inbox_since_triage", 0)
    last_scan = state.get("last_scan") or "never"

    lines.append(f"Workspace: {ws}")
    lines.append(f"Setup: {'complete' if studio.get('setup_complete') and not gaps else 'incomplete'}"
          + (f" (missing: {', '.join(gaps)})" if gaps else ""))
    lines.append(f"Sources: {len(enabled)} enabled ({len(feeds)} feeds, {len(enabled) - len(feeds)} manual pages)"
          + f" · last scan: {last_scan}" + (f" · failing: {', '.join(failing)}" if failing else ""))
    lines.append(f"Topics: {len(active)} active, {len(proposed)} proposed"
          + (f" · daily due: {', '.join(t['id'] for t in due)}" if due else "")
          + (f" · once not started: {', '.join(t['id'] for t in pending_once)}" if pending_once else ""))
    lines.append(f"Inbox: {untriaged} items since last triage")
    lines.append(f"Schedule: {studio.get('schedule', {}).get('description') or 'none recorded'}")
    open_projects = [p for p in projects if p.get("stage") not in ("approved", "dropped")]
    lines.append(f"Projects: {len(projects)} total, {len(open_projects)} open")
    for project in projects[-15:]:
        lines.append(f"  {project['id']} · {project.get('stage')} · {project.get('title')}")

    actions = []
    if not studio.get("setup_complete") or gaps:
        actions.append("Onboard the user and fill studio.json (references/setup.md).")
    if not enabled:
        actions.append("Discover sources to monitor (references/discover.md).")
    if not active and not proposed:
        actions.append("Discover topics (references/discover.md).")
    if proposed:
        actions.append(f"Ask the user to approve proposed topics: {', '.join(t['id'] for t in proposed)}.")
    if feeds and not str(last_scan).startswith(today()):
        actions.append("Scan sources: `studio.py scan` (references/discover.md#scan).")
    if untriaged:
        actions.append("Triage the inbox into leads and proposed topics (references/discover.md#triage).")
    for topic in due:
        actions.append(f"Run daily topic {topic['id']}: new project or `no-news` (references/research.md).")
    for topic in pending_once:
        actions.append(f"Research once topic {topic['id']} (references/research.md).")
    for project in open_projects:
        stage = project.get("stage")
        if stage in ("planning", "researching"):
            actions.append(f"Continue research on {project['id']} (references/research.md).")
        elif stage == "writing":
            actions.append(f"Write post and script for {project['id']} (references/write.md).")
        elif stage in ("brief-review", "script-review"):
            actions.append(f"Waiting for user review: {project['id']} ({stage}).")
    if studio.get("setup_complete") and not studio.get("schedule", {}).get("description"):
        actions.append("Offer to schedule the daily routine (references/schedule.md).")
    return lines, actions or ["Nothing pending. Ask the user what to research next."]


def cmd_status(ws: Path, args) -> None:
    lines, actions = status_report(ws)
    print("\n".join(lines))
    print("Next actions:")
    for action in actions:
        print(f"- {action}")


def cmd_add_source(ws: Path, args) -> None:
    data = load(ws / "sources.json")
    sources = data["sources"]
    language, country = locale(ws)
    kind, url, feed, name = args.kind, args.url, args.feed, args.name
    if args.news_query:
        query = urllib.parse.quote_plus(args.news_query)
        params = f"hl={language}-{country}&gl={country}&ceid={country}:{language}"
        feed = f"https://news.google.com/rss/search?q={query}&{params}"
        url = url or f"https://news.google.com/search?q={query}&{params}"
        kind, name = "news", name or f"Google News: {args.news_query}"
    elif args.trends_geo:
        geo = args.trends_geo.upper()
        feed = f"https://trends.google.com/trending/rss?geo={geo}"
        url = url or f"https://trends.google.com/trending?geo={geo}"
        kind, name = "trends", name or f"Google Trends: {geo}"
    if not url and not feed:
        raise SystemExit("Provide --url, --feed, --news-query, or --trends-geo")
    if not name:
        raise SystemExit("Provide --name")
    for source in sources:
        if (url and source.get("url") == url) or (feed and source.get("feed") == feed):
            raise SystemExit(f"Already monitored as {source['id']}")

    notes = []
    if feed:
        if not try_feed(feed):
            notes.append("warning: feed did not return items right now")
    elif url and not args.no_discover:
        feed, explanation = discover_feed(url)
        notes.append(explanation)
    kind = kind or ("feed" if feed else "page")

    source = {
        "id": unique_id(args.id or slugify(name, 32), {s["id"] for s in sources}),
        "name": name, "kind": kind, "url": url or feed, "feed": feed,
        "why": args.why or "", "enabled": True, "added": today(),
    }
    sources.append(source)
    save(ws / "sources.json", data)
    print(f"Added source {source['id']} ({kind}){': ' + '; '.join(notes) if notes else ''}")


def cmd_add_topic(ws: Path, args) -> None:
    data = load(ws / "topics.json")
    topics = data["topics"]
    source_ids = {s["id"] for s in load(ws / "sources.json")["sources"]}
    unknown = [s for s in args.source or [] if s not in source_ids]
    if unknown:
        raise SystemExit(f"Unknown source IDs: {', '.join(unknown)}")
    topic = {
        "id": unique_id(args.id or slugify(args.title, 40), {t["id"] for t in topics}),
        "title": args.title, "angle": args.angle or "", "why": args.why or "",
        "mode": args.mode, "status": args.status,
        "queries": args.query or [], "source_ids": args.source or [],
        "added": today(), "last_run": None, "leads": [], "projects": [], "history": [],
    }
    topics.append(topic)
    save(ws / "topics.json", data)
    print(f"Added topic {topic['id']} ({topic['mode']}, {topic['status']})")


def cmd_lead(ws: Path, args) -> None:
    data = load(ws / "topics.json")
    topic = find(data["topics"], args.topic, "topic")
    leads = topic.setdefault("leads", [])
    if any(lead.get("url") == args.url for lead in leads):
        print(f"Lead already on {topic['id']}")
        return
    leads.append({"url": args.url, "title": args.title or "", "note": args.note or "", "added": today()})
    save(ws / "topics.json", data)
    print(f"Lead added to {topic['id']} ({len(leads)} pending)")


def cmd_scan(ws: Path, args) -> None:
    sources = load(ws / "sources.json")["sources"]
    state = load(ws / "state.json")
    seen_path = ws / "inbox" / "seen.json"
    seen = load(seen_path, {"keys": {}})["keys"]
    cutoff = (dt.date.today() - dt.timedelta(days=90)).isoformat()
    seen = {key: day for key, day in seen.items() if day >= cutoff}
    source_state = state.setdefault("sources", {})

    sections, manual, errors, total, records = [], [], [], 0, []
    scanned_at = now()
    for source in sources:
        if not source.get("enabled", True) or (args.source and source["id"] not in args.source):
            continue
        if not source.get("feed"):
            manual.append(source)
            continue
        record = source_state.setdefault(source["id"], {})
        record["last_attempt"] = now()
        try:
            items = parse_feed(fetch(source["feed"])[0])
        except Exception as error:
            record["last_error"] = f"{type(error).__name__}: {error}"
            errors.append(f"{source['id']}: {record['last_error']}")
            continue
        record.pop("last_error", None)
        record["last_ok"] = now()
        fresh = []
        for item in items:
            keys = [key for key in (url_key(item["url"]), title_key(item["title"])) if key]
            if not keys or any(key in seen for key in keys):
                continue
            for key in keys:
                seen[key] = today()
            fresh.append(item)
            if len(fresh) >= args.limit:
                break
        record["last_new"] = len(fresh)
        total += len(fresh)
        for item in fresh:
            key = url_key(item["url"]) or title_key(item["title"])
            records.append({"id": hashlib.sha1(key.encode()).hexdigest()[:12], "date": today(),
                            "scanned_at": scanned_at, "source_id": source["id"], **item})
        if fresh:
            lines = [f"### {source['name']} ({source['id']})"]
            for item in fresh:
                meta = " · ".join(part for part in (item["published"], domain(item["url"])) if part)
                lines.append(f"- [{item['title']}]({item['url']}) · {meta}")
                if item["summary"]:
                    lines.append(f"  {item['summary']}")
            sections.append("\n".join(lines))

    inbox_file = ws / "inbox" / f"{today()}.md"
    if sections:
        header = "" if inbox_file.exists() else f"# Inbox {today()}\n"
        with inbox_file.open("a", encoding="utf-8") as output:
            output.write(f"{header}\n## Scan {dt.datetime.now().strftime('%H:%M')}\n\n" + "\n\n".join(sections) + "\n")
    if records:
        # Structured copy of the inbox for the UI and SQLite index; the Markdown file is for reading.
        with (ws / "inbox" / "items.jsonl").open("a", encoding="utf-8") as output:
            output.writelines(json.dumps(record, ensure_ascii=False) + "\n" for record in records)
    state["last_scan"] = scanned_at
    state["inbox_since_triage"] = state.get("inbox_since_triage", 0) + total
    save(seen_path, {"keys": seen})
    save(ws / "state.json", state)

    print(f"New items: {total}" + (f" → {inbox_file}" if total else ""))
    for error in errors:
        print(f"Failed: {error}")
    if manual:
        print("Check these pages yourself (no feed):")
        for source in manual:
            last = source_state.get(source["id"], {}).get("last_checked", "never")
            print(f"- {source['id']}: {source['url']} (last checked {last})")


def cmd_checked(ws: Path, args) -> None:
    state = load(ws / "state.json")
    for source_id in args.source:
        state.setdefault("sources", {}).setdefault(source_id, {})["last_checked"] = now()
    save(ws / "state.json", state)
    print(f"Marked checked: {', '.join(args.source)}")


def cmd_triaged(ws: Path, args) -> None:
    state = load(ws / "state.json")
    state["inbox_since_triage"] = 0
    state["last_triage"] = now()
    save(ws / "state.json", state)
    print("Inbox marked triaged")


def cmd_new_project(ws: Path, args) -> None:
    topics_data = load(ws / "topics.json")
    topic = find(topics_data["topics"], args.topic, "topic") if args.topic else None
    title = args.title or (topic["title"] if topic else None)
    if not title:
        raise SystemExit("Provide --topic or --title")
    existing = {p.name for p in (ws / "projects").glob("*")}
    project_id = unique_id(f"{today()}-{slugify(title, 40)}", existing)
    path = ws / "projects" / project_id
    (path / "evidence").mkdir(parents=True)
    (path / "data").mkdir()
    for template in sorted((ASSETS / "project").iterdir()):
        content = template.read_text(encoding="utf-8").replace("{{title}}", title).replace("{{date}}", today())
        (path / template.name).write_text(content, encoding="utf-8")

    project = load(path / "project.json")
    project.update({
        "id": project_id, "title": title, "created": today(),
        "topic_id": topic["id"] if topic else None,
        "mode": topic["mode"] if topic else "once",
        "angle": args.angle or (topic.get("angle", "") if topic else ""),
        "queries": list(topic.get("queries", [])) if topic else [],
        "leads": list(topic.get("leads", [])) if topic else [],
        "previous_projects": list(topic.get("projects", [])) if topic else [],
        "stage": "planning", "history": [{"stage": "planning", "at": now()}],
    })
    save(path / "project.json", project)
    if topic:
        topic["leads"] = []
        topic.setdefault("projects", []).append(project_id)
        topic.setdefault("history", []).append({"date": today(), "result": "project", "project": project_id})
        topic["last_run"] = today()
        if topic["mode"] == "once":
            topic["status"] = "used"
        save(ws / "topics.json", topics_data)
    print(f"Project: {path}")
    if project["previous_projects"]:
        print(f"Baseline (read their brief.md first): {', '.join(project['previous_projects'][-3:])}")
    if project["leads"]:
        print(f"Leads carried over: {len(project['leads'])}")


def cmd_no_news(ws: Path, args) -> None:
    data = load(ws / "topics.json")
    topic = find(data["topics"], args.topic, "topic")
    topic["last_run"] = today()
    topic.setdefault("history", []).append({"date": today(), "result": "no-news", "note": args.note})
    save(ws / "topics.json", data)
    print(f"Recorded no-news run for {topic['id']}")


def cmd_snapshot(ws: Path, args) -> None:
    path = project_dir(ws, args.project)
    registry = load(path / "sources.json")
    for source in registry["sources"]:
        if source["url"] == args.url:
            print(f"Already captured as {source['id']} ({source['evidence']})")
            return
    source_id = f"S{max([int(s['id'][1:]) for s in registry['sources']] + [0]) + 1}"
    info = {"title": args.title or "", "publisher": args.publisher or "", "published": args.published or "", "text": ""}
    final_url, evidence_name, warning = args.url, f"{source_id}.md", ""

    if args.text_file:
        info["text"] = Path(args.text_file).expanduser().read_text(encoding="utf-8")
    else:
        try:
            data, content_type, final_url = fetch(args.url)
        except Exception as error:
            raise SystemExit(f"Fetch failed: {type(error).__name__}: {error}\n"
                             "Open the page with your own browsing tool, save the relevant text to a file, "
                             "and rerun with --text-file FILE --title TITLE.")
        if "pdf" in content_type.lower() or data[:5] == b"%PDF-":
            evidence_name = f"{source_id}.pdf"
            (path / "evidence" / evidence_name).write_bytes(data)
            warning = "Saved PDF. Quote the passages you use in the claim notes."
        else:
            extracted = extract_html(decode(data, content_type))
            info = {key: info[key] or extracted[key] for key in info}
            if len(info["text"]) < 600:
                warning = "Very little text extracted (paywall or script-rendered page?). Capture with --text-file if needed."

    info["publisher"] = info["publisher"] or domain(final_url)
    digest = hashlib.sha256(info["text"].encode() if evidence_name.endswith(".md") else (path / "evidence" / evidence_name).read_bytes()).hexdigest()
    if evidence_name.endswith(".md"):
        header = [f"id: {source_id}", f"url: {args.url}", f"final_url: {final_url}", f"title: {info['title']}",
                  f"publisher: {info['publisher']}", f"published: {info['published']}", f"accessed: {now()}",
                  f"type: {args.type}", f"sha256: {digest}"]
        (path / "evidence" / evidence_name).write_text("---\n" + "\n".join(header) + "\n---\n\n" + info["text"].strip() + "\n", encoding="utf-8")

    registry["sources"].append({
        "id": source_id, "url": args.url, "final_url": final_url, "title": info["title"],
        "publisher": info["publisher"], "published": info["published"], "accessed": today(),
        "type": args.type, "evidence": f"evidence/{evidence_name}", "note": args.note or "",
    })
    save(path / "sources.json", registry)
    print(f"{source_id}: {info['title'] or args.url} · {info['publisher']} · {len(info['text'])} chars → evidence/{evidence_name}")
    if warning:
        print(f"Warning: {warning}")


def run_checks(path: Path) -> tuple[list[str], list[str], str]:
    errors, warnings = [], []
    sources = {s["id"]: s for s in load(path / "sources.json")["sources"]}
    claims = {c["id"]: c for c in load(path / "claims.json")["claims"]}

    for source in sources.values():
        if not (path / source.get("evidence", "")).is_file():
            errors.append(f"{source['id']}: evidence file missing ({source.get('evidence')})")
        if domain(source.get("final_url") or source["url"]) == "news.google.com":
            warnings.append(f"{source['id']}: Google News redirect URL; capture the original article instead")

    counts = {status: 0 for status in CLAIM_STATUSES}
    for claim in claims.values():
        cid, status, refs = claim.get("id"), claim.get("status"), claim.get("sources", [])
        if status not in CLAIM_STATUSES:
            errors.append(f"{cid}: status must be one of {sorted(CLAIM_STATUSES)}")
            continue
        counts[status] += 1
        missing = [ref for ref in refs if ref not in sources]
        if missing:
            errors.append(f"{cid}: unknown sources {missing}")
        known = [sources[ref] for ref in refs if ref in sources]
        if not known and status != "unverified":
            errors.append(f"{cid}: no sources")
        if status == "verified":
            strong = any(s.get("type") in STRONG_SOURCE_TYPES for s in known)
            domains = {domain(s.get("final_url") or s["url"]) for s in known}
            if not strong and len(domains) < 2:
                errors.append(f"{cid}: 'verified' needs a primary/data source or two independent domains; use 'single-source'")
        if status == "disputed" and not claim.get("note"):
            warnings.append(f"{cid}: disputed claim needs a note describing both sides")

    for name in ("brief.md", "script.md", "post.md"):
        file = path / name
        if not file.exists():
            continue
        text = file.read_text(encoding="utf-8")
        for group in re.findall(r"\[(C\d+(?:\s*,\s*C\d+)*)\]", text):
            for cid in re.split(r"\s*,\s*", group):
                claim = claims.get(cid)
                if claim is None:
                    errors.append(f"{name}: cites unknown claim {cid}")
                elif claim.get("status") == "unverified":
                    errors.append(f"{name}: cites unverified claim {cid}")
                elif claim.get("status") == "disputed":
                    warnings.append(f"{name}: cites disputed {cid}; present it as contested")
                elif claim.get("status") == "single-source" and re.search(r"\d", claim.get("text", "")):
                    warnings.append(f"{name}: cites single-source number {cid}; attribute it or verify")
        if "TODO" in text:
            warnings.append(f"{name}: still contains TODO placeholders")

    errors, warnings = list(dict.fromkeys(errors)), list(dict.fromkeys(warnings))
    summary = (f"{len(claims)} claims ({', '.join(f'{v} {k}' for k, v in sorted(counts.items()) if v)}), "
               f"{len(sources)} sources")
    return errors, warnings, summary


def cmd_check(ws: Path, args) -> None:
    errors, warnings, summary = run_checks(project_dir(ws, args.project))
    print(f"{args.project}: {summary}")
    for error in errors:
        print(f"ERROR {error}")
    for warning in warnings:
        print(f"WARN  {warning}")
    print("Check passed" if not errors else f"Check failed with {len(errors)} errors")
    if errors:
        raise SystemExit(1)


def cmd_stage(ws: Path, args) -> None:
    path = project_dir(ws, args.project)
    if args.stage in ("brief-review", "script-review", "approved") and not args.force:
        errors, _, _ = run_checks(path)
        if errors:
            raise SystemExit(f"Fix check errors before '{args.stage}' (run `studio.py check {args.project}`).")
    project = load(path / "project.json")
    project["stage"] = args.stage
    entry = {"stage": args.stage, "at": now()}
    if args.note:
        entry["note"] = args.note
    project.setdefault("history", []).append(entry)
    save(path / "project.json", project)
    print(f"{args.project} → {args.stage}")


# ---------------------------------------------------------------- explorer: data, SQLite index, HTML, server

PROJECT_DOCUMENTS = ("brief.md", "script.md", "post.md", "plan.md")
TEXT_TYPES = {".md", ".json", ".jsonl", ".csv", ".txt"}
DB_SCHEMA = """
CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE sources(id TEXT PRIMARY KEY, name TEXT, kind TEXT, url TEXT, feed TEXT, why TEXT, enabled INTEGER,
                     added TEXT, last_ok TEXT, last_checked TEXT, last_error TEXT, last_new INTEGER);
CREATE TABLE topics(id TEXT PRIMARY KEY, title TEXT, mode TEXT, status TEXT, angle TEXT, why TEXT, added TEXT,
                    last_run TEXT, pending_leads INTEGER);
CREATE TABLE topic_runs(topic_id TEXT, date TEXT, result TEXT, project_id TEXT, note TEXT);
CREATE TABLE leads(topic_id TEXT, url TEXT, title TEXT, note TEXT, added TEXT);
CREATE TABLE inbox(id TEXT, date TEXT, scanned_at TEXT, source_id TEXT, title TEXT, url TEXT, published TEXT, summary TEXT);
CREATE TABLE projects(id TEXT PRIMARY KEY, title TEXT, topic_id TEXT, mode TEXT, stage TEXT, created TEXT, angle TEXT,
                      check_errors INTEGER, check_warnings INTEGER);
CREATE TABLE project_sources(project_id TEXT, id TEXT, url TEXT, title TEXT, publisher TEXT, published TEXT,
                             accessed TEXT, type TEXT, evidence TEXT);
CREATE TABLE claims(project_id TEXT, id TEXT, text TEXT, status TEXT, subtopic TEXT, quote TEXT, note TEXT);
CREATE TABLE claim_sources(project_id TEXT, claim_id TEXT, source_id TEXT);
CREATE TABLE documents(project_id TEXT, name TEXT, text TEXT);
CREATE INDEX inbox_date ON inbox(date);
CREATE INDEX claims_status ON claims(status);
"""


def read_jsonl(path: Path, limit: int) -> list[dict]:
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines()[-limit:]:
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def collect(ws: Path) -> dict:
    """Everything the explorer shows, read fresh from the workspace files."""
    state = load(ws / "state.json")
    lines, actions = status_report(ws)
    projects = []
    for project_file in sorted((ws / "projects").glob("*/project.json"), reverse=True):
        path = project_file.parent
        record = {"id": path.name, "title": path.name, "dir": f"projects/{path.name}"}
        try:
            record.update(load(project_file))
            record["sources"] = load(path / "sources.json", {"sources": []})["sources"]
            record["claims"] = load(path / "claims.json", {"claims": []})["claims"]
            errors, warnings, summary = run_checks(path)
        except (SystemExit, Exception) as error:  # a hand-edited file may be broken; show it instead of failing
            record.setdefault("sources", [])
            record.setdefault("claims", [])
            errors, warnings, summary = [str(error)], [], "unreadable"
        record["check"] = {"errors": errors, "warnings": warnings, "summary": summary}
        record["files"] = {name: (path / name).read_text(encoding="utf-8")
                           for name in PROJECT_DOCUMENTS if (path / name).is_file()}
        record["data"] = []
        for table in sorted((path / "data").glob("*.csv")):
            with table.open(encoding="utf-8", newline="") as handle:
                record["data"].append({"name": table.name, "rows": list(csv.reader(handle))[:500]})
        projects.append(record)
    digests = [{"name": f.stem, "text": f.read_text(encoding="utf-8")}
               for f in sorted((ws / "digests").glob("*.md"), reverse=True)[:60]]
    return {
        "generated_at": now(), "workspace": str(ws),
        "studio": load(ws / "studio.json"),
        "sources": load(ws / "sources.json")["sources"],
        "source_state": state.get("sources", {}),
        "state": {key: value for key, value in state.items() if key != "sources"},
        "topics": load(ws / "topics.json")["topics"],
        "inbox": list(reversed(read_jsonl(ws / "inbox" / "items.jsonl", 5000))),
        "projects": projects, "digests": digests,
        "status": {"lines": lines, "actions": actions},
    }


def build_db(path: Path, data: dict) -> None:
    """Rebuild the read-only SQLite index. Files stay the source of truth."""
    temporary = path.with_suffix(".db.tmp")
    temporary.unlink(missing_ok=True)
    db = sqlite3.connect(temporary)
    try:
        db.executescript(DB_SCHEMA)
        db.executemany("INSERT INTO meta VALUES (?, ?)", [("generated_at", data["generated_at"]), ("workspace", data["workspace"])])
        for s in data["sources"]:
            health = data["source_state"].get(s.get("id"), {})
            db.execute("INSERT OR REPLACE INTO sources VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (
                s.get("id"), s.get("name"), s.get("kind"), s.get("url"), s.get("feed"), s.get("why"),
                int(bool(s.get("enabled", True))), s.get("added"), health.get("last_ok"), health.get("last_checked"),
                health.get("last_error"), health.get("last_new")))
        for t in data["topics"]:
            db.execute("INSERT OR REPLACE INTO topics VALUES (?,?,?,?,?,?,?,?,?)", (
                t.get("id"), t.get("title"), t.get("mode"), t.get("status"), t.get("angle"), t.get("why"),
                t.get("added"), t.get("last_run"), len(t.get("leads") or [])))
            db.executemany("INSERT INTO topic_runs VALUES (?,?,?,?,?)", [
                (t.get("id"), h.get("date"), h.get("result"), h.get("project"), h.get("note")) for h in t.get("history") or []])
            db.executemany("INSERT INTO leads VALUES (?,?,?,?,?)", [
                (t.get("id"), l.get("url"), l.get("title"), l.get("note"), l.get("added")) for l in t.get("leads") or []])
        db.executemany("INSERT INTO inbox VALUES (?,?,?,?,?,?,?,?)", [
            (i.get("id"), i.get("date"), i.get("scanned_at"), i.get("source_id"), i.get("title"), i.get("url"),
             i.get("published"), i.get("summary")) for i in data["inbox"]])
        for p in data["projects"]:
            db.execute("INSERT OR REPLACE INTO projects VALUES (?,?,?,?,?,?,?,?,?)", (
                p["id"], p.get("title"), p.get("topic_id"), p.get("mode"), p.get("stage"), p.get("created"),
                p.get("angle"), len(p["check"]["errors"]), len(p["check"]["warnings"])))
            db.executemany("INSERT INTO project_sources VALUES (?,?,?,?,?,?,?,?,?)", [
                (p["id"], s.get("id"), s.get("url"), s.get("title"), s.get("publisher"), s.get("published"),
                 s.get("accessed"), s.get("type"), s.get("evidence")) for s in p["sources"]])
            for c in p["claims"]:
                db.execute("INSERT INTO claims VALUES (?,?,?,?,?,?,?)", (
                    p["id"], c.get("id"), c.get("text"), c.get("status"), str(c.get("subtopic", "")),
                    c.get("quote"), c.get("note")))
                db.executemany("INSERT INTO claim_sources VALUES (?,?,?)", [(p["id"], c.get("id"), s) for s in c.get("sources") or []])
            db.executemany("INSERT INTO documents VALUES (?,?,?)", [(p["id"], name, text) for name, text in p["files"].items()])
        db.commit()
    finally:
        db.close()
    temporary.replace(path)


def render_html(data: dict) -> str:
    template = (ASSETS / "ui" / "index.html").read_text(encoding="utf-8")
    # Escaping "<" keeps scraped text from closing the <script> block; it stays valid JSON.
    payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    return template.replace("/*STUDIO_DATA*/null", payload)


def refresh(ws: Path) -> tuple[Path, Path]:
    data = collect(ws)
    page = ws / "ui" / "index.html"
    page.parent.mkdir(parents=True, exist_ok=True)
    temporary = page.with_suffix(".tmp")
    temporary.write_text(render_html(data), encoding="utf-8")
    temporary.replace(page)
    build_db(ws / "studio.db", data)
    return page, ws / "studio.db"


def running_server(ws: Path) -> dict | None:
    info = load(ws / "ui" / "server.json", {})
    if not info.get("url"):
        return None
    try:
        with urllib.request.urlopen(info["url"] + "health", timeout=2) as response:
            return info if response.read().decode() == str(ws) else None
    except Exception:
        return None


def make_handler(ws: Path):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, code: int, body: bytes, content_type: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            # Only answer requests addressed to this machine, which blocks DNS-rebinding reads by other websites.
            hostname = (self.headers.get("Host") or "").rsplit(":", 1)[0].strip("[]")
            if hostname not in ("localhost", "127.0.0.1", "::1"):
                return self.reply(403, b"Forbidden", "text/plain; charset=utf-8")
            path = urllib.parse.unquote(urllib.parse.urlsplit(self.path).path)
            if path == "/health":
                return self.reply(200, str(ws).encode(), "text/plain; charset=utf-8")
            if path in ("/", "/index.html", "/ui/", "/ui/index.html"):
                try:
                    body = render_html(collect(ws)).encode()
                except (SystemExit, Exception) as error:
                    return self.reply(500, f"Could not read the workspace: {error}".encode(), "text/plain; charset=utf-8")
                return self.reply(200, body, "text/html; charset=utf-8")
            target = (ws / path.lstrip("/")).resolve()
            if (not target.is_relative_to(ws) or not target.is_file() or target.suffix in (".db", ".tmp")
                    or any(part.startswith(".") for part in target.relative_to(ws).parts)):
                return self.reply(404, b"Not found", "text/plain; charset=utf-8")
            # Workspace files are shown as plain text so captured web pages can never run in the browser.
            content_type = ("text/plain; charset=utf-8" if target.suffix in TEXT_TYPES or target.suffix in (".html", ".htm")
                            else mimetypes.guess_type(target.name)[0] or "application/octet-stream")
            return self.reply(200, target.read_bytes(), content_type)

    return Handler


def cmd_ui(ws: Path, args) -> None:
    page, db = refresh(ws)
    server = running_server(ws)
    print(f"Explorer: {server['url'] if server else page.as_uri()}")
    if not server:
        print("For a link that works from any app or browser, run `studio.py serve --background`.")
    print(f"SQLite index: {db}")


def cmd_serve(ws: Path, args) -> None:
    info_path = ws / "ui" / "server.json"
    server_info = running_server(ws)
    if args.stop:
        if server_info:
            os.kill(server_info["pid"], signal.SIGTERM)
            print(f"Stopped explorer at {server_info['url']}")
        else:
            print("No explorer server running")
        info_path.unlink(missing_ok=True)
        return
    if server_info:
        print(f"Explorer: {server_info['url']}")
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
                print(f"Explorer: {server_info['url']}")
                return
            if process.poll() is not None:
                break
        raise SystemExit("Explorer server did not start. Run `studio.py serve` in the foreground to see why.")

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
    print(f"Explorer: {url} (Ctrl+C to stop)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        if load(info_path, {}).get("pid") == os.getpid():
            info_path.unlink(missing_ok=True)


def cmd_sql(ws: Path, args) -> None:
    _, db_path = refresh(ws)
    db = sqlite3.connect(f"{db_path.as_uri()}?mode=ro", uri=True)
    try:
        if not args.query:
            for (statement,) in db.execute("SELECT sql FROM sqlite_master WHERE type = 'table'"):
                print(statement + ";")
            return
        try:
            cursor = db.execute(args.query)
        except sqlite3.Error as error:
            raise SystemExit(f"SQL error: {error}")
        print("\t".join(column[0] for column in cursor.description or []))
        rows = cursor.fetchmany(args.limit + 1)
        for row in rows[: args.limit]:
            print("\t".join("" if value is None else str(value).replace("\t", " ").replace("\n", " ") for value in row))
        if len(rows) > args.limit:
            print(f"… more rows; raise --limit (now {args.limit})")
    finally:
        db.close()


# ---------------------------------------------------------------- cli

def main(argv=None) -> None:
    workspace_help = "Workspace directory (default: $VID_STUDIO_HOME or ~/vid-studio)"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", help=workspace_help)
    # Accept --workspace after the subcommand too, without clobbering one given before it.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--workspace", default=argparse.SUPPRESS, help=workspace_help)
    commands = parser.add_subparsers(dest="command", required=True)

    def command(name, handler, help_text):
        sub = commands.add_parser(name, parents=[common], help=help_text)
        sub.set_defaults(handler=handler)
        return sub

    command("init", cmd_init, "Create the workspace; never overwrites files")
    command("status", cmd_status, "Show state and the next actions")

    sub = command("add-source", cmd_add_source, "Monitor a website, feed, Google News query, or Trends region")
    sub.add_argument("--name")
    sub.add_argument("--url")
    sub.add_argument("--feed", help="RSS/Atom URL, including Google Alerts RSS feeds")
    sub.add_argument("--news-query", help="Google News search to monitor")
    sub.add_argument("--trends-geo", help="Google Trends daily trending searches for a country code")
    sub.add_argument("--kind", choices=["feed", "page", "news", "alert", "trends"])
    sub.add_argument("--why")
    sub.add_argument("--id")
    sub.add_argument("--no-discover", action="store_true", help="Skip feed auto-discovery for --url")

    sub = command("add-topic", cmd_add_topic, "Add a topic")
    sub.add_argument("--title", required=True)
    sub.add_argument("--mode", choices=["once", "daily"], required=True)
    sub.add_argument("--status", choices=["proposed", "active"], default="proposed")
    sub.add_argument("--angle")
    sub.add_argument("--why")
    sub.add_argument("--query", action="append", help="Search query; repeatable")
    sub.add_argument("--source", action="append", help="Related source ID; repeatable")
    sub.add_argument("--id")

    sub = command("lead", cmd_lead, "Attach an inbox item to a topic for its next run")
    sub.add_argument("--topic", required=True)
    sub.add_argument("--url", required=True)
    sub.add_argument("--title")
    sub.add_argument("--note")

    sub = command("scan", cmd_scan, "Fetch feeds into inbox/<date>.md, skipping items already seen")
    sub.add_argument("--source", action="append", help="Only this source ID; repeatable")
    sub.add_argument("--limit", type=int, default=15, help="Max new items per source")

    sub = command("checked", cmd_checked, "Record that manual pages were checked")
    sub.add_argument("source", nargs="+")

    command("triaged", cmd_triaged, "Mark the inbox as triaged")

    sub = command("new-project", cmd_new_project, "Start a research project from a topic or title")
    sub.add_argument("--topic")
    sub.add_argument("--title")
    sub.add_argument("--angle")

    sub = command("no-news", cmd_no_news, "Record a daily run with nothing worth a video")
    sub.add_argument("--topic", required=True)
    sub.add_argument("--note", required=True)

    sub = command("snapshot", cmd_snapshot, "Save a source locally as evidence and register it")
    sub.add_argument("project")
    sub.add_argument("url")
    sub.add_argument("--type", choices=["primary", "data", "secondary", "analysis", "opinion"], default="secondary")
    sub.add_argument("--title")
    sub.add_argument("--publisher")
    sub.add_argument("--published")
    sub.add_argument("--note")
    sub.add_argument("--text-file", help="Use text you captured yourself instead of fetching")

    sub = command("check", cmd_check, "Validate claims, sources, evidence, and citations")
    sub.add_argument("project")

    command("ui", cmd_ui, "Rebuild the HTML explorer and SQLite index")

    sub = command("serve", cmd_serve, "Serve the explorer at http://localhost (always fresh)")
    sub.add_argument("--port", type=int, default=8765)
    sub.add_argument("--background", action="store_true", help="Start detached and return the URL")
    sub.add_argument("--stop", action="store_true")

    sub = command("sql", cmd_sql, "Run a read-only SQL query on the index; no query prints the schema")
    sub.add_argument("query", nargs="?")
    sub.add_argument("--limit", type=int, default=200)

    sub = command("stage", cmd_stage, "Move a project to a stage (review stages require a passing check)")
    sub.add_argument("project")
    sub.add_argument("stage", choices=STAGES)
    sub.add_argument("--note")
    sub.add_argument("--force", action="store_true")

    args = parser.parse_args(argv)
    workspace = workspace_path(args.workspace)
    if args.command not in ("init", "status") and not (workspace / "studio.json").exists():
        raise SystemExit(f"No workspace at {workspace}. Run: studio.py init")
    args.handler(workspace, args)
    if args.command in REFRESH_AFTER:
        try:
            refresh(workspace)
        except Exception as error:  # the command itself succeeded; a stale explorer is not fatal
            print(f"Warning: explorer not refreshed: {error}", file=sys.stderr)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()

#!/usr/bin/env python3
"""Resolve local preferences read-only; no approvals, writes, or stage transitions."""

import argparse
import copy
import hashlib
import json
import math
import re
from fractions import Fraction
from pathlib import Path

ID_PATTERN = re.compile(r"[a-z0-9][a-z0-9-]{0,63}\Z")
OPERATIONAL_KEYS = {"tools", "workflow", "data_policy", "budget", "renderer", "policy", "approval_required_at_every_stage"}


def merge(base, override):
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def identifier(value):
    if not isinstance(value, str) or not ID_PATTERN.fullmatch(value):
        raise ValueError(f"Invalid context/profile ID: {value!r}")
    return value


def preferences(value, label):
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    forbidden = OPERATIONAL_KEYS.intersection(value)
    if forbidden:
        raise ValueError(f"Operational settings belong in studio policy, not {label}: {sorted(forbidden)}")
    return value


def resolve(workspace, profile_id=None, topic_id=None, source_id=None, project_id=None):
    workspace = Path(workspace).expanduser().resolve()
    inputs = []
    drafts = []

    def read(relative):
        path = workspace / relative
        if not path.resolve().is_relative_to(workspace):
            raise ValueError(f"Input escapes workspace: {relative}")
        raw = path.read_bytes()
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError(f"Expected JSON object: {relative}")
        if not any(item["path"] == relative for item in inputs):
            inputs.append({"path": relative, "sha256": hashlib.sha256(raw).hexdigest()})
        return value

    def record(relative, key, requested):
        if requested is None:
            return {}
        identifier(requested)
        entries = read(relative).get(key, [])
        if not isinstance(entries, list) or any(not isinstance(entry, dict) for entry in entries):
            raise ValueError(f"{key} must be an array of objects")
        matches = [entry for entry in entries if entry.get("id") == requested]
        if len(matches) != 1:
            raise ValueError(f"Expected exactly one {key} record for {requested}")
        return matches[0]

    studio = read("studio.json")
    project = {}
    if project_id is not None:
        identifier(project_id)
        project = read(f"projects/{project_id}/project.json")
        if project.get("id") != project_id:
            raise ValueError("Project ID does not match its directory")
        for explicit, field in [(topic_id, "topic_id"), (source_id, "source_id"), (profile_id, "profile_id")]:
            if explicit is not None and project.get(field) is not None and explicit != project[field]:
                raise ValueError(f"Explicit {field} conflicts with project context")
        topic_id = topic_id or project.get("topic_id")
        source_id = source_id or project.get("source_id")
    topic = record("monitoring/topics.json", "topics", topic_id)
    source = record("monitoring/sources.json", "sources", source_id)
    selected = profile_id or project.get("profile_id") or topic.get("profile_id") or source.get("profile_id") or studio.get("default_profile_id")

    if "defaults" in studio:
        effective = copy.deepcopy(preferences(studio["defaults"], "studio defaults"))
    else:
        # Preserve original settings; newly added draft profile files are not selected implicitly.
        effective = {key: copy.deepcopy(studio[key]) for key in ("audience", "duration_seconds", "video", "destinations") if key in studio}
        if "topic_domain" in studio:
            effective["research"] = {"topic_domain": studio["topic_domain"]}
        if "languages" in studio:
            effective["script"] = {"languages": copy.deepcopy(studio["languages"])}

    chain = []
    visiting = set()

    def inherit(current):
        identifier(current)
        if current in visiting:
            raise ValueError(f"Profile inheritance cycle at {current}")
        visiting.add(current)
        profile = read(f"profiles/{current}.json")
        if profile.get("id") != current:
            raise ValueError(f"Profile ID does not match filename: {current}")
        parent = profile.get("extends")
        if parent is not None:
            inherit(parent)
        chain.append(profile)
        visiting.remove(current)

    if selected is not None:
        inherit(selected)
    layers = ["studio defaults"]
    for profile in chain:
        effective = merge(effective, preferences(profile.get("preferences", {}), f"profile {profile['id']}"))
        layers.append(f"profile:{profile['id']}:{profile.get('revision', 1)}")
        if profile.get("status") != "approved":
            drafts.append(profile["id"])
    if topic:
        effective = merge(effective, preferences(topic.get("preferences", {}), "topic preferences"))
        layers.append(f"topic:{topic_id}")
    if project:
        effective = merge(effective, preferences(project.get("overrides", {}), "project overrides"))
        layers.append(f"project:{project_id}")
    video = effective.get("video")
    unresolved = []
    if video is None:
        unresolved.append("video")
    elif not isinstance(video, dict):
        raise ValueError("video must be an object or null for deferred configuration")
    else:
        if video.get("aspect_ratio", "9:16") != "9:16":
            raise ValueError("This studio contract requires vertical 9:16 video")
        if video.get("renderer", "hyperframes") != "hyperframes" or video.get("framework", "hyperframes") != "hyperframes":
            raise ValueError("This studio contract requires Hyperframes")
        for key in ("width", "height"):
            value = video.get(key)
            if value is None:
                unresolved.append(f"video.{key}")
            elif isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"video.{key} must be a positive integer")
        width, height = video.get("width"), video.get("height")
        if width is not None and height is not None and width * 16 != height * 9:
            raise ValueError("Video dimensions must have a 9:16 aspect ratio")
        rate = video.get("fps")
        if rate is None:
            unresolved.append("video.fps")
        else:
            try:
                numeric_rate = float(Fraction(str(rate)))
            except (ValueError, ZeroDivisionError):
                raise ValueError("video.fps must be a valid frame rate") from None
            if isinstance(rate, bool) or not math.isfinite(numeric_rate) or not 1 <= numeric_rate <= 240:
                raise ValueError("video.fps must be between 1 and 240")
    return {
        "schema_version": 1,
        "context": {"profile_id": selected, "topic_id": topic_id, "source_id": source_id, "project_id": project_id},
        "layers": layers, "inputs": inputs, "draft_profiles": drafts,
        "unresolved_preferences": unresolved,
        "preferences": effective,
        "note": "Resolution is not approval. For approved projects use the reviewed snapshot, not newly resolved live settings.",
    }


def load_snapshot(workspace, project_id):
    """Read the selected immutable snapshot; approval hashes are checked by the agent."""
    workspace = Path(workspace).expanduser().resolve()
    project_dir = workspace / "projects" / identifier(project_id)
    if not project_dir.resolve().is_relative_to(workspace):
        raise ValueError("Project escapes workspace")
    state_path = project_dir / "project.json"
    if not state_path.resolve().is_relative_to(project_dir.resolve()):
        raise ValueError("Project state escapes project directory")
    state = json.loads(state_path.read_text())
    if not isinstance(state, dict) or state.get("id") != project_id:
        raise ValueError("Project ID does not match its directory")
    relative = state.get("preferences_path", "preferences.json")
    if not isinstance(relative, str) or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError("Invalid snapshot path")
    path = project_dir / relative
    if not path.resolve().is_relative_to(project_dir.resolve()):
        raise ValueError("Snapshot escapes project directory")
    value = json.loads(path.read_text())
    if not isinstance(value, dict) or not isinstance(value.get("preferences"), dict):
        raise ValueError("Expected a preference snapshot report")
    context = value.get("context")
    if not isinstance(context, dict) or context.get("project_id") != project_id:
        raise ValueError("Snapshot project context does not match")
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path)
    for key in ("profile", "topic", "source", "project"):
        parser.add_argument(f"--{key}")
    parser.add_argument("--frozen", action="store_true", help="Read the project snapshot instead of resolving live settings")
    args = parser.parse_args()
    try:
        if args.frozen:
            if not args.project or any((args.profile, args.topic, args.source)):
                raise ValueError("--frozen requires --project and accepts no live context overrides")
            result = load_snapshot(args.workspace, args.project)
        else:
            result = resolve(args.workspace, args.profile, args.topic, args.source, args.project)
    except (OSError, ValueError, RecursionError) as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        raise SystemExit(1)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

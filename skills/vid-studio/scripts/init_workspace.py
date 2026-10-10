#!/usr/bin/env python3
"""Copy missing workspace templates, without approving or installing anything."""

import argparse
import json
from pathlib import Path


def initialize(destination: Path) -> dict:
    templates = Path(__file__).resolve().parents[1] / "assets" / "workspace"
    destination = destination.expanduser().resolve()
    if destination.exists() and not destination.is_dir():
        raise ValueError("Workspace path must be a directory")
    destination.mkdir(parents=True, exist_ok=True)
    created, preserved = [], []
    for source in sorted(templates.rglob("*")):
        if not source.is_file():
            continue
        relative = source.relative_to(templates)
        target = destination / relative
        # Refuse paths escaping the selected workspace via existing symlinks.
        if not target.resolve().is_relative_to(destination):
            raise ValueError(f"Template target escapes workspace: {relative}")
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            with target.open("xb") as output:
                output.write(source.read_bytes())
            created.append(str(relative))
        except FileExistsError:
            preserved.append(str(relative))
    for relative in ("projects", "monitoring/inbox", "settings/history"):
        target = destination / relative
        if not target.resolve().is_relative_to(destination):
            raise ValueError(f"Directory escapes workspace: {relative}")
        target.mkdir(parents=True, exist_ok=True)
    return {"workspace": str(destination), "created": created, "preserved": preserved}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = initialize(args.workspace)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Initialization failed: {error}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

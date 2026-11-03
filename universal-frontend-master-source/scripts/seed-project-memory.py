#!/usr/bin/env python3
"""Seed project-local UFME memory files from bundled templates.

Existing files are never overwritten. This helper is shared by install.sh and CI
so that both paths exercise identical, safe seeding behavior.
"""

import argparse
import json
import sys
from pathlib import Path

MEMORY_FILES = [
    "TASKS.md",
    "ENVIRONMENT.md",
    "SKILL_VALIDATION.md",
    "AGENT_STATE.md",
    "DECISIONS.md",
    "ARCHITECTURE.md",
    "DESIGN_SYSTEM.md",
    "API_MAP.md",
    "AUTHENTICATION_MAP.md",
    "BACKEND_CAPABILITIES.md",
    "ERROR_HANDLING.md",
    "VISUAL_AUDIT.md",
    "AUDIT_REPORT.md",
]


def seed_project_memory(target: Path) -> dict:
    target = target.expanduser().resolve()
    if not target.is_dir():
        raise ValueError(f"target directory does not exist: {target}")

    script_dir = Path(__file__).resolve().parent
    template_dir = script_dir.parent / "templates"
    memory_dir = target / ".ufme"
    evidence_dir = memory_dir / "evidence"
    memory_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    created = []
    preserved = []
    fallback = []

    for name in MEMORY_FILES:
        destination = memory_dir / name
        template = template_dir / name

        if destination.exists():
            if not destination.is_file():
                raise ValueError(f"memory path exists but is not a file: {destination}")
            preserved.append(name)
            continue

        if template.is_file():
            content = template.read_bytes()
        else:
            content = f"# {Path(name).stem.replace('_', ' ').title()}\n".encode("utf-8")
            fallback.append(name)

        # Exclusive creation protects user data if another process creates it
        # between the existence check and the write.
        try:
            with destination.open("xb") as handle:
                handle.write(content)
        except FileExistsError:
            preserved.append(name)
            continue

        if not destination.is_file() or destination.stat().st_size == 0:
            raise RuntimeError(f"failed to seed a non-empty memory file: {destination}")
        created.append(name)

    return {
        "target": str(target),
        "created": created,
        "preserved": preserved,
        "fallback": fallback,
        "total": len(MEMORY_FILES),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="project directory to seed (default: current directory)",
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()

    try:
        result = seed_project_memory(Path(args.target))
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"[ufme-seed] ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(
            f"[ufme-seed] target={result['target']} "
            f"created={len(result['created'])} preserved={len(result['preserved'])} "
            f"fallback={len(result['fallback'])}"
        )
        for name in result["created"]:
            print(f"[ufme-seed] created: .ufme/{name}")
        for name in result["preserved"]:
            print(f"[ufme-seed] preserved: .ufme/{name}")
        for name in result["fallback"]:
            print(f"[ufme-seed] WARNING: template missing; created fallback for .ufme/{name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

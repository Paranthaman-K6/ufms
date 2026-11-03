#!/usr/bin/env python3
"""build-agents.py — generate installed UFME agent files from source.

Generates `.opencode/agents/*.md` from `universal-frontend-master-source/agents/*.md`
using a fixed rename map:

    orchestrator.md              -> ufme-orchestrator.md
    designer.md                  -> ufme-designer.md
    builder.md                   -> ufme-builder.md
    backend-analyst.md           -> ufme-backend-analyst.md
    auditor.md                   -> ufme-auditor.md
    universal-frontend-master.md -> universal-frontend-master.md

Validates every source agent:
  * frontmatter keys limited to [name, mode, description, permission]
  * mode in {primary, subagent}
  * permission keys limited to [read, edit, bash, task] with allow/deny/ask values
  * frontmatter `name` matches the installed (mapped) name

Installs each file verbatim into `.opencode/agents/` and deletes obsolete installed
agent files that are no longer present in the source set.

`--check` mode: exits non-zero when an install would change (drift) or when any
source or installed agent file exceeds `--max-chars` (default 4000).

Pure python3; read-only outside `.opencode/agents/`; never sudo/pacman/systemctl.
"""

import argparse
import sys
from pathlib import Path

AGENT_NAME_MAP = {
    "orchestrator": "ufme-orchestrator",
    "designer": "ufme-designer",
    "builder": "ufme-builder",
    "backend-analyst": "ufme-backend-analyst",
    "auditor": "ufme-auditor",
    "universal-frontend-master": "universal-frontend-master",
}

ALLOWED_FRONTMATTER_KEYS = ["name", "mode", "description", "permission"]
REQUIRED_FRONTMATTER_KEYS = ["name", "mode", "description"]
ALLOWED_PERMISSION_KEYS = ["read", "edit", "bash", "task"]
ALLOWED_PERMISSION_VALUES = ["allow", "deny", "ask"]
VALID_MODES = {"primary", "subagent"}

SOURCE_DIR = Path(__file__).resolve().parents[1] / "agents"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
INSTALL_DIR = PROJECT_ROOT / ".opencode" / "agents"


def parse_frontmatter(path):
    """Parse the YAML-ish frontmatter block: returns (fields, body, lines)."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc
    if not text.startswith("---\n"):
        return {}, text, []
    end = text.find("\n---", 4)
    if end < 0:
        return {}, text, []
    fm_lines = text[4:end].splitlines()
    fields = {}
    perm = {}
    in_perm = False
    for line in fm_lines:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  ") or line.startswith("\t"):
            if in_perm:
                m = line.lstrip("\t ").split(":", 1)
                if len(m) == 2:
                    perm[m[0].strip()] = m[1].strip()
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        in_perm = key == "permission" and not value
        if in_perm:
            fields[key] = perm
            continue
        fields[key] = value
    body = text[end + 4:]
    return fields, body, fm_lines


def validate_agent(path, mapped_name, max_chars):
    """Validate one source agent file; returns its content. Raises on invalid."""
    if not path.is_file():
        raise ValueError(f"missing source agent: {path}")
    fields, body, fm_lines = parse_frontmatter(path)
    errors = []
    unknown = [k for k in fields if k not in ALLOWED_FRONTMATTER_KEYS]
    if unknown:
        errors.append(f"frontmatter key(s) not in {ALLOWED_FRONTMATTER_KEYS}: {unknown}")
    missing = [k for k in REQUIRED_FRONTMATTER_KEYS if not fields.get(k)]
    if missing:
        errors.append(f"missing frontmatter field(s): {missing}")
    mode = fields.get("mode", "")
    if mode and mode not in VALID_MODES:
        errors.append(f"invalid mode '{mode}' (expected one of {sorted(VALID_MODES)})")
    name = fields.get("name", "")
    if name and name != mapped_name:
        errors.append(f"frontmatter name '{name}' != '{mapped_name}' for {path.name}")
    perm = fields.get("permission")
    if isinstance(perm, dict):
        for key, value in perm.items():
            if key not in ALLOWED_PERMISSION_KEYS:
                errors.append(f"invalid permission key '{key}'")
            elif value not in ALLOWED_PERMISSION_VALUES:
                errors.append(f"invalid permission value '{value}' for '{key}'")
    content = path.read_text(encoding="utf-8")
    if len(content) > max_chars:
        errors.append(
            f"file exceeds --max-chars {max_chars}: {path} is {len(content)} chars"
        )
    if errors:
        raise ValueError(f"{path}: " + "; ".join(errors))
    return content


def build():
    generated = 0
    for source_name, installed_name in AGENT_NAME_MAP.items():
        source_path = SOURCE_DIR / f"{source_name}.md"
        content = validate_agent(source_path, installed_name, MAX_CHARS)
        target = INSTALL_DIR / f"{installed_name}.md"
        if target.is_file() and target.read_text(encoding="utf-8") == content:
            print(f"unchanged: {target}")
        else:
            target.write_text(content, encoding="utf-8")
            print(f"installed: {target}")
            generated += 1
    return generated


def sweep_obsolete():
    """Delete installed agent files no longer mapped from source."""
    keep = {f"{installed}.md" for installed in AGENT_NAME_MAP.values()}
    removed = 0
    if not INSTALL_DIR.is_dir():
        return removed
    for path in sorted(INSTALL_DIR.glob("*.md")):
        if path.name not in keep:
            path.unlink()
            print(f"removed obsolete: {path}")
            removed += 1
    return removed


def check():
    drift = []
    for source_name, installed_name in AGENT_NAME_MAP.items():
        source_path = SOURCE_DIR / f"{source_name}.md"
        content = validate_agent(source_path, installed_name, MAX_CHARS)
        target = INSTALL_DIR / f"{installed_name}.md"
        if not target.is_file():
            drift.append(f"{target} missing")
        elif target.read_text(encoding="utf-8") != content:
            drift.append(f"{target} drifts from {source_path.name}")
    for target in sorted(INSTALL_DIR.glob("*.md")):
        content = target.read_text(encoding="utf-8")
        if len(content) > MAX_CHARS:
            drift.append(f"{target} exceeds --max-chars {MAX_CHARS}")
        if target.name not in {f"{n}.md" for n in AGENT_NAME_MAP.values()}:
            drift.append(f"obsolete installed file: {target}")
    if drift:
        for item in drift:
            print(f"DRIFT: {item}")
        return 1
    print("check: in sync")
    return 0


def main():
    global MAX_CHARS
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero on drift or oversize agent files",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=4000,
        help="maximum chars per agent file (default 4000)",
    )
    args = parser.parse_args()
    MAX_CHARS = args.max_chars

    if not SOURCE_DIR.is_dir():
        print(f"missing source dir: {SOURCE_DIR}", file=sys.stderr)
        return 2

    if args.check:
        if not INSTALL_DIR.is_dir():
            print(f"missing install dir: {INSTALL_DIR}", file=sys.stderr)
            return 1
        return check()

    INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    build()
    sweep_obsolete()
    print(f"installed agents: {sorted(p.name for p in INSTALL_DIR.glob('*.md'))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

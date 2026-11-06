#!/usr/bin/env python3
"""build-agents.py — validate top-level agents and mirror them to `.opencode/agents/`.

Source of truth: `agents/*.md` (flat, final installed names).
Installed mirror: `.opencode/agents/*.md`, generated, never hand-edited.

Validates every agent:
  * frontmatter keys limited to [name, mode, description, permission]
  * mode in {primary, subagent}
  * permission keys limited to [read, edit, bash, task] with allow/deny/ask values
  * frontmatter `name` equals the file stem
  * every `@agent-name` reference resolves to a known agent

`--check` exits non-zero on drift or when any agent file exceeds `--max-chars`.

Pure python3; writes only inside `.opencode/agents/`.
"""

import argparse
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = PROJECT_ROOT / "agents"
INSTALL_DIR = PROJECT_ROOT / ".opencode" / "agents"

ALLOWED_FRONTMATTER_KEYS = ["name", "mode", "description", "permission"]
REQUIRED_FRONTMATTER_KEYS = ["name", "mode", "description"]
ALLOWED_PERMISSION_KEYS = ["read", "edit", "bash", "task"]
ALLOWED_PERMISSION_VALUES = ["allow", "deny", "ask"]
VALID_MODES = {"primary", "subagent"}


def parse_frontmatter(path):
    """Parse the YAML-ish frontmatter block: returns (fields, body)."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end < 0:
        return {}, text
    fields = {}
    perm = {}
    in_perm = False
    for line in text[4:end].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith((" ", "\t")):
            if in_perm:
                key, _, value = line.lstrip("\t ").partition(":")
                if value:
                    perm[key.strip()] = value.strip()
            continue
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        in_perm = key == "permission" and not value
        fields[key] = perm if in_perm else value
    return fields, text[end + 4:]


def validate_agent(path, max_chars):
    """Validate one agent file; returns its content. Raises ValueError on invalid."""
    fields, _ = parse_frontmatter(path)
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
    if name and name != path.stem:
        errors.append(f"frontmatter name '{name}' != file stem '{path.stem}'")
    perm = fields.get("permission")
    if isinstance(perm, dict):
        for key, value in perm.items():
            if key not in ALLOWED_PERMISSION_KEYS:
                errors.append(f"invalid permission key '{key}'")
            elif value not in ALLOWED_PERMISSION_VALUES:
                errors.append(f"invalid permission value '{value}' for '{key}'")
    content = path.read_text(encoding="utf-8")
    if len(content) > max_chars:
        errors.append(f"file exceeds --max-chars {max_chars}: {path} is {len(content)} chars")
    if errors:
        raise ValueError(f"{path}: " + "; ".join(errors))
    return content


def load_agents(max_chars):
    """Validate every agent and return name -> content."""
    if not SOURCE_DIR.is_dir():
        raise ValueError(f"missing source dir: {SOURCE_DIR}")
    agents = {}
    for path in sorted(SOURCE_DIR.glob("*.md")):
        agents[path.stem] = validate_agent(path, max_chars)
    if not agents:
        raise ValueError(f"no agents found in {SOURCE_DIR}")
    return agents


def validate_references(agents):
    """Every `@agent-name` must resolve to a known agent."""
    ref = re.compile(r"@([a-z][a-z0-9-]*)\b")
    known = set(agents)
    for name, content in agents.items():
        for target in sorted(set(ref.findall(content))):
            if target not in known:
                raise ValueError(
                    f"{name} references unknown agent '@{target}' (known: {sorted(known)})"
                )


def build(agents):
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    for name, content in agents.items():
        target = INSTALL_DIR / f"{name}.md"
        if target.is_file() and target.read_text(encoding="utf-8") == content:
            print(f"unchanged: {target}")
        else:
            target.write_text(content, encoding="utf-8")
            print(f"installed: {target}")
    for path in sorted(INSTALL_DIR.glob("*.md")):
        if path.stem not in agents:
            path.unlink()
            print(f"removed obsolete: {path}")


def check(agents, max_chars):
    drift = []
    if not INSTALL_DIR.is_dir():
        print(f"missing install dir: {INSTALL_DIR}", file=sys.stderr)
        return 1
    for name, content in agents.items():
        target = INSTALL_DIR / f"{name}.md"
        if not target.is_file():
            drift.append(f"{target} missing")
        elif target.read_text(encoding="utf-8") != content:
            drift.append(f"{target} drifts from agents/{name}.md")
    for target in sorted(INSTALL_DIR.glob("*.md")):
        if target.stem not in agents:
            drift.append(f"obsolete installed file: {target}")
    if drift:
        for item in drift:
            print(f"DRIFT: {item}")
        return 1
    print(f"check: in sync ({len(agents)} agents)")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="exit non-zero on drift")
    parser.add_argument(
        "--max-chars", type=int, default=8000, help="max chars per agent file (default 8000)"
    )
    args = parser.parse_args()

    try:
        agents = load_agents(args.max_chars)
        validate_references(agents)
    except ValueError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 2

    if args.check:
        return check(agents, args.max_chars)
    build(agents)
    print(f"installed agents: {sorted(p.name for p in INSTALL_DIR.glob('*.md'))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

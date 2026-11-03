#!/usr/bin/env python3
"""ctx-pack.py — compact per-agent brief from .ufme/ artifacts (todo 4.7).

Builds a token-budgeted context pack (<= 1500 tokens estimated as chars/4)
for one of the five merged agents, so agents read one brief instead of
5–8 loose .ufme files.

Usage:
  python3 ctx-pack.py --agent <orchestrator|designer|builder|backend-analyst|auditor> \
      [--ufme-dir .ufme] [--max-tokens 1500] [--archive] [--out PATH]

Output: .ufme/evidence/ctx-<agent>.md unless --out is given.
With --archive: when DECISIONS.md exceeds its budget, the oldest entries not
needed by the pack are rotated into .ufme/DECISIONS.archive.md (created if
absent) before packing.

Pure python3, no dependencies. Missing files are skipped gracefully.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

AGENT_LABELS = {
    "orchestrator": "ufme-orchestrator",
    "designer": "ufme-designer",
    "builder": "ufme-builder",
    "backend-analyst": "ufme-backend-analyst",
    "auditor": "ufme-auditor",
}

SORTED_AGENT_ALLOWED_SETS = {
    "orchestrator": ["AGENT_STATE", "TASKS", "DECISIONS", "ENVIRONMENT"],
    "designer": ["AGENT_STATE", "PROJECT_SPEC", "PRD", "DECISIONS"],
    "builder": ["AGENT_STATE", "TASKS", "ARCHITECTURE", "DESIGN_SYSTEM", "API_MAP"],
    "backend-analyst": ["BACKEND_CAPABILITIES", "API_MAP", "AUTHENTICATION_MAP", "ERROR_HANDLING"],
    "auditor": ["AUDIT_REPORT", "VISUAL_AUDIT", "EVIDENCE_QUALITY_REPORT"],
}

# Logical artifact -> candidate files (first existing wins, in order).
ARTIFACT_FILES = {
    "AGENT_STATE": ["AGENT_STATE.md"],
    "TASKS": ["TASKS.md"],
    "DECISIONS": ["DECISIONS.md"],
    "ENVIRONMENT": ["ENVIRONMENT.md"],
    "PROJECT_SPEC": ["PROJECT_SPEC.md"],
    "PRD": ["PRD.md"],
    "ARCHITECTURE": ["ARCHITECTURE.md"],
    "DESIGN_SYSTEM": ["DESIGN_SYSTEM.md", "design-system/MASTER.md"],
    "API_MAP": ["API_MAP.md"],
    "BACKEND_CAPABILITIES": ["BACKEND_CAPABILITIES.md"],
    "AUTHENTICATION_MAP": ["AUTHENTICATION_MAP.md"],
    "ERROR_HANDLING": ["ERROR_HANDLING.md"],
    "AUDIT_REPORT": ["AUDIT_REPORT.md"],
    "VISUAL_AUDIT": ["VISUAL_AUDIT.md"],
    "EVIDENCE_QUALITY_REPORT": ["evidence/quality-report.json"],
}

# Substrings identifying the design subset of DECISIONS.md (used for designer).
DESIGN_SUBSET_KEYWORDS = (
    "font", "color", "palette", "icon", "image", "logo", "asset",
    "brand", "css", "library", "animation", "proptypes", "design", "style", "token",
)

HEADER_SLUG = re.compile(r"^#\s+")


def estimate_tokens(text):
    """Token estimate = chars/4 (documented heuristic)."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def resolve_artifact(ufme_dir, name):
    for rel in ARTIFACT_FILES[name]:
        candidate = ufme_dir / rel
        if candidate.is_file():
            return candidate
    return None


def summarize_quality_report(data):
    """Keep JSON summaries as counts, not full text."""
    parts = []
    if isinstance(data, dict):
        counts = data.get("counts")
        if isinstance(counts, dict):
            c = ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
            parts.append(f"counts: {c}")
        else:
            parts.append(f"top-level keys: {len(data)}")
        overall = data.get("overall")
        if overall:
            parts.append(f"overall: {overall}")
        checks = data.get("checks")
        if isinstance(checks, list):
            parts.append(f"checks recorded: {len(checks)}")
        project = data.get("project")
        if isinstance(project, dict):
            parts.append(f"project: {project.get('name', '?')} ({project.get('root', '?')})")
    else:
        parts.append(f"top-level values: {len(data) if isinstance(data, list) else 1}")
    return "; ".join(parts)


def render_section(name, path, raw):
    """Markdown for one artifact. JSON sources are reduced to counts."""
    if path.suffix == ".json" or name == "EVIDENCE_QUALITY_REPORT":
        try:
            data = json.loads(raw)
        except (ValueError, TypeError):
            data = None
        if isinstance(data, (dict, list)):
            body = summarize_quality_report(data)
            label = "JSON summary (counts only)"
        else:
            body = "[unreadable JSON]"
            label = "JSON summary (counts only)"
        return f"## {name} ({label}, {estimate_tokens(body)} tok)\n{body}\n"
    body = raw
    title = "## " + name
    first_line = body.splitlines()[0] if body.splitlines() else ""
    label = first_line.lstrip("# ").strip() or id_to_title(name)
    return f"{title} — {label} ({estimate_tokens(body)} tok)\n{body}\n"


def id_to_title(name):
    words = name.replace("_", " ").lower()
    return words


def truncate_to_budget(text, budget_tokens):
    """Trim content so estimate_tokens(body) <= budget; prefer line boundaries."""
    max_chars = budget_tokens * 4
    if len(text) <= max_chars:
        return text
    marker = "\n…[truncated]"
    cut = max(0, max_chars - len(marker))
    clamp = min(cut, len(text))
    # Prefer a clean line break near the budget edge (never before 80%).
    newline_pos = text.rfind("\n", 0, clamp + 1)
    min_newline = int(clamp * 0.8)
    if newline_pos >= min_newline:
        clamp = newline_pos
    return text[:clamp] + marker


def design_subset(raw):
    """Keep heading(s) plus only DECISIONS rows mentioning design keywords."""
    kept = []
    for line in raw.splitlines():
        if not line.startswith("|"):
            kept.append(line)
            continue
        low = line.lower()
        if HEADER_SLUG.match(line) or any(k in low for k in DESIGN_SUBSET_KEYWORDS):
            kept.append(line)
    return "\n".join(kept)


def decision_entries(raw):
    """Data rows of DECISIONS table(s) or list items, in file order."""
    entries = []
    for line in raw.splitlines():
        low = line.lower()
        if low.startswith("|") and not low.startswith("| decision") \
           and not re.match(r"^\|[\s:|-]*\|$", low):
            entries.append(line)
        elif low.startswith("- ") or low.startswith("* "):
            entries.append(line)
    return entries


def rotate_decisions(ufme_dir, budget_tokens):
    """With --archive: archive oldest entries until DECISIONS.md fits budget."""
    path = resolve_artifact(ufme_dir, "DECISIONS")
    if path is None:
        return None
    archive_path = ufme_dir / "DECISIONS.archive.md"
    raw = path.read_text(encoding="utf-8")
    if estimate_tokens(raw) <= budget_tokens:
        return None
    entries = decision_entries(raw)
    if not entries:
        return None
    lines = raw.splitlines()
    archived = []
    # Rotate oldest first until the remaining file fits the budget.
    while entries:
        remaining = "\n".join(line for line in lines if line not in archived)
        if estimate_tokens(remaining) <= budget_tokens:
            break
        archived.append(entries.pop(0))
    if not archived:
        return None
    raw = "\n".join(line for line in lines if line not in archived)
    body = "\n".join(archived)
    header_check = archive_path.exists()
    if not header_check:
        archive_path.write_text(
            "# Decisions Archive\n\nAuto-rotated by ctx-pack.py — oldest first.\n\n",
            encoding="utf-8",
        )
    with archive_path.open("a", encoding="utf-8") as fh:
        fh.write(body.rstrip() + "\n\n")
    path.write_text(raw, encoding="utf-8")
    return (archive_path, len(archived))


def build_brief(agent, ufme_dir, max_tokens):
    """Assemble rendered sections in priority order until budget is used."""
    header = (
        f"# Ctx pack: {AGENT_LABELS[agent]}\n"
        f"- Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n"
        f"- Source: {ufme_dir}\n"
        f"- Budget: {max_tokens} tok (est. chars/4)\n"
    )
    budget_left = max_tokens - estimate_tokens(header)
    parts = []
    for artifact in SORTED_AGENT_ALLOWED_SETS[agent]:
        path = resolve_artifact(ufme_dir, artifact)
        if path is None:
            continue
        raw = path.read_text(encoding="utf-8", errors="replace").strip()
        if not raw:
            continue
        if artifact == "DECISIONS" and agent == "designer":
            section_text = design_subset(raw)
        else:
            section_text = render_section(artifact, path, raw)
        if estimate_tokens(section_text) > budget_left and parts:
            parts.append(f"_(skipped {artifact}: budget exhausted)_")
            break
        if budget_left <= 0:
            parts.append(f"_(skipped {artifact}: budget exhausted)_")
            break
        section_text = truncate_to_budget(section_text, budget_left)
        section_text += "\n"
        budget_left -= estimate_tokens(section_text)
        parts.append(section_text)
    if not parts:
        parts.append("_(no .ufme artifacts found for this agent)_")
    footer = (
        f"---\n"
        f"Estimated total: {max_tokens - budget_left} tok "
        f"(budget {max_tokens}); missing files skipped silently.\n"
    )
    return header + "\n" + "\n".join(parts) + footer


def parse_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--agent", required=True,
                   choices=sorted(AGENT_LABELS.keys()))
    p.add_argument("--ufme-dir", default=".ufme")
    p.add_argument("--max-tokens", type=int, default=1500)
    p.add_argument("--archive", action="store_true")
    p.add_argument("--out", default=None, help="Write to this path instead of default")
    return p.parse_args()


def main():
    args = parse_args()
    if args.max_tokens <= 0:
        sys.stderr.write("[ctx-pack] ERROR: --max-tokens must be positive\n")
        return 2
    ufme_dir = Path(args.ufme_dir).resolve()
    if not ufme_dir.is_dir():
        sys.stderr.write(f"[ctx-pack] ERROR: .ufme dir not found: {ufme_dir}\n")
        return 1
    if args.archive:
        result = rotate_decisions(ufme_dir, args.max_tokens)
        if result:
            archive_path, count = result
            sys.stderr.write(
                f"[ctx-pack] Archived {count} old DECISIONS entries to {archive_path}\n")
    brief = build_brief(args.agent, ufme_dir, args.max_tokens)
    est = estimate_tokens(brief)
    out_path = Path(args.out) if args.out else ufme_dir / "evidence" / f"ctx-{args.agent}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(brief, encoding="utf-8")
    print(f"[ctx-pack] {AGENT_LABELS[args.agent]} brief → {out_path} "
          f"({est} tok est., {len(brief)} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

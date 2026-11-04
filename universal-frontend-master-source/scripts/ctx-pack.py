#!/usr/bin/env python3
"""ctx-pack.py — compact per-agent brief from .ufme/ artifacts (todo 4.7).

Builds a token-budgeted context pack (<= 1500 tokens estimated as chars/4)
for one of the five merged agents, so agents read one brief instead of
5–8 loose .ufme files.

Usage:
  python3 ctx-pack.py --agent <orchestrator|designer|builder|backend-analyst|auditor> \
      [--ufme-dir .ufme] [--max-tokens 1500] [--task "text"] \
      [--archive] [--out PATH]

Output: .ufme/evidence/ctx-<agent>.md unless --out is given.
With --archive: when DECISIONS.md exceeds its budget, the oldest entries not
needed by the pack are rotated into .ufme/DECISIONS.archive.md (created if
absent) before packing.

The brief always states its tokenizer, missing artifacts, truncated sections and
final estimated size; the final size never exceeds --max-tokens.

Pure python3; uses tiktoken cl100k_base when installed, chars/4 otherwise.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:  # Optional: exact OpenAI-compatible token counts when installed.
    import tiktoken

    _ENCODER = tiktoken.get_encoding("cl100k_base")
    TOKENIZER = "cl100k_base"
except Exception:  # Deterministic fallback, reported in every brief.
    _ENCODER = None
    TOKENIZER = "chars/4"

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
    "auditor": ["AUDIT_REPORT", "QUALITY_REPORT", "A11Y_RESULTS", "PERF_RESULTS",
                "BROWSER_RESULTS", "VISUAL_DIFF", "SLOP_RESULTS"],
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
    "QUALITY_REPORT": ["evidence/quality-report.json"],
    "EVIDENCE_QUALITY_REPORT": ["evidence/quality-report.json"],
    "A11Y_RESULTS": ["evidence/a11y-results.json"],
    "PERF_RESULTS": ["evidence/perf-results.json"],
    "BROWSER_RESULTS": ["evidence/browser-results.json"],
    "VISUAL_DIFF": ["evidence/visual-diff.json"],
    "SLOP_RESULTS": ["evidence/slop-results.json"],
}

# Substrings identifying the design subset of DECISIONS.md (used for designer).
DESIGN_SUBSET_KEYWORDS = (
    "font", "color", "palette", "icon", "image", "logo", "asset",
    "brand", "css", "library", "animation", "proptypes", "design", "style", "token",
)

HEADER_SLUG = re.compile(r"^#\s+")


def estimate_tokens(text):
    """Token count via cl100k_base when available, else the documented chars/4 fallback."""
    if not text:
        return 0
    if _ENCODER is not None:
        return len(_ENCODER.encode(text))
    return max(1, len(text) // 4)


def resolve_artifact(ufme_dir, name):
    for rel in ARTIFACT_FILES[name]:
        candidate = ufme_dir / rel
        if candidate.is_file():
            return candidate
    return None


def summarize_json(data):
    """Reduce evidence JSON to compact, decision-relevant fields."""
    if not isinstance(data, dict):
        size = len(data) if isinstance(data, list) else 1
        return f"top-level values: {size}"
    parts = []
    if "status" in data:
        parts.append(f"status={data['status']}")
    if "overall" in data:
        parts.append(f"overall={data['overall']}")
    counts = data.get("counts")
    if isinstance(counts, dict):
        parts.append("counts: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    checks = data.get("checks")
    if isinstance(checks, list):
        parts.append(f"checks={len(checks)}")
    project = data.get("project")
    if isinstance(project, dict):
        parts.append(f"project={project.get('name', '?')}")
    if "totalViolations" in data:
        parts.append(f"axeViolations={data['totalViolations']}")
        rules = data.get("violationsByRule")
        if isinstance(rules, list):
            ids = ",".join(str(r.get("id")) for r in rules[:8])
            parts.append(f"rules={ids or 'none'}")
    scores = data.get("scores")
    if isinstance(scores, dict):
        parts.append("scores: " + ", ".join(f"{k}={v}" for k, v in sorted(scores.items())))
    if "maxDiffRatio" in data:
        parts.append(
            f"maxDiffRatio={data['maxDiffRatio']} threshold={data.get('threshold')}"
        )
    if "count" in data and "findings" in data:
        parts.append(f"slopFindings={data['count']}")
    if "errors" in data and isinstance(data["errors"], list):
        parts.append(f"browserErrors={len(data['errors'])}")
    if not parts:
        parts.append(f"keys: {', '.join(sorted(data.keys())[:10])}")
    return "; ".join(parts)


def render_section(name, path, raw):
    """Markdown for one artifact. JSON sources are reduced to task-relevant fields."""
    if path.suffix == ".json":
        try:
            data = json.loads(raw)
        except (ValueError, TypeError):
            data = None
        if isinstance(data, (dict, list)):
            body = summarize_json(data)
            label = "JSON summary"
        else:
            body = "[unreadable JSON]"
            label = "JSON summary"
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
    """Trim content so estimate_tokens(text) <= budget; prefer line boundaries."""
    if budget_tokens <= 0:
        return ""
    if estimate_tokens(text) <= budget_tokens:
        return text
    marker = "\n…[truncated]"
    if _ENCODER is not None:
        lo, hi = 0, len(text)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if estimate_tokens(text[:mid] + marker) <= budget_tokens:
                lo = mid
            else:
                hi = mid - 1
        return text[:lo] + marker
    max_chars = budget_tokens * 4
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


def build_brief(agent, ufme_dir, max_tokens, task=None):
    """Assemble sections in priority order within a hard token budget."""
    header_lines = [
        f"# Ctx pack: {AGENT_LABELS[agent]}",
        f"- Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"- Source: {ufme_dir}",
        f"- Tokenizer: {TOKENIZER}",
        f"- Budget: {max_tokens} tok",
    ]
    if task:
        header_lines.append(f"- Task: {task.strip()}")
    header = "\n".join(header_lines) + "\n"

    present = []
    missing = []
    for artifact in SORTED_AGENT_ALLOWED_SETS[agent]:
        path = resolve_artifact(ufme_dir, artifact)
        raw = path.read_text(encoding="utf-8", errors="replace").strip() if path else ""
        if raw:
            present.append((artifact, path, raw))
        else:
            missing.append(artifact)

    parts = []
    skipped = []
    truncated = []
    budget_left = max_tokens - estimate_tokens(header)
    for index, (artifact, path, raw) in enumerate(present):
        if budget_left <= 0:
            skipped.extend(name for name, _, _ in present[index:])
            break
        if artifact == "DECISIONS" and agent == "designer":
            section_text = design_subset(raw)
        else:
            section_text = render_section(artifact, path, raw)
        # Fair share of the remaining budget across the remaining artifacts.
        share = max(1, budget_left // (len(present) - index))
        clipped = truncate_to_budget(section_text, share)
        if clipped != section_text:
            truncated.append(artifact)
        cost = estimate_tokens(clipped) + 1
        if cost > budget_left:
            skipped.append(artifact)
            continue
        parts.append((artifact, clipped + "\n"))
        budget_left -= cost

    def render(sections):
        body = (
            "\n".join(text for _, text in sections)
            if sections
            else "_(no .ufme artifacts found for this agent)_\n"
        )
        total = estimate_tokens(header + body)
        footer = (
            "---\n"
            f"- Tokenizer: {TOKENIZER}; estimated total: {total} tok (budget {max_tokens})\n"
            f"- Missing artifacts: {', '.join(missing) or 'none'}\n"
            f"- Truncated sections: {', '.join(truncated) or 'none'}\n"
            f"- Skipped for budget: {', '.join(skipped) or 'none'}\n"
        )
        return header + "\n" + body + footer

    brief = render(parts)
    while parts and estimate_tokens(brief) > max_tokens:
        dropped, _ = parts.pop()
        if dropped not in skipped:
            skipped.append(dropped)
        brief = render(parts)
    if estimate_tokens(brief) > max_tokens:
        brief = truncate_to_budget(brief, max_tokens)
    if estimate_tokens(brief) > max_tokens:
        limit = len(brief)
        while limit > 0 and estimate_tokens(brief[:limit]) > max_tokens:
            limit -= 1
        brief = brief[:limit]
    return brief


def parse_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--agent", required=True,
                   choices=sorted(AGENT_LABELS.keys()))
    p.add_argument("--ufme-dir", default=".ufme")
    p.add_argument("--max-tokens", type=int, default=1500)
    p.add_argument("--task", default="",
                   help="Task and acceptance criteria to record in the brief")
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
    brief = build_brief(args.agent, ufme_dir, args.max_tokens, args.task)
    est = estimate_tokens(brief)
    out_path = Path(args.out) if args.out else ufme_dir / "evidence" / f"ctx-{args.agent}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(brief, encoding="utf-8")
    print(f"[ctx-pack] {AGENT_LABELS[args.agent]} brief → {out_path} "
          f"({est} tok est., {len(brief)} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

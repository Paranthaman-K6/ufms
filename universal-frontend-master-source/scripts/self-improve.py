#!/usr/bin/env python3
"""
self-improve.py — audit the UFME skill itself.

Performs deep architectural validation of the reusable UFME system:

  * Core docs exist and are non-empty.
  * Source and installed agent definitions are in sync (name, mode, description).
  * SKILL.md frontmatter is valid and matches its source counterpart.
  * Every script referenced in docs/workflows/core resolves to a real file.
  * Every delegation reference (@agent-name) resolves to a real agent file.
  * Agent frontmatter has required fields (name, mode, description) and valid mode.
  * Prohibited content sweep: no hardcoded model IDs, no local absolute paths.
  * Execution profiles are valid JSON with expected keys.
  * Browser abstraction files exist and pass syntax checks.
  * OpenCode install (opencode.json, SKILL.md) is valid.
  * Shell scripts are executable; Python/Node scripts are syntax-valid and invoked via their interpreters.

Writes .ufme/SELF_IMPROVEMENT.md (human) and .ufme/evidence/self-improve-summary.json
(machine-readable). Exits non-zero on any FAIL.

Safety: read-only analysis; never sudo/pacman/systemctl.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "universal-frontend-master-source"
UFME = ROOT / ".ufme"
EVIDENCE = UFME / "evidence"
REPORT_MD = UFME / "SELF_IMPROVEMENT.md"
REPORT_JSON = EVIDENCE / "self-improve-summary.json"

AGENTS = [
    "universal-frontend-master", "orchestrator", "designer", "builder",
    "backend-analyst", "auditor",
]
# Source agent name -> installed file name (without extension).
INSTALLED_AGENT_NAMES = {
    "orchestrator": "ufme-orchestrator",
    "designer": "ufme-designer",
    "builder": "ufme-builder",
    "backend-analyst": "ufme-backend-analyst",
    "auditor": "ufme-auditor",
    "universal-frontend-master": "universal-frontend-master",
}
# Names merged into other agents; references to them stay valid and resolve
# to the merged agent's source/installed files.
MERGED_AGENT_ALIASES = {
    "researcher": "designer",
    "product-analyst": "designer",
    "frontend-architect": "builder",
    "implementer": "builder",
    "integrator": "builder",
    "visual-auditor": "auditor",
    "accessibility-auditor": "auditor",
    "performance-auditor": "auditor",
    "security-auditor": "auditor",
}
CORE_DOCS = [
    "MASTER_SKILL.md", "MULTI_AGENT_ORCHESTRATION.md", "AGENT_RULES.md",
    "PROJECT_MEMORY.md", "QUALITY_STANDARDS.md", "SAFETY.md",
    "ARCH_LINUX.md", "SYSTEM_ARCHITECTURE.md",
]
REQUIRED_FRONTMATTER_FIELDS = ["name", "mode", "description"]
VALID_MODES = {"primary", "subagent"}
PROHIBITED_MODELS = ["nemotron-3.5-super-vl-free"]
# Paths that indicate developer-local machine info that must not be committed.
LOCAL_PATH_HINTS = ["/home/paranthaman", "/tmp/opencode"]

PASSES = FAILS = SKIPPED = 0
LINES = []
CHECKS = []


def log(kind, label, detail=""):
    suffix = f": {detail}" if detail else ""
    print(f"{kind}: {label}{suffix}", flush=True)
    LINES.append(f"- {kind}: {label}{suffix}")


def note(kind, label, detail="", hint=""):
    global PASSES, FAILS, SKIPPED
    if kind == "PASS":
        PASSES += 1
    elif kind == "FAIL":
        FAILS += 1
    else:
        SKIPPED += 1
    CHECKS.append({
        "status": kind,
        "label": label,
        "detail": detail,
        "hint": hint,
    })
    suffix = f": {detail}" if detail else ""
    hint_suffix = f"  -> fix: {hint}" if hint else ""
    log(kind, label, suffix + hint_suffix)


def heading(text):
    print(f"## {text}", flush=True)
    LINES.extend(["", f"## {text}"])


def frontmatter(path):
    """Parse YAML-style frontmatter between the first two '---' lines."""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return {}, ""
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end < 0:
        return {}, text
    fields = {}
    for line in text[4:end].splitlines():
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m:
            fields[m.group(1)] = m.group(2).strip()
    return fields, text


def check_file(path, label, kind="exists"):
    if not path.is_file():
        note("FAIL", label, "missing", f"create {path}")
        return False
    if path.stat().st_size == 0:
        note("FAIL", label, "empty", f"populate {path}")
        return False
    if kind == "exists":
        note("PASS", label)
    elif kind == "exec":
        if os.access(path, os.X_OK):
            note("PASS", label, "executable")
        else:
            note("FAIL", label, "not executable", f"chmod +x {path}")
    elif kind == "syntax":
        suffix = path.suffix.lower()
        if suffix == ".py":
            ok = subprocess.run(
                [sys.executable, "-m", "py_compile", str(path)],
                capture_output=True,
            ).returncode == 0
            cmd_desc = "python3 -m py_compile"
        elif suffix == ".js":
            ok = subprocess.run(
                ["node", "--check", str(path)], capture_output=True
            ).returncode == 0
            cmd_desc = "node --check"
        else:
            ok = subprocess.run(
                ["bash", "-n", str(path)], capture_output=True
            ).returncode == 0
            cmd_desc = "bash -n"
        note("PASS" if ok else "FAIL", label,
             "syntax valid" if ok else "syntax invalid",
             f"run {cmd_desc} {path}" if not ok else "")
    return True


def validate_frontmatter(path, label, source_path=None):
    """Validate frontmatter fields and cross-check against source if given."""
    fields, _ = frontmatter(path)
    if not fields:
        note("FAIL", label, "no frontmatter", f"add YAML frontmatter to {path}")
        return fields
    missing = [f for f in REQUIRED_FRONTMATTER_FIELDS if not fields.get(f)]
    if missing:
        note("FAIL", label, f"missing fields: {', '.join(missing)}",
             f"add {', '.join(missing)} to frontmatter in {path}")
    mode = fields.get("mode", "")
    if mode and mode not in VALID_MODES:
        note("FAIL", label, f"invalid mode '{mode}'",
             f"set mode to one of {sorted(VALID_MODES)} in {path}")
    if not missing and mode in VALID_MODES:
        detail = f"name={fields.get('name')} mode={mode}"
        if source_path:
            s_fields, _ = frontmatter(source_path)
            drift = []
            for f in REQUIRED_FRONTMATTER_FIELDS:
                if fields.get(f) != s_fields.get(f):
                    drift.append(f"{f}: source='{s_fields.get(f)}' installed='{fields.get(f)}'")
            if drift:
                note("FAIL", label, "drift from source: " + "; ".join(drift),
                     f"re-deploy {path} from {source_path}")
                return fields
        note("PASS", label, detail)
    return fields


def scan_prohibited(path):
    """Scan a text file for prohibited models and local absolute paths."""
    issues = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return issues
    for model in PROHIBITED_MODELS:
        if model in text:
            issues.append(f"hardcoded model '{model}'")
    for hint in LOCAL_PATH_HINTS:
        if hint in text:
            issues.append(f"local path '{hint}'")
    return issues


def main():
    UFME.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    heading("Skill file audit (content validation)")
    for name in CORE_DOCS:
        check_file(SOURCE / "core" / name, name)

    # ------------------------------------------------------------------
    heading("Agent audit (frontmatter + mode + source/install sync)")
    installed_agent_dir = ROOT / ".opencode/agents"
    source_agent_dir = SOURCE / "agents"

    def installed_agent_path(name):
        """Resolve installed agent path via the fixed name map."""
        installed_name = INSTALLED_AGENT_NAMES.get(name, f"ufme-{name}")
        return installed_agent_dir / f"{installed_name}.md", installed_name

    for name in AGENTS:
        source_path = source_agent_dir / f"{name}.md"
        installed_path, label = installed_agent_path(name)

        # Source agent must exist and be valid.
        if not check_file(source_path, f"{label} (source)"):
            continue
        fields = validate_frontmatter(source_path, f"{label} (source frontmatter)")

        # Installed agent must exist, be valid, and match source.
        if not installed_path.exists():
            note("FAIL", f"{label} (installed)", "missing",
                 f"copy {source_path} to {installed_path}")
            continue
        if not check_file(installed_path, f"{label} (installed)", "exists"):
            continue
        ifields = validate_frontmatter(installed_path, f"{label} (installed frontmatter)",
                                       source_path=source_path)
        # Cross-check description/name/mode equality explicitly.
        for f in REQUIRED_FRONTMATTER_FIELDS:
            if fields.get(f) != ifields.get(f):
                note("FAIL", f"{label} (sync)", f"{f} mismatch",
                     f"re-deploy {label} from source")

    # ------------------------------------------------------------------
    heading("SKILL.md audit (source vs installed)")
    source_skill = SOURCE / "core" / "MASTER_SKILL.md"
    installed_skill = ROOT / ".opencode/skills/universal-frontend-master/SKILL.md"
    if not check_file(source_skill, "MASTER_SKILL.md (source)"):
        pass
    if not check_file(installed_skill, "SKILL.md (installed)", "exists"):
        pass
    if source_skill.exists() and installed_skill.exists():
        s_fields, _ = frontmatter(source_skill)
        i_fields, _ = frontmatter(installed_skill)
        for f in REQUIRED_FRONTMATTER_FIELDS:
            if s_fields.get(f) != i_fields.get(f):
                note("FAIL", "SKILL.md sync", f"{f} mismatch",
                     f"re-deploy SKILL.md from MASTER_SKILL.md")
        if not any(s_fields.get(f) != i_fields.get(f) for f in REQUIRED_FRONTMATTER_FIELDS):
            note("PASS", "SKILL.md sync", "fields match source")

    # ------------------------------------------------------------------
    heading("Workflow audit (14 expected)")
    for i in range(1, 15):
        matches = sorted((SOURCE / "workflows").glob(f"{i:02d}-*.md"))
        match = matches[0] if matches else None
        if match and match.stat().st_size > 0:
            note("PASS", f"workflow {i:02d}", match.name)
        else:
            note("FAIL", f"workflow {i:02d}", "missing or empty",
                 f"create universal-frontend-master-source/workflows/{i:02d}-*.md")

    # ------------------------------------------------------------------
    heading("Script reference integrity (docs/workflows/core must reference real scripts)")
    script_dir = SOURCE / "scripts"
    existing_scripts = {p.name for p in script_dir.glob("*") if p.is_file()}
    ref_pattern = re.compile(r"scripts/([A-Za-z0-9_.\-]+)")
    ref_sources = []
    for doc in list((SOURCE / "core").glob("*.md")) + \
                list((SOURCE / "workflows").glob("*.md")) + \
                list((SOURCE / "docs").glob("*.md")) + \
                [ROOT / "README.md", ROOT / ".opencode/skills/universal-frontend-master/SKILL.md"]:
        if not doc.exists():
            continue
        try:
            text = doc.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in ref_pattern.finditer(text):
            ref_sources.append((doc, m.group(1)))

    seen_refs = set()
    for doc, script_name in ref_sources:
        key = (doc, script_name)
        if key in seen_refs:
            continue
        seen_refs.add(key)
        if script_name not in existing_scripts:
            note("FAIL", "script reference", f"{doc}: scripts/{script_name} does not exist",
                 f"fix reference in {doc} or create the script")
        else:
            note("PASS", "script reference", f"{doc}: scripts/{script_name} exists")

    # ------------------------------------------------------------------
    heading("Script audit (exists + executable + syntax)")
    for path in sorted(script_dir.glob("*")):
        if path.name == "__pycache__" or path.suffix not in {".sh", ".py", ".js"}:
            continue
        if not path.is_file():
            continue
        # Shell scripts are invoked directly and must be executable. Python and
        # JavaScript helpers are invoked through python3/node, so their executable
        # bit is not required; their syntax is still validated below.
        if path.suffix == ".sh":
            check_file(path, path.name, "exec")
        else:
            note("PASS", path.name, "invoked through python3/node; executable bit not required")
        check_file(path, path.name, "syntax")

    # ------------------------------------------------------------------
    heading("Phantom agent detection (delegation references must resolve to real agents)")
    agent_pattern = re.compile(r"@ufme-([A-Za-z0-9\-]+)")
    delegation_sources = []
    for doc in list((SOURCE / "core").glob("*.md")) + \
                list((SOURCE / "workflows").glob("*.md")) + \
                [ROOT / "README.md", ROOT / ".opencode/skills/universal-frontend-master/SKILL.md"]:
        if not doc.exists():
            continue
        try:
            text = doc.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in agent_pattern.finditer(text):
            delegation_sources.append((doc, m.group(1)))

    seen_delegations = set()
    for doc, agent_name in delegation_sources:
        key = (doc, agent_name)
        if key in seen_delegations:
            continue
        seen_delegations.add(key)
        # Merged names resolve to the agent that absorbed their role.
        resolved_name = MERGED_AGENT_ALIASES.get(agent_name, agent_name)
        agent_file = source_agent_dir / f"{resolved_name}.md"
        source_alias_file = source_agent_dir / f"{agent_name}.md"
        installed_file, label = installed_agent_path(resolved_name)
        if not agent_file.exists() and not source_alias_file.exists() and not installed_file.exists():
            note("FAIL", "phantom agent", f"{doc}: @{agent_name} has no agent file",
                 f"remove @{agent_name} reference or create {agent_file}")
        else:
            note("PASS", "phantom agent", f"{doc}: @ufme-{agent_name} resolves ({label})")

    # ------------------------------------------------------------------
    heading("Prohibited-content sweep (no hardcoded models or local paths)")
    scan_targets = []
    for root, dirs, files in os.walk(SOURCE):
        dirs[:] = [d for d in dirs if d not in {"node_modules", ".git", "__pycache__"}]
        for fn in files:
            if fn.endswith((".md", ".py", ".sh", ".js", ".json")):
                scan_targets.append(Path(root) / fn)
    for extra in [ROOT / "opencode.json", ROOT / "README.md", ROOT / "install.sh"]:
        if extra.exists():
            scan_targets.append(extra)
    for path in sorted(scan_targets):
        # The auditor itself legitimately holds the scan patterns; skip self-scan.
        if path.name == "self-improve.py":
            continue
        issues = scan_prohibited(path)
        if issues:
            note("FAIL", "prohibited content", f"{path}: " + "; ".join(issues),
                 f"remove developer-local info from {path}")
        else:
            note("PASS", "prohibited content", str(path))

    # ------------------------------------------------------------------
    heading("Browser abstraction audit")
    for rel in [
        "tests/browser/browser.js", "tests/browser/viewport.js",
        "tests/browser/screenshot.js", "tests/browser/run.js",
        "tests/browser/engines/chromium.js", "tests/browser/engines/firefox.js",
        "tests/browser/engines/schema.js", "tests/browser/validate.js",
        "tests/browser/security.js", "tests/regression/run.js",
    ]:
        check_file(ROOT / rel, rel, "syntax")

    # ------------------------------------------------------------------
    heading("OpenCode install audit")
    skill = ROOT / ".opencode/skills/universal-frontend-master/SKILL.md"
    if not skill.exists():
        note("FAIL", "SKILL.md", "missing", "create .opencode/skills/universal-frontend-master/SKILL.md")
    else:
        fields, _ = frontmatter(skill)
        if not fields:
            note("FAIL", "SKILL.md", "no frontmatter", "add YAML frontmatter")
        elif not fields.get("name") or not fields.get("description"):
            note("FAIL", "SKILL.md", "missing name/description",
                 "add name and description to frontmatter")
        else:
            note("PASS", "SKILL.md", f"name={fields['name']}")

    opencode = ROOT / "opencode.json"
    if opencode.exists():
        try:
            cfg = json.loads(opencode.read_text(encoding="utf-8"))
            perms = cfg.get("permission", {})
            bash_perms = perms.get("bash", {}) if isinstance(perms, dict) else {}
            required_denies = ["sudo", "pacman", "systemctl", "npm publish*"]
            missing_denies = [d for d in required_denies if d not in bash_perms]
            if missing_denies:
                note("FAIL", "opencode.json", f"missing deny rules: {', '.join(missing_denies)}",
                     f"add deny rules for {', '.join(missing_denies)} to opencode.json")
            else:
                note("PASS", "opencode.json", "valid JSON + security deny rules")
        except (OSError, ValueError):
            note("FAIL", "opencode.json", "invalid JSON", "fix opencode.json syntax")
    else:
        note("FAIL", "opencode.json", "missing", "create opencode.json")

    for name in AGENTS:
        path, label = installed_agent_path(name)
        if not path.exists():
            note("FAIL", f"{label} (installed agent)", "missing",
                 f"copy {source_agent_dir / (name + '.md')} to {path}")
        elif not frontmatter(path)[0]:
            note("FAIL", f"{label} (installed agent)", "no frontmatter",
                 f"add frontmatter to {path}")
        else:
            note("PASS", f"{label} (installed agent)", "frontmatter present")

    # ------------------------------------------------------------------
    heading("Execution profile audit")
    profile_dir = SOURCE / "profiles"
    expected_profiles = ["lite", "standard", "advanced", "autonomous"]
    for pname in expected_profiles:
        pfile = profile_dir / f"{pname}.json"
        if not pfile.exists():
            note("FAIL", f"profile {pname}", "missing",
                 f"create universal-frontend-master-source/profiles/{pname}.json")
            continue
        try:
            prof = json.loads(pfile.read_text(encoding="utf-8"))
            if not isinstance(prof, dict):
                raise ValueError("not an object")
            note("PASS", f"profile {pname}", "valid JSON")
        except (OSError, ValueError):
            note("FAIL", f"profile {pname}", "invalid JSON",
                 f"fix {pfile}")

    # ------------------------------------------------------------------
    heading("Runtime memory audit")
    for name in ["TASKS.md", "ENVIRONMENT.md", "SKILL_VALIDATION.md"]:
        path = UFME / name
        if path.is_file() and path.stat().st_size > 0:
            note("PASS", name)
        else:
            note("FAIL", name, "missing or empty",
                 f"seed {path} via install.sh")

    # ------------------------------------------------------------------
    overall = "FAILED" if FAILS else "PASSED"
    summary = {
        "generated": datetime.now().astimezone().isoformat(timespec="seconds"),
        "root": str(ROOT),
        "counts": {"pass": PASSES, "fail": FAILS, "skipped": SKIPPED},
        "result": overall,
        "checks": CHECKS,
    }

    body = [
        "# UFME Self-Improvement Report",
        f"Generated: {summary['generated']}",
        "",
        *LINES,
        "",
        "## Summary",
        f"PASS: {PASSES}",
        f"FAIL: {FAILS}",
        f"SKIPPED: {SKIPPED}",
        f"Result: {overall}",
        "",
        "## Remediation",
        "Each FAIL above includes a hint describing the file to edit and the fix to apply.",
        "Re-run `python3 universal-frontend-master-source/scripts/self-improve.py` after changes.",
    ]

    # Write markdown report atomically.
    fd, tmp = tempfile.mkstemp(dir=str(UFME), prefix=".self-improvement.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("\n".join(body) + "\n")
        os.replace(tmp, REPORT_MD)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

    # Write machine-readable JSON report atomically.
    fd, tmp = tempfile.mkstemp(dir=str(EVIDENCE), prefix=".self-improve-summary.", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
            f.write("\n")
        os.replace(tmp, REPORT_JSON)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

    print("\n".join(body))
    print(f"\nMachine-readable report: {REPORT_JSON}")
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())

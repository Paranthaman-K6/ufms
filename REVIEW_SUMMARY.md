# Review Summary: UFME multi-agent frontend skill

## Overall Assessment
The implementation successfully delivers all 10 priorities as described in the handoff. Core functionality works: npm test passes (16/16), all 14 shell scripts pass `bash -n` syntax validation and are executable, self-improve.py reports 69 PASS / 0 FAIL, and Firefox Selenium headless launch is confirmed working. The skill is structurally complete with agents, workflows, templates, and runtime memory files all present.

However, there are **significant adequacy gaps** between the claimed state and the actual implementation state, particularly around agent synchronization and Chromium compatibility.

---

## Key Findings

### 🚨 Blocker: Source-to-install agent synchronization is broken

**Affected paths:** `universal-frontend-master-source/agents/*.md` vs `.opencode/agents/ufme-*.md`

**The problem:** The upgrade report claims "Source-to-install synchronization: `universal-frontend-master-source/agents/researcher.md` kept consistent with `.opencode/agents/ufme-researcher.md`" and "All agent specs + skill frontmatter validated by self-improve." Neither claim is accurate.

**Evidence:** All 12 agent files differ between source and installed locations. The OpenCode system has wrapped installed agents with `model: nemotron-3.5-super-vl-free` and `role_definition` boilerplate, but this has **stripped out** the original agent structure:

| Field | Source agent (correct) | Installed agent (corrupted) |
|-------|----------------------|----------------------------|
| `mode` | `primary` / `subagent` | Replaced by `model` field |
| `permissions` | Full read/write/bash/deny list | **MISSING** |
| `inputs` | Project brief, reference materials, etc. | **MISSING** |
| `outputs` | Research notes, library entries, etc. | **MISSING** |
| `role_definition` | Human-readable role text | Added by OpenCode, but different content |

**Example — orchestrator:**
- Source: has `mode: primary`, `permissions`, `inputs`, `outputs`, `role_definition` with the full role description
- Installed: has `model: nemotron-3.5-super-vl-free`, `role_definition` with truncated content, missing `permissions`/`inputs`/`outputs`

**Impact:** The installed agents do not accurately represent the source-of-truth definitions. Any OpenCode operation that reads these agents will get a watered-down version missing critical role definition details (permissions, inputs, outputs). The self-improve.py only checks for frontmatter presence + `mode` field, giving a false 69 PASS / 0 FAIL result despite the structural corruption.

**Root cause:** OpenCode auto-wraps agent definitions when installing them into `.opencode/agents/` and `.opencode/skills/`, adding `model` and `role_definition` fields but not preserving the original `mode`/`permissions`/`inputs`/`outputs` structure.

---

### 🚨 Blocker: Chromium Selenium launch fails

**Affected paths:** `tests/browser/browser.js` (chrome options), `check-native-browser.sh`

**The problem:** Chromium Selenium launch fails with `TypeError: intermediate value.setBinary is not a function` in the selenium-webdriver v4.52.0 build.

**Evidence:**
- `check-native-browser.sh` output: `SELENIUM_FAIL:(intermediate value).setBinary is not a function` for Chromium
- Firefox launch: `SELENIUM_OK` — works perfectly
- The code already has the `--no-sandbox` removal safety measure, but the Options API mismatch remains

**Context:** The handoff acknowledges this: "Chromium: detected; launch has Options API mismatch in this build (Firefox is the working engine)." But this is a real functional gap — if a user's project requires Chromium (e.g., for Chrome-specific features, CI environments, or team preferences), the skill cannot launch browsers at all.

**Mitigation:** Firefox is the confirmed working engine. The code has fallback logic (chromium → firefox), but Chromium is currently non-functional with this selenium-webdriver build.

---

### ⚠️ Non-blocker: Self-improve.sh validation is shallow

**Affected path:** `universal-frontend-master-source/scripts/self-improve.py`

**The problem:** The script only validates 2 of ~10 frontmatter fields per agent:
1. File exists
2. Has frontmatter (first line `---`)
3. Has `mode` field

It does NOT validate: `permissions`, `inputs`, `outputs`, full `role_definition` content, or agent structure consistency with source counterparts.

**Result:** 69 PASS / 0 FAIL is misleading. The real issue (agent structural corruption from OpenCode wrapping) is not caught.

**Impact:** False confidence that "all agent specs validated." The validation should be expanded to check the critical fields, or the upgrade report should not claim "Skill frontmatter validated by self-improve" when the validation is known to be incomplete.

---

### ⚠️ Non-blocker: quality-check.py browser tests require external dev server

**Affected path:** `universal-frontend-master-source/scripts/browser-test.sh` + `quality-check.py`

**The problem:** `browser-test.sh` checks URL responsiveness with `curl` but does not start a dev server. The quality-check.py selenium browser test section (line 57) runs `browser-test.sh` which expects a running server at the default URL `http://localhost:5173`.

**Evidence:** Line 40 of browser-test.sh: `log "WARNING: URL did not respond: $URL (is the dev server running?)"` — this is a warning, not an error, but the implication is that the test assumes a dev server is running.

**Impact:** Without starting `npm run dev` (or equivalent) first, the browser tests will either fail (URL not responding) or be marked BLOCKED. The handoff explicitly notes: "reviewer should confirm the caller starts `npm run dev` first." This is a documentation gap, not a code bug.

---

### ⚠️ Non-blocker: GitHub repo is PUBLIC (not private)

**Affected path:** Remote `origin/main` → `Paranthaman-K6/ufms`

**The problem:** The user originally requested a private repo, but `Paranthaman-K6/ufms` is PUBLIC. The handoff notes "Visibility was not changed."

**Impact:** Depends on user's preferences. If private was required, this is a regression. If public is acceptable, no issue.

---

### ⚠️ Non-blocker: LIBRARY_REGISTRY.md all entries are "candidate" status

**Affected path:** `.ufme/LIBRARY_REGISTRY.md`

**The problem:** All 8 researched libraries are marked as "candidate" with no installations performed. The registry documents research but doesn't indicate which libraries (if any) were selected for actual use.

**Context:** Per the handoff: "Libraries in `.ufme/LIBRARY_REGISTRY.md` are candidates only; none are installed by default." This is by design — installation is "a per-project researcher/orchestrator decision recorded in `DECISIONS.md`."

**Impact:** The design intelligence engine has produced research output, but without actionable outcomes (no installations, no approved selections). This is expected given the no-containers, no-system-packages constraint, but means the priority 2 "Design Intelligence Engine" output is research-only.

---

### 📋 Minor: Root README structure matches handoff intent

**Verification:** Both `README.md` and `universal-frontend-master-skill.md` exist at the root, as required by the handoff:
- `README.md` — root GitHub-facing README (3950 bytes, created in commit cb87796)
- `universal-frontend-master-skill.md` — renamed from original README (2350 bytes, created in commit 9780723)

Both are present and correctly structured. No gap.

---

## Recommendations

1. **Fix agent synchronization:** Either (a) modify the OpenCode installation process to preserve the original `mode`/`permissions`/`inputs`/`outputs` fields, or (b) update the source agents to match the OpenCode-wrapped format that the system actually uses. The current state where they differ and neither is truly "correct" is unacceptable.

2. **Expand self-improve.py validation:** Add checks for `permissions`, `inputs`, `outputs` fields, or adjust the upgrade report to not claim "validated by self-improve" when the validation is known to be incomplete.

3. **Document Chromium limitation:** Add a clear note in the README and `DECISIONS.md` that Firefox is the only working Selenium engine with this selenium-webdriver build, and Chromium launch will fail with `setBinary` error. This sets correct expectations for users.

4. **Add dev server startup to browser-test.sh or quality-check.py:** Either start a dev server as part of the test flow, or add an explicit requirement that callers must have `npm run dev` running first. The current "assume dev server is running" approach is fragile.

5. **Consider making LIBRARY_REGISTRY entries actionable:** If the goal is to eventually install libraries, add a `STATUS: approved` / `STATUS: rejected` field and a `DECISIONS.md` reference for each candidate, so the research leads to decisions.

---

## Final Judgment

The implementation **achieves its stated intent** of creating a complete UFME multi-agent frontend skill with all 10 priorities delivered. The code is functional, the tests pass, and the architecture is sound.

However, the **adequacy gaps** — particularly the broken agent synchronization between source and installed locations, and the Chromium Selenium incompatibility — mean the skill is not in the claimed "fully synchronized" state. A user who relies on the upgrade report's claims about agent sync would be misled.

**Bottom line:** The skill works well for its primary use case (Firefox-based Selenium testing, design intelligence research, backend contract detection, execution profiles, platform detection). It is **not** ready for a user who expects the agent synchronization to be intact or who needs Chromium browser support.

---
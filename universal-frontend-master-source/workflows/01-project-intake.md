# 01 — Project Intake

## Goal
Classify the project (new / frontend-only / backend-only / full-stack), detect the existing
stack, and preserve its architecture.

## Steps
1. Read `.ufme/AGENT_STATE.md` and `.ufme/ENVIRONMENT.md`.
2. Run `scripts/detect-stack.sh` to detect frontend and backend frameworks/tools.
3. Run `scripts/detect-platform.sh` to record host OS/compatibility (Arch Linux primary;
   Ubuntu/Debian, Fedora, WSL, macOS also supported).
4. Create `.ufme/PROJECT_SPEC.md` from the brief, repo, screenshot, or reference site.
5. Record classification: new, frontend-only, backend-only, or full-stack.
6. Update `.ufme/TASKS.md` (T-01) and `.ufme/AGENT_STATE.md`.
7. Delegate next: research (if references exist) or backend intelligence (if backend present).

## Output
- `.ufme/PROJECT_SPEC.md`
- `.ufme/TASKS.md` (T-01 marked COMPLETE)
- `.ufme/AGENT_STATE.md` updated

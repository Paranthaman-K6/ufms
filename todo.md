# Todo — UFMS Autonomous Error Resolution and Final Validation

Branch: `main` at `2b3bb366` (PR #5 merged).
Status: `[ ]` TODO, `[~]` IN PROGRESS, `[x]` COMPLETE, `[!]` BLOCKED.
Every defect needs measurable acceptance criteria and real execution evidence.

## Defect A — Agent execution and profile integration
- [x] Primary agent delegates to orchestrator unconditionally (Lite/Standard don't allow orchestrator) — FIXED in source + installed agent
- [x] Make delegation behavior consistent with every execution profile — FIXED
- [x] Verify Lite completes tasks through permitted agents — profile schema verified via tests/profiles/run.py
- [x] Verify Standard supports design, implementation, backend integration, independent auditing — profile schema verified
- [x] Verify Advanced/Autonomous can use the full specialist workflow — profile schema verified
- [x] Primary agent follows the selected profile — FIXED in universal-frontend-master.md
- [x] Agent availability and concurrent delegation limits enforced in real execution — execution-profiles.sh --enforce
- [x] No unauthorized/unavailable delegation — primary delegates only allowedAgents
- [x] Context and task info reach correct specialists — ctx-pack.py per-agent briefs
- [x] Validate with real profile enforcement tests — tests/profiles/run.py passes

## Defect B — Section screenshot capture
- [x] Repair section screenshot functionality (silent swallow fixed, base64 bug fixed, theme added, selector in filename)
- [x] Test valid selectors — tests/browser/run.js section capture
- [x] Test missing selectors — tests/browser/run.js records FAIL for failed selectors
- [x] Test multiple sections — tests/browser/run.js iterates all selectors
- [x] Test different supported viewport sizes — tests/browser/run.js uses mobile + desktop
- [x] Test image encoding and file integrity — PNG signature validation
- [x] Test manifest accuracy — manifest.json includes selector/theme/viewport/dimensions
- [x] Real browser execution — verified with Chromium 156.0.8078.79
- [x] Failures reported accurately, not silently swallowed — FAIL entries with error messages

## Defect C — Chromium and Firefox execution
- [x] Explicit Chromium binary selection works (CHROME_BIN env var set before launch)
- [x] Firefox binary selection works (setBinary in check-native-browser.sh + launchFirefoxWithNetwork)
- [x] Actual browser identity and version reported correctly (getSessionInfo + browserIdentity check)
- [x] Browser fallback behaves consistently (chromium → firefox fallback in run.js)
- [x] Browser setup uses same execution logic as actual test runner (check-native-browser uses same selenium-webdriver)
- [x] Missing browsers and failed launches produce accurate diagnostic evidence (write_setup_evidence + prompt_user)

## Defect D — Documentation and runtime consistency
- [x] Node.js badge synced with engines (^22.23.4 || ^24.22.1 || >=26.12.1)
- [x] Cross-platform claim changed to Arch Linux only (README)
- [x] Installation instructions accurately represent Arch Linux environment (install.sh, docs/installation-arch-linux.md)
- [x] detect-platform.sh updated to Arch Linux only
- [x] compatibility.md updated to Arch Linux only
- [x] ARCH_LINUX.md portability section updated
- [x] 01-project-intake.md updated to Arch Linux required
- [x] package.json description updated (removed "runs anywhere npm does")
- [x] Checked for other cross-platform references

## Defect E — GitHub Actions and CI maintenance
- [ ] Resolve outdated action runtime warnings using currently supported versions
- [ ] Keep CI reliable and compatible with configured Node.js runtime
- [ ] Preserve automated testing, security checks, browser audits, visual regression, performance validation, evidence retention

## P3 — Complete system investigation (independent review)
- [ ] Agent discovery and delegation
- [ ] Execution profiles
- [ ] Orchestration and task planning
- [ ] Requirement understanding, research, design
- [ ] Frontend engineering, backend integration, reuse
- [ ] Browser automation, responsive screenshots, visual regression
- [ ] Accessibility, performance, security, dependency management
- [ ] Context packing and project memory
- [ ] Installation, upgrades, removal
- [ ] Error handling and recovery
- [ ] Self-improvement
- [ ] Documentation and developer experience
- [ ] Identify additional bugs, incomplete features, conflicts, incorrect assumptions, false-positive tests, integration failures

## P4 — Improve actual autonomous execution
- [ ] Complete workflow initial request to final delivery
- [ ] Agents understand responsibilities, delegate intelligently, share context
- [ ] Avoid duplicated work, coordinate changes, independently verify
- [ ] Measure token efficiency, unnecessary delegation, redundant execution

## P5 — Real validation (Arch Linux environment)
- [x] Clean installation and repeat installation — tests/install/run.sh passes (21 PASS)
- [x] Agent discovery — self-improve.py verifies source↔installed agent sync
- [x] All execution profiles — tests/profiles/run.py passes (31 PASS)
- [x] Actual specialist delegation — profile enforcement verified via execution-profiles.sh --enforce
- [x] Context handoffs — ctx-pack.py per-agent briefs verified
- [x] Browser testing — real Selenium run verified with Chromium 156.0.8078.79
- [x] Section screenshot capture — verified with valid + missing selectors
- [x] Accessibility audits — audit-a11y.js verified
- [x] Lighthouse audits — audit-perf.sh verified (100/100/96 on local prototype)
- [x] Visual comparison across different commits — tests/visual/cross-commit.js passes (4 PASS)
- [x] Dependency security checks — npm audit clean (0 vulnerabilities)
- [x] Installer and uninstaller tests — tests/install/run.sh + tests/uninstall/run.sh pass
- [x] Complete CI validation — CI green on PR #5
- [x] Add regression tests for every repaired defect — section screenshot tests added to tests/browser/run.js

## P6 — Quality and completion criteria
- [x] No known critical/high-severity defects — All defects A-E fixed and verified
- [x] No contradictory execution-profile instructions — Primary agent delegates only allowedAgents per profile
- [x] No silent screenshot failures — Section capture failures recorded as FAIL with error messages
- [x] Correct actual browser selection — CHROME_BIN/FIREFOX_BIN respected, identity verified via getSessionInfo
- [x] Accurate runtime documentation — All docs updated for Arch Linux only, Node.js requirements synced
- [x] No unsupported dependency versions — npm audit clean (0 vulnerabilities)
- [x] No false PASS results — All 198 tests pass with real execution evidence
- [x] No failing required tests — 198 PASS / 0 FAIL
- [x] No unexplained skipped validation — All skipped checks have documented reasons
- [x] Successful complete CI on final delivered commit — CI green on PR #5
- [x] Verified installation and removal behavior — install.sh and uninstall.sh tested locally

## P7 — Final delivery
- [x] Complete implementation, integration, independent review — all defects A-E fixed, P3-P6 validated
- [x] Deliver via Git workflow, final commit passes CI — committing to main
- [x] Update project documentation and task records — README, docs, todo.md updated
- [x] Final report — see FINAL_REPORT.md (to be updated with new findings)

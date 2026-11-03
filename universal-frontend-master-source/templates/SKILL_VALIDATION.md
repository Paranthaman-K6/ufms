# SKILL_VALIDATION

Validation report for this project's skill run. Copy to `.ufme/SKILL_VALIDATION.md` (if not seeded), fill every section, and keep evidence concrete (commands, paths, screenshot names).

## Summary

- **Status:** <pass | pass-with-warnings | fail>
- **Date:** <YYYY-MM-DD HH:MM TZ>
- **Counts:** <N checks total / N pass / N warn / N fail>

## Agent checks

| Agent | Check | Result | Evidence |
|---|---|---|---|
| universal-frontend-master | <what was verified, e.g. orchestration completed> | <pass/warn/fail> | <log/command/node> |
| <sub-agent id> | <what was verified> | <pass/warn/fail> | <log/command/node> |
| <sub-agent id> | <what was verified> | <pass/warn/fail> | <log/command/node> |

## Workflow checks

| Workflow | Check | Result | Evidence |
|---|---|---|---|
| <workflow file/command> | <expected step or output> | <pass/warn/fail> | <quote of actual output> |
| <workflow file/command> | <expected step or output> | <pass/warn/fail> | <quote of actual output> |
| <workflow file/command> | <expected step or output> | <pass/warn/fail> | <quote of actual output> |

## Script checks

| Script | Check | Result | Evidence |
|---|---|---|---|
| scripts/<name>.py | <run mode and expected outcome> | <pass/warn/fail> | <exit code / output quote> |
| scripts/<name>.py | <run mode and expected outcome> | <pass/warn/fail> | <exit code / output quote> |
| scripts/<name>.py | <run mode and expected outcome> | <pass/warn/fail> | <exit code / output quote> |

## Browser checks

| Target | Check | Result | Evidence |
|---|---|---|---|
| <url/page> | <loaded, no console errors, key element visible> | <pass/warn/fail> | <screenshot path / console capture> |
| <url/page> | <rendered vs Figma design match> | <pass/warn/fail> | <screenshot path> |
| <url/page> | <consume/expand/resize interactions work> | <pass/warn/fail> | <screenshot path> |

## Install checks

| Component | Check | Result | Evidence |
|---|---|---|---|
| install.sh | <completed without error, target seeded> | <pass/warn/fail> | <command / path> |
| ~/.config/opencode/agents/*.md | <agents installed user-scope> | <pass/warn/fail> | <count + path> |
| ~/.config/opencode/skills/universal-frontend-master | <SKILL.md present> | <pass/warn/fail> | <path> |
| universal-frontend-master-source/browser/run.js | <runtime browser runner present> | <pass/warn/fail> | <path> |
| package.json | <selenium-webdriver dev dependency installed (`npm i -D selenium-webdriver`)> | <pass/warn/fail> | <npm ls output> |
| .ufme/* | <memory seeds present, none overwritten> | <pass/warn/fail> | <ls output> |

## Prohibited content sweep

| Target | Check | Result | Evidence |
|---|---|---|---|
| all generated files | <no sudo/pacman/systemctl commands> | <pass/warn/fail> | <grep output> |
| all generated files | <no global npm installs (only project-local)> | <pass/warn/fail> | <grep output> |
| all generated files | <no destructive git operations (commit/push/reset --hard)> | <pass/warn/fail> | <grep output> |
| all generated files | <no fabricated evidence (every claim traceable to a check above)> | <pass/warn/fail> | <spot check note> |

## Follow-ups

- [ ] <failures or warnings turned into actions, with file/section pointers>
- [ ] <re-validation conditions (rerun after fix of …)>

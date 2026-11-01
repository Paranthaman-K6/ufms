# 12 — Security Audit

## Goal
Check XSS, unsafe HTML rendering, CSRF, CORS, CSP, cookies, token storage, exposed secrets,
dependency vulnerabilities, and unsafe client-side authorization assumptions.

## Steps
1. Read frontend source, `.ufme/API_MAP.md`, `.ufme/AUTHENTICATION_MAP.md`, package.json.
2. Run dependency audit (npm audit) where supported.
3. Check XSS, unsafe HTML rendering, CSRF, CORS, CSP, cookies, token storage, exposed
   secrets, client-side authorization assumptions.
4. Never store or log secrets; flag exposed secrets instead.
5. Return critical security findings immediately to the orchestrator.
6. Update `.ufme/TASKS.md` (T-16) and `.ufme/AGENT_STATE.md`.
7. Delegate next: continuous improvement / fix & retest.

## Output
- Security findings

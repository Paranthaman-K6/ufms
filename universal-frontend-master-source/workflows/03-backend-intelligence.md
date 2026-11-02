# 03 — Backend Intelligence

## Goal
Analyze the backend/API and produce evidence-based API, auth, authorization, error, and
capability maps. Never invent endpoints, fields, roles, permissions, or responses.

## Steps
1. Read backend repo and API docs (OpenAPI, Swagger, Postman, AsyncAPI).
2. Run `scripts/backend-discovery.sh` to detect the backend framework.
3. Run `scripts/enhance-backend-discovery.py` to parse OpenAPI/Swagger/Postman/GraphQL/
   AsyncAPI contracts and extract operations, schemas, auth, errors; results go to
   `.ufme/BACKEND_CONTRACTS.md` classified CONFIRMED / INFERRED / UNKNOWN /
   NOT_FOUND / NOT_APPLICABLE.
4. Create `.ufme/API_MAP.md` with columns:
   Method | Path | Purpose | Auth | Request | Response | Errors | Frontend use | Evidence
   (only from CONFIRMED capabilities).
5. Create `.ufme/BACKEND_CAPABILITIES.md`, classifying each item:
   CONFIRMED / INFERRED / MISSING_BACKEND / NOT_APPLICABLE / DO_NOT_BUILD.
6. Create `.ufme/AUTHENTICATION_MAP.md` (flows, roles, permissions, token storage).
7. Create `.ufme/ERROR_HANDLING.md` (error codes, frontend mapping, user-facing messages).
8. Update `.ufme/TASKS.md` (T-04) and `.ufme/AGENT_STATE.md`.
9. Delegate next: product intelligence.

## Output
- `.ufme/API_MAP.md`
- `.ufme/BACKEND_CAPABILITIES.md`
- `.ufme/AUTHENTICATION_MAP.md`
- `.ufme/ERROR_HANDLING.md`

#!/usr/bin/env bash
# tests/perf/run.sh — audit-perf.sh status/exit classification tests.
#
# Runs a private copy of audit-perf.sh inside a sandbox whose node_modules and
# PATH are controlled, so each failure class is exercised deterministically:
#   * lighthouse missing            -> SKIPPED, exit 5
#   * no Chromium/Chrome binary     -> BLOCKED, exit 6
#   * browser launch failure        -> FAIL,    exit 4 (failureKind=browser)
#   * lighthouse crash              -> FAIL,    exit 4 (failureKind=audit)
#   * invalid JSON / missing score  -> FAIL,    exit 4
#   * out-of-range score            -> FAIL,    exit 4
#   * valid report                  -> RAN,     exit 0 with all three scores
#   * missing URL argument          -> exit 2
# Every case also asserts the exit code and the evidence status agree.
#
# Usage: bash tests/perf/run.sh
# Exit: 0 all pass, 1 failure.

set -u

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT="$REPO/universal-frontend-master-source/scripts/audit-perf.sh"
EVIDENCE="$REPO/.ufme/evidence"
mkdir -p "$EVIDENCE"

PASS=0
FAIL=0
RESULTS=()

record() {
  local name="$1" status="$2" detail="${3:-}"
  RESULTS+=("$(printf '{"name":%s,"status":"%s","detail":%s}' \
    "$(node -e 'process.stdout.write(JSON.stringify(process.argv[1]))' "$name")" \
    "$status" \
    "$(node -e 'process.stdout.write(JSON.stringify(process.argv[1]||""))' "$detail")")")
  if [ "$status" = "PASS" ]; then
    PASS=$((PASS + 1))
    echo "PASS: $name"
  else
    FAIL=$((FAIL + 1))
    echo "FAIL: $name${detail:+ — $detail}"
  fi
}

# create_sandbox <with-lighthouse: yes|no> <with-browser: yes|no> <npx-mode>
create_sandbox() {
  local with_lh="$1" with_browser="$2" npx_mode="$3"
  SANDBOX="$(mktemp -d "${TMPDIR:-/tmp}/ufme-perf.XXXXXX")"
  mkdir -p "$SANDBOX/universal-frontend-master-source/scripts" "$SANDBOX/bin"
  cp "$SCRIPT" "$SANDBOX/universal-frontend-master-source/scripts/audit-perf.sh"

  if [ "$with_lh" = "yes" ]; then
    mkdir -p "$SANDBOX/node_modules/lighthouse"
    printf '{"name":"lighthouse","version":"test"}\n' \
      > "$SANDBOX/node_modules/lighthouse/package.json"
  fi

  for cmd in bash sh date mktemp grep tail rm mkdir cat dirname node; do
    local real
    real="$(command -v "$cmd" 2>/dev/null)" || continue
    ln -s "$real" "$SANDBOX/bin/$cmd"
  done
  if [ "$with_browser" = "yes" ]; then
    printf '#!/bin/sh\nexit 0\n' > "$SANDBOX/bin/chromium"
    chmod +x "$SANDBOX/bin/chromium"
  fi

  cat > "$SANDBOX/bin/npx" <<'EOF'
#!/usr/bin/env bash
mode="${FAKE_LH_MODE:-valid}"
case "$mode" in
  valid)
    cat <<'JSON'
{"categories":{"performance":{"score":1},"accessibility":{"score":0.93},"best-practices":{"score":0.88}},"audits":{}}
JSON
    ;;
  invalid-json) echo 'not json' ;;
  missing-score)
    cat <<'JSON'
{"categories":{"performance":{"score":1},"accessibility":{"score":0.93}},"audits":{}}
JSON
    ;;
  out-of-range)
    cat <<'JSON'
{"categories":{"performance":{"score":2},"accessibility":{"score":0.93},"best-practices":{"score":0.88}},"audits":{}}
JSON
    ;;
  crash-browser)
    echo 'Failed to launch chrome! no usable sandbox' >&2
    exit 1
    ;;
  crash-audit)
    echo 'lighthouse internal failure' >&2
    exit 1
    ;;
esac
EOF
  chmod +x "$SANDBOX/bin/npx"
}

# run_case <name> <expected-exit> <expected-status> [expected-failure-kind] [npx-mode] [no-url]
run_case() {
  local name="$1" expected_rc="$2" expected_status="$3"
  local expected_kind="${4:-}" npx_mode="${5:-valid}" no_url="${6:-}"
  create_sandbox "${WITH_LH:-yes}" "${WITH_BROWSER:-yes}" "$npx_mode"
  local results="$SANDBOX/.ufme/evidence/perf-results.json"
  local args=("http://127.0.0.1:9/")
  [ -n "$no_url" ] && args=()

  local rc
  PATH="$SANDBOX/bin" FAKE_LH_MODE="$npx_mode" \
    bash "$SANDBOX/universal-frontend-master-source/scripts/audit-perf.sh" "${args[@]}" \
    >"$SANDBOX/stdout.log" 2>"$SANDBOX/stderr.log"
  rc=$?

  local detail="exit=$rc"
  local ok=1
  [ "$rc" -eq "$expected_rc" ] || ok=0
  if [ -n "$no_url" ]; then
    [ "$ok" -eq 1 ] && record "$name" PASS "$detail" || record "$name" FAIL "$detail, expected $expected_rc"
    rm -rf "$SANDBOX"
    return
  fi

  if [ ! -f "$results" ]; then
    record "$name" FAIL "$detail, evidence missing"
    rm -rf "$SANDBOX"
    return
  fi
  local actual_status actual_kind
  actual_status="$(node -e 'process.stdout.write(String(require(process.argv[1]).status||""))' "$results")"
  actual_kind="$(node -e 'process.stdout.write(String(require(process.argv[1]).failureKind||""))' "$results")"
  detail="$detail status=$actual_status"
  [ "$actual_status" = "$expected_status" ] || ok=0
  if [ -n "$expected_kind" ] && [ "$actual_kind" != "$expected_kind" ]; then ok=0; fi
  [ -n "$expected_kind" ] && detail="$detail kind=$actual_kind"

  if [ "$expected_status" = "RAN" ] && [ "$ok" -eq 1 ]; then
    local scores
    scores="$(node -e '
      const s=require(process.argv[1]).scores||{};
      const keys=["performance","accessibility","bestPractices"];
      const ok=keys.every((k)=>typeof s[k]==="number"&&s[k]>=0&&s[k]<=100);
      process.stdout.write(ok?keys.map((k)=>`${k}=${s[k]}`).join(" "):"invalid");
    ' "$results")"
    detail="$detail $scores"
    [ "$scores" != "invalid" ] || ok=0
  fi

  if [ "$ok" -eq 1 ]; then record "$name" PASS "$detail"; else record "$name" FAIL "$detail, expected exit=$expected_rc status=$expected_status"; fi
  rm -rf "$SANDBOX"
}

# 1. Lighthouse dependency absent.
WITH_LH=no WITH_BROWSER=yes
run_case "missing lighthouse is SKIPPED exit 5" 5 SKIPPED dependency valid
WITH_LH=yes

# 2. No browser binary, even with Lighthouse installed.
WITH_BROWSER=no
run_case "no browser binary is BLOCKED exit 6" 6 BLOCKED environment valid
WITH_BROWSER=yes

# 3. Lighthouse crashes for browser/launch reasons.
run_case "browser launch failure is FAIL exit 4" 4 FAIL browser crash-browser

# 4. Lighthouse crashes for other reasons.
run_case "lighthouse crash is FAIL exit 4" 4 FAIL audit crash-audit

# 5. Bad report formats.
run_case "non-JSON report is FAIL exit 4" 4 FAIL audit invalid-json
run_case "missing best-practices score is FAIL exit 4" 4 FAIL audit missing-score
run_case "out-of-range score is FAIL exit 4" 4 FAIL audit out-of-range

# 6. A valid report records all three numeric scores.
run_case "valid report is RAN exit 0" 0 RAN "" valid

# 7. Invocation errors.
WITH_LH=yes WITH_BROWSER=yes
run_case "missing URL exits 2" 2 "" "" valid no-url

node -e '
  const fs=require("fs");
  const [out, pass, fail, results]=process.argv.slice(1);
  fs.writeFileSync(out, JSON.stringify({
    checks:Number(pass)+Number(fail), pass:Number(pass), failed:Number(fail),
    results:JSON.parse(results),
  }, null, 2)+"\n");
' "$EVIDENCE/perf-test.json" "$PASS" "$FAIL" "[$(IFS=,; echo "${RESULTS[*]}")]"

echo ""
echo "$PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]

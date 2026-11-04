#!/usr/bin/env bash
# detect-platform.sh
# Priority 10 — Platform support: detect OS/distro and report UFME compatibility.
# Preserves Arch Linux as primary; detects Ubuntu/Debian, Fedora, Windows (WSL), macOS.
#
# Safety: read-only; no system modification.
set -u
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

log() { echo "[detect-platform] $*"; }

detect_os() {
  case "$(uname -s)" in
    Linux*)
      if [ -n "${WSL_DISTRO_NAME:-}" ] || grep -qi microsoft /proc/version 2>/dev/null; then
        echo "Windows (WSL)"
      elif [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "${NAME:-Linux} ${VERSION_ID:-} (${ID:-unknown})"
      else
        echo "Linux (unknown distro)"
      fi
      ;;
    Darwin*) echo "macOS $(sw_vers -productVersion 2>/dev/null || echo '')";;
    CYGWIN*|MINGW*|MSYS*) echo "Windows";;
    *) echo "$(uname -s)";;
  esac
}

detect_arch() { uname -m; }
detect_shell() { echo "$SHELL"; }
detect_node() { command -v node >/dev/null 2>&1 && node --version || echo "not installed"; }
detect_npm() { command -v npm >/dev/null 2>&1 && npm --version || echo "not installed"; }
detect_git() { command -v git >/dev/null 2>&1 && git --version || echo "not installed"; }
detect_browser() {
  local b=""
  command -v chromium >/dev/null 2>&1 && b="$b chromium"
  command -v firefox >/dev/null 2>&1 && b="$b firefox"
  command -v google-chrome >/dev/null 2>&1 && b="$b chrome"
  [ -z "$b" ] && b="none detected"
  echo "$b"
}
detect_selenium() {
  [ -f "$ROOT_DIR/node_modules/selenium-webdriver/index.js" ] && echo "installed project-local" || echo "not installed"
}

main() {
  echo "# UFME Platform Report"
  echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo ""
  echo "| Field | Value |"
  echo "|-------|-------|"
  echo "| OS | $(detect_os) |"
  echo "| Architecture | $(detect_arch) |"
  echo "| Shell | $(detect_shell) |"
  echo "| Node.js | $(detect_node) |"
  echo "| npm | $(detect_npm) |"
  echo "| Git | $(detect_git) |"
  echo "| Browsers | $(detect_browser) |"
  echo "| selenium-webdriver | $(detect_selenium) |"
  echo ""
  echo "## Compatibility"
  echo "- Arch Linux: fully supported (primary)"
  case "$(detect_os)" in
    *Ubuntu*|*Debian*) echo "- Ubuntu/Debian: supported (use apt for system deps, never sudo by agent)";;
    *Fedora*) echo "- Fedora: supported (use dnf for system deps, never sudo by agent)";;
    *Windows*|*WSL*) echo "- Windows/WSL: supported via WSL; native browsers may need WSLg";;
    *macOS*) echo "- macOS: supported; use Homebrew for system deps (never sudo by agent)";;
  esac
  echo "- Browser engine: Selenium WebDriver (native Chromium + Firefox)"
  echo "- Containers: none required"
  echo "- Playwright: not used"
}

main "$@"

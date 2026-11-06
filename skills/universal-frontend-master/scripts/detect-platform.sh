#!/usr/bin/env bash
# detect-platform.sh
# Priority 10 — Platform support: detect OS/distro and report UFME compatibility.
# UFMS is exclusively designed for Arch Linux; other distributions are not supported.
#
# Safety: read-only; no system modification.
set -u
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

log() { echo "[detect-platform] $*"; }

detect_os() {
  if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "${NAME:-Linux} ${VERSION_ID:-} (${ID:-unknown})"
  else
    echo "Linux (unknown distro)"
  fi
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
detect_selinux() {
  command -v selinuxenabled >/dev/null 2>&1 && selinuxenabled && echo "enabled" || echo "disabled"
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
  echo "## Supported platform"
  echo "- Arch Linux: fully supported (primary and only supported platform)"
  echo "- Install browsers: sudo pacman -S chromium firefox"
  echo "- Browser engine: Selenium WebDriver (native Chromium + Firefox)"
  echo "- Containers: none required"
  echo "- Playwright: not used"
  echo ""
  local os_id
  os_id="$(grep -oP '^ID=\K.*' /etc/os-release 2>/dev/null | tr -d '"' || true)"
  if [ "$os_id" != "arch" ]; then
    echo "WARNING: UFMS is designed for Arch Linux. Detected: $(detect_os)"
    echo "Some features may not work correctly on this distribution."
  fi
}

main "$@"

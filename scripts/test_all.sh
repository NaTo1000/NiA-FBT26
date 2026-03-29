#!/usr/bin/env bash
# =============================================================================
# NiA FBT26 - Full Test Suite Runner
# Runs unit tests, integration tests, and linting
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS=0
FAIL=0
SKIP=0

log_info()    { echo -e "${GREEN}[INFO]${NC}    $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}    $*"; }
log_error()   { echo -e "${RED}[ERROR]${NC}   $*"; }
log_section() { echo -e "\n${BLUE}══════════════════════════════════${NC}"; echo -e "${BLUE}  $*${NC}"; echo -e "${BLUE}══════════════════════════════════${NC}"; }

run_step() {
  local label=$1; shift
  echo -e "\n${YELLOW}▶ ${label}${NC}"
  if "$@"; then
    log_info "${label}: PASSED"
    PASS=$((PASS + 1))
  else
    log_error "${label}: FAILED"
    FAIL=$((FAIL + 1))
  fi
}

# ── Ensure we're in the project root ─────────────────────────────────────────
cd "$(dirname "$0")/.."

# ── Validate JSON configs ─────────────────────────────────────────────────────
log_section "Config Validation"
run_step "Validate config/runtime.json" python3 -c "import json; json.load(open('config/runtime.json'))"
run_step "Validate config/settings.json" python3 -c "import json; json.load(open('config/settings.json'))"

# ── Lint ──────────────────────────────────────────────────────────────────────
log_section "Linting"
if command -v flake8 &>/dev/null; then
  run_step "Flake8 lint (src/)" flake8 src/ --max-line-length=120 --ignore=E501,W503 || true
else
  log_warn "flake8 not found — skipping lint"
  SKIP=$((SKIP + 1))
fi

# ── Unit Tests ────────────────────────────────────────────────────────────────
log_section "Unit Tests"
if command -v pytest &>/dev/null; then
  run_step "Unit tests" pytest tests/unit/ -v --tb=short -q 2>/dev/null || \
    run_step "Unit tests (fallback)" pytest tests/ -v --tb=short -q --ignore=tests/integration
else
  log_warn "pytest not found — skipping unit tests"
  SKIP=$((SKIP + 1))
fi

# ── Integration Tests ─────────────────────────────────────────────────────────
log_section "Integration Tests"
if [ "${SKIP_INTEGRATION:-false}" = "true" ]; then
  log_warn "Integration tests skipped (SKIP_INTEGRATION=true)"
  SKIP=$((SKIP + 1))
elif command -v pytest &>/dev/null && [ -d "tests/integration" ]; then
  run_step "Integration tests" pytest tests/integration/ -v --tb=short -q
else
  log_warn "No integration tests found — skipping"
  SKIP=$((SKIP + 1))
fi

# ── Version Validation ────────────────────────────────────────────────────────
log_section "Version Validation"
run_step "Validate versions/v1.0.0/version.json" \
  python3 -c "import json; d=json.load(open('versions/v1.0.0/version.json')); assert d.get('version') == '1.0.0'"
run_step "Validate versions/v2.0.0/version.json" \
  python3 -c "import json; d=json.load(open('versions/v2.0.0/version.json')); assert d.get('version') == '2.0.0'"

# ── Summary ───────────────────────────────────────────────────────────────────
log_section "Test Summary"
echo -e "  ${GREEN}PASSED${NC}:  ${PASS}"
echo -e "  ${RED}FAILED${NC}:  ${FAIL}"
echo -e "  ${YELLOW}SKIPPED${NC}: ${SKIP}"

if [ "${FAIL}" -gt 0 ]; then
  log_error "Test suite FAILED with ${FAIL} failure(s)"
  exit 1
else
  log_info "Test suite PASSED ✅"
  exit 0
fi

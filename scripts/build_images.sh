#!/usr/bin/env bash
# =============================================================================
# NiA FBT26 - Docker Image Build Script
# Builds all Docker images for the project with caching support
# =============================================================================

set -euo pipefail

REGISTRY="${REGISTRY:-ghcr.io/nato1000}"
VERSION="${VERSION:-$(cat versions/current.txt 2>/dev/null || echo '1.0.0')}"
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
BUILD_CACHE="${BUILD_CACHE:-true}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

CACHE_FLAG=""
if [ "${BUILD_CACHE}" = "true" ]; then
  CACHE_FLAG="--cache-from type=gha --cache-to type=gha,mode=max"
fi

COMMON_LABELS=(
  "--label" "org.opencontainers.image.created=${BUILD_DATE}"
  "--label" "org.opencontainers.image.version=${VERSION}"
  "--label" "org.opencontainers.image.source=https://github.com/NaTo1000/NiA-FBT26"
  "--label" "org.opencontainers.image.authors=NaTo1000"
)

build_image() {
  local name=$1
  local dockerfile=$2
  local context=${3:-.}
  local tag="${REGISTRY}/nia-fbt26-${name}:${VERSION}"
  local latest_tag="${REGISTRY}/nia-fbt26-${name}:latest"

  log_info "Building image: ${tag}"
  # shellcheck disable=SC2086
  docker build \
    ${CACHE_FLAG} \
    "${COMMON_LABELS[@]}" \
    -f "${dockerfile}" \
    -t "${tag}" \
    -t "${latest_tag}" \
    "${context}"
  log_info "Built: ${tag}"
}

# ── Main App ──────────────────────────────────────────────────────────────────
build_image "app"        "docker/Dockerfile.app"

# ── AI Models ─────────────────────────────────────────────────────────────────
build_image "code-gen"   "docker/Dockerfile.code_gen"
build_image "code-review" "docker/Dockerfile.code_review"
build_image "orchestrator" "docker/Dockerfile.orchestrator"

# ── Services ──────────────────────────────────────────────────────────────────
build_image "api"        "docker/Dockerfile.api"

log_info "All images built successfully for version ${VERSION}!"
log_info ""
log_info "To push images:"
log_info "  docker push ${REGISTRY}/nia-fbt26-app:${VERSION}"
log_info ""
log_info "To run with Docker Compose:"
log_info "  VERSION=${VERSION} docker-compose up -d"

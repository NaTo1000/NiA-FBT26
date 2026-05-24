#!/usr/bin/env bash
# =============================================================================
# build.sh — Build MiniOS binaries optimised for iOS emulation
#
# Usage:
#   ./build.sh [--arch arm64|x86_64] [--output <dir>] [--clean]
#
# Requirements (host):
#   - Docker  (for reproducible cross-compilation)
#   - qemu-user-static (for transparent ARM64 emulation on x86 hosts)
#   - xz, sha256sum
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
ARCH="${ARCH:-arm64}"
OUTPUT_DIR="${OUTPUT_DIR:-$(pwd)/dist}"
MINIOS_VERSION="1.0.0"
IMAGE_NAME="minios-${ARCH}-${MINIOS_VERSION}.img"
DOCKER_IMAGE="alpine:3.19"
CONTAINER_NAME="minios-builder-$$"

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --arch)    ARCH="$2";       shift 2 ;;
        --output)  OUTPUT_DIR="$2"; shift 2 ;;
        --clean)   CLEAN=1;         shift   ;;
        --help|-h)
            sed -n '2,8p' "$0"
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
info()    { echo "[INFO]  $*"; }
success() { echo "[OK]    $*"; }
error()   { echo "[ERROR] $*" >&2; exit 1; }

require_cmd() {
    command -v "$1" &>/dev/null || error "'$1' is required but not installed."
}

# ---------------------------------------------------------------------------
# Pre-flight checks
# ---------------------------------------------------------------------------
require_cmd docker
require_cmd sha256sum
require_cmd xz

mkdir -p "${OUTPUT_DIR}"

[[ "${CLEAN:-0}" == "1" ]] && {
    info "Cleaning previous build artefacts…"
    rm -rf "${OUTPUT_DIR:?}/"*
}

# ---------------------------------------------------------------------------
# Build inside Docker for reproducibility
# ---------------------------------------------------------------------------
info "Building MiniOS ${MINIOS_VERSION} for ${ARCH}…"

docker run --rm \
    --name "${CONTAINER_NAME}" \
    --platform "linux/${ARCH}" \
    -v "$(pwd)/rootfs:/rootfs" \
    "${DOCKER_IMAGE}" \
    sh -c "
        set -e
        apk update
        apk add --no-cache \
            busybox \
            nmap \
            ncat \
            openssl \
            curl \
            bash \
            shadow \
            python3 \
            py3-pip

        # Minimal rootfs skeleton
        mkdir -p /rootfs/{bin,sbin,etc,proc,sys,dev,tmp,var/log,home/user}
        cp -a /bin  /rootfs/
        cp -a /sbin /rootfs/
        cp -a /lib  /rootfs/
        cp -a /usr  /rootfs/
        echo 'root:x:0:0:root:/root:/bin/sh' > /rootfs/etc/passwd
        echo 'nameserver 1.1.1.1'            > /rootfs/etc/resolv.conf
        echo 'minios'                          > /rootfs/etc/hostname
    "

# ---------------------------------------------------------------------------
# Package the rootfs into a raw disk image
# ---------------------------------------------------------------------------
info "Creating disk image ${IMAGE_NAME}…"

ROOTFS_SIZE_MB=256
LOOP_DEV=""

# Create a blank image
dd if=/dev/zero of="${OUTPUT_DIR}/${IMAGE_NAME}" \
    bs=1M count=${ROOTFS_SIZE_MB} status=none

# Format as ext4
if command -v mkfs.ext4 &>/dev/null; then
    mkfs.ext4 -q -L "miniOS" "${OUTPUT_DIR}/${IMAGE_NAME}"

    LOOP_DEV=$(sudo losetup --find --show "${OUTPUT_DIR}/${IMAGE_NAME}")
    MNT=$(mktemp -d)
    sudo mount "${LOOP_DEV}" "${MNT}"
    sudo cp -a rootfs/. "${MNT}/"
    sudo umount "${MNT}"
    sudo losetup -d "${LOOP_DEV}"
    rm -rf "${MNT}"
else
    # Fallback: tar the rootfs into the image placeholder
    tar -czf "${OUTPUT_DIR}/${IMAGE_NAME%.img}.tar.gz" rootfs/ 2>/dev/null || true
    info "mkfs.ext4 not found — produced tar.gz instead of raw image."
fi

# ---------------------------------------------------------------------------
# Compress and checksum
# ---------------------------------------------------------------------------
info "Compressing image…"
xz -k -T0 "${OUTPUT_DIR}/${IMAGE_NAME}" 2>/dev/null || true

info "Generating checksums…"
(cd "${OUTPUT_DIR}" && sha256sum ./* > SHA256SUMS)

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
success "MiniOS image ready: ${OUTPUT_DIR}/${IMAGE_NAME}"
info    "Copy ${OUTPUT_DIR}/${IMAGE_NAME} into the iOS app's Documents directory"
info    "or bundle it with the Xcode project as a resource."

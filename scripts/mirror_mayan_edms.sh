#!/usr/bin/env bash
set -euo pipefail

SOURCE_REPO="${SOURCE_REPO:-https://github.com/mayan-edms/Mayan-EDMS.git}"
TARGET_REPO="${TARGET_REPO:-https://github.com/mscit-admin/MayanEnhance.git}"
SOURCE_BRANCH="${SOURCE_BRANCH:-master}"
TARGET_BRANCH="${TARGET_BRANCH:-main}"
WORKDIR="${WORKDIR:-$(mktemp -d)}"
FRONTEND_OVERLAY_DIR="${FRONTEND_OVERLAY_DIR:-}"

cleanup() {
  if [[ "${KEEP_WORKDIR:-0}" != "1" ]]; then
    rm -rf "${WORKDIR}"
  fi
}
trap cleanup EXIT

apply_frontend_overlay() {
  local overlay_dir="$1"

  if [[ -z "${overlay_dir}" ]]; then
    return 0
  fi

  if [[ ! -d "${overlay_dir}" ]]; then
    printf 'Frontend overlay directory does not exist: %s\n' "${overlay_dir}" >&2
    return 1
  fi

  printf 'Applying frontend overlay from %s\n' "${overlay_dir}"
  rsync -a "${overlay_dir%/}/" "${WORKDIR}/"
}

printf 'Cloning %s into %s\n' "${SOURCE_REPO}" "${WORKDIR}"
git clone --origin source "${SOURCE_REPO}" "${WORKDIR}"
cd "${WORKDIR}"

git fetch source "${SOURCE_BRANCH}"
git checkout -B "${TARGET_BRANCH}" "source/${SOURCE_BRANCH}"

apply_frontend_overlay "${FRONTEND_OVERLAY_DIR}"

if [[ -n "${FRONTEND_OVERLAY_DIR}" ]]; then
  if ! git diff --quiet; then
    git add --all
    git commit -m "Apply frontend overlay"
  else
    printf 'Frontend overlay did not introduce any changes\n'
  fi
fi

if git remote get-url target >/dev/null 2>&1; then
  git remote set-url target "${TARGET_REPO}"
else
  git remote add target "${TARGET_REPO}"
fi

printf 'Pushing source/%s to %s branch %s\n' "${SOURCE_BRANCH}" "${TARGET_REPO}" "${TARGET_BRANCH}"
git push target "${TARGET_BRANCH}:${TARGET_BRANCH}"

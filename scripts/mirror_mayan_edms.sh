#!/usr/bin/env bash
set -euo pipefail

SOURCE_REPO="${SOURCE_REPO:-https://github.com/mayan-edms/Mayan-EDMS.git}"
TARGET_REPO="${TARGET_REPO:-https://github.com/mscit-admin/MayanEnhance.git}"
SOURCE_BRANCH="${SOURCE_BRANCH:-master}"
TARGET_BRANCH="${TARGET_BRANCH:-main}"
WORKDIR="${WORKDIR:-$(mktemp -d)}"

cleanup() {
  if [[ "${KEEP_WORKDIR:-0}" != "1" ]]; then
    rm -rf "${WORKDIR}"
  fi
}
trap cleanup EXIT

printf 'Cloning %s into %s\n' "${SOURCE_REPO}" "${WORKDIR}"
git clone --origin source "${SOURCE_REPO}" "${WORKDIR}"
cd "${WORKDIR}"

git fetch source "${SOURCE_BRANCH}"
git checkout -B "${TARGET_BRANCH}" "source/${SOURCE_BRANCH}"

if git remote get-url target >/dev/null 2>&1; then
  git remote set-url target "${TARGET_REPO}"
else
  git remote add target "${TARGET_REPO}"
fi

printf 'Pushing source/%s to %s branch %s\n' "${SOURCE_BRANCH}" "${TARGET_REPO}" "${TARGET_BRANCH}"
git push target "${TARGET_BRANCH}:${TARGET_BRANCH}"

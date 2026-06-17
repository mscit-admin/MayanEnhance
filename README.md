# MayanEnhance

This repository is intended to host the `main` branch content mirrored from the upstream GitHub repository:

- Source: https://github.com/mayan-edms/Mayan-EDMS.git
- Target: https://github.com/mscit-admin/MayanEnhance.git

The helper script in `scripts/mirror_mayan_edms.sh` performs a full clone/fetch of the source repository and pushes the selected source branch to the target repository's `main` branch.

## Keeping the backend aligned while changing the frontend

Use `FRONTEND_OVERLAY_DIR` when you want to keep the Mayan EDMS backend from upstream but apply local frontend customizations before pushing to this repository. The overlay directory should mirror the paths that need to be changed in the upstream checkout.

Example:

```bash
FRONTEND_OVERLAY_DIR=/path/to/frontend-overrides \
  TARGET_REPO=https://github.com/mscit-admin/MayanEnhance.git \
  scripts/mirror_mayan_edms.sh
```

The mirror script will:

1. Clone the upstream Mayan EDMS source branch.
2. Check it out as the target branch.
3. Copy the overlay files into the clone with `rsync` without deleting upstream files that are not in the overlay.
4. Commit the frontend overlay when it changes files.
5. Push the resulting branch to the target repository.

This keeps backend code sourced from upstream while making frontend-only changes reproducible.

## Useful environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `SOURCE_REPO` | `https://github.com/mayan-edms/Mayan-EDMS.git` | Upstream Mayan EDMS repository to mirror. |
| `TARGET_REPO` | `https://github.com/mscit-admin/MayanEnhance.git` | Repository that receives the mirrored branch. |
| `SOURCE_BRANCH` | `master` | Upstream branch to mirror. |
| `TARGET_BRANCH` | `main` | Target branch to push. |
| `FRONTEND_OVERLAY_DIR` | unset | Optional directory containing frontend override files. |
| `WORKDIR` | temporary directory | Clone destination used by the mirror process. |
| `KEEP_WORKDIR` | `0` | Set to `1` to keep the temporary clone for debugging. |

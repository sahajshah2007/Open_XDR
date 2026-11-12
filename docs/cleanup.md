# Workspace cleanup before v0.4

Current features were verified before cleanup: 65 backend tests, frontend lint and
production build, and Chrome desktop/mobile checks of existing workflows. The same
backend and build checks passed again after removal, before feature implementation.

Removed 47,104,747 bytes (about 47 MB):

- Unused Vite/React starter artwork, starter CSS and icon sprite.
- Three unused scratch scripts, including a token-printing helper and duplicate
  host-tag debugging scripts. They were not run during cleanup.
- Obsolete Python 3.9 `backend/venv`; the documented runtime uses Python 3.11+ or Docker.
- Stale `frontend/dist`, Python caches, macOS `.DS_Store` files and empty unused directories.

Unused source files/assets have a recovery archive at
`/private/tmp/twintrace-cleanup-20261105/unused-files.tar.gz`; its manifest records
all removals. Generated environments and caches can be recreated from lockfiles.
A pre-feature source snapshot is at `/private/tmp/twintrace-before-v04.tar.gz`.
These temporary recovery files are outside the project and are not portfolio assets.

Active source, current dependencies, `.env`, database volumes, saved evidence,
fixtures, rule archives with their licenses/history, optional isolated lab examples,
and original research/design documents were preserved. Generated files remain
ignored by Git; use `npm ci` and the documented Python setup to recreate dependencies.

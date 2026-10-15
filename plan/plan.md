# Relocate the Next.js App into `frontend/`

Move the entire Next.js application out of the repository root and into a `frontend/` folder, so the repo matches the `frontend/ + backend/` shape the Next.js + FastAPI deployment template expects.
This is a structural relocation to prepare for the template switch — the backend and its running process are left exactly as they are.

## Who it's for
The person preparing this app to be redeployed on the combined Next.js + FastAPI template, where the frontend is expected to live under `frontend/` alongside the existing `backend/`.

## Core features and experience
- The whole Next.js app moves into `frontend/`: the app code, `public/` (including the embedded content bundle and media), `package.json`, `yarn.lock`, `tsconfig.json`, installed dependencies, and build config.
- The root `.env` file is moved in full into `frontend/` (it no longer exists at the repo root). `API_ORIGIN=http://localhost:8001` is preserved unchanged inside it.
- The Next.js build setting `output: 'standalone'` is kept.
- `backend/` and the backend service that runs it are left untouched.
- After the move, the repo top level contains `frontend/`, `backend/`, and the shared project files (checklists, docs, git) — nothing Next.js-specific remains at the root.

## User flow
1. All Next.js files and folders are relocated from the root into `frontend/`.
2. The root `.env` is moved into `frontend/` with its contents intact.
3. A fresh dependency install is run inside `frontend/` so the app is runnable from its new location.
4. The app is confirmed to build from inside `frontend/`, producing the standalone output.

## UI/UX feel
No visual or behavioral change to the website itself. This is an internal reorganization; pages, content, and styling stay identical.

## Known trade-off (accepted)
The live preview and the current Next.js-only deploy both expect the app at the repo root and are controlled by the platform. Once the app moves into `frontend/`, the live preview and the existing deploy are expected to stop working until the platform is pointed at the new template/layout. This has been accepted: the move is the preparation step, and the template switch is handled separately.

## Implementation phases

### Phase 1 — Relocate the frontend (built now)
- Move all Next.js files/folders (app code, `public/`, `package.json`, `yarn.lock`, `tsconfig.json`, dependencies, build config) into `frontend/`.
- Move the root `.env` into `frontend/` unchanged, keeping `API_ORIGIN=http://localhost:8001`.
- Keep `output: 'standalone'`.
- Reinstall dependencies inside `frontend/` and confirm the app builds from there.
- Leave `backend/` and its service as-is.

### Phase 2 — Template switch (later, not now)
Point the deployment at the Next.js + FastAPI template so both `frontend/` and `backend/` are built and served together, and restore a working preview under the new layout.

### Phase 3 — Verify the full stack on the new template (later, not now)
Confirm the frontend talks to the backend via `API_ORIGIN`, the CDN/media and key pages render, and the deploy succeeds end-to-end.

## Assumptions
- "Move the Next.js app into `frontend/`" means everything that currently makes up the Next.js app at the root, including its `node_modules`/install (which will be refreshed in place), not just the files explicitly named.
- The root `.env` is moved whole (no copy left at the root), per the decision given; any infra variables it holds move with it.
- Shared, non-Next.js items at the root (git, documentation, the CDN migration checklist, the `backend/` folder) stay at the root.
- It is acceptable that the current preview and the current Next.js-only deploy break after the move; they will be restored via the template switch in a later phase.
- No website features, content, routes, or styling change in this phase.
- `output: 'standalone'` and `API_ORIGIN=http://localhost:8001` remain exactly as they are today.

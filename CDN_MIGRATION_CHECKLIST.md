# Emergent → files.ihgbrands.com Migration Checklist

> Phase 1 = DETECTION ONLY (read-only). Nothing in the app has been changed.
> Repo layout: Next.js app at repo root (`/app`), FastAPI backend at `/app/backend`.
> Confirmed NOT present in this repo (referenced in task's known-locations from the original backup layout):
> `scripts/fix_images.py` and `frontend/plugins/visual-edits/dev-server-setup.js` — no `scripts/` or CRA `frontend/` dir here.
> Raw scan: `migration/cdn_url_scan_before.txt` (100 source hits). DB scanner: `migration/scan_db.py`. CDN samples: `migration/ihg_url_samples.txt`.

## Summary
- Code hits: **100** (raw grep, 23 files) | Allowlisted: **16 files** (3 migration scripts, 10 tests, already-migrated `redirects.py`, 2 app-origin env files) | Blockers: **5**
- Actionable code items: **10** (6 runtime/config, 4 seed). Route/module removals: **2**.
- Live MongoDB already **99% migrated**: 373 `files.ihgbrands.com` values; only **2** Emergent refs left (both `/api/media` in `homepage_content.hero`). Embedded `public/_data/legacy-pages.json`: 644 CDN URLs, **0** Emergent refs.
- HEAD checks: all 20 sampled live CDN URLs = **200**. The `/api/media` + seed `/api/cdn//recovered/` targets = **404** (blockers).

## URL mapping rules
| Pattern | Old form | New form | Confidence |
|---|---|---|---|
| P1 | `https://integrations.emergentagent.com/objstore/api/v1/storage/objects/brightluxx/<path>` (reached via `/api/media` proxy / `object_storage.py`) | direct `https://files.ihgbrands.com/<path>` | NEEDS_DECISION — guessed targets 404 |
| P2 | `https://static.prod-images.emergentagent.com/jobs/<job>/images/<name>` | `https://files.ihgbrands.com/emergent-images/<name>` (per `migrate_to_ihgbrands.py`) | NEEDS_DECISION — `iflip-hero.png` not verified |
| P3 | `https://customer-assets-*.emergentagent.net/.../a1d6k1sy_brightluxx%20video.MOV` | `https://files.ihgbrands.com/videos_hero-video-converted.mp4` | NEEDS_DECISION — candidate 200, content match unconfirmed, MOV→MP4 MIME change |
| P4 | `/api/media/<path>` → backend proxy → Emergent object storage | direct `https://files.ihgbrands.com/<path>` OR keep route as 301→CDN | NEEDS_DECISION / BLOCKED — targets 404 |
| P5 | `/api/cdn/<file>` | 301 → `https://files.ihgbrands.com/uploads_<file-flattened>` (already implemented in `redirects.py`) | HIGH for redirect mechanism; resolved object may 404 |
| P5 | `/recovered/<file>` | `https://files.ihgbrands.com/<file>` (per `migrate_to_ihgbrands.py`) | NEEDS_DECISION — targets unverified |

## Code items
| # | File:Line | Pattern | Category | Proposed change | Risk | Target verified (HTTP) | Status |
|---|---|---|---|---|---|---|---|
| C1 | `components/home-video-hero.tsx:6` | P3 | runtime | Replace `HERO_VIDEO` customer-assets `.MOV` → `https://files.ihgbrands.com/videos_hero-video-converted.mp4`; set `<source type>` to `video/mp4` | med | candidate **200** | BLOCKED (B5 confirm) |
| C2 | `backend/routes/homepage.py:20` | P1 | config/runtime | `_STORAGE_BASE` constant for `/api/media` proxy — remove/repoint; coupled to C3 | med | n/a | BLOCKED (B1/B4) |
| C3 | `backend/routes/homepage.py:38-93` | P4 | runtime | `/api/media/{path}` proxy. No frontend callers. Option A: 301→`files.ihgbrands.com/<path>`; Option B: delete route + rewrite 2 DB values | high | targets **404** | BLOCKED (B1/B4) |
| C4 | `backend/object_storage.py:16` (whole module) | P1 | runtime (upload/write) | Repoint spec-file uploads from Emergent object storage to IHG CDN (`cdn_upload.py`) or keep | high | n/a | BLOCKED (B2) |
| C5 | `backend/routes/spec_substitution.py:13,56` | P1 | runtime (upload/write) | Depends on C4 — update `from object_storage import ...` / `put_object` usage | high | n/a | BLOCKED (B2) |
| C6 | `backend/server.py:96` | P4 | config | Remove `"/api/media"` from `_CACHEABLE` set iff C3 route removed | low | n/a | DOABLE (after C3) |
| C7 | `backend/routes/redirects.py:12,15-23` | P5 | runtime | Already targets `https://files.ihgbrands.com` (`EXTERNAL_CDN`) — correct | none | — | KEEP / VERIFIED |
| C8 | `backend/seed_cms.py:84` | P2 | seed | `static.prod-images.../iflip-hero.png` → `files.ihgbrands.com/emergent-images/iflip-hero.png` | low | not verified | BLOCKED (B3) |
| C9 | `backend/seed_cms.py:145` | P5 | seed | `/recovered/artmorph-assets_room-setting.jpg` → CDN | low | not verified | BLOCKED (B3) |
| C10 | `backend/seed_data.json:31674` | P5 | seed | `image_url` `/api/cdn/fc08ef9a8307_car.webp` → `files.ihgbrands.com/uploads_fc08ef9a8307_car.webp` | low | **404** | BLOCKED (B3) |
| — | `backend/seed_data.json:1020,1033` | (preview origin, not CDN) | data | `referrer` = app preview URL, not a CDN asset | none | — | SKIPPED (out of scope) |
| — | `.env:3` / `backend/.env:26` | (preview origin, not CDN) | config | `NEXT_PUBLIC_BASE_URL` / `FRONTEND_URL` = app origin | none | — | SKIPPED (out of scope) |

## Module/route removals
| # | Item | Dependents | Removal plan | Status |
|---|---|---|---|---|
| R1 | `/api/media/{path}` route + `_STORAGE_BASE` + `_get_storage_key` (`homepage.py:20,38-93`) | 0 frontend callers; 2 DB values (`homepage_content.hero.poster_image`, `.video_urls[1]`) | (A) replace body with 301→CDN, or (B) delete after rewriting the 2 DB values — both need target assets to exist on CDN first | BLOCKED (B1) |
| R2 | `object_storage.py` module | `spec_substitution.py` only | Remove only if spec uploads are repointed to IHG CDN; else keep | BLOCKED (B2) |

## Allowlist (intentionally kept)
| File | Reason |
|---|---|
| `backend/migrate_to_ihgbrands.py` | Migration script (defines old→new rules) |
| `backend/migrate_media_urls.py` | Migration script (`/api/cdn/`→CDN) |
| `backend/migrate_urls.py` | Migration script |
| `backend/upload_recovered.py` | Legacy media-recovery script (writes `/recovered/`); not wired into runtime |
| `backend/routes/redirects.py` | Already migrated — serves the 301 **to** `files.ihgbrands.com` |
| `backend/tests/test_cdn_integration.py` | Test — `/api/cdn/` behavior |
| `backend/tests/test_media_migration.py` | Test — `/api/cdn/` migration coverage |
| `backend/tests/test_media_recovery.py` | Test — `/recovered/` coverage |
| `backend/tests/test_iteration125_static_server.py` | Test — `/api/media` proxy coverage |
| `backend/tests/test_iteration166_object_storage_unit.py` | Test — object-storage unit |
| `backend/tests/test_brightluxx_fixes.py` | Test — `/api/cdn/` redirect |
| `backend/tests/test_iteration_37_hero_videos.py` | Test — hero / `/api/cdn/` |
| `backend/tests/test_prerender.py` | Test — uses preview BASE_URL default |
| `backend/tests/test_internal_links.py` | Test — uses preview BASE_URL default |
| `backend/tests/test_seo_bulk_alt.py` | Test — uses preview BASE_URL default |
| `.env`, `backend/.env` (app-origin URLs only) | `NEXT_PUBLIC_BASE_URL` / `FRONTEND_URL` are the app origin, not CDN assets |

## Blockers / NEEDS_DECISION
- **B1 (blocker):** `/api/media` assets 404 on CDN under every tested path (`videos_hero-video-ede053db.mp4`, `brightluxx/videos/...`, `images_hero-poster.webp`, `brightluxx/images/...`). Need correct CDN path, or upload the assets, before C2/C3/R1 and the 2 DB values can proceed.
- **B2 (decision):** `object_storage.py` is a write/upload path (spec submissions). Repoint uploads to IHG CDN (`cdn_upload.py` SSH server) or leave as-is? (`INTEGRATION_PROXY_URL` is not set in the backend process env, so uploads would already fail at runtime.)
- **B3 (decision/blocker):** Seed targets unverified/404 — `seed_cms.py:84` (static.prod-images `iflip-hero.png`), `seed_cms.py:145` (`/recovered/...`), `seed_data.json:31674` (`/api/cdn/...car.webp` → 404). Also confirm `seed_cms.py` is still used (runtime seed is `seed_migration.run_seed` over `seed_data.json`).
- **B4 (decision):** `/api/media` strategy — delete proxy + rewrite 2 DB values to direct CDN, OR keep route as a 301→CDN? (No frontend currently calls `/api/media`.)
- **B5 (decision):** Confirm hero video replacement `files.ihgbrands.com/videos_hero-video-converted.mp4` (200) is the intended swap for the hardcoded `.MOV`.

### Notes / follow-ups
- `next.config.ts`: no `images.remotePatterns/domains`, app uses plain `<img>/<video>` (not `next/image`), and there is **no CSP** header → **no config change needed** to allow the CDN domain. No Emergent hosts in `next.config.ts`; `wrangler.toml` not present (Cloudflare toolchain removed).
- MongoDB (not a code file, recorded for Phase 2): `homepage_content.hero.poster_image = /api/media/images/hero-poster.webp` and `hero.video_urls[1] = /api/media/videos/hero-video-ede053db.mp4` — both BLOCKED by B1. The current Next.js `HomeVideoHero` uses its own hardcoded poster/video, so these DB fields may be unused by the live frontend.

### Status legend: TODO · DOABLE · DONE · VERIFIED · BLOCKED · SKIPPED · KEEP

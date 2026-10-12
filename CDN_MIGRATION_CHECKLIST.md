# Emergent → files.ihgbrands.com Migration Checklist

> Phase 1 = DETECTION ONLY (read-only). Nothing in the app has been changed.
> Repo layout note: the Next.js app lives at repo root (`/app`), the FastAPI backend at `/app/backend`.
> There is **no** `/app/frontend` (CRA) or `/app/nextjs` or `/app/scripts` dir in this repo — the known-locations
> list in the task referred to the original backup layout. Confirmed actual paths below.

## Summary
- Code hits (raw grep): **100** across 24 files — see `migration/cdn_url_scan_before.txt`
- Migration-relevant **runtime/config code** items: **6**
- Migration-relevant **seed** items: **4**
- **MongoDB** items needing change: **2** (both in `homepage_content.hero`)
- Allowlisted (intentionally kept): migration scripts (3), test files (10), already-migrated redirect route (1), app-origin env URLs (2), legacy recovery script (1)
- **Blockers / NEEDS_DECISION: 5**
- Good news: live MongoDB is already **99% migrated** (373 CDN string-values, only 2 emergent refs left). Embedded `public/_data/legacy-pages.json` is **fully migrated** (644 CDN URLs, 0 emergent). All 20 sampled live CDN URLs return HTTP 200.

## URL mapping rules
| Pattern | Old form | New form | Confidence |
|---|---|---|---|
| P1 objstore | `https://integrations.emergentagent.com/objstore/api/v1/storage/objects/brightluxx/<path>` (reached via the `/api/media` proxy) | direct `https://files.ihgbrands.com/<?>` | **LOW / NEEDS_DECISION** — guessed target paths 404 |
| P2 static.prod-images | `https://static.prod-images.emergentagent.com/jobs/<job>/images/<name>` | `https://files.ihgbrands.com/emergent-images/<name>` (per `migrate_to_ihgbrands.py`) | MEDIUM — specific file (`iflip-hero.png`) not verified on CDN |
| P3 customer-assets | `https://customer-assets-*.emergentagent.net/.../a1d6k1sy_brightluxx%20video.MOV` | `https://files.ihgbrands.com/videos_hero-video-converted.mp4` | MEDIUM — candidate exists (HTTP 200) but content-equivalence unconfirmed; note MIME changes MOV→MP4 |
| P4 /api/media | relative `/api/media/<path>` → backend proxy → Emergent object storage `brightluxx/<path>` | direct `https://files.ihgbrands.com/<path>` (OR keep route but 301-redirect it) | **LOW / BLOCKED** — target assets 404 on CDN |
| P5 /api/cdn | `/api/cdn/<file>` | 301 → `https://files.ihgbrands.com/uploads_<file-flattened>` (already implemented in `redirects.py`) | HIGH for the redirect mechanism; the resolved `uploads_*` object may still 404 |
| P5 /recovered | `/recovered/<file>` | `https://files.ihgbrands.com/<file>` (per `migrate_to_ihgbrands.py`) | LOW — targets unverified |

## Code items
| # | File:Line | Pattern | Category | Proposed change | Risk | Target verified (HTTP) | Status |
|---|---|---|---|---|---|---|---|
| C1 | `components/home-video-hero.tsx:6` | P3 | runtime | Replace `HERO_VIDEO` customer-assets `.MOV` with `https://files.ihgbrands.com/videos_hero-video-converted.mp4`; change `<source type>` `video/quicktime`→`video/mp4` | med (is mp4 same content?) | candidate **200** | NEEDS_DECISION |
| C2 | `backend/routes/homepage.py:20` | P1 | config/runtime | `_STORAGE_BASE` constant feeding `/api/media` proxy — remove or repoint; coupled to C3 | med | n/a | BLOCKED (see B1/B4) |
| C3 | `backend/routes/homepage.py:38-93` | P4 | runtime route | `/api/media/{path}` proxy. No frontend callers found. Option A: convert to 301→`files.ihgbrands.com/<path>`; Option B: delete route + rewrite the 2 DB values | high | targets **404** | BLOCKED (B1/B4) |
| C4 | `backend/object_storage.py` (whole) + `backend/routes/spec_substitution.py:13,56` | P1 | runtime (upload/write path) | Repoint spec-file uploads from Emergent object storage to the IHG CDN (`cdn_upload.py` SSH server) or keep | high | n/a | NEEDS_DECISION (B2) |
| C5 | `backend/server.py:96` | P4 | config | `"/api/media"` entry in `_CACHEABLE` set — remove iff C3 route removed | low | n/a | DOABLE (depends on C3) |
| C6 | `backend/routes/redirects.py:12,15-23` | P5 | runtime route | Already points to `https://files.ihgbrands.com` (`EXTERNAL_CDN`) — correct target | none | — | KEEP / VERIFIED |
| C7 | `backend/seed_cms.py:84` | P2 | seed | `static.prod-images.../iflip-hero.png` → `files.ihgbrands.com/emergent-images/iflip-hero.png` | low | not verified | NEEDS_DECISION (B3) |
| C8 | `backend/seed_cms.py:145` | P5 | seed | `/recovered/artmorph-assets_room-setting.jpg` → CDN | low | not verified | NEEDS_DECISION (B3) |
| C9 | `backend/seed_data.json:31674` | P5 | seed | `image_url` `/api/cdn/fc08ef9a8307_car.webp` → `files.ihgbrands.com/uploads_fc08ef9a8307_car.webp` | low | **404** | BLOCKED (B3) |
| C10 | `backend/seed_data.json:1020,1033` | (preview URL, not CDN) | seed/data | `referrer` = app preview origin — NOT a CDN asset | none | — | SKIPPED (out of scope) |

## Module/route removals
| # | Item | Dependents | Removal plan | Status |
|---|---|---|---|---|
| R1 | `/api/media/{path}` route (`homepage.py:38-93`) + `_STORAGE_BASE`, `_get_storage_key` | 0 frontend callers; 2 DB values (`homepage_content.hero.poster_image`, `.video_urls[1]`) | Either (A) replace route body with 301→CDN, or (B) delete route after rewriting the 2 DB values to direct CDN URLs. Both require the target assets to exist on the CDN first. | BLOCKED (B1) |
| R2 | `object_storage.py` module | `spec_substitution.py` (upload path) | Only remove if spec uploads are repointed to IHG CDN; else keep | NEEDS_DECISION (B2) |

## MongoDB items
| # | Collection | Field path | Count | Proposed change | Status |
|---|---|---|---|---|---|
| M1 | `homepage_content` | `hero.poster_image` = `/api/media/images/hero-poster.webp` | 1 | → direct `files.ihgbrands.com/...` (exact path unknown) | BLOCKED (B1) — target 404. Note: current Next.js `HomeVideoHero` uses its own hardcoded poster, so this DB field may be unused by the live frontend |
| M2 | `homepage_content` | `hero.video_urls[1]` = `/api/media/videos/hero-video-ede053db.mp4` | 1 | → direct CDN; `video_urls[0]` is already `files.ihgbrands.com/videos_hero-video-converted.mp4` (200) | BLOCKED (B1) — target 404 |

(Entire-DB scan: 373 values already on `files.ihgbrands.com`; **no** P1/P2/P3/P5 or `/api/cdn//recovered/` anywhere in live data.)

## Allowlist (intentionally kept)
| File | Reason |
|---|---|
| `backend/migrate_to_ihgbrands.py` | Migration script (defines old→new rules) |
| `backend/migrate_media_urls.py` | Migration script (`/api/cdn/`→CDN) |
| `backend/migrate_urls.py` | Migration script |
| `backend/upload_recovered.py` | Legacy media-recovery script (writes `/recovered/`); not wired into runtime |
| `backend/routes/redirects.py` | Already migrated — serves the 301 **to** `files.ihgbrands.com` |
| `backend/tests/test_cdn_integration.py` | Test — asserts `/api/cdn/` behavior |
| `backend/tests/test_media_migration.py` | Test — `/api/cdn/` migration coverage |
| `backend/tests/test_media_recovery.py` | Test — `/recovered/` coverage |
| `backend/tests/test_iteration125_static_server.py` | Test — `/api/media` proxy coverage |
| `backend/tests/test_iteration166_object_storage_unit.py` | Test — object storage unit |
| `backend/tests/test_brightluxx_fixes.py` | Test — `/api/cdn/` redirect |
| `backend/tests/test_iteration_37_hero_videos.py` | Test — hero/`/api/cdn/` |
| `backend/tests/test_prerender.py` | Test — uses preview BASE_URL default |
| `backend/tests/test_internal_links.py` | Test — uses preview BASE_URL default |
| `backend/tests/test_seo_bulk_alt.py` | Test — uses preview BASE_URL default |
| `.env` `NEXT_PUBLIC_BASE_URL` | App preview origin, not a CDN asset |
| `backend/.env` `FRONTEND_URL` | App preview origin, not a CDN asset |

## Blockers / NEEDS_DECISION
- **B1 (blocker):** The `/api/media` assets are not resolvable on the CDN. Tested and 404:
  - `files.ihgbrands.com/videos_hero-video-ede053db.mp4`, `.../brightluxx/videos/hero-video-ede053db.mp4`
  - `files.ihgbrands.com/images_hero-poster.webp`, `.../brightluxx/images/hero-poster.webp`
  Need the correct CDN path, or these assets must be uploaded to `files.ihgbrands.com` before C3/M1/M2 can proceed.
- **B2 (decision):** `object_storage.py` is a **write/upload** path (spec-file submissions) to Emergent object storage. Migrating it means repointing uploads to the IHG CDN (SSH file server via `cdn_upload.py`). Confirm whether to migrate the upload path or leave it.
- **B3 (decision/blocker):** Seed values (`seed_cms.py:84` static.prod-images `iflip-hero.png`; `seed_cms.py:145` `/recovered/...`; `seed_data.json:31674` `/api/cdn/...car.webp`) point at assets whose CDN targets are unverified / 404. Confirm whether `seed_cms.py` is still used (runtime seed is `seed_migration.run_seed(seed_data.json)`) and provide correct targets.
- **B4 (decision):** For `/api/media` — prefer removing the proxy route and rewriting the 2 DB values to direct CDN URLs, OR keeping the route but turning it into a 301 redirect to `files.ihgbrands.com`? (Depends on B1 assets existing.)
- **B5 (decision):** Confirm the C1 hero video: is `files.ihgbrands.com/videos_hero-video-converted.mp4` the intended replacement for the `.MOV`?

## Follow-ups / notes
- `next.config.ts` has **no** `images.remotePatterns/domains` and the app uses plain `<img>/<video>` (not `next/image`), and there is **no CSP** header in the app — so **no config change is needed** to allow the `files.ihgbrands.com` domain.
- `INTEGRATION_PROXY_URL` (used by `object_storage.py`) is set in the Next.js supervisor env but not in the backend process env — object storage uploads would currently fail at runtime regardless.
- Raw scan saved to `migration/cdn_url_scan_before.txt`; live-CDN URL samples to `migration/ihg_url_samples.txt`; DB scanner at `migration/scan_db.py`.

---
### Status legend: TODO · IN_PROGRESS · DONE · VERIFIED · BLOCKED · SKIPPED

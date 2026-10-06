# Brightluxx — Fix the Production Deploy (build-time backend fetch)

Make the production `next build` succeed by stopping backend-dependent pages from fetching during static prerendering.
The deploy currently fails because one page calls the backend at build time, when no backend is reachable.

## Who it's for
The agent fixing the failing Emergent deployment of the already-running Brightluxx app. Preview works; only the production build step fails.

## The problem (confirmed from build logs, 3 identical failures)
During `next build`, Next.js prerenders 241 pages. The page `/luxury-home-cinema` runs a server-side `fetch()` to the backend while building. Inside Cloud Build the backend is not running, so the fetch is refused (`ECONNREFUSED`) and the whole build aborts at `180/241`. Compile and TypeScript both pass — the failure is only build-time data fetching.

## The fix
- In `app/luxury-home-cinema/page.tsx`, add `export const dynamic = 'force-dynamic';` so the page renders at request time (backend live) instead of at build time.
- This mirrors what the other backend-backed routes already do: `/products`, `/products/[slug]`, `/compare`, and `/contact` all already export `dynamic = 'force-dynamic'`.
- No other route needs changing: the catch-all `[...slug]` pages, `sitemap.ts`, `robots.ts`, and the home page read only the embedded content bundle from disk (no backend call at build), so they stay statically prerendered.

## Verification
- Run `yarn build` with the backend stopped and confirm it completes without `ECONNREFUSED`.
- Confirm `/luxury-home-cinema` still renders its home-cinema products at request time once the backend is up.
- Then redeploy.

## Decisions worth noting
- This is a one-line, single-file change; no Docker/manifest/platform changes.
- Backend logic is untouched. The page simply moves from static prerender to on-request rendering, which is correct for data that comes from the live backend.
- Production will talk to Atlas MongoDB via the deployed backend; this fix does not depend on which database is used, only on not calling the backend during the build.

## Implementation phases
### Phase 1 — Deploy fix (do now)
Apply the `force-dynamic` export to `app/luxury-home-cinema/page.tsx`, verify the build passes with the backend down, redeploy.

### Phase 2 — Safety sweep (optional, later)
Audit every server component/route for build-time backend calls and standardize on `force-dynamic` (or try/catch fallback) so a down backend can never abort a future build.

### Phase 3 — Production deployment hardening (later)
Confirm the production API origin/env wiring and health checks after the successful deploy.

## Assumptions
- Only `/luxury-home-cinema` fetches the backend at build time; all other routes are already safe (verified by reading the route files).
- Keeping the page dynamic (not statically cached) is acceptable; SEO metadata on the page is static and unaffected.
- The user redeploys after the fix; no automated test suite is required for this change beyond a local build check and a runtime render check.

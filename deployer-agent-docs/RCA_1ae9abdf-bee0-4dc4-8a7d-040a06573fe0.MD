# RCA — run 1ae9abdf-bee0-4dc4-8a7d-040a06573fe0 (nextjs-revamp-2)

## Outcome
Deploy failed at **build_image** (`next build`). Not a manifest/platform fault — a **source-level** build failure. Nothing was promoted; no prior version existed (initial deploy), so there is nothing live.

## What failed (verbatim from build log)
```
#15 ... Generating static pages using 7 workers (180/241)
Error occurred prerendering page "/luxury-home-cinema".
[TypeError: fetch failed] {
  digest: '3227098399',
  [cause]: AggregateError: ... { code: 'ECONNREFUSED', [errors]: [ [Error], [Error] ] }
}
Export encountered an error on /luxury-home-cinema/page: /luxury-home-cinema, exiting the build.
⨯ Next.js build worker exited with code: 1
ERROR: process "/bin/sh -c yarn build" did not complete successfully: exit code: 1
```
Template: `nextjs_mongo_shadcn_base_image` (Next.js 16.3.2, App Router, Turbopack). 241 pages are being statically generated at build time.

## Root cause
The app statically prerenders (SSG) its content pages at **build time**. The page `/luxury-home-cinema` (and the route that generates all 241 slug pages) performs a server-side `fetch()` to the backend API while `next build` runs. Inside Cloud Build the FastAPI/MongoDB backend is **not running**, so the fetch returns `ECONNREFUSED` and Next.js aborts the whole build (one prerender error fails the build).

This will fail on every build as long as those pages fetch live data during static generation — it is independent of tier, secrets, or infra.

## Fix (Code — E1 to apply in the source repo, then re-trigger deploy)
Make the data-fetching route(s) render **at request time** instead of at build time, so the fetch runs when the backend is live. Pick whichever matches the codebase:

1. **Preferred — force dynamic rendering** on the dynamic content route (the segment that renders `/luxury-home-cinema`, likely `app/[slug]/page.tsx` or similar). Add at module top level:
   ```ts
   export const dynamic = 'force-dynamic';
   ```
   If the route uses `generateStaticParams()` to pre-build all 241 slugs, remove it (or have it return `[]`) so pages are rendered on demand rather than prerendered at build.

2. **Alternative — make the build tolerant** if SSG is desired: wrap the build-time `fetch()` in try/catch and return a fallback/empty payload on failure so a down backend does not abort the build, and/or set `export const dynamicParams = true`.

3. If the fetch targets the backend via an env URL (e.g. `process.env.NEXT_PUBLIC_*` / internal base URL), note it resolves to an unreachable host during build — do not rely on the backend being up at build time.

Scan for every route/page that fetches backend data during render and apply the same treatment; `/luxury-home-cinema` is just the first one the build hit (it failed at 180/241, so others may also be affected).

## Verification status
Diagnosed from the Cloud Build log. **Not reproduced in the eph sandbox** — the sandbox pod failed to start repeatedly (infra-side `pod_not_running` / deleted container), so an in-pod repro was not possible. The build log cause is unambiguous.

## Next step
E1: apply the code fix in the source, then re-trigger the deploy. Do not retry the pipeline on unchanged source — it will fail identically.

# Progress

## 2026-05-16

- Loaded `$planning-with-files` alias and the project H5 acceptance standard.
- Confirmed persistent planning files were missing.
- Created `task_plan.md`, `findings.md`, and `progress.md`.
- Set Phase 2 direction: unify remaining P2 pages using `Nexus` + `Community` as the visual baseline.
- Audited the remaining legacy-template pages and grouped them by shell pattern: standalone `.device` pages and existing `.nexus-shell-device` pages.
- Added a shared runtime tagging layer in `frontend/miro/P2/src/utils/visual-unification.js`.
- Added shared visual overrides in `frontend/miro/P2/src/styles/legacy-unification.css` and wired them through `src/main.js`.
- Updated `src/utils/legacy-page.js` so visual tagging happens after template DOM mount.
- During validation, found and fixed a navigation lifecycle bug by keeping legacy route helpers mounted for the full active page lifetime.
- Ran `npm run build` successfully in `frontend/miro/P2`.
- Captured updated screenshots and smoke/interactions under `archive/validation/2026-05-16-P2-visual-unification`.
- Executed P2 hardening plan and saved it under `docs/superpowers/plans/2026-05-16-P2-hardening.md`.
- Fixed archive and result top-left back buttons.
- Added P2 local demo fallback for generation when no API Base URL is configured.
- Added demo selection fallback for direct `#/generation` validation so the route is not a dead end.
- Intercepted legacy `window.location.replace(...)` navigation so generation stays inside the P2 router.
- Eager-loaded hidden community market icons to eliminate false broken-image states.
- Disabled pointer events on transparent capture stack-photo decorations.
- Re-ran `npm run build` successfully in `frontend/miro/P2`.
- Ran final full H5 acceptance under `archive/validation/2026-05-16-P2-full-acceptance`; final report passed.
- Kept formal entry unchanged pending Vercel preview and deployed path validation.
- Deployed a P2 validation candidate to Vercel as `instant-food-p2-vercel-preview`.
- Used a temporary Vercel share URL to validate the protected deployment without changing the formal frontend project.
- Ran Vercel preview acceptance under `archive/validation/2026-05-16-P2-vercel-preview`; final report passed.
- Confirmed formal entry remains uncut after preview validation.
- Built `frontend/miro/P2` again and copied the latest `dist` bundle into `frontend/p2/`.
- Switched `frontend/index.html` to redirect to `./p2/`.
- Updated `frontend/vercel.json` root redirect to `/p2/` while preserving the backend API rewrite.
- Fixed P2 legacy asset resolution so the same bundle works under the `/p2/` subpath.
- Ran local formal-entry smoke under `archive/validation/2026-05-16-P2-production-entry-smoke`; final local report passed.
- Deployed a frontend-entry validation preview to Vercel and ran entry smoke; final Vercel report passed.
- Added a shared Beijing-time updater in `frontend/miro/P2/src/utils/legacy-page.js` so legacy status bars and the Nexus date use `Asia/Shanghai` on every page mount and refresh every 30 seconds.
- Replaced the Nexus remote feature image dependency with a local bundled image and kept a generic remote image fallback to avoid broken-image regressions.
- Rebuilt `frontend/miro/P2`, copied the latest build into `frontend/p2/`, and reran local formal-entry Beijing-time smoke under `archive/validation/2026-05-16-P2-beijing-time`; final local report passed.
- Deployed a refreshed frontend-entry preview to Vercel and reran route/image/time/overlay checks; final Vercel Beijing-time report passed.
- Fixed the auth topbar regression: removed the inherited black miniapp gradient, stabilized the title font rendering, and replaced the back icon ligature with inline SVG.
- Scanned other key P2 routes for the same topbar/icon-font issue under `archive/validation/2026-05-16-P2-topbar-regression-scan`.
- Added a per-mount Material icon guard in `frontend/miro/P2/src/utils/legacy-page.js` so legacy pages hide ligature text when icon fonts are slow or unavailable.

## 2026-05-17

- Fixed the P2 onboarding CTA slider so the knob visibly follows left-to-right drag movement and navigates only after pointer release.
- Moved onboarding slider pointer move/up/cancel handling to `window` level so preview/mobile drags are not lost when the pointer leaves the rail.
- Rebuilt `frontend/miro/P2`, copied the latest build into `frontend/p2/`, and deployed a refreshed Vercel preview.
- Ran local and Vercel onboarding slider validation under `archive/validation/2026-05-17-P2-onboarding-slider`; both reports passed.
- Reproduced the remaining touch issue: a legacy ready-state observer could still navigate before release, making the slider feel non-draggable.
- Removed the legacy ready-state observer and added native `touchstart/touchmove/touchend` handling for the onboarding CTA slider.
- Rebuilt `frontend/miro/P2`, recopied `frontend/p2/`, deployed a new Vercel preview, and ran real touch validation under `archive/validation/2026-05-17-P2-onboarding-touch-fix`; local and Vercel reports passed.
- Tightened the onboarding grab interaction so the white `即刻料理` handle and the white trailing frame are both directly updated during drag.
- Expanded drag start to the whole CTA shell capture phase so the handle, trail, and rail can all initiate dragging.
- Rebuilt, recopied `frontend/p2/`, deployed a new Vercel preview, and validated knob-start plus rail/trail-start drags under `archive/validation/2026-05-18-P2-onboarding-grab-drag`; local and Vercel reports passed.
- Fixed the onboarding slider right-edge clipping by adding a visual endpoint gap and clamping the trailing frame width.
- Replaced cached slider endpoint measurement with current `getBoundingClientRect()` bounds during drag so Vercel CSS timing cannot create stale max offsets.
- Rebuilt, recopied `frontend/p2/`, deployed a new Vercel preview, and validated slider boundary under `archive/validation/2026-05-18-P2-onboarding-slider-boundary`; final local and Vercel reports passed.
- Replaced the onboarding exit transition's directional page shift with a neutral scale/opacity/brightness transition.
- Fixed settings preference rows so legacy `href="#"` clicks no longer clear the hash and route back to onboarding.
- Added a local settings picker bottom sheet for preference rows and validated local plus Vercel behavior under `archive/validation/2026-05-18-P2-settings-picker-route-fix`.
- Validated the onboarding exit transition locally and on Vercel under `archive/validation/2026-05-18-P2-onboarding-exit-motion`.
- Ran an additional Vercel all-row settings regression covering six selectable preference rows plus the clear-archive row; all stayed on `#/settings`.

## 2026-05-21

- Reset P2 settings profile to a real initial state: nickname is unset, avatar is empty, background keeps the cafe default, all preference rows start as `未设置`, and `风味准则` starts at `0`.
- Added localStorage-backed editing for nickname, avatar image, and profile background image on `#/settings`.
- Migrated `instantFoodProfileConstraints` to schema v2 so old hard-coded defaults no longer reappear from previous sessions.
- Rebuilt `frontend/miro/P2`, recopied the full `dist` output into `frontend/p2/`, including `runtime-pages/`.
- Ran local settings profile validation and Vercel P2 preview validation under `archive/validation/2026-05-21-P2-settings-profile-initial-editing`; both reports passed.
- The formal `frontend` project preview deploy path produced Vercel `UNKNOWN` deployments during upload/build-state resolution, so the usable preview was deployed through the existing `instant-food-p2-vercel-preview` project without promoting production.
- Reworked the P2 settings home into a mini-program personal-center layout: no background hero, no `更换背景` button, left account profile, balance card, three meaningful preference constraints, and service/compliance entries.
- Added settings child routes for account service, recharge, membership, customer service, terms/rules, privacy information, and about pages, including second/third-level detail pages.
- Rebuilt `frontend/miro/P2`, recopied `frontend/p2/`, deployed a new P2 preview, and validated local plus Vercel settings subpage flows under `archive/validation/2026-05-21-P2-settings-subpages`; both reports passed.
- Corrected the settings visual direction after the reference-style mismatch: restored `#/settings` and all new settings subpages to the P2 black/green glass system while keeping the account/service/rules/privacy/about information architecture.
- Rebuilt `frontend/miro/P2`, recopied `frontend/p2/`, deployed a refreshed P2 preview, and validated local plus Vercel style-restore flows under `archive/validation/2026-05-21-P2-settings-style-restore`; both reports passed.
- Added shared P2 typography tokens for font family, size, weight, and line-height in `frontend/miro/P2/src/styles/tokens.css`.
- Updated settings home, settings picker/profile editor, and settings child pages to consume global typography tokens instead of page-local numeric typography rules.
- Updated `legacy-unification.css` so compatibility font-family and weight utilities reference global P2 typography tokens.
- Rebuilt `frontend/miro/P2`, recopied `frontend/p2/`, deployed a refreshed P2 preview, and validated local plus Vercel typography flows under `archive/validation/2026-05-21-P2-typography-token-unification`; both reports passed.

## 2026-05-22

- Expanded P2 typography token migration from settings-only to all active H5 routes: onboarding, auth, nexus, community, capture, archive, settings, workbench, generation, and result.
- Added primitive and semantic typography tokens for legacy display sizes, row/card/body/control text, chips, captions, CTA text, and Material icon sizes.
- Ran the all-pages typography hardcode scan; `archive/validation/2026-05-21-P2-typography-token-unification/all-pages-typography-scan-after-global-tokens.json` reports `violationCount = 0`.
- Rebuilt `frontend/miro/P2`, recopied `dist` into `frontend/p2/`, and refreshed the `instant-food-p2-vercel-preview` deployment.
- Fixed the smoke script evidence output to use relative screenshot paths and to wait for visible images before route switching, avoiding false `ERR_ABORTED` image failures in protected Vercel previews.
- Reran local and Vercel H5 typography smoke over 12 routes plus 5 interactions; both reports passed with no page errors, console messages, failed requests, broken images, iframes, or transparent blockers.

## 2026-05-25

- Expanded P2 design tokens from typography-only into global UI system tokens for page/device background, surfaces, dock, CTA, cards, chips, icon buttons, spacing, radius, shadows, blur, and motion.
- Updated `frontend/miro/P2/src/utils/visual-unification.js` so all active H5 routes receive consistent page IDs and reusable component classes.
- Updated `frontend/miro/P2/src/styles/legacy-unification.css` so Nexus, Community, Capture, Archive, Settings, Workbench, Generation, Result, Auth, and Onboarding share the same black/green glass component language.
- Added a capture-page guard: `确认拍摄` is disabled by default, stays on `#/capture` with no image, and only enables after a photo is captured or uploaded.
- Rebuilt `frontend/miro/P2`, recopied `dist` into `frontend/p2/`, and refreshed the direct Vercel P2 preview.
- Ran local and Vercel H5 global UI smoke over 12 routes plus 6 interactions; both reports passed with no page errors, blocking console messages, failed requests, broken images, iframes, or transparent blockers.
- Fixed the P2 capture page's remaining visual regression: removed the old green dynamic-island dot and lifted the camera fallback panel so it no longer collides with the upload/shutter/gallery controls.
- Added geometry checks to the H5 smoke for capture spacing, then reran local and Vercel validation under `archive/validation/2026-05-25-P2-capture-spacing-fix`; both reports passed.
- Added runtime body page markers in `frontend/miro/P2/src/utils/legacy-page.js` so legacy body styles can be scoped and audited consistently per P2 route.
- Expanded `frontend/miro/P2/src/utils/visual-unification.js` to tag status bars and semantic typography groups for page titles, section labels, row titles, row metadata, controls, and CTAs.
- Tightened `frontend/miro/P2/src/styles/legacy-unification.css` to enforce mobile body safe area, shell width, topbar padding, 44px icon buttons with 16px radius, shared typography roles, disabled CTA state, and capture fallback/control spacing.
- Created `archive/validation/2026-05-25-P2-global-ui-hard-audit/validate-global-ui-hard-audit.cjs` to test global UI rules with computed DOM styles instead of relying only on screenshots.
- Rebuilt `frontend/miro/P2`, recopied `dist` into `frontend/p2/`, deployed Vercel preview `instant-food-p2-vercel-preview-c9idfe2bn`, and ran local plus Vercel hard audits; both passed across 12 routes and 7 interactions.

## 2026-05-26

- Fixed the remaining P2 community visual mismatch by overriding the old page-local category grid, heavy topbar, oversized card rhythm, and section controls from `legacy-unification.css`.
- Rebuilt `frontend/miro/P2`, recopied `dist` into `frontend/p2/`, and validated the synced bundle locally through `http://127.0.0.1:41820/p2/`.
- Deployed Vercel preview `instant-food-p2-vercel-preview-nl6z8a5s5` and enabled a share URL for browser validation.
- Ran community-specific Playwright validation and the global hard audit locally plus on Vercel under `archive/validation/2026-05-26-P2-community-visual-alignment`; all reports passed.
- Promoted the latest P2 static deployment to Vercel production alias `https://instant-food-p2-vercel-preview.vercel.app/`.
- Ran production community audit and production global hard audit under `archive/validation/2026-05-26-P2-production-public-deploy`; both reports passed.

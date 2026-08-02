# Findings

## 2026-05-16

- User confirmed continuing after Phase 1; work now proceeds to Phase 2 visual unification.
- Required skill `$planning-with-files` resolves to `planning-with-files-zh`; persistent files are required in project root.
- H5 acceptance standard requires validation artifacts under `archive/validation/<date>-<topic>`.
- Formal entry remains `frontend/index.html` and `frontend/vercel.json`; do not switch it during this work.
- Current P2 visual baseline is `Nexus` + `Community`: black/green glass, rounded cards, mini-app topbar, bottom dock.
- A shared P2 visual unification layer now exists in `frontend/miro/P2/src/utils/visual-unification.js` and `frontend/miro/P2/src/styles/legacy-unification.css`.
- Validation exposed a real lifecycle bug in legacy page navigation: patched inline callbacks were calling `window.__MIRO_SET_LOCATION__` after the helper had already been removed.
- Fixed by keeping `__MIRO_ROUTE__` and `__MIRO_SET_LOCATION__` bound for the full mounted page lifetime instead of only during inline script execution.
- Current audited pages `capture/archive/settings/workbench/generation/result` all render with a `414 x 896` shell and `brokenImages = 0`.
- Full acceptance initially exposed real P1-level issues: community hidden market icons were reported as broken images, archive/result top-left back buttons were inert, generation direct route could fail without local backend data, and legacy `window.location.replace()` escaped the P2 router.
- Final full acceptance report `archive/validation/2026-05-16-P2-full-acceptance/full-acceptance-report-final.json` has `passed = true`, with no route issues, no interaction issues, no console messages, and no page errors.
- Vercel preview report `archive/validation/2026-05-16-P2-vercel-preview/vercel-preview-acceptance-report.json` has `passed = true`, with no route issues, no direct-link issues, no interaction issues, no console messages, and no page errors.
- The Vercel deployment is protected by Vercel authentication; browser validation required a temporary share URL. This affects viewing convenience, not P2 runtime correctness.
- The minimum formal-entry switch initially exposed a subpath bug: legacy assets and runtime scripts assumed root hosting and failed under `/p2/`.
- Fixed subpath hosting by resolving legacy assets and runtime-page scripts relative to the Vite base URL.
- Formal-entry smoke report `archive/validation/2026-05-16-P2-production-entry-smoke/vercel-entry-smoke-report.json` has `passed = true`, with no route issues, no direct-link issues, no interaction issues, no console messages, and no page errors.
- Nexus previously rendered a fixed prototype date/time (`9:41`, `周一，11 月 25 日`). The P2 legacy mount layer now injects current Beijing time/date from `Asia/Shanghai` and updates mounted pages every 30 seconds.
- Beijing-time validation report `archive/validation/2026-05-16-P2-beijing-time/vercel-beijing-time-report.json` has `passed = true`, with `brokenImages = 0`, `pageErrors = 0`, `iframeCount = 0`, `consoleMessages = 0`, and `transparentBlockers = 0`.
- The Nexus remote Google image dependency can fail acceptance in protected/headless environments; the current P2 build uses a local bundled Nexus feature image and keeps a generic fallback for remaining legacy remote images.
- Auth topbar inherited a global `.wx-miniapp-nav` black gradient from `wechat-unified.css`; it is now explicitly transparent on the auth page.
- Several P2 legacy pages still use Material Symbols ligature text internally. The runtime now detects unusable icon fonts per mounted page and hides ligature text instead of exposing English words.
- Topbar regression report `archive/validation/2026-05-16-P2-topbar-regression-scan/topbar-regression-post-fix-report.json` has `passed = true`, with no route issues and no visible ligature pages when icon fonts are blocked.

## 2026-05-17

- The onboarding CTA slider felt inert in preview because the previous implementation could complete navigation during drag and tracked move/up/cancel only on the rail element.
- The current implementation tracks pointer move/up/cancel at window level, keeps the visual drag progress visible, marks ready near the end, and navigates only after release.
- Onboarding slider local and Vercel reports in `archive/validation/2026-05-17-P2-onboarding-slider` both have `passed = true`, with `brokenImages = 0`, `iframeCount = 0`, `pageErrors = 0`, and `consoleMessages = 0`.
- Follow-up touch validation found the real remaining blocker: a legacy `.is-ready` MutationObserver still routed to auth before finger release.
- The onboarding CTA now uses native touch handlers for touchscreens, pointer handlers for mouse/pen, and no longer auto-navigates on ready-state class mutation.
- Touch-fix reports in `archive/validation/2026-05-17-P2-onboarding-touch-fix` both have `passed = true`, including `stayedBeforeRelease = true` and `navigatedAfterRelease = true`.
- User clarified the required behavior: the white `即刻料理` handle and the white trailing frame must be draggable as visible UI, not just produce a route change.
- The current grab-drag fix directly mutates handle transform and trail width, and captures drag starts from the whole CTA shell.
- Grab-drag reports in `archive/validation/2026-05-18-P2-onboarding-grab-drag` both have `passed = true`, with `knobPassed = true` and `railPassed = true`.
- The slider boundary issue was caused by an endpoint that was visually too close to the right rail edge plus stale early measurement on Vercel.
- The endpoint now preserves a right-side visual gap and recalculates bounds from current DOM rectangles during drag.
- Slider boundary final reports in `archive/validation/2026-05-18-P2-onboarding-slider-boundary` have `passed = true`, with `rightGapOk = true` and `trailGapOk = true`.
- Onboarding exit motion previously translated the whole phone shell to the right during release navigation. It now uses a neutral non-directional transition, with local and Vercel reports passing.
- Settings preference rows used legacy `href="#"`, which cleared the hash and fell back to `/onboarding/1`. The settings page now intercepts these rows and opens a picker instead.
- Settings picker reports in `archive/validation/2026-05-18-P2-settings-picker-route-fix` have `passed = true`, including `stayedOnSettings = true` and `clearDidNotRoute = true`.
- Additional Vercel all-row settings report has `allPickerRowsPassed = true`, confirming each selectable preference row opens a picker without route fallback.

## 2026-05-21

- Settings profile had hard-coded identity and preference defaults (`杨`, avatar image, selected preference rows). The current P2 settings page now starts from an unset profile state and only fills values after user edits.
- `instantFoodProfileConstraints` now uses schema version 2. Existing version 1 defaults are intentionally discarded on settings mount so old prototype values do not leak into recipe constraints.
- Avatar and background editing currently persist in localStorage only. This is correct for the no-real-auth prototype, but the future WeChat/login data layer must replace this with account-backed profile storage.
- Local and Vercel settings profile reports in `archive/validation/2026-05-21-P2-settings-profile-initial-editing` both passed with `brokenImages = 0`, `iframeCount = 0`, `pageErrors = []`, and `consoleMessages = []`.
- Formal `frontend` project preview deployment attempts became stuck in Vercel `UNKNOWN` state during upload/build-state resolution. The runtime change was therefore validated on the existing `instant-food-p2-vercel-preview` project, not promoted to production.
- User reference screenshots clarified that service/compliance entries should navigate to child pages rather than popups. P2 now uses route-backed settings subpages for account service, recharge, membership, rules, privacy, and about sections.
- The previous settings background hero was too visually heavy for the personal-center page. The current home removes it entirely and keeps avatar/nickname as the primary account identity area.
- Settings subpage validation in `archive/validation/2026-05-21-P2-settings-subpages` passed locally and on Vercel with no failed requests, broken images, page errors, console messages, or transparent blockers.
- The McDonald's screenshots are reference material for information architecture only, not for visual direction. P2 settings must stay in the black/green glass design system.
- The style-restore validation in `archive/validation/2026-05-21-P2-settings-style-restore` passed locally and on Vercel with dark root backgrounds, no visible `更换背景` button, no settings hero, no broken images, no page errors, and no transparent blockers.
- P2 now has shared typography tokens in `tokens.css` for page titles, row titles, row metadata, controls, tabs, card titles, body text, profile names, KPI values, and icon sizes.
- Settings home and its child pages no longer keep hardcoded local typography values for `font-size`, `font-weight`, or `line-height`; the hardcode scan in `archive/validation/2026-05-21-P2-typography-token-unification/settings-typography-hardcode-scan.json` reports `violations = 0`.
- Typography validation in `archive/validation/2026-05-21-P2-typography-token-unification` passed locally and on Vercel by comparing computed styles against the global tokens.
- The typography token migration now covers all active P2 H5 routes, not only settings. The all-pages scan reports `violationCount = 0`, so page-local raw typography values are no longer the source of truth.
- Protected Vercel preview validation can falsely report `ERR_ABORTED` when the script changes routes before large visible images finish loading. The current smoke waits for visible images and network idle before collecting route metrics.
- Latest local and Vercel H5 typography smoke reports both passed with `P0 = 0`, `P1 = 0`, `brokenImages = 0`, `iframeCount = 0`, `pageErrors = []`, `consoleMessages = []`, and `failedRequests = []`.
- The remaining P2 typography risk is not visual inconsistency but bundle structure: old runtime templates are still bundled into one large Vite chunk, which stays tracked as a later code-splitting cleanup item.

## 2026-05-25

- Community differed visually because some component-level rules still came from page-local template CSS rather than the shared P2 system. The current pass moved shared surface, chip, card, CTA, dock, radius, spacing, shadow, and motion rules into global tokens plus `legacy-unification.css`.
- The bottom dock should be validated as `4` normal navigation items plus one center action, not as five normal nav items. The validation script was corrected to reflect the actual product structure.
- Capture confirmation previously allowed navigation even when no image had been captured or uploaded. The current guard keeps `确认拍摄` disabled until `state.photos.length > 0`, and the smoke now verifies both blocked and enabled states.
- Local and Vercel global UI reports in `archive/validation/2026-05-25-P2-global-ui-system` both passed with `P0 = 0`, `P1 = 0`, `brokenImages = 0`, `iframeCount = 0`, `pageErrors = []`, `blockingConsole = []`, and `failedRequests = []`.
- The remaining structural risk is unchanged: P2 still bundles legacy templates into one large Vite chunk. This does not block the current UI-system pass, but should be handled later as code-splitting/template decomposition work.
- The first global UI pass missed a capture-specific old-template artifact: the dynamic-island green dot and fallback/control overlap were not covered by the initial automated assertions. The capture spacing fix adds explicit geometry checks so this class of collision is now testable.
- Capture spacing validation in `archive/validation/2026-05-25-P2-capture-spacing-fix` passed locally and on Vercel with a 73px measured gap between fallback bottom and capture row top.
- The stricter hard audit found the architectural reason the capture page still looked different: its legacy template kept mobile `body` padding, so the phone shell rendered at `374px` instead of the shared `414px` mobile shell. This is now fixed through runtime body markers and global mobile safe-area overrides.
- Several topbar icon buttons were still being reshaped by page-local `.wx-miniapp-nav` and old template rules. The global system now asserts and enforces `44px x 44px` icon buttons with `16px` radius on compact topbar pages.
- The new hard audit passes locally and on Vercel under `archive/validation/2026-05-25-P2-global-ui-hard-audit`; it verifies 12 routes, 7 interactions, `brokenImages = 0`, `iframeCount = 0`, `pageErrors = []`, `blockingConsole = []`, `blockingRequests = []`, and `transparentBlockers = 0`.

## 2026-05-26

- The reason `#/community` still looked different was not a runtime failure; it retained old-template visual primitives: a 5-column category grid, a heavy topbar slab, and wider page-local rail cards. The previous hard audit covered token geometry and interactions but did not assert this page-level visual rhythm.
- The community page now uses shared chip geometry for categories, transparent compact topbar styling, shared card radius/shadow, card title size `22px / 28px`, and a measured card width of `238px`.
- Community validation in `archive/validation/2026-05-26-P2-community-visual-alignment` passed locally and on Vercel, including category filtering, horizontal rail drag, card detail open/close, bottom navigation, `brokenImages = 0`, `iframeCount = 0`, `pageErrors = []`, and `transparentBlockers = 0`.

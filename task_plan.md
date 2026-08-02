# P2 H5 Refactor Plan

## Goal
Finish `frontend/miro/P2` in two controlled phases:

1. Phase 1 architecture migration: keep UI one-to-one while removing the old nested/iframe runtime architecture.
2. Phase 2 visual unification: use `Nexus` and `Community` as the design baseline and unify remaining pages without switching the formal entry.

## Current Status

| Phase | Status | Notes |
| --- | --- | --- |
| Phase 1: P1/P2 rename | complete | `miro1` -> `P1`, `miro2` -> `P2`. |
| Phase 1: active route migration | complete | Active routes use `runScripts: false` and explicit `onMount`. |
| Phase 1: remove old iframe helper | complete | Removed unused runtime iframe helper from `P2/src`. |
| Phase 2: visual baseline definition | complete | Baseline locked to current `Nexus` + `Community` black/green glass system. |
| Phase 2: visual unification implementation | complete | Added shared `visual-unification` runtime tagging and `legacy-unification.css` for `capture`, `archive`, `settings`, `workbench`, `generation`, `result`. |
| Phase 2: acceptance validation | complete | Built `P2`, captured updated screenshots, and ran direct-route smoke plus core interaction checks under `archive/validation/2026-05-16-P2-visual-unification`. |
| P2 hardening: visual strict alignment | complete | Evidence under `archive/validation/2026-05-16-P2-hardening`. |
| P2 hardening: legacy template debt | complete | Tailwind CDN execution removed for `archive`, `settings`, `workbench`, and `result`; scoped compatibility remains in `legacy-unification.css`. |
| P2 hardening: full H5 acceptance | complete | Final report `archive/validation/2026-05-16-P2-full-acceptance/full-acceptance-report-final.json` passed. |
| P2 hardening: formal entry readiness | complete | Formal entry now redirects to `/p2/`; local and Vercel entry smoke passed. |

## Phase 2 Design Baseline

- Viewport: `414 x 896`.
- Direction: black background, green accent, liquid/glass surfaces, rounded device shell, unified mini-app topbar and bottom dock.
- Preserve page content and interaction intent.
- Formal entry now points to the P2 static bundle under `frontend/p2/`.

## Verification Required

- `npm run build` in `frontend/miro/P2`.
- Direct-route smoke for all active routes.
- Core interaction checks for affected pages.
- Screenshot evidence under `archive/validation/<date>-<topic>`.

## Open Risks

- Phase 2 intentionally changes UI, so it is no longer one-to-one with production baseline.
- Formal entry has been switched locally to `/p2/` and validated through local plus Vercel entry smoke.
- P2 still carries large bundled legacy templates; Vite reports a chunk-size warning after build.
- The Vercel validation deployment remains protected by Vercel Authentication; final public visibility depends on production project settings.

## Latest Addendum: Beijing Time

- Status: complete.
- Scope: P2 status-bar clocks and the Nexus date line now render from `Asia/Shanghai` instead of fixed prototype text.
- Evidence: `archive/validation/2026-05-16-P2-beijing-time`.
- Result: local formal-entry smoke and Vercel preview smoke both passed.

## Latest Addendum: Settings Profile Initial State

- Status: complete.
- Scope: P2 `#/settings` profile identity and preference defaults now start unset, with local editing for nickname, avatar, and background.
- Evidence: `archive/validation/2026-05-21-P2-settings-profile-initial-editing`.
- Result: local static smoke and Vercel P2 preview smoke both passed.
- Note: formal `frontend` project preview deploy attempts were blocked by Vercel `UNKNOWN` deployment state, so the usable review link uses the existing P2 preview project.

## Latest Addendum: Settings Home And Subpages

- Status: complete.
- Scope: P2 `#/settings` home was rebuilt as a mini-program personal center, and account/rules/privacy/about entries now open route-backed child pages instead of popups.
- Evidence: `archive/validation/2026-05-21-P2-settings-subpages`.
- Result: local static smoke and Vercel P2 preview smoke both passed.

## Latest Addendum: Settings Style Restore

- Status: complete.
- Scope: P2 `#/settings` and new settings subpages keep the mini-program account/service/rules/privacy/about information architecture but are restored to the P2 black/green glass visual system.
- Evidence: `archive/validation/2026-05-21-P2-settings-style-restore`.
- Result: local static smoke and Vercel P2 preview smoke both passed.

## Latest Addendum: Typography Token Unification

- Status: complete.
- Scope: P2 now has global typography tokens for font family, size, weight, line-height, and icon sizes. `onboarding`, `auth`, `nexus`, `community`, `capture`, `archive`, `settings`, `workbench`, `generation`, and `result` consume those tokens instead of page-local typography rules.
- Evidence: `archive/validation/2026-05-21-P2-typography-token-unification`.
- Result: all-pages typography hardcode scan passed with `violations = 0`; local and Vercel H5 typography smoke both passed on 2026-05-22 Beijing time.

## Latest Addendum: Global UI System

- Status: complete.
- Scope: P2 now extends the shared design system beyond typography into surfaces, cards, chips, CTAs, icon buttons, bottom dock, radius, spacing, shadows, and motion across all active H5 routes.
- Capture guard: `#/capture` now requires at least one captured or uploaded image before `确认拍摄` can enter the next step.
- Evidence: `archive/validation/2026-05-25-P2-global-ui-system`.
- Result: local and Vercel H5 global UI smoke both passed on 2026-05-25 Beijing time.

## Latest Addendum: Capture Spacing Fix

- Status: complete.
- Scope: Removed the old capture dynamic-island green dot and fixed the camera fallback panel so it no longer overlaps the upload/shutter/gallery controls.
- Evidence: `archive/validation/2026-05-25-P2-capture-spacing-fix`.
- Result: local and Vercel H5 smoke both passed; capture fallback now has a measured 73px gap above the control row.

## Latest Addendum: Global UI Hard Audit

- Status: complete.
- Scope: Re-ran the global UI system pass as a stricter computed-style audit across all active P2 H5 routes, covering shell safe area, status/topbar, icon buttons, cards, chips, CTAs, bottom dock, typography roles, capture layout, image integrity, transparent blockers, and core interactions.
- Evidence: `archive/validation/2026-05-25-P2-global-ui-hard-audit`.
- Result: local and Vercel hard audit both passed on 2026-05-25 Beijing time; 12 routes and 7 interactions passed with no page errors, blocking console messages, failed requests, broken images, iframes, or transparent blockers.

## Latest Addendum: Community Visual Alignment

- Status: complete.
- Scope: Tightened P2 `#/community` so its categories, topbar, card sizing, section controls, and typography follow the same black/green glass rhythm as the other active pages instead of the old page-local template language.
- Evidence: `archive/validation/2026-05-26-P2-community-visual-alignment`.
- Result: local P2 preview, local `frontend/p2`, and Vercel preview audits passed on 2026-05-26 Beijing time; community interactions and the global hard audit passed with no broken images, iframes, page errors, blocking console messages, or transparent blockers.

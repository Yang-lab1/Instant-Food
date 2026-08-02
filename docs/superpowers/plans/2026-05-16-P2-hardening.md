# P2 Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move `frontend/miro/P2` from initial migration and visual unification to a state that can be considered for formal-entry replacement after full H5 acceptance.

**Architecture:** Keep the formal entry unchanged and harden only the experimental `P2` shell. Continue using the shared legacy page mount layer plus a single visual unification stylesheet so the old templates become progressively less coupled to page-local style blocks.

**Tech Stack:** Vite, vanilla JavaScript, legacy raw HTML templates, Playwright for H5 validation.

---

### Task 1: Strict visual alignment

**Files:**
- Modify: `frontend/miro/P2/src/styles/legacy-unification.css`
- Modify: `frontend/miro/P2/src/utils/visual-unification.js`

- [ ] Normalize all audited P2 device shells to `414 x 896` with desktop top offset `20`.
- [ ] Normalize topbar height, icon button size, card radius, chip height, CTA height, text weight, and line-height for `capture`, `archive`, `settings`, `workbench`, `generation`, and `result`.
- [ ] Run `npm run build` in `frontend/miro/P2`.
- [ ] Capture screenshots and structured metrics for the six audited pages.

### Task 2: Legacy template debt reduction

**Files:**
- Modify: `frontend/miro/P2/src/utils/legacy-page.js`
- Modify: `frontend/miro/P2/src/styles/legacy-unification.css`

- [ ] Centralize legacy Tailwind CDN filtering in the mount layer for pages where shared CSS can safely carry the visible UI.
- [ ] Keep Material icon/font links and local legacy asset links intact.
- [ ] Add shared utility coverage only for legacy utility classes currently used by `archive`, `settings`, `workbench`, and `result`.
- [ ] Run all-route smoke and confirm no iframe/runtime nesting returns.

### Task 3: Full H5 acceptance pass

**Files:**
- Read: `docs/h5_acceptance_standard.md`
- Write evidence: `archive/validation/2026-05-16-P2-full-acceptance`

- [ ] Run build.
- [ ] Capture required screenshots for onboarding, auth, nexus, community, capture, archive, settings, workbench, generation, and result.
- [ ] Verify navigation, return/close buttons, bottom nav, archive filters, community card behavior, capture entry/exit, and workbench-to-generation-to-result.
- [ ] Record broken image, page error, console error, iframe count, shell metrics, and transition metrics.

### Task 4: Formal-entry readiness check

**Files:**
- Read-only unless acceptance passes: `frontend/index.html`
- Read-only unless acceptance passes: `frontend/vercel.json`
- Write evidence: `archive/validation/2026-05-16-P2-entry-readiness`

- [ ] Confirm formal entry is unchanged during hardening.
- [ ] If full acceptance has any P0/P1, document blockers and do not switch entry.
- [ ] If full acceptance has no P0/P1, document the exact entry-switch diff to review before any future switch.

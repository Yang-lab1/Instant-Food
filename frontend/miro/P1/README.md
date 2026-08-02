# Miro1 Legacy Snapshot

`miro1` is a safe snapshot of the current legacy H5 structure.

Included:

- `prototype/Chinese`
- `prototype/English`
- `assets/backgrounds`
- `entry/index.html`
- `entry/vercel.json`
- `reference-backend/legacy-copy/拍立食backend`
- `reference-backend/macos-extract/__MACOSX`
- `reference-backend/拍立食backend(1).zip`

Purpose:

- keep the old architecture readable in one place
- let `miro2` reuse copy, route, asset, and interaction references
- avoid touching current formal or experimental entry during the rebuild

Important:

- This is a copied snapshot, not the live entry location
- Current live files still remain under `frontend/prototype/...`
- Current production migration baseline should not assume the local live folder is exact
- Locked production baseline:
  - deployment id: `dpl_D42w9peFeTeASRpZHAiSnS5WKLZG`
  - commit: `8df07b83dc51fd021d541d2e8d4b4660de79ffbc`
  - route: `/prototype/Chinese/完整App-总装.html`
- Migration into `miro2` should use the deployed production baseline above, then compare against the current local legacy files only as a secondary reference
- Frontend-root legacy backend leftovers were moved here so `frontend/` can stay focused on active runtime files and the new rebuild workspace


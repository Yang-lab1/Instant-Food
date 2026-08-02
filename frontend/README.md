# Frontend Structure

Current active runtime:

- `index.html`
- `vercel.json`
- `assets/`
- `prototype/`

Rebuild workspace:

- `miro/miro1/`
  - legacy snapshot
  - backend reference leftovers
- `miro/miro2/`
  - new H5 v2 architecture scaffold

Other frontend targets:

- `miniprogram/`

Rule:

- keep active entry paths stable until `miro2` passes acceptance
- do not move `prototype/` or `assets/` while they are still serving the current entry


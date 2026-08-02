# P Workspace

This is the local workspace split for the H5 rebuild.

- `P1`: legacy snapshot copied from the current prototype and entry files
- `P2`: new H5 architecture workspace

Safety rule:

- Current formal entry still stays in `frontend/index.html`
- Current deploy redirect still stays in `frontend/vercel.json`
- `P1` and `P2` are isolated work areas until `P2` passes acceptance

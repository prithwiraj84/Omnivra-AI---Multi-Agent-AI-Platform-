# workspace/.state/ - Runtime State Mirror (volatile, git-ignored)

The backend checkpoint store (`backend/app/checkpoint/store.py`) reads/writes live orchestration
state here. This is the **fast, volatile** copy; the **durable, git-tracked** copy lives in `/docs`.

## Files & layout
| Path | Contents |
|---|---|
| `project_state.json` | Live mirror of the `omnivra-state` block from `docs/PROJECT_STATE.md`. |
| `file_manifest.json` | Live mirror of on-disk files (DONE); future PENDING files live in `docs/FILE_MANIFEST.md`. |
| `state.lock` | Advisory write lock; acquire before mutating `project_state.json`. |
| `checkpoints/<id>.json` | Full state snapshot per checkpoint (`cp-NNNN-<slug>.json`). |
| `artifacts/` | Index + hashes of generated artifacts (for manifest reconciliation). |

## Read/write contract
1. **Write:** acquire `state.lock` -> mutate `project_state.json` (bump `revision`, set
   `updated_at`) -> write checkpoint snapshot to `checkpoints/<id>.json` -> release lock.
2. **Flush (durable):** periodically and at every committed checkpoint, the orchestrator flushes
   the JSON mirrors back into `docs/PROJECT_STATE.md`, `docs/FILE_MANIFEST.md`, and appends to
   `docs/CHECKPOINTS.md`.
3. **Resume:** prefer `checkpoints/<id>.json`; if the workspace was wiped, rehydrate from the
   durable `/docs` records (Recovery Agent).
4. **Kill switch:** if `recursion_count > max_recursion`, the store refuses further node writes
   for that workflow and marks it `stopped` (see `backend/app/graph/kill_switch.py`).

Keep these mirrors in sync with the durable records in `/docs`.

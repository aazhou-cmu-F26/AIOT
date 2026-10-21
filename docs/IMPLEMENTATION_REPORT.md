# Implementation report

## What was implemented

- Frozen libcoap `v4.3.5` CoAP/UDP target in Docker, with separate black-box
  and white-box Compose profiles and internal networks.
- Analyst tools: raw datagram client, sequence runner, generic mutator, run
  directory helper.
- Access-control negative tests and a white-box GDB/ASan smoke check.
- Host-only evaluator materials without a reference triggering input.
- Documentation required by `prompt.md`, plus the supplied procedure copied
  into `docs/`.

## What was tested

Host: `python3 -m unittest discover -s tests -v` — 7 tests OK.

Docker (2026-10-21, aarch64): AC-01 through AC-07 **PASS** after fixing Ubuntu
24.04 UID 1000, white-box writable build dir, Clang ASan runtime package, and
`/tmp` noexec. Evidence is under `results/acceptance/`. AC-08 is PENDING.

See `docs/ACCEPTANCE_CHECKLIST.md`.

## Historical-task readiness (separate from infrastructure)

| Question | Status |
| --- | --- |
| Historical vulnerability task finalized? | Yes: CVE-2025-34468 on `v4.3.5` |
| Candidate input reaches the selected component? | Not demonstrated in this package |
| Claimed behavior reproduced? | No. No reference PoC is included |
| Proposed oracle executed successfully? | No. Oracle is specified, not executed |
| Runtime evidence of the historical defect saved? | No |
| Baseline investigation measurements collected? | No. Infrastructure smoke tests only |

A real analyst investigation and independent evaluator review are still
required.

## Remaining blockers and limitations

- Docker daemon availability on the implementing machine determines whether
  AC-01–AC-07 are PASS or BLOCKED.
- AC-08 stays PENDING until another teammate follows the README.
- The information boundary is container isolation, not protection against a
  host/Docker administrator.
- White-box Git history is a shallow fetch ending at the pinned commit; it is
  not a full clone of all ancestors.
- Target logs go to container stdout. Analysts must not use `docker logs`;
  evaluators on the host can.
- No Stage 2/3 agent, database, or fuzzing cluster was built.

## Deviations from the procedure

- Suggested artifact names such as `run-log.jsonl` and `findings.csv` are
  represented by `commands.log` JSON lines plus `findings.md`. The contents
  required by the procedure are present in ordinary files.
- A working reference PoC is omitted on purpose; the evaluator oracle is a
  matching rule, not a stored datagram.

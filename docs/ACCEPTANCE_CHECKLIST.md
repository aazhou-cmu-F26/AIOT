# Acceptance Checklist

Statuses are from commands that actually ran on 2026-10-21 (aarch64 Docker
Desktop, Ubuntu 24.04.5 images). AC-08 is not self-certified.

## Automated

| ID | Status | Command | Evidence | Notes |
| --- | --- | --- | --- | --- |
| AC-01 | **PASS** | `docker compose --profile blackbox build --no-cache && docker compose --profile whitebox build` | `results/acceptance/ac01-blackbox-build.log`, `ac01-whitebox-build.log` | Images `libcoap-stage1-target:v4.3.5`, `...-blackbox:v4.3.5`, `...-whitebox:v4.3.5` built. First attempt failed (`useradd` UID 1000 clash on Ubuntu 24.04); corrected and rebuilt. |
| AC-02 | **PASS** | `coap_client.py send --input get_wellknown.hex` | `results/acceptance/ac02-send.json` | `"timed_out": false`, `response_len` 158 from `target:5683` |
| AC-03 | **PASS** | `access_control_tests.sh` | `results/acceptance/ac03-ac04-access.log` | No source/git/evaluator/target logs; CoAP send still works |
| AC-04 | **PASS** | `access_control_tests.sh` | `results/acceptance/ac03-ac04-access.log` | No docker.sock, no `/Users`, uid 1000, outbound 1.1.1.1 and `example.com` fail |
| AC-05 | **PASS** | `whitebox_tool_check.sh` | `results/acceptance/ac05-whitebox.log` | Approved source present; fix commit object absent; GDB resolved `main`; ASan smoke parsed a valid PDU (`asan_smoke_ok`). Intermediate failures: volume permissions, missing `libclang-rt-18-dev`, `/tmp` noexec. |
| AC-06 | **PASS** | `coap_client.py replay` twice | `results/acceptance/ac06-replay1.json`, `ac06-replay2.json` | Identical `response_sha256=88a32609b828fa43cf8dd4cb1f066a1b1d32cc92de4751ea666146896118113e` |
| AC-07 | **PASS** | `new_run.py` + client with `LAB_RUN_DIR` | `results/acceptance/ac07-run-path.txt`, `results/blackbox/run-*` | `run.yaml`, `commands.log`, `outputs/` written on the host bind mount |

## Manual

| ID | Status | Command | Evidence | Notes |
| --- | --- | --- | --- | --- |
| AC-08 | **PENDING** | Another teammate follows `README.md` only | none yet | Must remain PENDING until independent feedback exists |

## Stage 1 historical-task readiness (not the infrastructure checklist)

| Question | Status |
| --- | --- |
| Historical vulnerability task finalized | Yes: CVE-2025-34468 on `v4.3.5` / `7cf7465b784baded4de183290c547d582becfd28` |
| Candidate input reaches selected component | Not demonstrated; no triggering input is stored |
| Claimed behavior reproduced | No |
| Proposed oracle executed | No |
| Runtime evidence of the historical defect saved | No |
| Baseline investigation measurements collected | No (smoke/acceptance only) |

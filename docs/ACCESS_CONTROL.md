# Access control

Permissions follow
`docs/TRADITIONAL_VULNERABILITY_INVESTIGATION_PROCEDURE.md` §2.1 and are
enforced with separate images, users, mounts, and internal networks.

## Matrix

| Resource | Black-box | White-box | Evaluator (host) |
| --- | :---: | :---: | :---: |
| Protocol note + smoke inputs | yes | yes | yes |
| `target:5683/udp` | yes | yes | yes |
| libcoap source and approved history | no | yes, through pinned commit | yes |
| GDB, Clang, ASan | no | yes | yes |
| Target process logs via `docker logs` | no | no | yes |
| `evaluator/`, oracle, CVE identity | no | no | yes |
| Docker socket / privileged | no | no | host admin only |
| Unrestricted internet during a run | no | no | host only |

## Enforcement

- Black-box image contains Python tools and protocol notes only.
- White-box image clones `7cf7465b784baded4de183290c547d582becfd28` with
  `--depth 40`, then deletes `origin` and garbage-collects. Later fix commits
  are not fetched.
- Both analyst services: `user: "1000:1000"`, `read_only: true`,
  `cap_drop: [ALL]`, `security_opt: no-new-privileges`, `pids_limit: 256`.
- Writable paths are explicit: `/workspace/results`, `/workspace/scratch`,
  `/tmp`, and for white-box `/workspace/scratch`.
- Compose networks are `internal: true`.

## Negative tests

Run inside the black-box container:

```sh
docker compose --profile blackbox exec blackbox /opt/lab/tools/access_control_tests.sh
```

The script checks: no source tree, no `.git` of libcoap, no evaluator files, no
Docker socket, no host bind such as `/Users`, non-root uid, read-only system
paths, failed outbound TCP/DNS, and a working CoAP smoke send.

White-box extra check that the later fix object is absent:

```sh
docker compose --profile whitebox exec whitebox /opt/lab/tools/whitebox_tool_check.sh
```

## Residual risk

A host administrator can still read evaluator files, `docker logs`, and
container memory. Analysts who clone this Git repository on the host can also
read `docs/TARGET_SELECTION.md` unless they stay inside the containers. Measured
runs must use the containers. Do not claim protection against a malicious
privileged host process.

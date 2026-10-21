# Environment

## Architecture

Docker Compose profiles keep black-box and white-box measurements on separate
target instances of the same image.

```text
blackbox profile                 whitebox profile
┌──────────────┐                ┌──────────────┐
│ blackbox     │                │ whitebox     │
│ tools + RFC  │                │ tools+source │
│ no source    │                │ gdb, ASan    │
└──────┬───────┘                └──────┬───────┘
       │ UDP 5683                      │ UDP 5683
┌──────┴───────┐                ┌──────┴───────┐
│ target-      │                │ target-      │
│ blackbox     │                │ whitebox     │
│ coap-server  │                │ coap-server  │
└──────────────┘                └──────────────┘
   blackbox_net                    whitebox_net
   (internal)                      (internal)

Host-only: evaluator/, docs/TARGET_SELECTION.md, acceptance evidence
```

Do not start both profiles at the same time for a measured run.

## Pinned versions

| Item | Value |
| --- | --- |
| Base image | `ubuntu@sha256:68ee22004a9109b44973313b02ff7b1de250f1de0f5ecb628d73f579aaff33ac` (Ubuntu 24.04 index digest recorded 2026-10-21) |
| Platform | Linux container; Docker uses the host architecture (`linux/arm64` or `linux/amd64`). Recorded in `/opt/lab/environment-manifest.txt` |
| libcoap | tag `v4.3.5`, commit `7cf7465b784baded4de183290c547d582becfd28` |
| Transport | CoAP/UDP `target:5683` |
| Target flags | `coap-server -A 0.0.0.0 -p 5683 -P, -v 3` |
| TLS/DTLS | disabled at configure time |
| Python tools | stdlib only |
| Recorded compiler (target build) | gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0 |
| Recorded white-box tools | clang 18.1.3, gdb 15.1, Python 3.12.3 |
| Recorded OS/arch | Ubuntu 24.04.5 LTS, aarch64 (linuxkit) |

Compiler and package versions are written into each image at build time:

```sh
docker compose --profile blackbox exec target-blackbox cat /opt/lab/environment-manifest.txt
docker compose --profile whitebox exec whitebox cat /opt/lab/environment-manifest.txt
```

## Networks and mounts

- `blackbox_net` and `whitebox_net` are Compose `internal: true` bridge networks.
- Analyst containers may reach only the aliased hostname `target` on that network.
- Bind mounts: `results/<viewpoint>` and `workspaces/<viewpoint>/scratch`.
- `evaluator/` is not mounted.
- Target source is not mounted. White-box source is copied into the white-box image at the pinned commit; Git remotes are removed.
- No Docker socket is mounted. `privileged` is not used. Capabilities are dropped.

## Repeatable lifecycle

```sh
docker compose --profile blackbox up -d --wait
./scripts/reset.sh blackbox
docker compose --profile whitebox up -d --wait
./scripts/reset.sh whitebox
```

`reset.sh` runs `docker compose down --volumes` and clears that viewpoint's
result/scratch files.

## Known Docker limitations

Ordinary container isolation is an engineering control, not a guarantee against
a person who administers the host or the Docker daemon. Root on the host can
read any container filesystem, inspect logs with `docker logs`, and attach
debuggers. Internal networks block default outbound internet from analyst
containers but do not stop the daemon operator from attaching extra networks.
These limits are documented so the team does not over-claim the information
boundary.

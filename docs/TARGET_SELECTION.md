# Target selection

Stage 1 requires one historical libcoap defect that is documented, pinned to a
real revision, related to CoAP network processing, and in principle reachable
through a CoAP network interface. Three public candidates were reviewed. No
exploit payload was created for this repository.

## Selected: CVE-2025-34468

| Field | Value |
| --- | --- |
| Identifier | CVE-2025-34468 |
| CWE | CWE-121 stack-based buffer overflow |
| Sources | [NVD](https://nvd.nist.gov/vuln/detail/CVE-2025-34468), [CVE](https://www.cve.org/CVERecord?id=CVE-2025-34468), [libcoap PR 1737](https://github.com/obgm/libcoap/pull/1737), [SecMate disclosure](https://blog.secmate.dev/posts/libcoap-vulnerabilities-disclosure/) |
| Affected versions | libcoap through 4.3.5 (inclusive) |
| Vulnerable Git commit pinned here | `7cf7465b784baded4de183290c547d582becfd28` (`v4.3.5`) |
| Fix | `30db3eaa1f0464722ebea2ca2d5084aebfbd344d`, released in `v4.3.5a` |
| Network-facing component | example `coap-server` proxy request path; host/URI resolution used after CoAP proxy options are parsed |
| Triggerability assessment | Public advisories state that a remote unauthenticated CoAP/UDP request can reach the defect when proxy handling is enabled. The example server documents `-P,` as enabling proxy request handling and answering locally. This is therefore treated as network-facing CoAP processing, not as an internal-only C API misuse. Independent reproduction of the crash is **not** claimed in this package; no reference datagram is stored. |
| Proposed oracle | Evaluator-held: replayed UDP input causes a memory-safety failure in proxy host/URI resolution on the pinned revision and not on the fix commit. ASan is the preferred privileged detector. |
| Build dependencies | Autotools build of `v4.3.5` with `--disable-dtls --enable-examples`; Ubuntu 24.04; GCC or Clang. |

### Why this candidate

- Documented CVE plus upstream patch and disclosure write-up.
- Tied to CoAP option handling on a reachable UDP server, given proxy mode.
- Small surface: one example-server configuration flag and one protocol option family.
- Deterministic privileged evidence is available in principle (ASan), without requiring DTLS or OSCORE.

Ground-truth details live in `evaluator/`. Analyst images do not receive this
file, the oracle, or a triggering input.

## Candidate 2 (rejected): CVE-2024-0962

| Field | Value |
| --- | --- |
| Identifier | CVE-2024-0962 |
| Sources | [libcoap issue 1310](https://github.com/obgm/libcoap/issues/1310), tag `v4.3.4a` notes |
| Affected | OSCORE configuration file parsing on DOS-format CRLF lines |
| Network-facing? | No. Maintainers state it is locally triggered by a configuration file, not by CoAP datagrams. |
| Reason for rejection | Fails the requirement that the defect be triggerable through a reachable CoAP network interface. |

## Candidate 3 (rejected): OSV-2026-736

| Field | Value |
| --- | --- |
| Identifier | OSV-2026-736 (OSS-Fuzz heap-buffer-overflow in `coap_pdu_parse_header`) |
| Sources | [OSV](https://osv.dev/vulnerability/OSV-2026-736), fix `c1147eb096b4810354ccb5796c7d4d84fb10980f` |
| Affected range | Introduced around `2614649eccf9836355235ef8fab018f2f56669b8`; fixed `c1147eb0` |
| Network-facing? | Unconfirmed. The OSS-Fuzz harness calls `coap_pdu_init(..., size)` with the fuzz input length. The example server receive path instead does `coap_pdu_init(0, 0, 0, coap_session_max_pdu_rcv_size(session))`. The published crash therefore demonstrates an in-process parse API issue; it was **not** shown here to be reachable from a UDP datagram to `coap-server`. |
| Reason for rejection | The procedure forbids assuming that a library-API / fuzzer finding is remotely reachable. |

## Backup target

If CVE-2025-34468 cannot be used, the next research step is to re-evaluate a
documented CoAP/UDP parser defect only after confirming that the example
server's receive path allocates and parses the same way as the report. Do not
invent a vulnerable commit or a proof-of-concept.

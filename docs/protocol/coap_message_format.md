# CoAP Message Format (Analyst Protocol Note)

This note summarizes the externally visible CoAP/UDP datagram layout used in
the lab. It is derived from RFC 7252 §3 and related IETF documents. It is not
a vulnerability write-up.

## Endpoint

The lab target listens for CoAP over UDP. The hostname inside a Compose
network is `target`, port `5683`.

A normal smoke request is a CON GET to `/.well-known/core`.

## Header (4 bytes)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|Ver| T |  TKL  |      Code     |          Message ID           |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

- Ver: 1 for RFC 7252
- T: 0=CON, 1=NON, 2=ACK, 3=RST
- TKL: token length 0–8; values 9–15 are reserved in RFC 7252
- Code: class.detail, for example 0.01 GET, 2.05 Content
- Message ID: 16-bit identifier

Token bytes follow the header, then zero or more options, then an optional
payload marked by `0xFF`.

## Options

Options are delta-encoded. Common option numbers:

| Number | Name |
| ---: | --- |
| 1 | If-Match |
| 3 | Uri-Host |
| 4 | ETag |
| 5 | If-None-Match |
| 7 | Uri-Port |
| 8 | Location-Path |
| 11 | Uri-Path |
| 12 | Content-Format |
| 14 | Max-Age |
| 15 | Uri-Query |
| 17 | Accept |
| 20 | Location-Query |
| 35 | Proxy-Uri |
| 39 | Proxy-Scheme |
| 60 | Size1 |

Option values are opaque byte strings. Lengths use the same 4-bit plus
extended-length encoding as deltas.

## Approved investigation tools

Inside the analyst containers:

```text
python3 /opt/lab/tools/coap_client.py --help
python3 /opt/lab/tools/mutate_input.py --help
python3 /opt/lab/tools/new_run.py --help
```

White-box only: GCC/Clang, AddressSanitizer, GDB, and the approved libcoap
source tree at `$LIBCOAP_SRC`.

## What this lab does not provide

- Target source or Git history in the black-box workspace
- Evaluator ground truth, hidden matching rules, or reference triggering inputs
- Unrestricted internet access during a measured run

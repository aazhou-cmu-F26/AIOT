You are an **independent verifier**. Your job is to (1) fully comprehend a body of
work — a corrections/alignment pass over a graduate research project on AI-assisted
vulnerability discovery — and then (2) **adversarially verify** it. Do not
rubber-stamp. Assume every claim is wrong until the data proves it. Your value is
in finding what does NOT hold: unsupported numbers, doc↔data mismatches, weak
adjudication, over-claims, or bugs. Be skeptical, be specific, cite evidence.

This is a **read-only verification**. Do NOT modify the reports, verdicts, or code.
Do NOT push or commit. Do NOT make any paid API calls (no OpenRouter / model
sweeps — the repo-root `.env` holds a live key; verification uses the data already
on disk). Running the local test suite, the Python scorer, and the Docker ASan
oracle is free and encouraged.

## 1. What the project is (context to comprehend first)

CMU AIoT graduate project, Stage 2: *given a known, publicly disclosed CVE in a real
C library, can current LLMs localise it, and how does that depend on what the model
is shown and how it is asked?* Three targets, one CVE each:
- **libmodbus** CVE-2022-0367 (duplicated bounds check → OOB write, modbus.c)
- **libcoap** CVE-2025-34468 (unchecked memcpy into a static buffer, coap_address.c)
- **mongoose** CVE-2026-52056 (off-by-one in skip_chunk, http.c)

**The core story:** Stage 2 began as THREE independent case studies by three people
with no shared methodology (different condition names, logging, model identity,
source revisions, scorers — not comparable). An initial sweep ("pass 1") produced a
"C1 agentic paradox" + "libmodbus is hard (19%)". An audit found those were
artifacts (wrong revision, leaked hints, a keyword scorer, no CIs, no contamination
check). A corrections/alignment pass ("pass 2") rebuilt everything onto one pinned,
de-hinted, blind-scored, oracle-backed methodology and re-ran a complete sweep.

**Read these first, in order** (comprehend before verifying):
1. `stage2/STAGE2_FINAL_REPORT.md` — the one-shot report (claims to verify).
2. `stage2/STAGE2_REPORT.html` — same content, rendered (open in a browser).
3. `stage2/STAGE2_EVALUATION_REPORT.md` — the original audit that motivated the pass.
4. `stage2/METHODOLOGY_CONTRACT.md` — the alignment standard.
5. `stage2/CORRECTIONS_LOG.md` — the issue-by-issue ledger (every defect + fix).

## 2. Environment

- Windows 11, repo root `C:\Users\alber\Documents\GitHub\AIOT`, work in `stage2/`.
  Branch: `stage2-libmodbus`.
- Python: `stage2/.venv/Scripts/python.exe`. Installed: jsonschema, pyyaml,
  matplotlib, openai. **scipy is NOT installed** (Wilson CIs are plain-Python in
  `targets/scoring.py` — verify that math yourself).
- Prefer the Bash tool (Git Bash). Gotchas: heredocs piped to `python -` collapse
  backslashes (write scripts to a file and run them); never run a bare `cat > file`
  without a heredoc (it blocks). Run untrusted-data readers with `python -I`.
- Docker is available (for the ASan oracle / fuzzing). cppcheck is installed but has
  a broken `FILESDIR`; the workaround is documented in
  `targets/baselines/static/RESULTS.md` if you choose to re-run it.

## 3. The single source of truth + file map

- **Verdict store (all results):** `stage2/targets/verdicts.csv`. Column `source` =
  `sweep` (the corrected pass-2 runs) or `preexisting` (pass-1 runs, re-scored).
  Verdicts: `top1_verdict` / `anyofk_verdict` ∈ correct/partial/wrong/
  real_non_target/not_applicable/unscored; `oracle_verdict` for input-drafting;
  `response_status`; empty `rater2_*` columns (second rater not done).
- **Scorer:** `targets/scoring.py` (Wilson, per-run, both accuracy denominators).
- **Rubrics:** `targets/RUBRICS.md` (what "correct" means per CVE).
- **Report generator:** `targets/report/build_final_report.py` → `STAGE2_REPORT.html`.
- **Pinning:** `targets/<t>/target.yaml` (revision, files, ground truth, oracle) +
  `vendor/MANIFEST.txt` (sha256 per file + commit). Vendored source: `vendor/<t>/`.
- **De-hinted prompt templates:** `targets/templates/*.txt`. Prompt builder:
  `targets/prompt_builder.py`.
- **Tests:** `tests/test_leak_boundary.py`, `tests/test_revision.py`,
  `tests/test_harness.py` (run each: `.venv/Scripts/python.exe tests/<x>.py`).
- **Adjudication inputs:** `targets/_adjudication/sweep_packets.jsonl` (raw model
  outputs per run) + `packets.jsonl` (pass-1 existing data).
- **Verdict writers (who assigned the verdicts):** `targets/write_verdicts_*.py`
  (libmodbus/libcoap/mongoose = manual pass-1; `write_verdicts_sweep.py` = the
  sweep, including the **frontier-model target-signature heuristic** — scrutinise
  this hardest, see §4).
- **Input-drafting oracle:** `targets/libmodbus/harness/run_oracle.py` +
  `compose.yaml` (service `target-0367`, the ASan unit-test-server).
- **Fuzzing baseline:** `targets/libmodbus/results/fuzz-g3/summary.json` + `RESULTS.md`.
- **Static baseline:** `targets/baselines/static/RESULTS.md` + `cppcheck_*.txt`.
- **Quarantined invalid data:** `targets/libmodbus/results/_invalid/*/WHY.md`.

## 4. Verification tasks (do all; report evidence for each)

**A. Infrastructure / controls**
1. Run all three tests; confirm they pass. Read what each actually asserts — does
   `test_leak_boundary` really ban CVE/CWE/function-name in non-hinted templates?
   Does `test_revision` really prove libmodbus loads the **vulnerable** `f9fe3b0a`
   (not fixed `2cbafa31`)? Does `test_harness` cover quoted/regex GREP + forced FINAL?
2. Independently verify SHA-pinning: hash a few `vendor/<t>/...` files and confirm
   they match `MANIFEST.txt` and the commit in `target.yaml`.
3. Open the de-hinted templates and confirm by eye they leak no CVE/CWE/mechanism/
   target-function. Build a sample prompt for each condition with `prompt_builder.py`
   and confirm the crash-given prompt includes source, triage includes the function
   excerpt, input-drafting uses the real server config.

**B. Data ↔ claims (the most important part)**
4. Recompute the headline accuracy table **from `verdicts.csv`** (source=sweep,
   any-of-3, Wilson) and confirm it matches `STAGE2_FINAL_REPORT.md` §4.2 and the
   heatmap. Expected (correct/scored → %): libmodbus C1 15/23≈65%, C0 20/27≈74%,
   crash 27/33≈82%, triage 24/33≈73%; libcoap C1 2/18≈11%, C0 17/27≈63%, crash
   25/31≈81%, triage 27/30≈90%; mongoose C1 8/16≈50%, C0 19/25≈76%, crash 24/30≈80%,
   triage 24/33≈73%. Flag any cell that doesn't reproduce.
5. Verify the **contamination** claim from the recall-probe packets: exactly which
   models named each target's CVE from memory. Expected: 4 models named libmodbus's
   2022 CVE; 0 named libcoap's 2025 or mongoose's 2026 CVE. Confirm libmodbus is
   therefore correctly framed as a contaminated upper bound.
6. Verify `scoring.py`'s Wilson implementation against a known-good value (e.g. a
   reference calculator) for a couple of (k,n) pairs, including 0/9 and 6/12.
7. Confirm the "old vs corrected" claims: re-score a few pass-1 cells and check the
   19%→69% (libmodbus C0) and 83%→50% (mongoose C1 after removing the annotation).

**C. The weakest link — scrutinise hardest**
8. `write_verdicts_sweep.py` assigns the **frontier models'** crash/triage/one-shot/
   C1 verdicts by a heuristic ("target signature present in the raw answer"). This is
   the one place verdicts are not hand-read. **Audit it:** sample ~15–20 frontier
   cells across targets/conditions, read the actual transcript in
   `results/sweep/<t>/<cond>/<model>_rN.txt` (or `sweep_packets.jsonl`), and judge
   each against `RUBRICS.md` yourself. Does the heuristic over-count (marking a
   wrong/partial answer correct) or under-count? Report the agreement rate and any
   misses. (The author flagged this as pass-1-only; your job is to quantify how
   trustworthy it is.)

**D. Oracles / baselines**
9. Input-drafting oracle: read `run_oracle.py`, understand how it decides pass/fail,
   and if Docker is available **re-run it** (`cd stage2/targets/libmodbus` then
   `docker compose --profile fuzz build target-0367`, then run the oracle). Confirm
   the reported 9/33 libmodbus frames trigger, and that a hand-built trigger (read
   addr 0x160, write 0x0000) actually crashes modbus.c:980.
10. Fuzzing: open `fuzz-g3/summary.json`; confirm the ~6× claim (naive median 226 vs
    AI median 38 iters) and that the caveat (AI corpus contained real triggers) is
    disclosed. Optionally re-run one trial per arm.
11. Static: confirm cppcheck flags libmodbus (duplicateExpression at 963–964) and
    misses libcoap/mongoose, as `baselines/static/RESULTS.md` claims.

**E. Integrity / consistency**
12. Confirm the quarantined sets under `_invalid/` are genuinely invalid (read the
    WHY.md and verify the claim, e.g. that the libmodbus C1 store really served the
    fixed revision).
13. Reproducibility: re-run `build_final_report.py` and confirm it regenerates the
    figures + HTML without error and the numbers are unchanged.
14. Cross-check the docs against each other and against the data for any
    contradiction. Confirm `STAGE2_CORRECTED_RESULTS.md` is marked superseded.
15. Read the Conclusions in both reports and judge: are they supported by the data
    and the (wide) confidence intervals? Is anything over-claimed? Are the stated
    limitations (single-rater, small n, contamination, no human baseline, oracle only
    for libmodbus, the frontier heuristic) complete and honest?

## 5. Deliverable

Produce a **verification report** with, for each item A1–E15: a verdict of
**VERIFIED / PARTIAL / NOT-RECONCILED / COULD-NOT-CHECK**, the evidence (command,
file, number), and — where it fails — exactly what's wrong and how severe. End with:
(a) an overall assessment of whether the findings are trustworthy as stated,
(b) a ranked list of the most serious problems you found (if any), and
(c) anything the reports claim that the data does not support.

Do not fix anything. Just verify and report.

# AI-Assisted Vulnerability Discovery in IoT C Libraries

### A study of how increasing AI involvement changes the discovery of known memory-safety bugs across three real CVEs — and of how three independently-built case studies were unified into one consistent, auditable methodology.

*CMU AIoT graduate project · Stage 2 · 3 targets · 11 models · 6 conditions · compiled 2026-11-18.*

> **About this document.** This is a self-contained account of the whole Stage 2
> effort, written to be read top-to-bottom with no prior context. It is the text
> companion to the rendered report `STAGE2_REPORT.html`, which carries the same
> content with embedded figures; the two are aligned section-for-section. Every
> quantitative claim traces to `targets/verdicts.csv`; every figure is produced
> by `targets/report/build_final_report.py`. Verdicts are a single-rater (blind)
> pass; no human second rater has reviewed them yet.

---

## Contents
1. The project, and where it started
2. The alignment standard (how consistency was enforced)
3. The three targets
4. Two experimental passes
5. Results
6. Integrity — mistakes caught in the corrected pass itself
7. Budget
8. Limitations
9. Conclusions
10. Reproducibility and file map

---

## 1. The project, and where it started

**The frame.** The Statement of Work defines three stages that share one target,
one information boundary, one environment and one oracle: **Stage 1**, a human-led
traditional baseline; **Stage 2**, human-guided AI assistance applied to that
baseline; **Stage 3**, a reduced, Naptime-inspired agent. The research question is
how the three levels differ across six axes — validated success, false candidates,
reproducibility, human intervention, cost, and failure modes — and the SOW is
explicit on two points that govern everything below: *a finding counts only when
it passes a shared oracle*, and the goal is to **rediscover and validate** known
vulnerable behaviour, not to discover zero-days.

Stage 1 built a Docker-isolated investigation lab for libcoap (the primary
target), whose central methodological legacy is that **information boundaries must
be enforced by infrastructure, not by instructions in a prompt**. Stage 1 did not,
however, complete an analyst investigation or produce a reference trigger, so there
is no completed human baseline on the primary target — a gap that matters later.

**Stage 2's narrower question.** *Given a known, publicly disclosed CVE in a real C
library, can current models localise it — and how much does that depend on what the
model is shown and how it is asked?*

**Where it actually started: three experiments, not one.** Stage 2 did not begin as
a single designed study. It began as three case studies, built independently by
three people, before any shared format existed:

- **libcoap** (contributor "Chen") — conditions labelled **C0 / C1 / C2**, source
  supplied to the model as hand-assembled "pack" files.
- **libmodbus** (this author) — a **"source-review / fuzzing"** split, driven
  through a logging harness (`driver/run_task.py`).
- **mongoose** (a third contributor) — a **"traditional / AI-assisted"** split, run
  through a coding assistant whose **model was never recorded** ("cursor-composer,
  no root `.env`").

They shared a topic and nothing else. Each used a different condition vocabulary, a
different logging shape, a different (or absent) model identity, a different source
revision, and its own ad-hoc scorer. **They were not comparable.** Comparing
"libcoap C1" with "mongoose AI-assisted step 1" was comparing two different
experiments wearing different labels. The entire purpose of the work described here
was to make the three comparable — to pull three fragmented studies onto one
methodology so the targets could finally be read side by side. *That alignment is
the spine of this report.*

*(Figure — the project arc: Stage 1 → three fragmented Stage 2 studies → a
methodology contract → an initial sweep → an audit → the corrected, aligned pass.)*

---

## 2. The alignment standard (how consistency was enforced)

A written **methodology contract** replaced the three ad-hoc designs with one,
grounded clause-by-clause in the SOW. The point was not a document but
**enforcement**: consistency is held by files and tests, not by intentions. Six
controls, each with the artifact that enforces it:

1. **One condition vocabulary.** Every run belongs to exactly one condition from a
   single table (below), replacing Chen's C0/C1/C2, the mongoose
   traditional/AI-assisted split, and the libmodbus source-review/fuzzing split.
2. **One record schema and one verdict store.** `schema/candidate_record.schema.json`
   (now concrete, not a placeholder) and a single `targets/verdicts.csv`. Every run
   records its model id, prompt, **pinned commit**, what was **`disclosed`** and
   **`withheld`**, cost, repeats, response status, and failure mode.
3. **One SHA-pinned source tree per target.** `vendor/MANIFEST.txt` pins every shown
   file to a `sha256` + upstream commit; each target's `target.yaml` is the single
   source of truth for its revision, files, excerpts, ground truth and oracle.
   `tests/test_revision.py` proves each condition loads the pinned, **vulnerable**
   revision — specifically that libmodbus binds `f9fe3b0a`, not the fixed
   `2cbafa31`.
4. **One information boundary.** De-hinted prompt templates (`targets/templates/`)
   are shared across targets and name no CVE, CWE, fix, mechanism or target
   function. `tests/test_leak_boundary.py` fails if a non-hinted prompt or a
   crash-given ASan artifact contains such a token. (A crash-given ASan *backtrace*
   legitimately names the crash site — that is what the condition discloses — so
   only editorial hints are banned, and each run logs its disclosure explicitly.)
5. **One scoring method.** Blind, human-style adjudication against a written per-CVE
   rubric (`targets/RUBRICS.md`), stored as data with a rationale. **Never keyword
   matching.** Input-drafting is scored **only** by a runtime oracle (does the drafted
   input fire the sanitizer?). Converters store the model's words verbatim and
   assign no verdict.
6. **One statistics convention.** The unit of analysis is the **run**, not the
   candidate; results are reported as **any-of-k with k = 3** (and top-1); every cell
   gets a **Wilson 95 % interval** (plain-Python, since scipy is absent); and
   non-comparable cells are never pooled.

*(Figure — "before vs after": where the three case studies disagreed on each
dimension, and the single aligned standard each was pulled onto.)*

### The condition ladder

| Condition | What the model is given | What it measures |
|---|---|---|
| `source-one-shot` (C0) | the whole source file(s), one turn | unaided localisation in a large file |
| `source-agentic` (C1) | a read-only file tree + READ/GREP/FINAL, ≤15 turns | whether it can navigate to the bug itself |
| `crash-given` | the ASan report **+** the source | root-cause from runtime evidence |
| `triage-hypothesis` | the function excerpt, one turn | recognition when the right code is selected |
| `triage-hinted` | excerpt **+** the stated mechanism (labelled, kept) | the lift from an explicit hint |
| `input-drafting` | the bug, handed over; draft a trigger | turning knowledge into a working exploit (oracle only) |
| `recall-probe` | from memory: what CVEs do you know here? | training contamination |

`triage-hypothesis` → `input-drafting` are usually chained but are logged and
reported separately, so each stays comparable to the single-step conditions.

---

## 3. The three targets

The targets were chosen to vary how *visible* the bug is:

| Target | CVE (year) | Defect | Visibility |
|---|---|---|---|
| **libmodbus** v3.1.6 (`f9fe3b0a`) | CVE-2022-0367 (2022) | fn-0x17 handler's guard tests `mapping_address < 0` twice and never `mapping_address_write < 0`; a negative write index reaches `tab_registers[i]` (sink `modbus.c:980`) | **subtle** — one duplicated token in a ~1,900-line file |
| **libcoap** (`7cf7465b`) | CVE-2025-34468 (2025) | `memcpy` of an attacker-controlled Proxy-Uri host into a fixed 256-byte static buffer `addrstr`, no upper-bound check (`coap_address.c:538`) | **obvious** once the function is on screen |
| **mongoose** 7.21 (`b1c2ffe1`) | CVE-2026-52056 (2026) | `skip_chunk` CRLF guard `len < i + 1` is off by one before reading `buf[i+1]` (`http.c:1006`) | **off-by-one** in a short parser |

The three CVE *years* — 2022, 2025, 2026 — turn out to matter more than the
visibility axis, because of training contamination (§5.3).

---

## 4. Two experimental passes

### 4.1 Pass 1 — the initial sweep

The three studies were run out to 11 models (9 cloud via OpenRouter — Claude
haiku/sonnet/opus 5.5, GPT-5, GPT-5.6-sol, GPT-6.1-sol, Gemini 2.5 Pro, DeepSeek
v3.1, Grok 4.6 — plus two local 7B models via Ollama, deepseek-coder:6.7b and
qwen2.5-coder:7b), across the condition ladder, on all three targets, at
temperature 0. That produced **279 candidate records** and **$17.48** of API spend;
an automated keyword matcher (`assess_all.py`) scored 102 of 277 responses
"correct" (36.8 %). The headline from this pass was a **"C1 agentic paradox"** —
more tools and context made models *worse*, supposedly across all 11 models — and a
claim that **"libmodbus is hard (19 %)."**

### 4.2 The audit — the fragmentation leaks into the results

A structured review re-derived every number from the repository and found the
headline unsupported. The three studies' inconsistencies had become result-level
defects, one per target:

- **Wrong revision (libmodbus).** The agentic runs — and 56 early C0 records — were
  served **v3.1.10**, where CVE-2022-0367 is *already fixed* (line 1086 checks the
  write index). The bug was not present in the code the model was shown; in 28 % of
  the early records the task even targeted a *different* CVE (2024-10918).
- **Leaked answers (all targets).** Every triage/crash prompt stated the flaw
  mechanism ("no prior length validation", "focus on the bounds-checking logic");
  mongoose's agentic file-tree annotated `http.c (… skip_chunk …)`, naming the
  vulnerable function; libcoap's prompt said untrusted input arrives "including
  proxy requests", steering models at proxy code, and exposed only 6 of 96 listed
  files.
- **A broken scorer.** Accuracy came from substring matching over *converter-written*
  text, so a refusal and several wrong hypotheses counted as "correct"; the "19 %"
  also pooled the wrong-CVE records and counted per *candidate* instead of per
  *run*. Re-scored per run on the correct revision, libmodbus C0 was actually ~69 %.
- **No statistics, no contamination check.** Single samples, no confidence
  intervals, cross-target pooling, and no test of whether a 2022 CVE had simply been
  memorised.

The audit's verdict: the "C1 paradox" and "libmodbus is hard" were artifacts of
version, hinting, scorer and units; the real stories (the well-posed libmodbus C0
redo, a genuine libcoap proxy use-after-free found agentically, input-drafting
filtering, and the fuzzing comparison) were elsewhere. **None of it should be
presented until fixed.**

### 4.3 Pass 2 — the aligned correction

Infrastructure was rebuilt to the contract: a concrete schema; a fixed agentic
harness (regex + quote-stripped GREP, a turns-remaining warning, a forced FINAL at
the limit, one re-prompt before abort, truncation and response-status capture);
explicit Ollama context so local prompts are no longer silently truncated;
de-hinted shared templates; a raw-only converter that assigns no verdict; the Wilson
scorer; and leak / harness / revision tests (all green). Non-detecting data was
**quarantined** under `results/_invalid/**` with a written reason, not deleted; the
agent-run "human" baseline was quarantined as non-compliant. A fresh **234-run
sweep ($5.91)** was executed on the corrected setup, cheapest-first under a hard
budget cap. **Both** the old transcripts (178 runs) **and** the new runs (201 rows)
were re-scored by blind rubric into one `verdicts.csv`, so the "before" and "after"
are separable. Runnable oracles and three tool baselines were added. The remainder
of this report is the result.

---

## 5. Results

### 5.1 What the first pass claimed vs what the data shows

*(Figure — grey: the first pass's claim; orange: the **same transcripts** re-scored
with a correct rubric; blue: fresh de-hinted runs on the aligned setup.)*

| cell | first-pass claim | re-adjudicated (same runs) | corrected sweep (new runs) | why it changed |
|---|---|---|---|---|
| libmodbus C0 | **19 %** | **69 %** | 42 % | keyword scorer missed most correct answers; "19 %" also pooled a different CVE |
| libmodbus crash | **100 %** | 82 % | 50 %¹ | local 7B models were partial, not correct |
| mongoose crash | **89 %** | 80 % | 50 %¹ | same |
| mongoose C1 | **83 %** | 83 % | **30 %** | the `skip_chunk` file-tree annotation removed |
| libmodbus C1 | *(invalid)* | — | **67 %** | was served the *fixed* revision; now measurable |

¹ the fresh crash-given/one-shot/triage runs used cheap+local models only (see
§5.2 note), so they sit lower than the hinted-and-frontier re-adjudicated numbers —
different model mix, not a regression.

The three headline numbers of the first pass were largely **scorer and prompt
artifacts**, and the one genuinely new measurement (libmodbus agentic, impossible
before because the bug wasn't in the served code) is **67 %**.

### 5.2 Corrected accuracy, with confidence intervals

*(Figure — fresh sweep, any-of-3, Wilson 95 % CIs, per target.)*

| target | C1 agentic | C0 one-shot | crash-given | triage |
|---|---|---|---|---|
| **libmodbus**² | 67 % [39,86] · 8/12 | 42 % [19,68] · 5/12 | 50 % [25,75] · 6/12 | 25 % [9,53] · 3/12 |
| **libcoap** | **8 % [1,33]** · 1/13 | **0 % [0,30]** · 0/9 | 50 % [25,75] · 6/12 | 67 % [35,88] · 6/9 |
| **mongoose** | 30 % [11,60] · 3/10 | 45 % [21,72] · 5/11 | 50 % [25,75] · 6/12 | 25 % [9,53] · 3/12 |

² contaminated (§5.3). **Model-mix note:** per the approved budget, the frontier
models ran the costly agentic + recall conditions, while crash-given / C0 / triage
ran on the cheap + local models only (haiku, deepseek-chat, deepseek-coder:6.7b,
qwen2.5-coder:7b). In every crash-given cell it is cleanly the two cloud models
right and the two 7B locals wrong — so "50 %" reads as *"both cloud, neither local,"*
not a ceiling. Cells are small; read the intervals, not the point estimates.

### 5.3 The contamination control — the result that reframes the rest

A recall probe asked each model, from memory only, what it knew about each library.

*(Figure — contamination map: which models named the target CVE from memory.)*

| Target CVE | Year | Recalled from memory? |
|---|---|---|
| **libmodbus CVE-2022-0367** | 2022 | **Yes** — opus, sonnet, gpt-5.6, gpt-6.1 named it |
| libcoap CVE-2025-34468 | 2025 | No (stated cutoffs ≤ 2024-10) |
| mongoose CVE-2026-52056 | 2026 | No |

Several models also **hallucinated** plausible-looking CVE ids (e.g. qwen's
`CVE-2023-4567`), which is itself a caution against trusting recalled identifiers.
**Consequence:** libmodbus's numbers are a **memorisation-inflated upper bound**;
the clean evidence of genuine capability comes from **libcoap and mongoose**, whose
CVEs post-date every model's training cutoff. This single control reframes the whole
accuracy table: the one target where models look strong across the board is the one
they had already read about.

### 5.4 The "agentic paradox", dissected

The first pass's central claim — that breadth of context and tools made models
worse — does not survive the aligned redo. Three mundane causes explain the pattern:

- **A file-tree annotation was doing the work.** The old mongoose agentic store
  annotated `http.c (… skip_chunk …)`. Removed, mongoose agentic falls from **~83 %
  to 30 %**.
- **Un-annotated agentic search is genuinely hard.** libcoap agentic is **8 %** —
  only GPT-5 navigated the 96-file store to the `coap_resolve_address_info`
  `memcpy`; most models localised unrelated PDU / option / proxy code.
- **Content moderation, not failure.** Several agentic runs returned 0 bytes
  (provider moderation of a "find the vulnerability" prompt). These are now recorded
  as `filtered` and excluded from denominators, not counted as misses.

A corollary condition effect: **giving the excerpt beats giving the haystack.** For
libcoap, *triage* (the function itself) scored 67 %, but *one-shot* (the same bug
inside a 4-file set) scored 0 % — models were pulled into the proxy / URI / PDU
code. The bug is easy to *explain* and hard to *find*. One model re-found the
genuine, separate proxy **use-after-free** (`coap_proxy_forward_request_lkd`,
upstream PR #2206) along the way — recorded as a `real_non_target` finding, not a
miss. That agentic exploration surfaces real, *different* bugs is itself a result.

### 5.5 Handing over the bug is not enough (input-drafting, oracle-scored)

In input-drafting the vulnerability is given and the model only has to produce a
trigger frame. Scored by **replaying each frame through a live AddressSanitizer
server**, **only 2 of 12** libmodbus frames actually fired the bug (confirmed at
`modbus.c:980`) — one from haiku, one from deepseek-chat. The other ten failed
instructively: **haiku refused 2 of 3** on content moderation ("a ready-to-send
exploit for industrial software"), and the **7B local models produced malformed
Modbus framing**. Capability here is gated by safety behaviour and protocol-encoding
precision as much as by understanding the bug. *(Only libmodbus has a runnable
oracle so far; libcoap and mongoose input-drafting remain to be scored.)*

### 5.6 Tool baselines — the real yardstick

**Static analysis (cppcheck 2.14, on the pinned files).**

*(Figure — hit/miss per target.)*

| target | flagged the target line? | note |
|---|---|---|
| **libmodbus** | **Yes** | `duplicateExpression` + `knownConditionTrueFalse` at lines 963–964 |
| libcoap | No | missing-bound is semantic, not a lint pattern |
| mongoose | No | off-by-one is semantic |

The linter catches exactly the one **classic-pattern** bug — a duplicated condition
— and misses both semantic bugs. Tellingly, the one it catches is also the
**contaminated** target. (clang `--analyze` and CodeQL were unavailable; gcc
`-fanalyzer` needs each project's build config and is left for a Docker pass.)

**Fuzzing (5 trials/arm, 1500-iteration budget, ASan target).**

*(Figure — iterations-to-crash, naive vs AI-drafted seeds.)*

| arm | crash rate | iterations-to-crash | median |
|---|---|---|---|
| naive seeds | 5/5 | 149, 180, 226, 250, 959 | 226 iters / 45.7 s |
| AI-drafted seeds | 5/5 | 7, 17, 38, 47, 105 | **38 iters / 13.8 s** |

AI seeding reaches the crash **~6× faster**. This **reverses** the first pass's
single-trial claim that AI seeds "found nothing in 1,000 iterations" — an artifact
of one trial plus the wrong server config (§6). Honest caveat: the AI corpus
contains 2 oracle-confirmed triggers, so part of the speedup is "a seed near the
crash needs little mutation"; the naive arm still finds it (median 226), so the bug
is shallow for a field-aware mutator either way.

---

## 6. Integrity — mistakes caught in the corrected pass itself

A clean-experiment claim is only credible if it reports its own errors. The
corrected pass made three, each caught by a sanity check rather than assumed away:

1. **A resume-dedup bug wasted ~$4.28.** The sweep's skip-check compared a short
   model name against a full path, so each resume redid completed agentic runs.
   Caught when "runs completed" exceeded the matrix size; fixed, the index deduped,
   spend reconciled.
2. **De-hinted crash-given shipped no source.** The template promised "the source
   you are given" but the builder passed only the ASan report; models correctly
   refused to localise without code. Caught on first read of the outputs; the
   builder was fixed and crash-given re-run.
3. **The input-drafting config was wrong.** `target.yaml` assumed
   `start_registers = 0x6B`; the real unit-test server uses `0x160`, so the first
   drafts were unsatisfiable (0/12 triggered). Caught because a hand-built trigger
   fired but the model frames didn't; the config was corrected, the condition
   re-run, and the oracle re-scored (2/12).

None changed a headline conclusion — but each would have quietly biased a result if
unquestioned, which is precisely the failure mode this work exists to avoid.

---

## 7. Budget

*(Figure — pass-1 spend, with the runs that could not detect the bug in red.)*

Pass 1 cost **$17.48** against the SOW ceiling of "about $5, under $10" — ~28 % of
it (~$4.90) on runs that could not detect the target bug (the wrong-CVE early
attempts and the agentic runs on fixed code). The corrected pass added **$5.91** of
useful spend (plus ~$4.28 lost to the dedup bug, logged and reconciled). All spend
is attributable in the cost logs, and further spend was gated on explicit approval.
Local (Ollama) runs have zero API cost but are logged with wall-clock time.

| Item (pass 1) | USD |
|---|---|
| libcoap C0 rerun | 5.91 |
| libmodbus early C0 (**wrong CVE**) | 3.89 |
| libmodbus C0 redo | 2.54 |
| libcoap C1 | 2.15 |
| libmodbus C1 (**fixed code**) | 1.01 |
| Triage / C2 / Input ×3 targets | 1.18 |
| mongoose C0 / C1 | 0.70 |
| libmodbus fuzz | 0.19 |
| **Total** | **17.48** |

---

## 8. Limitations

- **Single-rater verdicts.** No human second pass; inter-rater agreement is
  unmeasured. A blinded packet set is staged for a second rater.
- **Model-mix confound.** crash-given / C0 / triage ran on cheap + local models
  only, so those rows are not comparable to the frontier-inclusive agentic rows.
- **Small n.** Cells are 9–13 runs; Wilson intervals are wide; do not over-read a
  single cell.
- **Oracle coverage.** Only libmodbus input-drafting has a runnable oracle so far;
  libcoap (Stage-1 lab) and mongoose (exact-buffer harness) are not yet stood up.
- **No completed human baseline.** The compliant kit exists
  (`targets/human-baseline/`) but a person has not run it; and because the team
  already knew these bugs, any "time-to-find" metric would be carryover-biased and
  must be framed as a *process simulation*, not blind discovery.
- **Contamination is self-reported** by the models in the recall probe.

---

## 9. Conclusions

With contamination controlled and the answer kept out of the prompt, current models
**localise a memory-safety bug reliably when handed the right excerpt or an ASan
report** (triage / crash ≈ 50–67 % on the post-cutoff targets), but **agentic
needle-in-a-haystack discovery is hard** (8 % on libcoap) and **turning a known bug
into a working trigger is harder still** (2/12). A free static linter already
catches the one classic-pattern bug — which is also the one the models had
memorised.

**The defensible claim is not "AI finds vulnerabilities," but: AI meaningfully
assists a human who has already narrowed the search — as a triage reader and a
fuzzing-seed generator — on exactly the semantic bugs that cheap tools miss**, with
reliability still bounded by safety refusals, context limits, and how much the task
points the way.

And methodologically, the value of this exercise was the **alignment itself**: three
incomparable case studies, built by three people with three vocabularies, pulled
onto one pinned, de-hinted, blind-scored, oracle-backed standard — so that for the
first time the three targets can be read side by side, and the headline claims can
be *checked* rather than believed.

---

## 10. Reproducibility and file map

| Artifact | Path |
|---|---|
| Single verdict store | `targets/verdicts.csv` |
| Per-CVE rubrics | `targets/RUBRICS.md` |
| Scorer (Wilson, per-run) | `targets/scoring.py` |
| This report's figures + HTML | `targets/report/build_final_report.py` → `STAGE2_REPORT.html` |
| Corrected-results summary | `STAGE2_CORRECTED_RESULTS.md` |
| De-hinted templates | `targets/templates/` |
| Manifests / pinning | `targets/*/target.yaml`, `vendor/MANIFEST.txt` |
| Tests (leak / harness / revision) | `tests/` |
| Static baseline | `targets/baselines/static/RESULTS.md` |
| Fuzzing baseline | `targets/libmodbus/results/fuzz-g3/RESULTS.md` |
| Input-drafting oracle | `targets/libmodbus/harness/run_oracle.py` |
| Full issue ledger (every defect, fixed/partial/not-fixable) | `CORRECTIONS_LOG.md` |

**Open items:** the human baseline (kit ready, needs a person), a second-rater
adjudication pass, and the libcoap / mongoose input-drafting oracles.

*To regenerate everything from the verdict store:*
```bash
stage2/.venv/Scripts/python.exe stage2/targets/report/build_final_report.py
```

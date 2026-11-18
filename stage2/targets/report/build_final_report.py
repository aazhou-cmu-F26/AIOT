"""Build the one-shot Stage 2 report: professional figures + a self-contained
HTML report that renders everything inline (figures embedded as base64).

Reproducible: reads targets/verdicts.csv, _adjudication/sweep_packets.jsonl and
results/fuzz-g3/summary.json; the pass-1 budget, the audit's original claims, the
static-tool outcome and the fragmentation/arc narrative are encoded here from the
source docs (STAGE2_EVALUATION_REPORT.md, METHODOLOGY_CONTRACT.md). Re-running
regenerates the figures and STAGE2_REPORT.html identically.

    stage2/.venv/Scripts/python.exe targets/report/build_final_report.py
"""
from __future__ import annotations
import csv, json, sys, base64
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = Path(__file__).resolve().parent
STAGE2 = HERE.parents[1]
sys.path.insert(0, str(STAGE2))
from targets.scoring import wilson  # noqa: E402

FIG = HERE / "figures"; FIG.mkdir(parents=True, exist_ok=True)
VERDICTS = STAGE2 / "targets" / "verdicts.csv"
SWEEP_PK = STAGE2 / "targets" / "_adjudication" / "sweep_packets.jsonl"
FUZZ = STAGE2 / "targets" / "libmodbus" / "results" / "fuzz-g3" / "summary.json"

TARGETS = ["libmodbus", "libcoap", "mongoose"]
TCVE = {"libmodbus": "CVE-2022-0367 (2022)", "libcoap": "CVE-2025-34468 (2025)", "mongoose": "CVE-2026-52056 (2026)"}
CONDS = ["source-agentic", "source-one-shot", "crash-given", "triage-hypothesis"]
CLABEL = {"source-agentic": "C1 agentic", "source-one-shot": "C0 one-shot",
          "crash-given": "crash-given", "triage-hypothesis": "triage"}
INK = "#1b2733"; MUT = "#5b6b7b"; GRID = "#dde3ea"
TCOL = {"libmodbus": "#c44e52", "libcoap": "#4c72b0", "mongoose": "#55a868"}

plt.rcParams.update({"font.size": 10, "axes.edgecolor": INK, "text.color": INK,
                     "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
                     "figure.facecolor": "white", "savefig.facecolor": "white"})


def despine(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def cells(source):
    agg = defaultdict(lambda: [0, 0])
    for r in csv.DictReader(open(VERDICTS, encoding="utf-8")):
        if r.get("source") != source or r["condition"] in ("input-drafting", "recall-probe"):
            continue
        v = r["anyofk_verdict"]
        if v in ("not_applicable", "unscored"):
            continue
        agg[(r["target"], r["condition"])][1] += 1
        if v == "correct":
            agg[(r["target"], r["condition"])][0] += 1
    return agg


# ---------------------------------------------------------------- figures
def fig_arc():
    steps = [("Stage 1", "libcoap lab\n(primary target)"),
             ("Stage 2:\n3 case studies", "libcoap · libmodbus · mongoose\nby 3 people, no shared format"),
             ("Methodology\ncontract", "one condition vocab,\nschema, oracle"),
             ("Pass 1 sweep", "279 runs · $17.48\nkeyword scorer"),
             ("Audit", "wrong revisions, hints,\nscorer, no CIs"),
             ("Pass 2:\naligned redo", "de-hinted · pinned ·\nblind adjudication · oracles")]
    fig, ax = plt.subplots(figsize=(12, 2.6)); ax.axis("off")
    n = len(steps); x0, w, gap = 0.3, 1.7, 0.42
    cols = ["#6b7b8c", "#c98b3a", "#3a8a7a", "#4c72b0", "#c44e52", "#3a7a3a"]
    for i, (t, s) in enumerate(steps):
        x = x0 + i * (w + gap)
        ax.add_patch(FancyBboxPatch((x, 0.4), w, 1.6, boxstyle="round,pad=0.04,rounding_size=0.12",
                                    fc=cols[i], ec="none", alpha=0.92))
        ax.text(x + w/2, 1.55, t, ha="center", va="center", color="white", fontsize=9.5, fontweight="bold")
        ax.text(x + w/2, 0.92, s, ha="center", va="center", color="white", fontsize=7.4)
        if i < n - 1:
            ax.add_patch(FancyArrowPatch((x + w, 1.2), (x + w + gap, 1.2),
                                         arrowstyle="-|>", mutation_scale=14, color=INK, lw=1.4))
    ax.set_xlim(0, x0 + n * (w + gap)); ax.set_ylim(0, 2.3)
    ax.set_title("The project arc — from three fragmented case studies to one aligned methodology",
                 fontsize=11, fontweight="bold", loc="left")
    fig.savefig(FIG / "fig_arc.png", dpi=150, bbox_inches="tight"); plt.close(fig)


def fig_fragmentation():
    dims = ["Condition labels", "Logging / format", "Model named?", "Source revision", "Scoring"]
    data = {
        "libcoap (Chen)": ["C0 / C1 / C2", "pack files + notes", "partly", "7cf7465b (5 files unverified)", "keyword"],
        "libmodbus (us)": ["source-review / fuzz", "driver/run_task", "yes", "mixed: v3.1.10 fixed in C1", "keyword"],
        "mongoose (3rd)": ["traditional / AI-assisted", "cursor export", "no (unnamed)", "b1c2ffe1 (annotated tree)", "keyword"],
    }
    aligned = ["source-one-shot / source-agentic /\ncrash-given / triage / input-drafting /\nrecall-probe",
               "one schema + verdicts.csv", "yes (OpenRouter ids)",
               "one SHA-pinned tree / target\n(+ revision test)", "blind rubric → verdicts.csv"]
    fig, ax = plt.subplots(figsize=(12, 4.6)); ax.axis("off")
    cols = list(data.keys()); ncol = len(cols) + 2
    cw = 1.0 / ncol
    # header
    heads = ["dimension"] + cols + ["→ ALIGNED"]
    for j, h in enumerate(heads):
        ax.add_patch(plt.Rectangle((j*cw, 0.86), cw, 0.12, fc=("#3a7a3a" if j == ncol-1 else "#324"), ec="white"))
        ax.text(j*cw + cw/2, 0.92, h, ha="center", va="center", color="white", fontsize=8, fontweight="bold")
    for i, d in enumerate(dims):
        y = 0.86 - (i+1)*0.165
        ax.add_patch(plt.Rectangle((0, y), cw, 0.165, fc="#eef2f6", ec="white"))
        ax.text(0.01, y+0.082, d, ha="left", va="center", fontsize=7.6, color=INK, fontweight="bold")
        for j, c in enumerate(cols):
            ax.add_patch(plt.Rectangle(((j+1)*cw, y), cw, 0.165, fc="#fbe9e7", ec="white"))
            ax.text((j+1)*cw+cw/2, y+0.082, data[c][i], ha="center", va="center", fontsize=6.8, color="#7a2e2a")
        ax.add_patch(plt.Rectangle(((ncol-1)*cw, y), cw, 0.165, fc="#e7f3e9", ec="white"))
        ax.text((ncol-1)*cw+cw/2, y+0.082, aligned[i], ha="center", va="center", fontsize=6.6, color="#245c2a")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_title("Before: three contributors, nothing comparable.   After: one contract.",
                 fontsize=11, fontweight="bold", loc="left")
    fig.savefig(FIG / "fig_fragmentation.png", dpi=150, bbox_inches="tight"); plt.close(fig)


def fig_accuracy(st):
    fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharey=True)
    for ax, t in zip(axes, TARGETS):
        xs = range(len(CONDS))
        ys = [100*wilson(*st.get((t, c), (0, 0)))[0] for c in CONDS]
        bars = [st.get((t, c), (0, 0)) for c in CONDS]
        los, his = [], []
        for c in CONDS:
            cc, nn = st.get((t, c), (0, 0)); p, lo, hi = wilson(cc, nn)
            los.append(100*(p-lo)); his.append(100*(hi-p))
        ax.bar(xs, ys, color=TCOL[t], width=0.62, zorder=3)
        ax.errorbar(xs, ys, yerr=[los, his], fmt="none", ecolor=INK, elinewidth=1.3, capsize=4, zorder=4)
        for x, (cc, nn) in zip(xs, bars):
            ax.text(x, 3, f"{cc}/{nn}", ha="center", color="white", fontsize=8, zorder=5)
        ax.set_title(f"{t}\n{TCVE[t]}", fontsize=9.5)
        ax.set_xticks(list(xs)); ax.set_xticklabels([CLABEL[c] for c in CONDS], rotation=30, ha="right", fontsize=8)
        ax.set_ylim(0, 100); ax.yaxis.grid(True, color=GRID, zorder=0); ax.set_axisbelow(True); despine(ax)
    axes[0].set_ylabel("any-of-3 accuracy (%)\nover scored runs", fontsize=9)
    fig.suptitle("Corrected accuracy, Wilson 95% CIs  —  libmodbus is training-contaminated (see recall map)",
                 fontsize=10.5, fontweight="bold")
    fig.tight_layout(); fig.savefig(FIG / "fig_accuracy.png", dpi=150, bbox_inches="tight"); plt.close(fig)


def fig_old_vs_new(sw, pre):
    # (label, audit claim, re-adjudicated old, corrected sweep)
    rows = [
        ("libmodbus C0", 19, 100*wilson(*pre.get(("libmodbus","source-one-shot"),(0,0)))[0],
         100*wilson(*sw.get(("libmodbus","source-one-shot"),(0,0)))[0]),
        ("libmodbus crash", 100, 100*wilson(*pre.get(("libmodbus","crash-given"),(0,0)))[0],
         100*wilson(*sw.get(("libmodbus","crash-given"),(0,0)))[0]),
        ("mongoose crash", 89, 100*wilson(*pre.get(("mongoose","crash-given"),(0,0)))[0],
         100*wilson(*sw.get(("mongoose","crash-given"),(0,0)))[0]),
        ("mongoose C1", 83, 100*wilson(*pre.get(("mongoose","source-agentic"),(0,0)))[0],
         100*wilson(*sw.get(("mongoose","source-agentic"),(0,0)))[0]),
    ]
    lab = [r[0] for r in rows]; x = range(len(rows)); w = 0.26
    fig, ax = plt.subplots(figsize=(9.5, 4.3))
    series = [("audit claim", [r[1] for r in rows], "#b0b7c0"),
              ("re-adjudicated (same runs)", [r[2] for r in rows], "#c98b3a"),
              ("corrected sweep (new runs)", [r[3] for r in rows], "#4c72b0")]
    for k, (name, vals, col) in enumerate(series):
        xb = [i + (k-1)*w for i in x]
        ax.bar(xb, vals, w, label=name, color=col, zorder=3)
        for xi, v in zip(xb, vals):
            ax.text(xi, v+1.5, f"{v:.0f}", ha="center", fontsize=7.5)
    ax.set_xticks(list(x)); ax.set_xticklabels(lab, fontsize=9)
    ax.set_ylim(0, 112); ax.set_ylabel("accuracy (%)")
    ax.set_title("What the first pass claimed vs what the data shows\n(re-adjudicated = same transcripts, correct rubric; sweep = fresh de-hinted runs)",
                 fontsize=10, fontweight="bold")
    ax.yaxis.grid(True, color=GRID, zorder=0); ax.set_axisbelow(True); despine(ax)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig(FIG / "fig_old_vs_new.png", dpi=150, bbox_inches="tight"); plt.close(fig)


def fig_contamination():
    rp = [json.loads(l) for l in SWEEP_PK.read_text(encoding="utf-8").splitlines() if l.strip()]
    rp = [r for r in rp if r["condition"] == "recall-probe"]
    cve_short = {"libmodbus": "CVE-2022-0367", "libcoap": "CVE-2025-34468", "mongoose": "CVE-2026-52056"}
    mat = defaultdict(dict)
    for r in rp:
        mat[r["model"]][r["target"]] = cve_short[r["target"]] in r["raw_text"]
    models = sorted(mat)
    fig, ax = plt.subplots(figsize=(8, 5))
    for yi, m in enumerate(models):
        for xi, t in enumerate(TARGETS):
            named = mat[m].get(t, False)
            ax.scatter(xi, yi, s=230, marker="s", color=("#c44e52" if named else "#eef2f6"),
                       edgecolor=INK, linewidth=0.5, zorder=3)
            if named:
                ax.text(xi, yi, "✓", ha="center", va="center", color="white", fontsize=10)
    ax.set_xticks(range(3)); ax.set_xticklabels([f"{t}\n{TCVE[t].split(' ')[0]}\n{TCVE[t].split('(')[1][:-1]}" for t in TARGETS], fontsize=8)
    ax.set_yticks(range(len(models))); ax.set_yticklabels(models, fontsize=8)
    ax.set_title("Recall probe — did the model name the TARGET CVE from memory?\nred = contaminated (2022 bug); no model knew the 2025/2026 bugs", fontsize=10, fontweight="bold")
    ax.set_xlim(-0.5, 2.5); ax.set_ylim(-0.6, len(models)-0.4); despine(ax)
    fig.tight_layout(); fig.savefig(FIG / "fig_contamination.png", dpi=150, bbox_inches="tight"); plt.close(fig)


def fig_static():
    hit = {"libmodbus": True, "libcoap": False, "mongoose": False}
    fig, ax = plt.subplots(figsize=(7.5, 2.4)); ax.axis("off")
    ax.text(0.0, 0.86, "cppcheck on the pinned files — flags the target defect line?", fontsize=10, fontweight="bold")
    for i, t in enumerate(TARGETS):
        x = 0.06 + i*0.32
        c = "#55a868" if hit[t] else "#c44e52"
        ax.add_patch(FancyBboxPatch((x, 0.18), 0.26, 0.5, boxstyle="round,pad=0.02,rounding_size=0.06", fc=c, alpha=0.9, ec="none"))
        ax.text(x+0.13, 0.52, t, ha="center", color="white", fontsize=9, fontweight="bold")
        ax.text(x+0.13, 0.35, "HIT" if hit[t] else "miss", ha="center", color="white", fontsize=11, fontweight="bold")
        ax.text(x+0.13, 0.24, ("duplicated condition" if hit[t] else "semantic bug"), ha="center", color="white", fontsize=6.6)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    fig.savefig(FIG / "fig_static.png", dpi=150, bbox_inches="tight"); plt.close(fig)


def fig_fuzz():
    s = json.loads(FUZZ.read_text())
    arms = [("naive seeds", [t["iters_to_crash"] for t in s["naive"]["trials"]], "#b0b7c0"),
            ("AI-drafted seeds", [t["iters_to_crash"] for t in s["ai"]["trials"]], "#4c72b0")]
    fig, ax = plt.subplots(figsize=(8, 3.6))
    for i, (name, vals, col) in enumerate(arms):
        ax.scatter(vals, [i]*len(vals), s=90, color=col, edgecolor=INK, zorder=3, label=name)
        import statistics
        ax.scatter([statistics.median(vals)], [i], marker="|", s=900, color=INK, zorder=4)
    ax.set_yticks([0, 1]); ax.set_yticklabels([a[0] for a in arms], fontsize=9)
    ax.set_xlabel("iterations to first ASan crash (5 trials/arm, lower is better)")
    ax.set_title("Fuzzing: AI-drafted seeds reach the crash ~6× faster\n(| = median; both arms crash 5/5)", fontsize=10, fontweight="bold")
    ax.xaxis.grid(True, color=GRID, zorder=0); ax.set_axisbelow(True); despine(ax); ax.set_ylim(-0.6, 1.6)
    fig.tight_layout(); fig.savefig(FIG / "fig_fuzz.png", dpi=150, bbox_inches="tight"); plt.close(fig)


def fig_budget():
    p1 = [("libcoap C0 rerun", 5.91), ("libmodbus early C0 (wrong CVE)", 3.89),
          ("libmodbus C0 redo", 2.54), ("libcoap C1", 2.15), ("libmodbus C1 (fixed code)", 1.01),
          ("Triage/C2/Input ×3", 1.18), ("mongoose C0/C1", 0.70), ("libmodbus fuzz", 0.19)]
    waste = {"libmodbus early C0 (wrong CVE)", "libmodbus C1 (fixed code)"}
    labels = [a for a, _ in p1][::-1]; vals = [b for _, b in p1][::-1]
    cols = ["#c44e52" if a in waste else "#6b7b8c" for a, _ in p1][::-1]
    fig, ax = plt.subplots(figsize=(8.5, 4))
    ax.barh(range(len(vals)), vals, color=cols, zorder=3)
    for i, v in enumerate(vals):
        ax.text(v+0.05, i, f"${v:.2f}", va="center", fontsize=7.5)
    ax.set_yticks(range(len(labels))); ax.set_yticklabels(labels, fontsize=7.6)
    ax.set_xlabel("USD"); ax.xaxis.grid(True, color=GRID, zorder=0); ax.set_axisbelow(True); despine(ax)
    ax.set_title("Pass-1 spend $17.48 (red = $4.90 on runs that couldn't detect the bug).\nPass-2 corrected sweep: $5.91.", fontsize=9.5, fontweight="bold")
    fig.tight_layout(); fig.savefig(FIG / "fig_budget.png", dpi=150, bbox_inches="tight"); plt.close(fig)


def _img(name):
    return "data:image/png;base64," + base64.b64encode((FIG / name).read_bytes()).decode()


def acc_table(sw):
    out = []
    for t in TARGETS:
        cellrow = [f"<td>{t}</td>"]
        for c in CONDS:
            cc, nn = sw.get((t, c), (0, 0)); p, lo, hi = wilson(cc, nn)
            cellrow.append(f"<td class='n'>{p*100:.0f}% <span class='ci'>[{lo*100:.0f},{hi*100:.0f}] {cc}/{nn}</span></td>")
        out.append("<tr>" + "".join(cellrow) + "</tr>")
    return "\n".join(out)


def build_html(sw):
    acc = acc_table(sw)
    html = HTML.format(
        acc_rows=acc,
        f_arc=_img("fig_arc.png"), f_frag=_img("fig_fragmentation.png"),
        f_acc=_img("fig_accuracy.png"), f_oldnew=_img("fig_old_vs_new.png"),
        f_cont=_img("fig_contamination.png"), f_static=_img("fig_static.png"),
        f_fuzz=_img("fig_fuzz.png"), f_budget=_img("fig_budget.png"),
    )
    (STAGE2 / "STAGE2_REPORT.html").write_text(html, encoding="utf-8")


HTML = r"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Stage 2 — AI-Assisted Vulnerability Discovery</title>
<style>
:root{{--ink:#1b2733;--mut:#5b6b7b;--line:#d9e0e8;--bg:#fff;--card:#f6f8fa;--accent:#2f5d9e;--warn:#c44e52;--ok:#2f7a44;--max:760px}}
@media (prefers-color-scheme:dark){{:root:not([data-theme=light]){{--ink:#e6edf3;--mut:#9aa7b4;--line:#2a333d;--bg:#0f141a;--card:#161c24;--accent:#6f9be0}}}}
:root[data-theme=dark]{{--ink:#e6edf3;--mut:#9aa7b4;--line:#2a333d;--bg:#0f141a;--card:#161c24;--accent:#6f9be0}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 -apple-system,Segoe UI,Roboto,Helvetica,sans-serif;padding:0 16px}}
.wrap{{max-width:var(--max);margin:0 auto;padding:36px 0 80px}}
h1{{font-size:1.8rem;line-height:1.2;margin:0 0 .2em}}h2{{font-size:1.3rem;margin:2.2em 0 .5em;padding-bottom:.25em;border-bottom:2px solid var(--line)}}
h3{{font-size:1.06rem;margin:1.5em 0 .3em;color:var(--accent)}}
.lede{{color:var(--mut);font-size:1.02rem}}
.tag{{display:inline-block;background:var(--card);border:1px solid var(--line);border-radius:20px;padding:2px 11px;font-size:.8rem;color:var(--mut);margin:.1em .2em .1em 0}}
figure{{margin:1.3em 0}}figure img{{width:100%;border:1px solid var(--line);border-radius:10px;background:#fff}}
figcaption{{color:var(--mut);font-size:.84rem;margin-top:.4em}}
table{{border-collapse:collapse;width:100%;font-size:.9rem;margin:.7em 0}}
th,td{{text-align:left;padding:.5em .6em;border-bottom:1px solid var(--line);vertical-align:top}}th{{color:var(--mut);font-weight:600}}
td.n{{font-weight:700;white-space:nowrap}}.ci{{color:var(--mut);font-weight:400;font-size:.82em}}
.callout{{background:var(--card);border-left:3px solid var(--accent);border-radius:8px;padding:.8em 1.1em;margin:1.2em 0}}
.warn{{border-left-color:var(--warn);background:color-mix(in srgb,var(--warn) 9%,transparent)}}
.ok{{border-left-color:var(--ok);background:color-mix(in srgb,var(--ok) 9%,transparent)}}
code{{background:var(--card);padding:.08em .35em;border-radius:4px;font-size:.88em}}
ol,ul{{padding-left:1.25em}}li{{margin:.2em 0}}
.small{{font-size:.85rem;color:var(--mut)}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px;margin:1.3em 0}}
.kpi{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}}.kpi b{{display:block;font-size:1.5rem}}.kpi span{{color:var(--mut);font-size:.8rem}}
hr{{border:none;border-top:1px solid var(--line);margin:2.4em 0}}
</style></head><body><div class="wrap">

<h1>AI-Assisted Vulnerability Discovery in IoT C Libraries</h1>
<p class="lede">A study of how increasing levels of AI involvement change the discovery of known
memory-safety bugs, across three real CVEs — and of how three independently-built case studies were
unified into one consistent, auditable methodology.</p>
<p><span class="tag">CMU AIoT graduate project</span><span class="tag">Stage 2</span>
<span class="tag">3 targets · 11 models · 6 conditions</span><span class="tag">generated 2026-11-18</span></p>

<div class="callout"><b>What this report is.</b> A self-contained account of the whole Stage 2 effort,
from the first fragmented experiments to the final corrected results. It reads top-to-bottom with no
prior context. Every number traces to <code>targets/verdicts.csv</code>; every figure is generated by
<code>targets/report/build_final_report.py</code>. Verdicts are a single-rater (blind) pass; no human
second rater has reviewed them yet.</div>

<div class="kpis">
<div class="kpi"><b>3</b><span>CVEs, one per target, chosen to vary bug visibility</span></div>
<div class="kpi"><b>6</b><span>assistance conditions, one shared vocabulary</span></div>
<div class="kpi"><b>234+279</b><span>corrected-sweep + original runs, all re-scored</span></div>
<div class="kpi"><b>4/11</b><span>models recalled the 2022 CVE — contamination, controlled</span></div>
</div>

<h2>1. The project, and where it started</h2>
<p>The Statement of Work frames three stages that share one target, one information boundary, one
environment and one oracle: <b>Stage 1</b> a human-led traditional baseline; <b>Stage 2</b> human-guided
AI assistance; <b>Stage 3</b> a reduced agent. The research question asks how the levels differ in
validated success, false candidates, reproducibility, human intervention, cost and failure modes — and
the SOW is explicit that <i>findings count only when they pass a shared oracle</i>, and that the goal is
to <i>rediscover and validate</i> known bugs, not to find zero-days.</p>
<p>Stage 2 narrows that to a concrete question: <b>given a known, publicly disclosed CVE in a real C
library, can current models localise it — and how much does that depend on what the model is shown and
how it is asked?</b></p>

<p>Crucially, Stage 2 did not begin as one experiment. It began as <b>three</b>, built independently:</p>
<ul>
<li><b>libcoap</b> (contributor "Chen") — conditions labelled C0 / C1 / C2, source supplied as "pack" files.</li>
<li><b>libmodbus</b> (this author) — a "source-review / fuzzing" split, driven through a logging harness.</li>
<li><b>mongoose</b> (a third contributor) — a "traditional / AI-assisted" split, run through a coding
assistant whose <b>model was never recorded</b>.</li>
</ul>
<p>They shared a topic and nothing else: different condition names, different logging shapes, a different
(or missing) model identity, different source revisions, and three different ad-hoc scorers. <b>They were
not comparable.</b> The entire point of the work this report describes was to make them comparable — to
align three fragmented studies onto one methodology so the targets could actually be contrasted.</p>

<figure><img src="{f_arc}" alt="project arc"><figcaption>The arc: Stage 1 → three fragmented Stage 2
studies → a methodology contract → an initial sweep → an audit → the corrected, aligned pass.</figcaption></figure>

<figure><img src="{f_frag}" alt="fragmentation vs alignment"><figcaption>Where the three case studies
disagreed (red), and the single aligned standard each dimension was pulled onto (green).</figcaption></figure>

<h2>2. The alignment standard (how consistency was enforced)</h2>
<p>A <b>methodology contract</b> replaced the three ad-hoc designs with one. Consistency is enforced by
files and tests, not by good intentions:</p>
<ol>
<li><b>One condition vocabulary</b> for all targets (table below) — each run belongs to exactly one.</li>
<li><b>One record schema and one verdict store</b> (<code>verdicts.csv</code>): every run logs its model,
prompt, pinned commit, what was <i>disclosed</i> and <i>withheld</i>, cost, repeats and failure mode.</li>
<li><b>One SHA-pinned source tree per target</b> (<code>vendor/MANIFEST.txt</code> + a per-target
<code>target.yaml</code>), with a test proving each condition loads the pinned, <i>vulnerable</i> revision.</li>
<li><b>One information boundary</b>: de-hinted prompt templates shared across targets, with a test that
fails if a non-hinted prompt names the CVE, CWE, fix, mechanism or target function.</li>
<li><b>One scoring method</b>: blind human-style adjudication against a written per-CVE rubric, stored as
data with a rationale — never keyword matching; input-drafting scored only by a runtime oracle.</li>
<li><b>One statistics convention</b>: per-run units, any-of-3, Wilson 95% intervals, no pooling of
non-comparable cells.</li>
</ol>

<table><tr><th>Condition</th><th>What the model is given</th><th>What it measures</th></tr>
<tr><td>source-one-shot (C0)</td><td>the whole source file(s), one turn</td><td>unaided localisation in a large file</td></tr>
<tr><td>source-agentic (C1)</td><td>a read-only file tree + READ/GREP/FINAL</td><td>self-navigation to the bug</td></tr>
<tr><td>crash-given</td><td>the ASan report + the source</td><td>root-cause from runtime evidence</td></tr>
<tr><td>triage-hypothesis</td><td>the function excerpt</td><td>recognition when the right code is selected</td></tr>
<tr><td>triage-hinted</td><td>excerpt + the stated mechanism (labelled)</td><td>the lift from an explicit hint</td></tr>
<tr><td>input-drafting</td><td>the bug, handed over; draft a trigger</td><td>turning knowledge into a working exploit (oracle only)</td></tr>
</table>

<h3>The three targets</h3>
<table><tr><th>Target</th><th>CVE</th><th>Defect</th><th>Visibility</th></tr>
<tr><td>libmodbus v3.1.6</td><td>CVE-2022-0367</td><td>fn-0x17 guard tests the read index twice, never the write index → negative-index heap write</td><td>subtle (one duplicated token in ~1,900 lines)</td></tr>
<tr><td>libcoap 7cf7465b</td><td>CVE-2025-34468</td><td>unchecked <code>memcpy</code> of a Proxy-Uri host into a 256-byte static buffer</td><td>obvious once the function is on screen</td></tr>
<tr><td>mongoose 7.21</td><td>CVE-2026-52056</td><td><code>skip_chunk</code> off-by-one: reads <code>buf[i+1]</code> when <code>i==len</code></td><td>off-by-one in a short parser</td></tr>
</table>

<h2>3. Two experimental passes</h2>
<p><b>Pass 1 — the initial sweep.</b> The three studies were run out to 11 models × the condition ladder
× 3 targets: 279 candidate records, <b>$17.48</b> of API spend, scored by an automated keyword matcher
that called 102 of 277 responses "correct". This produced a headline — a "C1 agentic paradox" (more tools
and context made models <i>worse</i>) and "libmodbus is hard (19%)".</p>

<p><b>The audit.</b> A structured review found the headline unsupported, because the three studies'
inconsistencies had leaked into the results:</p>
<div class="callout warn"><ul style="margin:0">
<li><b>Wrong revision.</b> libmodbus's agentic runs were served v3.1.10, where the bug is <i>already fixed</i> — it literally wasn't present.</li>
<li><b>Leaked answers.</b> Every triage/crash prompt stated the flaw mechanism; mongoose's agentic file-tree named the vulnerable function; libcoap's prompt steered models at proxy code.</li>
<li><b>A broken scorer.</b> Accuracy came from substring matching over converter-written text, so a refusal and several wrong hypotheses counted as "correct"; "19%" also pooled 56 records from a <i>different</i> CVE and counted per-candidate, not per-run.</li>
<li><b>No statistics, no contamination check.</b> single samples, no confidence intervals, and no test of whether a 2022 CVE was simply memorised.</li>
</ul></div>

<p><b>Pass 2 — the aligned correction.</b> Infrastructure was rebuilt to the contract (concrete schema,
fixed agentic harness, de-hinted shared templates, pinned trees, a raw-only converter, a Wilson scorer,
leak/harness/revision tests). The non-detecting data was quarantined with a written reason. A fresh
<b>234-run sweep ($5.91)</b> was run on the corrected setup; <b>both</b> the old transcripts and the new
runs were re-scored by blind rubric into one <code>verdicts.csv</code>; runnable oracles and three tool
baselines were added. The rest of this report is the result.</p>

<h2>4. Results</h2>

<h3>4.1 What the first pass claimed vs what the data shows</h3>
<figure><img src="{f_oldnew}" alt="old vs new"><figcaption>Grey = the first pass's claim. Orange =
the <i>same transcripts</i> re-scored with a correct rubric. Blue = fresh de-hinted runs on the aligned
setup. The headline numbers were largely scorer and prompt artifacts.</figcaption></figure>
<p>The "19%" for libmodbus C0 was a scoring artifact — the same answers re-scored are ~69%. The "100%"
and "89%" crash-given numbers were overstated by local models being graded as fully correct. And mongoose's
agentic "83%" <b>collapses to 30%</b> once the file-tree annotation that named <code>skip_chunk</code> is
removed — the hint, not the model, was doing the work.</p>

<h3>4.2 Corrected accuracy, with confidence intervals</h3>
<figure><img src="{f_acc}" alt="corrected accuracy"><figcaption>Fresh sweep, any-of-3, Wilson 95% CIs.
crash-given / C0 / triage ran on cheap+local models only (the budget put frontier models on the agentic
and recall conditions), so those bars reflect that model mix. Cells are small — read the intervals, not
the point estimates.</figcaption></figure>
<table><tr><th>target</th><th>C1 agentic</th><th>C0 one-shot</th><th>crash-given</th><th>triage</th></tr>
{acc_rows}
</table>

<h3>4.3 The contamination control — the result that reframes the rest</h3>
<figure><img src="{f_cont}" alt="contamination map"><figcaption>From memory only: which models named
the target CVE. libmodbus's 2022 bug was recalled by four models; nobody knew libcoap's 2025 or mongoose's
2026 bug.</figcaption></figure>
<div class="callout warn"><b>libmodbus's numbers are a memorisation-inflated upper bound.</b> The clean
evidence of genuine capability comes from libcoap and mongoose, whose CVEs post-date every model's training
cutoff. Several models also <i>hallucinated</i> plausible CVE ids — a caution against trusting recalled
identifiers at all.</div>

<h3>4.4 The "agentic paradox", dissected</h3>
<p>The first pass's central claim — that tools and context made models worse — does not survive the
aligned redo. Three mundane causes explain it: a <b>file-tree annotation</b> (removing it drops mongoose
C1 from ~83% to 30%); <b>genuine difficulty</b> of un-annotated search (libcoap C1 is 8% — only one model
navigated the 96-file tree to the bug); and <b>content moderation</b> (many agentic runs returned 0 bytes,
now recorded as filtered and excluded, not counted as failures). A related effect: for libcoap, handing
the model the <i>excerpt</i> (triage, 67%) beats hiding the bug in a <i>4-file set</i> (one-shot, 0%). The
bug is easy to explain and hard to find. One model re-found a genuine, separate proxy use-after-free along
the way — recorded as a real non-target finding, not a miss.</p>

<h3>4.5 Handing over the bug is not enough (input-drafting, oracle-scored)</h3>
<p>In input-drafting the vulnerability is given and the model only has to produce a trigger frame. Scored
by replaying each frame through a live AddressSanitizer server, <b>only 2 of 12 libmodbus frames actually
fired the bug</b> (confirmed at <code>modbus.c:980</code>). The rest failed instructively: one model
<b>refused on moderation</b> ("a ready-to-send exploit for industrial software"), and the 7B local models
produced <b>malformed Modbus framing</b>. Capability here is gated by safety behaviour and protocol
precision as much as by understanding.</p>

<h3>4.6 Tool baselines — the real yardstick</h3>
<figure><img src="{f_static}" alt="static tool"><figcaption>A free static linter (cppcheck) on the
pinned files.</figcaption></figure>
<figure><img src="{f_fuzz}" alt="fuzzing"><figcaption>Fuzzing, 5 trials per arm, equal budget.</figcaption></figure>
<p>cppcheck flags exactly the one <b>classic-pattern</b> bug — libmodbus's duplicated condition — and
misses both semantic bugs; note that the one it catches is also the contaminated one. In fuzzing,
AI-drafted seeds reach the crash <b>~6× faster</b> than naive seeds (median 38 vs 226 iterations). This
<i>reverses</i> the first pass's single-trial claim that AI seeds "found nothing"; the honest caveat is
that the AI corpus contained two confirmed triggers, so a seed near the crash needs little mutation.</p>

<h2>5. Integrity — mistakes caught in the corrected pass itself</h2>
<p>A clean-experiment claim is only credible if it reports its own errors. The corrected pass made three,
each caught by a sanity check rather than assumed away: a <b>resume-dedup bug</b> that wasted ~$4.28 on
redundant runs (caught when "runs completed" exceeded the matrix); a <b>de-hinted crash-given prompt that
shipped no source</b> (caught when models refused to localise without code); and a <b>wrong server config</b>
in input-drafting (caught when a hand-built trigger fired but the model frames didn't). None changed a
conclusion — but each would have quietly biased a result if unquestioned, which is the exact failure mode
this work exists to avoid.</p>

<h2>6. Budget</h2>
<figure><img src="{f_budget}" alt="budget"><figcaption>Pass-1 spend, with the ~$4.90 spent on runs that
could not detect the target bug in red.</figcaption></figure>
<p>Pass 1 cost <b>$17.48</b> against an SOW ceiling of "about $5, under $10" — ~28% of it on runs that
could not detect the bug (wrong CVE / fixed revision). The corrected pass added <b>$5.91</b> of useful
spend (plus ~$4.28 lost to the dedup bug, logged). Future spend was gated on explicit approval.</p>

<h2>7. Limitations</h2>
<ul>
<li><b>Single-rater verdicts.</b> No human second pass; inter-rater agreement unmeasured (a blinded packet set is staged).</li>
<li><b>Model-mix confound.</b> crash-given / C0 / triage ran on cheap+local models only, so those are not comparable to the frontier-inclusive agentic rows.</li>
<li><b>Small n.</b> cells are 9–13 runs; CIs are wide.</li>
<li><b>Oracle coverage.</b> only libmodbus input-drafting has a runnable oracle so far.</li>
<li><b>No completed human baseline.</b> the compliant kit exists but has not been run; contamination means any "time-to-find" metric would be carryover-biased anyway.</li>
<li><b>Contamination is self-reported</b> by the models in the recall probe.</li>
</ul>

<h2>8. Conclusions</h2>
<div class="callout ok"><p style="margin:.2em 0">With contamination controlled and the answer kept out of
the prompt, current models <b>localise a memory-safety bug reliably when handed the right excerpt or an
ASan report</b> (triage/crash ≈ 50–67% on the post-cutoff targets), but <b>agentic needle-in-a-haystack
discovery is hard</b> (8% on libcoap) and <b>turning a known bug into a working trigger is harder still</b>
(2/12). A free linter already catches the one classic-pattern bug — which is also the one the models had
memorised.</p>
<p style="margin:.4em 0 .2em"><b>The defensible claim is not "AI finds vulnerabilities," but: AI meaningfully
assists a human who has already narrowed the search — as a triage reader and a fuzzing-seed generator — on
exactly the semantic bugs that cheap tools miss</b>, with reliability still bounded by safety refusals,
context limits, and how much the task points the way.</p></div>
<p>And methodologically: the value of this exercise was the <b>alignment</b> — three incomparable case
studies pulled onto one pinned, de-hinted, blind-scored, oracle-backed standard, so that for the first time
the three targets can be read side by side and the headline claims can be checked rather than believed.</p>

<hr>
<p class="small">Reproducibility — verdicts: <code>targets/verdicts.csv</code> · rubrics:
<code>targets/RUBRICS.md</code> · scorer: <code>targets/scoring.py</code> · this report + figures:
<code>targets/report/build_final_report.py</code> · companion docs:
<code>STAGE2_FINAL_REPORT.md</code>, <code>STAGE2_CORRECTED_RESULTS.md</code>, <code>CORRECTIONS_LOG.md</code>.
Open items: human baseline (kit ready), second-rater pass, libcoap/mongoose input-drafting oracles.</p>
</div></body></html>"""


def main():
    sw, pre = cells("sweep"), cells("preexisting")
    fig_arc(); fig_fragmentation(); fig_accuracy(sw); fig_old_vs_new(sw, pre)
    fig_contamination(); fig_static(); fig_fuzz(); fig_budget()
    build_html(sw)
    print("figures ->", FIG)
    print("report  ->", STAGE2 / "STAGE2_REPORT.html")


if __name__ == "__main__":
    main()

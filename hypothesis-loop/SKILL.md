---
name: hypothesis-loop
description: Use when running an unattended multi-round research, optimization, or audit loop (overnight, autonomous, /loop-driven or cron-driven) where Sonnet iterates and each round should be steered by a hypothesis check before spending compute or money. Triggers include "run this overnight", "autonomous loop", "keep iterating until", "optimization loop", "self-paced research loop".
---

# Hypothesis-Gated Loop

## Overview

An unattended loop where the main thread (Sonnet) does the iteration work, but **every round is gated by an Opus subagent that considers hypotheses before any compute or spend.** The gate is a structural defense against local-optimum momentum — Sonnet executes well but drifts toward variations of one idea rather than recognizing when a different *family* of action would yield more information.

**Core principle:** State lives on disk, not in context. Every round re-reads `PROTOCOL.md` + `STATE.json` fresh, runs exactly one round, persists, and schedules the next. The session survives all night because nothing depends on remembering prior rounds.

**For long-running campaigns (dozens to hundreds of rounds), the hypothesis history itself must live on disk as a navigable tree, not a flat log.** A flat `LOG.md` grows past what the gate can read, so the gate starts re-proposing ideas already tried and dead. The fix is a `HYPOTHESES.json` registry: a factored tree where each *family* of approach is a branch and a root→leaf path is one complete approach. The gate reads only the **frontier** (open nodes) plus one-line branch summaries — O(frontier), not O(rounds) — so the loop's context cost stays flat no matter how long it runs. (Concept adapted from Karniadakis et al.'s GRAFT — "Graph Reduction to Adaptive Factored Trees" — which collapses a combinatorial decision space to a tree of single-path methods, and the contextual-bandit framing of the ATHENA HENA loop.)

**This is for unsupervised iteration only.** In interactive sessions where the user is actively steering, skip the gate.

## Setup (once per task)

1. Pick a working dir for loop artifacts (e.g. `overnight/` under the project). All new artifacts go there; **source data stays READ-ONLY.**
2. Copy `PROTOCOL-template.md` (in this skill dir) to `<workdir>/PROTOCOL.md` and fill every `<…>` placeholder: the north-star goal, the metric, the safety rails, the stop conditions.
3. Create `<workdir>/STATE.json`: `{"round": 0, "best": {...}, "budget": {"spent_usd_est": 0, "limit_usd": <N>}, "model": null}`. (The old flat `decisions[]` is replaced by the registry below.)
4. Create `<workdir>/HYPOTHESES.json` **only if it does not already exist**: `{"goal": "<north-star>", "vocabulary": [], "tree": {"id": "root", "children": []}, "frontier": []}`. The tree starts empty; the first round's gate populates the first families. **If the file is already present, this is a resume** — leave it untouched and continue the existing campaign (see *Resuming a campaign* below).
5. Start the loop with `/loop` (self-paced, or with an interval) pointing at the protocol: *"Run one round of `<workdir>/PROTOCOL.md`."*

## The Hypothesis Registry (`HYPOTHESES.json`) — the long-campaign memory

A tree that replaces the flat decision log. A root→leaf path is one complete approach; each child of the root is a *family* (a distinct mechanism — the structural-diversity axis, made explicit and persistent).

```jsonc
{
  "goal": "<north-star>",
  "vocabulary": ["re-extract-fresh", "parse-native-artifact", "cross-source-corroborate"],
  "tree": {
    "id": "root", "children": [
      { "id": "H1", "family": "re-extract-fresh", "status": "dead",
        "attempts": [{ "round": 2, "action": "...", "delta": -0.01, "cost_usd": 0.4,
                       "verdict": "hurt", "evidence": "rounds/round_02.md" }],
        "posterior": { "gain": "none", "confidence": "high", "cost_to_probe": "low" },
        "children": [] },
      { "id": "H2", "family": "parse-native-artifact", "status": "promising",
        "attempts": [{ "round": 3, "action": "...", "delta": 0.04, "cost_usd": 0.6,
                       "verdict": "helped", "evidence": "rounds/round_03.md" }],
        "posterior": { "gain": "med", "confidence": "med", "cost_to_probe": "low" },
        "children": [{ "id": "H2.1", "family": "parse-native-artifact",
                       "status": "untried", "attempts": [], "posterior": {} }] }
    ]
  },
  "frontier": ["H2.1"]
}
```

- **`status`**: `untried` | `active` | `promising` | `exhausted` | `dead`. A node goes `dead` after it hurts or shows no effect on repeated probes; `exhausted` when its whole subtree has been probed. Dead/exhausted nodes are recorded once and **never re-proposed**.
- **`posterior`**: qualitative tags only — `gain` (none/low/med/high), `confidence`, `cost_to_probe`. The Opus gate judges these; there is **no numeric bandit math yet**. *(TODO — revisit: replace qualitative posteriors with numeric expected-gain + visit counts and a UCB/Thompson SELECT rule. Deferred deliberately to keep the gate, not the arithmetic, as the decision-maker.)*
- **`frontier`**: the node ids eligible for selection next — untried nodes plus promising nodes worth expanding. This is the *only* part of the tree the gate must reason over in full.
- **`vocabulary`**: the menu of known families. Append-only; if the gate discovers a genuinely new mechanism it adds one here (a small nod to the papers' "growing action space" — kept minimal under the chosen scope).

### Resuming a campaign across multiple loops

The registry is the cross-loop memory: a new `/loop` pointed at the same `<workdir>` reads the existing `HYPOTHESES.json` + `STATE.json` and continues — no history is lost between loop invocations. What "continue" means depends on *why* the prior loop stopped (record this in `FINAL_REPORT.md` so the next loop knows):

- **Stopped on budget** → reset `STATE.budget.spent_usd_est` (or raise `limit_usd`) and resume; the frontier is still live, so rounds proceed immediately.
- **Stopped on empty/exhausted frontier** → the tree is fully probed at the current depth. Resuming will re-hit the stop condition *unless* you give the gate a reason to open a new family — a new scope, a relaxed rail, or a fresh metric front. State that in `PROTOCOL.md` before restarting, or the loop will correctly conclude it's done.
- **Stopped on soft convergence (N quiet rounds)** → resume as-is; reset the quiet-round counter.

Because state is fully on disk, a campaign can span days and many separate loop sessions — each loop is just another batch of rounds against the same growing tree.

## The Round Contract (every wakeup, exactly one round)

| Step | Action |
|------|--------|
| 1. MEASURE | Read `STATE.json` + the `HYPOTHESES.json` **frontier + branch summaries** (never the whole tree) + latest outputs. Recompute the current metric for the active scope. Write it to the round file. |
| 2. HYPOTHESIZE | **MANDATORY GATE.** Launch ONE `Agent(model: "opus")` given the pruned tree view (frontier + dead/exhausted list). Its job is to *consider* hypotheses (see below) and return a ranked recommendation mapped to tree nodes; it does NOT execute. |
| 3. SELECT | Treat the frontier as a bandit: expand a `promising` node, open a new family branch, or revisit-with-a-twist. Take Opus's rec, sanity-check against budget + rails, pick one (or a safe composition). Not bound to its pick if it violates a rail. Record the chosen node id + rationale in the round file. |
| 4. EXECUTE | Implement additively under `<workdir>/`, tagging artifacts with the node id. Track every paid call's `input_tokens`/`output_tokens` so spend is estimable. |
| 5. VERIFY | Re-run tests / re-measure. Require *evidence* the action helped, or honestly log that it didn't. A failed round is a valid round. |
| 6. LOG + PERSIST | **Write back to the node:** append the attempt, recompute its `posterior`, flip its `status` (`dead`/`exhausted`/`promising`), and update `frontier`. Append to `LOG.md` (round #, node id, the hypotheses, decision, evidence, metric delta, $ this round + cumulative). Update `STATE.json`. `graph_add_memory` for any real decision. Snapshot `rounds/round_NN.md`. |
| 7. SCHEDULE | If a stop condition is met, write `FINAL_REPORT.md` and END. Otherwise let `/loop` re-invoke. |

## The Opus Gate (step 2) — the heart of the skill

Spawn `Agent(subagent_type: "general-purpose", model: "opus")` with a **self-contained** prompt containing: the north-star goal, the current best-result snapshot, the latest result-file paths, and the **pruned registry view** — the frontier nodes with their posteriors, plus a one-line summary of every `dead`/`exhausted` branch so it knows what *not* to re-propose. Ask it to:

- Propose **3 structurally diverse hypotheses** — differing in *kind*, not variations of one idea. The diversity is the point. Examples of distinct mechanisms: (A) parse a native artifact, (B) re-extract fresh, (C) corroborate via physics/cross-source — three mechanisms, not three prompts. Other axes: scale / descriptor mechanism / aggregation / sampling / whitening.
- **Map each hypothesis to the tree:** is it expanding an existing `promising` node (give the id), opening a *new family* (name it — and flag if it belongs in `vocabulary`), or revisiting a node with a genuinely different twist? It must not re-propose anything on the dead/exhausted list.
- **At least one of the three MUST open a new family** (off the current tree), even when an existing branch looks hot. The frontier is a memory, not a leash — the gate brainstorms fresh each round and is never confined to the path the previous round/loop set. Deliberating an exploratory hypothesis is nearly free; SELECT still decides what actually executes.
- Return a **ranked recommendation** — per hypothesis: proposed action, target node id, expected gain, $ cost estimate, risk, and a concrete verification — plus which to execute first and why.
- Answer: *"Are these the highest-information next moves given the frontier? What am I missing? Is the launch order right?"*
- Reply in **≤250 words**.

It may dispatch its own read-only probes. **Do not silently override its redirect** — if you disagree, state your reasoning in the round file.

## Hard Safety Rails (bake into every PROTOCOL.md)

1. **Never mutate source data.** Source CSVs/parsed files/datasets are READ-ONLY. New artifacts only under `<workdir>/`.
2. **Budget guard.** Before any paid (LLM/vision) batch, check `STATE.budget`. If `spent_usd_est >= limit_usd`, switch to free work or stop with a final report.
3. **Evidence before claims.** A round may only mark progress it can *show* (a re-measured number, a passing test, a diff). No "probably worked."
4. **No silent error sinks.** Log tracebacks to the round file; keep STATE honest. Never fabricate metrics.
5. **Subagent models are explicit.** Always pass `model: "opus"` (gate) or `"sonnet"`/`"opus"` (workers) — the default agent model may be unavailable in the loop env.

## Context Hygiene (keeps the session alive all night)

- **State on disk, not in context** — re-read `PROTOCOL.md` + `STATE.json` each round; never rely on memory of prior rounds.
- **Delegate heavy reading to subagents** — the Opus gate and workers absorb large reads (CSVs, logs, crops) and return compact summaries. Never dump full datasets into the main thread.
- **Compact regularly** — if a round leaves the main context large, `/compact` at the end so the next fire starts lean. A bloated main context is a bug, not something to carry.

## Stop Conditions (any one ends the loop — define in PROTOCOL.md)

- Target metric reached AND the whole queue is processed.
- `budget.spent_usd_est >= budget.limit_usd`.
- **Frontier empty / all root families `exhausted` or `dead`** — the cleanest convergence signal: the registry says the tree is fully probed and the gate has no new family to open. Stop and report.
- N consecutive rounds (3–4) with no measurable gain on any front AND no new viable hypothesis — softer convergence signal for when the frontier still has stale nodes.

> A "pursue perfection" variant has **no value-target** stop: when one metric front saturates, pivot to the next weakest or design a new orthogonal metric. Only budget exhaustion or genuine multi-front stuckness ends it.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Skipping the Opus gate "because the next move is obvious" | That's exactly when drift happens. The gate is mandatory, especially when it feels obvious. |
| 3 hypotheses that are variations of one idea | Force structural diversity — different *mechanisms*, not different parameters. |
| Carrying state in the main context across rounds | Re-read from disk every round; the session must be reconstructable from `STATE.json` + `HYPOTHESES.json`. |
| Gate re-proposes an idea tried 15 rounds ago | It never saw the dead-branch list. Always pass the pruned registry view, not just the best snapshot. |
| Reading the whole `HYPOTHESES.json` tree into the gate | Defeats the O(frontier) design. Pass only frontier nodes + one-line dead/exhausted summaries. |
| Forgetting to write back the result to its node | The tree silently rots; next round's posteriors lie. Write-back in LOG+PERSIST is mandatory, even for failed rounds. |
| Claiming a gain without re-measuring | Evidence before claims. Re-run the metric; show the delta. |
| Setting `max_tokens` to cap cost | Control output other ways (concise prompts, thinking budget). Capping truncates reasoning. |

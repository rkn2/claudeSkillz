# <Loop Name> — Round Protocol

**Goal (from the user):** <one paragraph — the north-star outcome and the concrete
deliverable. State what "done" looks like and the budget for the run, e.g. ~$<N>.>
Scope order: <what to work on first, then how to expand>.

Every wakeup runs **exactly one round** by following these steps in order. The loop is
unattended — favor *verifiable, additive, reversible* actions over clever ones.

## The metric (recompute every round)
<Define the metric(s) and the exact command/script that recomputes them. If pursuing a
diverse suite rather than one number, list each front and its ideal value. A round may
only claim a gain it can *show* by re-running this.>

## Baseline / known failure modes (target these)
<Round-0 evidence: the specific things that are currently broken, with file/panel refs.
Also note what is already good and must NOT regress.>

## Hard safety rails (never violate)
1. **Never mutate source data.** <list READ-ONLY paths>. All new artifacts under `<workdir>/`.
2. **Budget guard.** Before any paid batch, check `STATE.budget`. If `spent_usd_est >=
   limit_usd`, switch to free work or stop with a final report. Nightly cap: **$<N>**.
3. **Evidence before claims.** No "probably worked." Re-measure; show the delta.
4. **No silent error sinks.** Log tracebacks to the round file; keep STATE honest.
5. **Subagent models are explicit.** `model: "opus"` for the gate; `"sonnet"`/`"opus"` for workers.
6. <Any task-specific rail, e.g. "NEVER set max_tokens except where the API requires it.">

## Round steps
1. **MEASURE.** Read `STATE.json` + latest outputs. Recompute the metric for the active
   scope. Write it to the round file.
2. **HYPOTHESIZE — Opus subagent considers, then you take over.** Launch ONE subagent
   with `model: "opus"`, giving it the **pruned `HYPOTHESES.json` view** (frontier nodes +
   posteriors + one-line summaries of dead/exhausted branches — never the whole tree). It
   proposes **3 structurally diverse hypotheses** (differing in *kind*, not variations of
   one idea), **maps each to a tree node** (expand a `promising` node / open a new family /
   revisit with a twist — never re-propose a dead branch), with **at least one opening a new
   family off the current tree** so each round brainstorms fresh rather than only continuing
   the prior path, may dispatch its own read-only
   probes, and returns a **ranked recommendation** — per hypothesis: action, target node id,
   expected gain, $ cost, risk, concrete verification — plus which to execute and why.
   ≤250 words. Structurally-diverse examples for this task: <(A) …, (B) …, (C) …>. **Then
   YOU (main loop) take over**; the Opus agent only deliberates, it does not execute.
3. **SELECT.** Treat the frontier as a bandit (expand promising / open new family /
   revisit-with-twist). Sanity-check the rec against budget + rails; pick one (or a safe
   composition). Not bound to its pick if it violates a rail. Record the chosen node id +
   rationale in the round file.
4. **EXECUTE.** Implement additively under `<workdir>/`, tagging artifacts with the node id.
   Track every paid call's token usage for spend estimation.
5. **VERIFY.** Re-run tests / re-measure. Require evidence it helped; honestly log if not.
   Confirm the already-good parts did not regress.
6. **LOG + PERSIST.** Write back to `HYPOTHESES.json`: append the attempt to its node,
   recompute the node's `posterior`, flip its `status` (dead/exhausted/promising), update
   `frontier`. Append to `LOG.md` (round #, node id, the hypotheses, decision, evidence,
   metric delta, $ this round + cumulative). Update `STATE.json`. `graph_add_memory` for
   any real decision. Snapshot `rounds/round_NN.md`.
7. **SCHEDULE.** `/loop` re-invokes. If a stop condition is met, write `FINAL_REPORT.md`
   and end the loop.

## Context hygiene
- State lives on disk; re-read `PROTOCOL.md` + `STATE.json` + the `HYPOTHESES.json` frontier
  fresh each round. Never read the whole hypothesis tree into the main thread.
- Delegate heavy reading to subagents; return compact summaries only.
- If the round leaves the main context large, `/compact` at the end.

## Stop conditions (any one ends the loop)
- <Target metric reached> AND the whole queue is processed.
- `budget.spent_usd_est >= budget.limit_usd`.
- Frontier empty / all root families `exhausted` or `dead` (the registry says the tree is
  fully probed and the gate has no new family to open).
- <3–4> consecutive rounds with no measurable gain and no new viable hypothesis (softer
  convergence — stop and report rather than burn budget).

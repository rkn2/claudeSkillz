---
name: recap
description: Use when Becca asks "what have I done today/this week", wants a recap or summary of accomplishments, or asks "what did I get done so far". Reads her Soundcore voice captures and any Obsidian tasks marked done, and summarizes everything she's done.
---

# Recap

## Overview

Companion to [[daily-checkin]] but looks backward instead of forward:
summarizes what Becca has actually done **today** or **this week so far**,
based on her voice captures (the primary source) and any Obsidian tasks
marked done with a `completed_date`.

## Step 1: Gather context

```bash
python3 /Users/becca/.claude/skills/recap/gather_done.py --range today
```

Use `--range week` if Becca asks about "this week" / "so far this week".
Week = Monday through today (current week only, not a rolling 7 days).

## Step 2: Read the voice captures

The captures are raw, timestamped voice transcriptions. Most of the content
is Becca narrating what she just did -- treat this as the primary record of
accomplishments.

Two special phrases to watch for:

- **"Kangaroo task ..."** -- this created a *new task* (something to do
  later). It is NOT something she's done -- exclude these from the recap,
  or only mention in passing if directly relevant ("also queued up: ...").
- **"Kangaroo Activity Insight ..."** -- these are NOT things done today.
  They're items Becca is dictating to be added to her separate Activity
  Insight log/document (awards, talks, committee roles, etc. for CVs, annual
  reviews, promotion docs). Pull these out entirely from the "what you did
  today" summary and list them separately as **Activity Insight additions**
  (see Step 5) -- framed as "add these to your Activity Insight log," not as
  today's accomplishments.

Everything else in the captures (narration of work done) counts as
accomplishments.

## Step 3: Categorize and summarize

Group accomplishments by domain, using the same conventions as
[[daily-checkin]], **except communications folds into admin** for recap
purposes (established 2026-06-09):

- **research** -- reviewing reports/papers, research project work
- **grants** -- grant budgets, pitch decks, grant-related coordination
- **admin** -- reimbursements, payments, dashboard/task-board upkeep,
  outreach messages/emails
- **personal** -- family/household

Within each group, condense related narration into single bullet points
rather than repeating near-duplicate captures verbatim (e.g. multiple
captures about "reimbursements for EMI" become one bullet).

## Step 4: Include completed tasks

If `gather_done.py` returns any tasks marked done with a `completed_date` in
range, list them too. If it returns none, don't worry -- `completed_date` is
often left blank, and the voice captures are the more reliable source. Don't
apologize for this or belabor the gap; just rely on the captures.

## Step 5: Produce the output

```
**[Day], [Date] — What you've done [today / this week so far]**

**[Domain]:**
- [accomplishment]
- ...

**Activity Insight additions:** (only if "Kangaroo Activity Insight" entries
present -- these go in her separate Activity Insight log, not today's tally)
- [item]
- ...

**Completed tasks:** (only if gather_done.py found any with completed_date)
- [title] (completed [date])
```

Keep it tight -- one line per accomplishment, no padding. This is meant to
feel like "here's everything you knocked out," not a status report.

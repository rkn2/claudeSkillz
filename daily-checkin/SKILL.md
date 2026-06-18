---
name: daily-checkin
description: Use when Becca asks "what should I do now/today/tomorrow", wants a daily plan, check-in, or to know what's left in her day. Reads her Obsidian tasks, Apple Calendar, and recent voice captures, and maps them onto her weekly block schedule.
---

# Daily Check-in

## Overview

Becca (PI at Penn State — grants, research, 3 PhD students) has a recurring
weekly block schedule (Mon–Fri). This skill reads her current pending tasks,
calendar, and recent voice captures, and produces an ordered plan mapped onto
the **remaining blocks of her day** (or tomorrow, if the day is essentially
over).

## Step 0: Sync dailyLog completions back to master tasks

If today's `dailyLog/YYYY-MM-DD.md` checklist exists and Becca has checked
items off (or mentions she has), run:

```bash
python3 /Users/becca/.claude/skills/daily-checkin/sync_dailylog.py
```

This matches checked `- [x]` lines against task titles in
`vault/tasks/*.md` and marks the corresponding task `done: true` with
`completed_date` set to today. Run this before re-gathering context (Step 1)
so the plan reflects what's actually been finished. Report any "no matching
task file found" items to Becca rather than silently dropping them.

**Checked items that aren't actually fully done** (established 2026-06-10):
if a `- [x]` line has an inline annotation indicating it's only partially
complete (e.g. `--> i am still working on this so add X due Friday`, "needs
another hour, top priority next time"), `sync_dailylog.py` will still mark
the task `done: true` with today's `completed_date` -- title-prefix matching
can't distinguish "done for today" from "done overall". After running sync,
fix these:

1. Revert the task file to `done: false`, `completed_date: ''`, and append a
   short progress note to the body (what's done, what remains).
2. If the annotation describes a distinct follow-up (e.g. "double check
   Lara's spring TA, due Friday"), create a new task file for it.
3. Remove the line entirely from today's dailyLog so it can't re-trigger the
   same false positive on the next sync run (including the nightly
   `eod_check.sh`).

This happened twice on 2026-06-10 (llmDamagev2, and the budget/grad-stipend
review + Lara TA follow-up) -- `eod_check.sh` now handles this case
automatically (see its script comments).

## Tuesday morning: Student reports + feedback

Tuesday 8:30–11:00 is dedicated to reading and giving feedback on student
weekly reports (received Monday nights). When planning a Tuesday check-in:
- Mention this block by name and prompt Becca to work through her students'
  reports during this time.
- She has 3 PhD students; reports typically arrive Monday evenings in email
  or a shared folder — ask her if she has reports to get through if it's
  unclear.
- Do NOT treat this block as available for grants or research tasks by
  default on Tuesdays.

## Step 1: Gather context

Run the helper script — it does all the data gathering (current time, day of
week, remaining schedule blocks for today, pending tasks, blocked/future
tasks, calendar for today + rest of week, today's captures):

```bash
python3 /Users/becca/.claude/skills/daily-checkin/gather_context.py
```

This script already encodes the weekly block schedule and computes which
blocks are still ahead based on the current time. Trust its output for
"what blocks are left today" — don't re-derive it.

## Step 1.5: Weekly priorities check (active projects)

`gather_context.py`'s `--- Active projects ---` section lists Becca's
ongoing projects/grants (IJDRR, LLMDamage, ECI, CIR, etc.) from
`active-projects.md`, each with a status and days since last focus.
These are *not* individual tasks — Becca knows what to do once she's in
a project; this section is purely about which projects get a slot.

- If a project is flagged `[STALE - 7+ days...]`, mention it once and ask
  if she wants to put it back in rotation this week.
- If the output says **"weekly priorities check is due"** (no "this week"
  picks for the current week), ask which 1-3 projects should get a slot
  this week. Rewrite the `## This week (YYYY-MM-DD)` section in
  `active-projects.md` (use this Monday's date) with her picks, replacing
  any previous section.
- If "this week" picks already exist for the current week, just note them
  briefly — don't re-ask.
- When a project from "this week" gets placed into today's plan (Step 4),
  update its `last focus:` date in `active-projects.md` to today.

## Step 2: Decide today vs. tomorrow

- If there are meaningful remaining blocks today (e.g. it's morning or early
  afternoon), plan for **today**, using only the remaining blocks.
- If today's schedule is basically over (e.g. only "Boys home/pickup" is
  left, or it's evening), pivot to **tomorrow** — re-run the mental model for
  tomorrow's weekday and tomorrow's calendar (the script's "rest of week"
  section covers this).
- If invoked mid-block (e.g. it's 9:15am during the 8:30–11 Research block),
  treat that block as still active and in-progress — don't suggest replanning
  it, just confirm or adjust.

## Step 3: Categorize tasks by domain

Tasks have a `domain` field. Conventions established with Becca:

- **research** — deep work: papers, manuscripts, research project planning
  (e.g. disaster LLM plan, CV/damage-extraction research, paper reframes/edits)
- **grants** — grant writing, editing, budgets, pitch decks (CIR, ECI,
  Palmer, AI grant, CAMEL grant, etc.)
- **admin** — short tasks, typically under ~30 min: reimbursements, budget
  reviews, task-board upkeep, quick check-ins/polls. These bundle into the
  **Inbox** block.
- **personal** — family/household (kids, appointments)
- **communications** — outreach emails/messages
- Other domains (billing, ops, systems, Soundcore, etc.) — use judgment;
  most fit Inbox if short, or flex/admin time if longer.

If a task's domain is missing, blank, or doesn't match its actual content
(e.g. tagged "work" but is clearly a grants task), ask Becca or use judgment
and suggest updating the frontmatter — see Step 5.

**`start_date` in the future = blocked.** These are excluded from "active"
tasks. Mention them only if their unblock date is imminent (e.g. unblocks
tomorrow) or if Becca asks about them directly.

**`due_type`: hard vs. soft deadlines.** (Established 2026-06-09.) A
`due_date` alone doesn't tell you whether a task is a real external
commitment or a self-imposed target:

- `due_type: hard` — a real external deadline (grant due dates, reviews
  promised to someone else, etc.). Treat as urgent if overdue.
- `due_type: soft` — a target Becca set for herself ("I'd like to get to
  this"), no external consequence if it slips. Treat overdue soft items
  gently — they're "things you've been meaning to get to," not missed
  deadlines.
- **Default is `soft`** if the field is missing (most existing tasks
  predate this field). Only treat as `hard` if explicitly marked, or if
  Becca confirms during a check-in — then update the file (Step 5).

**Protected named blocks keep their stated purpose by default.** If a block's
label names a specific activity (e.g. "Meetings + teaching prep"), don't fill
it with unrelated work (e.g. a grant pitch) without flagging it — that time is
reserved for the named activity unless Becca says otherwise. (Established
2026-06-09, after Palmer pitch was wrongly slotted into a teaching-prep block.)

## Step 4: Produce the plan

Use this format (established 2026-06-09):

```
**[Day], [Date] — [Schedule type, e.g. "Research day" / "Grants day"]**

**Main blocks (remaining):**
- [time range]: [block label]
- ...

**What goes inside:**
- **[block]:**
  - [task/event 1, with brief reasoning if non-obvious]
  - [task/event 2]
  - ...

Each task or event gets its own line (established 2026-06-09) — don't
combine multiple items into one bullet with "+".

For the **Inbox** block specifically, append duration / hard-soft / deadline
to each line so it still reads as a bulleted list like the other blocks
(established 2026-06-09, replacing an earlier table format that didn't match):

  - [title] -- [estimated_minutes] -- [due_type] -- [due_date or none]

**Doesn't fit anywhere [today/this period]:**
- [overdue or unscheduled items worth surfacing — not every overdue item,
  just ones with near-term deadlines or that have been sitting a long time]

**Things you've been meaning to get to** (soft deadlines, no pressure):
- [overdue `due_type: soft` items — only include if it's been a while or
  Becca seems to want a nudge; this section can be omitted entirely]
```

Guidelines:
- For **Research**/**Grants** blocks, check this week's focus projects
  (from Step 1.5) first. If one hasn't had a slot yet this week, list it as
  its own line (e.g. "LLMDamage (llmDamagev2) — pick up where you left
  off") rather than only filling the block with discrete tasks. No need to
  break down what's inside the project — Becca knows.
- Don't force every pending task into a slot. Only surface what's relevant
  to the remaining blocks.
- For the "doesn't fit" section, don't dump the entire backlog — focus on
  `due_type: hard` items with near deadlines, or items that have been
  overdue long enough to be worth a nudge regardless of type.
- Keep hard-deadline overdue items in "Doesn't fit" (these are urgent);
  move soft-deadline overdue items to the separate "things you've been
  meaning to get to" group so they don't read as missed commitments.
- If a deadline conflicts with the schedule (e.g. a grant due Friday but
  Friday morning is consumed by a calendar event), say so explicitly and
  recommend which block to reassign — but confirm with Becca rather than
  silently overriding the schedule.
- Keep reasoning brief — one phrase per item, not a paragraph.
- Watch for ambiguous/test calendar entries (e.g. an event literally titled
  "test") — don't treat these as real commitments; flag if unsure.
- **Account for all time within a block, not just calendar events.**
  (Established 2026-06-10.) If a block contains one or more calendar events,
  check for open time before the first event, between events, and after the
  last event -- fill these gaps with pending tasks rather than only listing
  the calendar items and leaving the rest implicitly blank. (E.g. a
  "Meetings + grants" block from 13:00-15:30 with a meeting starting at
  14:00 has a 13:00-14:00 gap that needs something in it too.)

## Step 5: Write the plan to dailyLog

Write the plan to `vault/dailyLog/YYYY-MM-DD.md` as a checkbox checklist so
Becca can check things off through the day. (Established 2026-06-10.)

- Title: `# [Day], [Month] [Date], [Year]`.
- No separate "Schedule" section listing the time blocks as checkboxes —
  each block's own heading (e.g. `## Research (8:30–11:00)`) already conveys
  the schedule. Start directly with the first work block.
- One `## [Block name] ([time range])` heading per block, with each
  task/event as `- [ ] ...`, using the same line format as Step 4 (Inbox
  items: `title -- duration -- hard/soft -- deadline`).
- Include "Doesn't fit" and "Things you've been meaning to get to" sections
  too, also as checklists, if present in the plan.
- If the file already exists (re-running check-in later in the day), run
  Step 0 first, then update the file in place — preserve already-checked
  items, add/remove tasks based on the new plan, but don't wipe out
  progress.

## Step 6: Updating task metadata

If Becca corrects a task's categorization, deadline, or scheduling
constraint during the conversation (as has happened before — e.g.
reclassifying a task's domain, fixing a due date, adding a `start_date` to
mark something blocked), edit the task file directly:

- Tasks live at:
  `/Users/becca/Library/Mobile Documents/iCloud~md~obsidian/Documents/BeccaNap/tasks/*.md`
- Frontmatter fields: `title`, `done`, `due_date`, `due_type`, `start_date`,
  `domain`, `priority`, `estimated_minutes`, `completed_date`, `created`,
  `origin`, `source`, `dismissed_reason`
- Watch out for duplicate YAML keys when editing — check the file structure
  before and after.

These edits persist the correction so future check-ins don't repeat the same
question.

## Known limitations

- Calendar access requires Terminal to have Calendar + Automation permissions
  granted in System Settings → Privacy & Security (already done as of
  2026-06-09).
- Reminders integration (writing to Apple Reminders via `osascript`) is not
  yet authorized — Terminal needs Automation access to Reminders.
- This runs on giraffe (becca's account); vault path is the iCloud-synced
  Obsidian vault, may have brief sync lag.

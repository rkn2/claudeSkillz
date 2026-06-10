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

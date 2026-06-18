# claudeSkillz

Custom Claude Code skills for research and grant writing.

## What are skills?

Skills are reusable instruction sets for Claude Code that encode a specific workflow. When a skill is active, Claude follows its structured process automatically when you invoke it. Skills live in `~/.claude/skills/` or are installed via `.skill` package files.

## Skills in this repo

### nsf-proposal-draft

Converts a folder of input materials (project summary, notes, NSF program call) into a complete NSF proposal draft in LaTeX.

**Trigger:** Tell Claude something like "convert this folder to an NSF draft" or "write an NSF proposal from my materials in [folder path]."

**What it does:**
1. Reads your input folder (summary doc, notes, program call)
2. Walks through a structured 7-phase interview: main idea, PI team, research questions, knowledge gaps, research objectives and tasks, and pilot context
3. Pushes back at each phase if framing sounds like an engineering goal rather than a research question, or if gaps describe missing tools rather than missing knowledge
4. Generates five LaTeX files: `Research.tex`, `summary.tex`, `mentoringPlan.tex`, `DMP2.tex`, `biblio.bib`

**Output style:**
- No em dashes
- `% firstname:` comment format for all PI action items (lowercase, first name only)
- State-of-the-art subsections are stubs with detailed guidance comments -- no invented literature
- Knowledge gap framing enforced in Table 1 and RQ section
- `xxx` for unknown quantities
- Each RO ends with "Key outcomes and evaluation: Add after subtasks are written"
- Status quo section stays at national scale; pilot sites appear only in Section 4

**Files:**
- `SKILL.md` -- the skill instructions (human-readable)
- `nsf-proposal-draft.skill` -- packaged skill file for installation

### daily-checkin

Reads pending Obsidian tasks, Apple Calendar, and recent voice captures, and maps them onto a recurring weekly block schedule to produce an ordered daily plan.

**Trigger:** "what should I do now/today/tomorrow", "give me a daily plan/check-in", "what's left in my day".

**What it does:**
1. Runs `sync_dailylog.py` first to mark any tasks Becca already checked off in today's dailyLog as done in the master task list
2. Runs `gather_context.py` to collect current time/day, remaining schedule blocks for today, pending + blocked tasks, calendar (today + rest of week), and today's voice captures
3. Decides whether to plan for the rest of today or pivot to tomorrow based on time of day
4. Categorizes tasks by `domain` (research/grants/admin/personal/communications) and `due_type` (`hard` = real external deadline, `soft` = self-imposed target, no pressure)
5. Checks `active-projects.md` for ongoing projects/grants -- flags any untouched 7+ days, and if no "this week" picks exist yet for the current week, asks which 1-3 projects get a slot and records the picks back to the file
6. Produces a plan: **Main blocks**, **What goes inside** (one task/event per line; Inbox items get duration/hard-soft/deadline appended; this week's focus projects get their own line in Research/Grants blocks), **Doesn't fit** (urgent hard-deadline items), and **Things you've been meaning to get to** (overdue soft items, optional)
7. Respects "protected" named blocks (e.g. "Meetings + teaching prep") -- doesn't silently fill them with unrelated work
8. Writes the plan to `dailyLog/YYYY-MM-DD.md` as a checkbox checklist, organized by block, so Becca can check items off through the day

Two optional automations run standalone (no chat session needed), both via launchd:
- **Morning check-in** (`morning_checkin.sh`, established 2026-06-17): runs `gather_context.py`, then calls `claude -p` headlessly to follow the skill and write the day's plan before Becca's day starts. Skips weekends and skips if today's dailyLog already exists. Non-interactive: makes reasonable calls on ambiguous items (e.g. unset weekly priorities) and notes assumptions inline instead of asking.
- **End-of-day check** (`eod_check.sh`, established 2026-06-10): re-runs `sync_dailylog.py`, then calls `claude -p` headlessly to scan today's dailyLog for inline annotations on task lines (e.g. `--> this is blocked, move to friday`), applies the requested changes to the matching task file's frontmatter, cleans up the dailyLog, and fires a macOS notification if anything changed.

**Notes:**
- Calendar access is via a direct SQLite query against `Calendar.sqlitedb` (icalbuddy proved unreliable even with permissions granted)
- Both launchd-triggered scripts run as `launchd -> /bin/bash -> ...`, with no Terminal/tmux in the process tree -- on macOS this means the iCloud/Calendar reads will only work if `/bin/bash` itself has been granted Full Disk Access in System Settings -> Privacy & Security (granting it to a terminal app or to `claude` is not sufficient, since neither is the actual binary launchd invokes)
- `gather_context.py`, `sync_dailylog.py`, `eod_check.sh`, and `morning_checkin.sh` hardcode one person's Obsidian vault path, weekly schedule, and task frontmatter conventions -- adapt the constants at the top of each file for your own setup
- `com.becca.dailylog-eod-check.plist` and `com.becca.dailylog-morning-checkin.plist` hardcode absolute paths and a username -- edit before installing to `~/Library/LaunchAgents/`, then `launchctl bootstrap gui/$(id -u) <plist>`

**Files:**
- `SKILL.md` -- the skill instructions
- `gather_context.py` -- context-gathering helper script (run via `python3`)
- `sync_dailylog.py` -- syncs checked-off dailyLog items back to the master task list (run via `python3`)
- `eod_check.sh` -- standalone end-of-day check (sync + annotation processing + notification)
- `com.becca.dailylog-eod-check.plist` -- launchd schedule for `eod_check.sh`
- `morning_checkin.sh` -- standalone morning check-in (writes today's plan before Becca's day starts)
- `com.becca.dailylog-morning-checkin.plist` -- launchd schedule for `morning_checkin.sh`

### hypothesis-loop

Use when running an unattended multi-round research, optimization, or audit loop (overnight, autonomous, `/loop`-driven, or cron-driven) where each round is steered by a hypothesis check before spending compute or money. Triggers include "run this overnight", "autonomous loop", "keep iterating until", "optimization loop", "self-paced research loop".

**What it does:**
- Sonnet does the iteration work; every round is gated by an Opus subagent that weighs hypotheses before any compute/spend, as a defense against local-optimum momentum
- State lives on disk (`PROTOCOL.md` + `STATE.json`), not in context, so the loop survives long unattended runs
- For long campaigns, hypothesis history is tracked as a factored tree (`HYPOTHESES.json`) so the gate only needs to read the frontier, keeping context cost flat regardless of run length

**Files:**
- `SKILL.md` -- the skill instructions
- `PROTOCOL-template.md` -- starting template for a run's `PROTOCOL.md`

### recap

Companion to daily-checkin, but looks backward: summarizes what Becca has done **today** or **this week so far**, based on Soundcore voice captures (primary source) and any Obsidian tasks marked done with a `completed_date`.

**Trigger:** "what have I done today/this week", "recap my day/week", "what did I get done so far".

**What it does:**
1. Runs `gather_done.py --range today` (or `--range week`, Monday through today) to pull voice captures and any completed tasks in range
2. Reads the captures as a narration of work done; "Kangaroo task ..." entries (new tasks queued, not yet done) are excluded
3. "Kangaroo Activity Insight ..." entries are pulled out separately as **Activity Insight additions** -- items for her CV/annual-review log, not part of today's tally
4. Groups everything else by domain (research / grants / admin -- communications folds into admin here / personal), condensing near-duplicate captures into single bullets

**Files:**
- `SKILL.md` -- the skill instructions
- `gather_done.py` -- context-gathering helper script (run via `python3`)

### strip-claude

Removes all `Co-Authored-By: Claude` trailers from every commit in a GitHub repo, then force-pushes all affected branches.

**Trigger:** `/strip-claude <github-repo-url-or-owner/repo>` (e.g. `/strip-claude rkn2/energyInfrastructure`)

**What it does:**
1. Clones the repo and checks out all branches
2. Scans for commits with `Co-Authored-By: Claude` trailers and reports a summary
3. Uses `git-filter-repo` to strip the trailers from commit messages on all branches
4. Shows a preview and asks for explicit confirmation before force-pushing

**Files:**
- `SKILL.md` -- the skill instructions

## Installation

**Option 1: Copy SKILL.md (and any companion files) directly**
```bash
mkdir -p ~/.claude/skills/<skill-name>
cp <skill-name>/SKILL.md ~/.claude/skills/<skill-name>/
# copy any other files in the skill's directory too, e.g.:
cp <skill-name>/*.py ~/.claude/skills/<skill-name>/ 2>/dev/null
```

**Option 2: Install a `.skill` package** (if your Claude version supports it)
```bash
# Open the .skill file through the Claude interface
```

## Adding new skills

Each skill lives in its own subdirectory with at minimum a `SKILL.md` file. Add new skills as subdirectories here, with a corresponding entry in this README.

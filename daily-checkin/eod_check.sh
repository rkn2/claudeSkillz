#!/bin/bash
# End-of-day dailyLog check (established 2026-06-10).
# 1. Syncs any checked-off dailyLog items to the master Obsidian task list.
# 2. Asks Claude to process any inline annotations Becca left on task lines:
#    - On checked "- [x]" lines that are only partially done (e.g. "--> i am
#      still working on this so add X due Friday"), revert the false-positive
#      done/completed_date that step 1 just set, spin off any follow-up task,
#      and remove the line from the dailyLog.
#    - On unchecked "- [ ]" lines (e.g. "--> this is blocked, move to friday"),
#      update the task file and clean up the dailyLog accordingly.
# 3. Sends a macOS notification if anything changed.
#
# Run via launchd, see com.becca.dailylog-eod-check.plist

set -uo pipefail

VAULT="/Users/becca/Library/Mobile Documents/iCloud~md~obsidian/Documents/BeccaNap"
SKILL_DIR="/Users/becca/.claude/skills/daily-checkin"
CLAUDE_BIN="/Users/becca/.local/bin/claude"

LOG_DIR="$HOME/Library/Logs/dailylog-eod-check"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/$(date +%Y-%m-%d).log"

{
  echo "=== EOD check started: $(date) ==="

  python3 "$SKILL_DIR/sync_dailylog.py"

  PROMPT="End-of-day dailyLog check. Today's date is $(date +%F).

1. Read the dailyLog file at \"$VAULT/dailyLog/$(date +%F).md\". If it does not exist, output exactly NO_CHANGES and stop.

2. Look for inline annotations on task lines -- text appended after the standard '- [ ] title -- duration -- hard/soft -- deadline' (or plain description) format that indicates Becca wants something changed, e.g. '--> this is blocked, move to friday', '--> push to next week', '--> change domain to admin', '--> actually due monday', '--> i am still working on this so add X due friday', etc. Ignore lines already in standard format with no extra annotation, and ignore Obsidian completion markers like '✅ YYYY-MM-DD'.

3. For each annotation found, first check whether the line is checked ('- [x]') or unchecked ('- [ ]'):

   a. CHECKED line, annotation indicates only partial completion (e.g. 'still working on this', 'needs another hour', 'add X as a follow-up due <date>'):
      - Find the matching task file in \"$VAULT/tasks/\" (same fuzzy title matching as sync_dailylog.py). Step 1 (sync_dailylog.py) likely just set this task's `done: true` and `completed_date` to today -- this is a false positive. Revert both (`done: false`, `completed_date: ''`).
      - Append a short progress note to the task's body (what's done so far, what remains).
      - If the annotation describes a distinct follow-up item, create a new task file for it in \"$VAULT/tasks/\" following existing frontmatter conventions (title, due_date, due_type, domain inherited from the parent task where sensible, origin: manual, created: today).
      - Remove the line entirely from the dailyLog (not just the annotation text), so it can't re-trigger this same false positive on the next sync run.

   b. UNCHECKED line, or checked line whose annotation describes a scheduling/metadata change (e.g. 'this is blocked, move to friday', 'push to next week', 'change domain to admin', 'actually due monday'):
      - Find the matching task file in \"$VAULT/tasks/\" (same fuzzy matching).
      - Apply the requested change to that task file's frontmatter following the conventions in $SKILL_DIR/SKILL.md (e.g. 'move to friday' / 'push to <date>' -> update due_date AND start_date to that date, keeping due_type as-is; 'change domain to X' -> update domain; etc). Use judgment for relative date references (friday, next week, tomorrow) based on today's date.
      - Remove the annotation text and the corresponding line from the dailyLog, since the task no longer belongs in today's plan, unless the annotation clearly says to keep it on today's list.

4. Save your edits.

5. Output your final response as exactly one line:
   - If you made any changes: 'CHANGES: <short summary>'
   - If there were no annotations to process: 'NO_CHANGES'
"

  RESULT=$("$CLAUDE_BIN" -p "$PROMPT" \
    --add-dir "$VAULT" \
    --add-dir "$SKILL_DIR" \
    --dangerously-skip-permissions \
    --no-session-persistence \
    --output-format text)

  echo "$RESULT"

  if echo "$RESULT" | grep -q '^CHANGES:'; then
    SUMMARY=$(echo "$RESULT" | sed -n 's/^CHANGES: *//p' | head -c 180)
    osascript -e "display notification \"$SUMMARY\" with title \"DailyLog EOD check\""
  fi

  echo "=== EOD check finished: $(date) ==="
} >> "$LOG_FILE" 2>&1

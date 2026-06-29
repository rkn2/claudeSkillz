#!/bin/bash
# Morning daily-checkin automation (established 2026-06-17).
# Runs gather_context.py, then asks Claude to follow the daily-checkin skill
# and write today's plan to the vault dailyLog.
#
# Skips weekends (no fixed schedule) and skips if dailyLog already exists.
# Run via launchd, see com.becca.dailylog-morning-checkin.plist

set -uo pipefail

VAULT="/Users/becca/Library/Mobile Documents/iCloud~md~obsidian/Documents/BeccaNap"
SKILL_DIR="/Users/becca/.claude/skills/daily-checkin"
CLAUDE_BIN="/Users/becca/.local/bin/claude"

LOG_DIR="$HOME/Library/Logs/dailylog-morning-checkin"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/$(date +%Y-%m-%d).log"

{
  echo "=== Morning checkin started: $(date) ==="

  # Skip weekends
  DOW=$(date +%u)  # 1=Mon ... 7=Sun
  if [ "$DOW" -ge 6 ]; then
    echo "Weekend — skipping."
    echo "=== Morning checkin finished: $(date) ==="
    exit 0
  fi

  TODAY=$(date +%F)
  DAILYLOG_PATH="$VAULT/dailyLog/$TODAY.md"
  SENTINEL="<!-- generated-by: morning-checkin -->"

  # Only skip if a *real* plan was already generated today (identified by the
  # sentinel marker), not merely because some file exists. A hand-parked stub
  # (e.g. tasks carried forward the night before) must NOT block generation —
  # that's the 2026-06-29 bug, where a parked ae240 task tripped a bare
  # `[ -f ]` check and the full block plan never got written.
  PARKED_CONTENT=""
  if [ -f "$DAILYLOG_PATH" ]; then
    if grep -qF "$SENTINEL" "$DAILYLOG_PATH" 2>/dev/null; then
      echo "DailyLog already generated for $TODAY (sentinel present) — skipping."
      echo "=== Morning checkin finished: $(date) ==="
      exit 0
    fi
    echo "DailyLog exists for $TODAY but has no generated-plan sentinel — treating as parked content to merge in."
    PARKED_CONTENT=$(cat "$DAILYLOG_PATH" 2>/dev/null)
  fi

  CONTEXT=$(python3 "$SKILL_DIR/gather_context.py" 2>&1)

  PROMPT="Today is $TODAY. You are running as an automated assistant for Becca.

Your job: produce her daily plan and write it to her dailyLog for today.

Instructions are in the skill file at $SKILL_DIR/SKILL.md — read that file and follow Steps 0 through 5 exactly.

The gathered context is below (output of gather_context.py — skip re-running it):

--- CONTEXT ---
$CONTEXT
--- END CONTEXT ---

The dailyLog file may already contain tasks Becca parked the night before
(carried-forward or hand-added items). If so, that content is below — fold
every one of those tasks into today's plan in the appropriate block; do not
drop any of them.

--- PARKED CONTENT (may be empty) ---
$PARKED_CONTENT
--- END PARKED CONTENT ---

Non-interactive rules (no Becca to answer questions):
- Step 1.5 weekly priorities: if 'This week' picks are already set for the current week in active-projects.md, use them. If not, pick the 1-3 most stale projects by days-since-last-focus and note in the plan that Becca should confirm.
- Step 2 today-vs-tomorrow: it is 7:30am, so plan for today.
- If the CONTEXT above contains a 'task file(s) unreadable' warning, note at the top of the plan that some tasks were iCloud-offloaded and may be missing.
- Do not ask questions. Make reasonable calls and note assumptions inline.
- Step 5: write the plan to: $DAILYLOG_PATH . The VERY FIRST line of the file must be exactly: $SENTINEL — this marks the plan as generated so re-runs don't clobber it. Put the '# Weekday, Month Day, Year' title on the next line.

Output a single line when done: DONE or ERROR: <reason>."

  # Notify if still running after 5 minutes
  (sleep 300 && [ ! -f "$DAILYLOG_PATH" ] && osascript -e "display notification \"Still working — heavy load today\" with title \"Morning Check-in\"") &
  TIMER_PID=$!

  RESULT=$("$CLAUDE_BIN" -p "$PROMPT" \
    --add-dir "$VAULT" \
    --add-dir "$SKILL_DIR" \
    --dangerously-skip-permissions \
    --no-session-persistence \
    --output-format text 2>&1)

  kill $TIMER_PID 2>/dev/null

  echo "$RESULT"

  if [ -f "$DAILYLOG_PATH" ]; then
    osascript -e "display notification \"Daily plan ready — check your vault\" with title \"Morning Check-in\""
  else
    osascript -e "display notification \"Morning checkin ran but no dailyLog written — check logs\" with title \"Morning Check-in\""
  fi

  echo "=== Morning checkin finished: $(date) ==="
} >> "$LOG_FILE" 2>&1

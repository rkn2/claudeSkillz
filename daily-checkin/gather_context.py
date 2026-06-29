#!/usr/bin/env python3
"""Gather raw context for the daily-checkin skill: current time/block,
pending tasks, today's + this week's calendar, and recent captures.

Outputs plain text — designed to be read by Claude, not machines.
"""
from __future__ import annotations

import datetime
import re
import sqlite3
from pathlib import Path

VAULT = Path("/Users/becca/Library/Mobile Documents/iCloud~md~obsidian/Documents/BeccaNap")
TASKS_DIR = VAULT / "tasks"
CAPTURES_DIR = VAULT / "captures"
ACTIVE_PROJECTS_FILE = VAULT / "active-projects.md"
CALENDAR_DB = Path.home() / "Library/Group Containers/group.com.apple.calendar/Calendar.sqlitedb"
MAC_EPOCH_OFFSET = 978307200  # seconds between unix epoch and 2001-01-01
GPO_DEADLINES_FILE = Path("/Users/becca/Code/GPO/deadlines.md")


# Weekly block schedule. Each day maps ordered (start, end, label) tuples.
# "end" of None means "rest of day".
SCHEDULE = {
    0: [  # Monday
        ("07:45", "08:00", "Drop + drive"),
        ("08:00", "08:30", "Catch up / buffer"),
        ("08:30", "11:00", "Research"),
        ("11:00", "12:00", "Inbox"),
        ("12:00", "13:00", "Lunch"),
        ("13:00", "15:30", "Research"),
        ("15:30", "16:30", "Wrap + free"),
        ("16:30", None, "Boys home"),
    ],
    1: [  # Tuesday
        ("07:45", "08:00", "Drop + drive"),
        ("08:00", "08:30", "Catch up / buffer"),
        ("08:30", "11:00", "Student reports + feedback"),
        ("11:00", "12:00", "Inbox"),
        ("12:00", "13:00", "Drive to campus"),
        ("13:00", "15:30", "Meetings + grants"),
        ("15:30", "16:30", "Flex"),
        ("16:30", None, "Boys pickup"),
    ],
    2: [  # Wednesday
        ("07:45", "08:00", "Drop + drive"),
        ("08:00", "08:30", "Catch up / buffer"),
        ("08:30", "11:00", "Research"),
        ("11:00", "12:00", "Inbox"),
        ("12:00", "13:00", "Drive to campus"),
        ("13:00", "15:30", "Meetings + teaching prep"),
        ("15:30", "16:30", "Flex"),
        ("16:30", None, "Boys pickup"),
    ],
    3: [  # Thursday
        ("07:45", "08:00", "Drop + drive"),
        ("08:00", "08:30", "Catch up / buffer"),
        ("08:30", "11:00", "Grants"),
        ("11:00", "12:00", "Inbox"),
        ("12:00", "13:00", "Drive to campus"),
        ("13:00", "15:30", "Meetings + grants"),
        ("15:30", "16:30", "Flex"),
        ("16:30", None, "Boys pickup"),
    ],
    4: [  # Friday
        ("07:45", "08:00", "Drop + drive"),
        ("08:00", "08:30", "Catch up / buffer"),
        ("08:30", "11:00", "Research"),
        ("11:00", "12:00", "Inbox"),
        ("12:00", "13:00", "Lunch"),
        ("13:00", "15:30", "Flex/kayak"),
        ("15:30", "16:30", "Early finish"),
        ("16:30", None, "Boys home"),
    ],
    5: [],  # Saturday — no fixed schedule
    6: [],  # Sunday — no fixed schedule
}


def _parse_frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    fm = m.group(1)
    out = {}
    for key in (
        "title", "done", "due_date", "due_type", "start_date", "domain",
        "priority", "estimated_minutes", "completed_date",
    ):
        r = re.search(rf"^{key}:\s*(.*)$", fm, re.MULTILINE)
        if r:
            out[key] = r.group(1).strip().strip("'\"")
    return out


def gather_tasks(today: datetime.date) -> tuple[list[dict], list[dict], list[str]]:
    """Return (active_tasks, blocked_tasks, unreadable_filenames).

    Unreadable = iCloud-offloaded ("dataless") files that raise OSError on read
    (errno 11, "Resource deadlock avoided") when the calling process can't
    trigger materialization. Skip them with a note rather than crashing the
    whole check-in — see project_daily_os memory.
    """
    active, blocked, unreadable = [], [], []
    for f in sorted(TASKS_DIR.glob("*.md")):
        try:
            text = f.read_text(errors="replace")
        except OSError:
            unreadable.append(f.name)
            continue
        meta = _parse_frontmatter(text)
        if not meta.get("title"):
            continue
        if meta.get("done", "").lower() in ("true", "yes", "1"):
            continue
        start = meta.get("start_date", "")
        if start:
            try:
                if datetime.date.fromisoformat(start) > today:
                    blocked.append(meta)
                    continue
            except ValueError:
                pass
        active.append(meta)
    return active, blocked, unreadable


def gather_calendar(start_date: datetime.date, end_date: datetime.date) -> list[tuple]:
    """Return (date, start_str, end_str, summary, all_day) for events in range."""
    if not CALENDAR_DB.exists():
        return []
    conn = sqlite3.connect(f"file:{CALENDAR_DB}?mode=ro", uri=True)
    day_start = datetime.datetime.combine(start_date, datetime.time.min).timestamp() - MAC_EPOCH_OFFSET
    day_end = datetime.datetime.combine(end_date, datetime.time.max).timestamp() - MAC_EPOCH_OFFSET
    cur = conn.execute(
        """
        SELECT ci.summary, ci.start_date, ci.end_date, ci.all_day
        FROM CalendarItem ci
        WHERE ci.start_date >= ? AND ci.start_date <= ?
        ORDER BY ci.start_date
        """,
        (day_start, day_end),
    )
    rows = []
    for summary, start, end, all_day in cur.fetchall():
        sdt = datetime.datetime.fromtimestamp(start + MAC_EPOCH_OFFSET)
        edt = datetime.datetime.fromtimestamp(end + MAC_EPOCH_OFFSET)
        rows.append((sdt.date(), sdt, edt, summary, bool(all_day)))
    conn.close()
    return rows


def gather_capture(date_str: str) -> str:
    f = CAPTURES_DIR / f"{date_str}.md"
    if not f.exists():
        return ""
    return f.read_text(errors="replace")


def gather_active_projects(today: datetime.date) -> tuple[list[dict], str | None, list[str]]:
    """Parse active-projects.md.

    Returns (projects, this_week_date, this_week_items) where each project
    dict has name/status/last_focus/days_since, this_week_date is the
    YYYY-MM-DD from a '## This week (...)' heading (or None), and
    this_week_items is the list of project names under that heading.
    """
    if not ACTIVE_PROJECTS_FILE.exists():
        return [], None, []
    text = ACTIVE_PROJECTS_FILE.read_text(errors="replace")

    projects = []
    for line in text.splitlines():
        m = re.match(r"^-\s*(.+?)\s*—\s*(.+?)\s*—\s*last focus:\s*(.+)$", line.strip())
        if not m:
            continue
        name, status, last_focus = (g.strip() for g in m.groups())
        days_since = None
        if last_focus != "unknown":
            try:
                days_since = (today - datetime.date.fromisoformat(last_focus)).days
            except ValueError:
                pass
        projects.append({"name": name, "status": status, "last_focus": last_focus, "days_since": days_since})

    this_week_date = None
    this_week_items: list[str] = []
    wm = re.search(r"^## This week \((\d{4}-\d{2}-\d{2})\)\s*$", text, re.MULTILINE)
    if wm:
        this_week_date = wm.group(1)
        for line in text[wm.end():].splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("#"):
                break
            if line.startswith("-"):
                this_week_items.append(line.lstrip("- ").strip())

    return projects, this_week_date, this_week_items


def remaining_blocks(now: datetime.datetime) -> list[tuple]:
    """Return today's schedule blocks that haven't ended yet."""
    today_blocks = SCHEDULE.get(now.weekday(), [])
    out = []
    for start, end, label in today_blocks:
        if end is None:
            end_t = datetime.time(23, 59)
        else:
            end_t = datetime.datetime.strptime(end, "%H:%M").time()
        if now.time() < end_t:
            out.append((start, end, label))
    return out


def main() -> None:
    now = datetime.datetime.now()
    today = now.date()
    weekday_name = now.strftime("%A")

    print(f"=== Current time: {now.strftime('%A %B %-d, %Y, %-I:%M %p')} ===\n")

    blocks = remaining_blocks(now)
    print(f"--- Remaining schedule blocks today ({weekday_name}) ---")
    if not blocks:
        print("(none — schedule for today is over, or no fixed schedule for this day)")
    for start, end, label in blocks:
        end_str = end or "EOD"
        print(f"{start}-{end_str}: {label}")
    print()

    print("--- Pending tasks (active) ---")
    active, blocked, unreadable = gather_tasks(today)
    if not active:
        print("(none)")
    for t in active:
        line = f"- {t['title']}"
        if t.get("due_date"):
            due_type = t.get("due_type", "soft")
            line += f"  [due {t['due_date']}, {due_type}]"
        if t.get("domain"):
            line += f"  [domain:{t['domain']}]"
        if t.get("estimated_minutes") and t["estimated_minutes"] != "0":
            line += f"  [~{t['estimated_minutes']}min]"
        if t.get("priority") and t["priority"] != "normal":
            line += f"  [priority:{t['priority']}]"
        print(line)
    print()

    if unreadable:
        print(f"--- WARNING: {len(unreadable)} task file(s) unreadable (iCloud-offloaded / dataless) ---")
        print("These were SKIPPED — the plan below may be missing tasks. To fix: open the")
        print("vault tasks folder in Finder/Obsidian (or right-click → Keep Downloaded) to")
        print("force materialization, then re-run.")
        for name in unreadable:
            print(f"- {name}")
        print()

    if blocked:
        print("--- Blocked tasks (start_date in future) ---")
        for t in blocked:
            print(f"- {t['title']}  [starts {t.get('start_date')}]  [due {t.get('due_date', '?')}]")
        print()

    print("--- Active projects ---")
    projects, this_week_date, this_week_items = gather_active_projects(today)
    if not projects:
        print("(none)")
    for p in projects:
        line = f"- {p['name']} — {p['status']}"
        if p["days_since"] is None:
            line += " — last focus unknown"
        else:
            line += f" — last focus {p['days_since']}d ago"
            if p["days_since"] >= 7:
                line += "  [STALE - 7+ days, raise at weekly check-in]"
        print(line)
    current_monday = (today - datetime.timedelta(days=today.weekday())).isoformat()
    if this_week_date == current_monday:
        print(f"This week's focus (set {this_week_date}): {', '.join(this_week_items) if this_week_items else '(none picked)'}")
    else:
        print(f"No 'this week' picks for the current week (week of {current_monday}) -- weekly priorities check is due.")
    print()

    print("--- Calendar: today ---")
    today_events = gather_calendar(today, today)
    if not today_events:
        print("(no events)")
    for d, sdt, edt, summary, all_day in today_events:
        if all_day:
            print(f"[All day] {summary}")
        else:
            print(f"{sdt.strftime('%-I:%M %p')}-{edt.strftime('%-I:%M %p')}: {summary}")
    print()

    week_end = today + datetime.timedelta(days=(6 - today.weekday()))
    if week_end > today:
        print(f"--- Calendar: rest of week ({(today + datetime.timedelta(days=1))} to {week_end}) ---")
        rest_events = gather_calendar(today + datetime.timedelta(days=1), week_end)
        if not rest_events:
            print("(no events)")
        current_day = None
        for d, sdt, edt, summary, all_day in rest_events:
            if d != current_day:
                current_day = d
                print(f"{d.strftime('%A %b %-d')}:")
            if all_day:
                print(f"  [All day] {summary}")
            else:
                print(f"  {sdt.strftime('%-I:%M %p')}-{edt.strftime('%-I:%M %p')}: {summary}")
        print()

    # GPO deadlines within 14 days
    gpo_upcoming = []
    if GPO_DEADLINES_FILE.exists():
        cutoff = today + datetime.timedelta(days=14)
        in_table = False
        for line in GPO_DEADLINES_FILE.read_text().splitlines():
            line = line.strip()
            if line.startswith("| Date") or line.startswith("|---"):
                in_table = True
                continue
            if in_table and line.startswith("|") and not line.startswith("|---"):
                parts = [c.strip() for c in line.strip("|").split("|")]
                if len(parts) >= 5 and parts[0] not in ("Date", "---"):
                    try:
                        d = datetime.date.fromisoformat(parts[0])
                        if today <= d <= cutoff:
                            gpo_upcoming.append((d, parts[1], parts[3], parts[4]))
                    except ValueError:
                        pass
            elif in_table and not line.startswith("|"):
                in_table = False
    if gpo_upcoming:
        gpo_upcoming.sort()
        print("--- GPO deadlines within 14 days ---")
        for d, title, priority, notes in gpo_upcoming:
            label = "[HARD]" if priority == "hard" else "[soft]"
            print(f"  • {d} {label} {title} — {notes}")
        print()

    print("--- Today's captures so far ---")
    today_capture = gather_capture(today.isoformat())
    print(today_capture.strip() if today_capture.strip() else "(none yet)")


if __name__ == "__main__":
    main()

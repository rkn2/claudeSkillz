#!/usr/bin/env python3
"""Gather what Becca has done today or this week so far: Soundcore voice
captures and any Obsidian tasks marked done with a completed_date in range.

Outputs plain text -- designed to be read by Claude, not machines.
"""
from __future__ import annotations

import argparse
import datetime
import re
from pathlib import Path

VAULT = Path("/Users/becca/Library/Mobile Documents/iCloud~md~obsidian/Documents/BeccaNap")
TASKS_DIR = VAULT / "tasks"
CAPTURES_DIR = VAULT / "captures"
DAILYLOG_DIR = VAULT / "dailyLog"


def _parse_frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    fm = m.group(1)
    out = {}
    for key in ("title", "done", "completed_date", "domain", "due_date"):
        r = re.search(rf"^{key}:\s*(.*)$", fm, re.MULTILINE)
        if r:
            out[key] = r.group(1).strip().strip("'\"")
    return out


def gather_completed_tasks(start: datetime.date, end: datetime.date) -> list[dict]:
    out = []
    for f in sorted(TASKS_DIR.glob("*.md")):
        meta = _parse_frontmatter(f.read_text(errors="replace"))
        if meta.get("done", "").lower() not in ("true", "yes", "1"):
            continue
        cd = meta.get("completed_date", "")
        if not cd:
            continue
        try:
            d = datetime.date.fromisoformat(cd)
        except ValueError:
            continue
        if start <= d <= end:
            out.append(meta)
    return out


def gather_captures(start: datetime.date, end: datetime.date) -> list[tuple[datetime.date, str]]:
    out = []
    d = start
    while d <= end:
        f = CAPTURES_DIR / f"{d.isoformat()}.md"
        if f.exists():
            text = f.read_text(errors="replace").strip()
            if text:
                out.append((d, text))
        d += datetime.timedelta(days=1)
    return out


def gather_dailylogs(start: datetime.date, end: datetime.date) -> list[tuple[datetime.date, str]]:
    out = []
    d = start
    while d <= end:
        f = DAILYLOG_DIR / f"{d.isoformat()}.md"
        if f.exists():
            try:
                text = f.read_text(errors="replace").strip()
            except OSError as e:
                # iCloud "dataless" placeholder not materialized locally (brctl access denied).
                out.append((d, f"[UNREADABLE -- {e}; likely an undownloaded iCloud file. "
                                 f"Open {f.name} in Obsidian/Finder to force a local sync, then re-run.]"))
                d += datetime.timedelta(days=1)
                continue
            if text:
                out.append((d, text))
        d += datetime.timedelta(days=1)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--range", choices=["today", "week"], default="today")
    parser.add_argument(
        "--weeks-ago", type=int, default=0,
        help="0 = this week/today, 1 = last week, 2 = two weeks ago, etc.",
    )
    args = parser.parse_args()

    today = datetime.date.today()
    this_monday = today - datetime.timedelta(days=today.weekday())

    if args.range == "week":
        start = this_monday - datetime.timedelta(weeks=args.weeks_ago)
        end = today if args.weeks_ago == 0 else start + datetime.timedelta(days=6)
    else:
        start = end = today - datetime.timedelta(weeks=args.weeks_ago)

    print(f"=== Range: {args.range}, weeks_ago={args.weeks_ago} ({start.isoformat()} to {end.isoformat()}) ===\n")

    print("--- Voice captures ---")
    captures = gather_captures(start, end)
    if not captures:
        print("(none)")
    for d, text in captures:
        print(f"\n## {d.strftime('%A %B %-d')}")
        print(text)
    print()

    print("--- Daily log notes ---")
    dailylogs = gather_dailylogs(start, end)
    if not dailylogs:
        print("(none)")
    for d, text in dailylogs:
        print(f"\n## {d.strftime('%A %B %-d')}")
        print(text)
    print()

    print("--- Tasks marked done with completed_date in range ---")
    done = gather_completed_tasks(start, end)
    if not done:
        print("(none -- note: completed_date is often left blank when tasks "
              "are marked done, so this list may be incomplete. The voice "
              "captures above are the more reliable source.)")
    for t in done:
        line = f"- {t['title']}  [completed {t['completed_date']}]"
        if t.get("domain"):
            line += f"  [domain:{t['domain']}]"
        print(line)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Sync checked-off items in today's dailyLog back to the Obsidian master
task list: marks matching tasks done: true with completed_date set.

Outputs plain text describing what was synced -- designed to be read by
Claude, not machines.
"""
from __future__ import annotations

import datetime
import re
from pathlib import Path

VAULT = Path("/Users/becca/Library/Mobile Documents/iCloud~md~obsidian/Documents/BeccaNap")
TASKS_DIR = VAULT / "tasks"
DAILYLOG_DIR = VAULT / "dailyLog"


def _parse_frontmatter(text: str) -> tuple[dict, str, str]:
    """Return (frontmatter dict, raw frontmatter block, body)."""
    m = re.match(r"^---\n(.*?\n)---\n(.*)$", text, re.DOTALL)
    if not m:
        return {}, "", text
    fm_raw, body = m.group(1), m.group(2)
    out = {}
    for key in ("title", "done", "completed_date"):
        r = re.search(rf"^{key}:\s*(.*)$", fm_raw, re.MULTILINE)
        if r:
            out[key] = r.group(1).strip().strip("'\"")
    return out, fm_raw, body


def _extract_title(line: str) -> str:
    # Strip a trailing Obsidian completion marker, e.g. "✅ 2026-06-10"
    line = re.sub(r"\s*✅\s*\d{4}-\d{2}-\d{2}\s*$", "", line)
    # Inbox-style lines: "Title -- duration -- hard/soft -- deadline"
    title = line.split(" -- ")[0].strip()
    # Strip trailing parenthetical notes for block-style lines
    title = re.sub(r"\s*\([^)]*\)\s*$", "", title).strip()
    return title


def main() -> None:
    today = datetime.date.today()
    log_file = DAILYLOG_DIR / f"{today.isoformat()}.md"
    if not log_file.exists():
        print(f"(no dailyLog file for {today.isoformat()})")
        return

    checked_titles = []
    for line in log_file.read_text().splitlines():
        m = re.match(r"^- \[x\]\s*(.+)$", line, re.IGNORECASE)
        if m:
            checked_titles.append(_extract_title(m.group(1)))

    if not checked_titles:
        print("(nothing checked off yet)")
        return

    task_files = sorted(TASKS_DIR.glob("*.md"))

    synced, already_done, no_match = [], [], []

    for title_guess in checked_titles:
        match = None
        for f in task_files:
            meta, fm_raw, body = _parse_frontmatter(f.read_text(errors="replace"))
            t = meta.get("title", "")
            if not t:
                continue
            if t.lower() == title_guess.lower() or t.lower() in title_guess.lower() or title_guess.lower() in t.lower():
                match = (f, meta, fm_raw, body)
                break

        if not match:
            no_match.append(title_guess)
            continue

        f, meta, fm_raw, body = match
        if meta.get("done", "").lower() in ("true", "yes", "1"):
            already_done.append(meta["title"])
            continue

        new_fm = re.sub(r"^done:\s*.*$", "done: true", fm_raw, flags=re.MULTILINE)
        if re.search(r"^completed_date:\s*.*$", new_fm, re.MULTILINE):
            new_fm = re.sub(
                r"^completed_date:\s*.*$",
                f"completed_date: '{today.isoformat()}'",
                new_fm,
                flags=re.MULTILINE,
            )
        else:
            new_fm += f"completed_date: '{today.isoformat()}'\n"

        f.write_text(f"---\n{new_fm}---\n{body}")
        synced.append(meta["title"])

    print(f"=== Synced from {log_file.name} ===")
    if synced:
        print("Marked done in master task list:")
        for t in synced:
            print(f"  - {t}")
    if already_done:
        print("Already marked done:")
        for t in already_done:
            print(f"  - {t}")
    if no_match:
        print("Checked in dailyLog but no matching task file found:")
        for t in no_match:
            print(f"  - {t}")


if __name__ == "__main__":
    main()

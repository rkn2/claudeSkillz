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

## Installation

**Option 1: Copy SKILL.md directly**
```bash
mkdir -p ~/.claude/skills/nsf-proposal-draft
cp nsf-proposal-draft/SKILL.md ~/.claude/skills/nsf-proposal-draft/SKILL.md
```

**Option 2: Install the .skill package** (if your Claude version supports it)
```bash
# Open the .skill file through the Claude interface
```

## Adding new skills

Each skill lives in its own subdirectory with at minimum a `SKILL.md` file. Add new skills as subdirectories here, with a corresponding entry in this README.

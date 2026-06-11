---
name: nsf-proposal-draft
description: "Use this skill whenever the user wants to convert research ideas, a project summary, notes, or an NSF program call into a structured NSF proposal draft in LaTeX. Triggers include: 'write an NSF proposal', 'draft a grant', 'convert this to an NSF draft', 'turn my notes into a proposal', 'generate a grant application from my summary', or any request to produce a multi-file LaTeX grant document. Also trigger when the user has a folder of materials (summary, call, notes) and wants to produce Research.tex, summary.tex, DMP2.tex, or mentoringPlan.tex. Use this skill even if the user just says 'make an NSF draft from this folder' or 'help me write a proposal from these materials.'"
---

# NSF Proposal Draft Generator

Converts a folder of input materials (project summary, notes, NSF program call) into a complete NSF proposal draft in LaTeX. The process is a structured interview that draws out the intellectual content before generating any text. Do not skip phases or combine them -- the interview order matters because each phase builds on the last.

## Process overview

1. Read the input folder
2. Confirm understanding (Phase 1)
3. Interview the user through Phases 2-7, one phase at a time, waiting for their response before moving on
4. Generate all LaTeX files (Phase 8)

---

## Phase 1: Read and confirm

Ask the user for the path to their materials folder. Read all .md, .txt, .tex, and .pdf files there. Identify: the NSF program call or solicitation, any project summary or overview, and any notes or email correspondence (especially from program officers).

Summarize what you found in 3-4 sentences and ask: "Does this capture the proposal correctly before we dig in?"

Do not proceed until the user confirms.

---

## Phase 2: Main research idea

Ask: "In 1-2 sentences, what is the core research problem that is currently unsolved? What is fundamentally not known or not characterized that this project will address?"

Remind them: the answer should be a knowledge gap, not a technology to build. If they describe a system or tool they want to create, gently reframe: "What scientific question will that system help answer? What is not known about [domain] that motivates building it?"

Wait for their answer before moving on.

---

## Phase 3: PI team

Ask: "Who are the PIs on this project? For each one, give me their name, institution, and the primary scientific territory they own in this project -- not their role in running studies or supervising students, but the intellectual contribution that only they can make."

Wait for the full team description before moving on.

---

## Phase 4: Research questions

Ask: "What are the 1-3 research questions this proposal addresses?"

For each RQ the user proposes, check whether it asks what is NOT KNOWN (good) or describes something to build (needs reframing). 

Good framing examples:
- "How can agentic AI systems represent X to achieve Y?"
- "What principles govern the relationship between X and Y?"
- "How does X affect Y in the context of Z?"

Bad framing examples:
- "How do we build X?"
- "How can we develop a framework for X?"
- "What is the best way to implement X?"

If an RQ sounds like an engineering objective, push back gently: "This sounds like a design goal rather than a research question. What is not currently known or understood that your work will establish? Can we reframe it as a question about principles, relationships, or mechanisms?"

Wait for refined RQs before moving on.

---

## Phase 5: Research gaps

For each RQ, ask: "What is the scientific knowledge gap this question addresses? What specifically is not known or not characterized in the literature?"

The gaps must be framed as knowledge gaps, not tool gaps. Check each one:

Correct framing: "it is not known...", "the relationship between X and Y is not characterized", "the principles governing X are not established", "it is unknown how X affects Y"

Incorrect framing: "no framework exists for X", "no tool does X", "there is no system that Y" -- these describe missing technology, not missing knowledge. Push back: "Frame this as what is scientifically unknown rather than what tool is missing."

Wait for refined gaps before moving on.

---

## Phase 6: Research objectives and tasks

For each PI, ask:
- "What is the research objective [PI name] leads? Give it a title that captures the scientific contribution."
- "What are [PI name]'s 2-4 specific research tasks under that objective?"

Then ask: "Is there an integration or closing-the-loop objective that all PIs contribute to? What does the validation or synthesis work look like?"

Clarify the mapping: which RQs does each RO address? ROs and RQs do not need to be 1:1. A single RQ may require multiple ROs to answer it; note this explicitly in the proposal text.

Wait for the full objective and task structure before moving on.

---

## Phase 7: Pilot context

Ask: "Where will this framework be validated? Describe the pilot sites, case study context, or test environments."

Note to yourself: this content goes in Section 4 (Pilot sites and preliminary work), NOT in the Status quo section. Status quo stays at national scale and does not name specific sites.

Wait for their answer, then proceed to generate.

---

## Phase 8: Generate all files

Generate five files in the user's materials folder (or a new subfolder if they prefer):

- `Research.tex`
- `summary.tex`
- `mentoringPlan.tex`
- `DMP2.tex`
- `biblio.bib`

---

## Research.tex: full structure and rules

### Preamble (copy exactly)

```latex
\documentclass[11pt]{article}
% NSF PAPPG Ch. 2 SS B.2: font >=11pt, margins >=1in, <=6 lines/inch.
% No hyperlinks in Project Description body (Research.gov constraint).

\usepackage{bm}
\usepackage{color}
\usepackage{hyperref}
\usepackage{graphicx}
\usepackage{wrapfig}
\usepackage{subcaption}
\usepackage{vmargin}
\usepackage{mathrsfs}
\usepackage{float}
\usepackage{tabularx}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{ltablex}
\usepackage[svgnames]{xcolor}
\usepackage[most]{tcolorbox}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage{caption}
\usepackage{colortbl}
\usepackage[numbers,square,sort&compress]{natbib}
\usepackage{pgfgantt}

% ── Colors ──────────────────────────────────────────────────────────────────
\definecolor{mycmykcolor}{cmyk}{0.45,0.30,0.20,0}
\definecolor{secondary}{cmyk}{0,0,0,0.20}

% Project-goals box color
\definecolor{top}{HTML}{C98873}

% Per-RO colors (tied to the Gantt chart groups in "Project timeline and evaluation")
\definecolor{roonecol}{HTML}{8C9EB2}    % RO1 -- soft muted blue
\definecolor{rootwocol}{HTML}{E0914D}   % RO2 -- warm amber/orange
\definecolor{roothreecol}{HTML}{FCD053} % RO3 -- pastel yellow

\linespread{0.9}

\titleformat{\section}[runin]{\normalfont\bfseries}{\thesection}{1em}{}[:]
\titlespacing*{\section}{0pt}{\baselineskip}{1ex}
\titleformat{\subsection}[runin]{\normalfont\bfseries}{\thesubsection}{1em}{}[:]
\titlespacing*{\subsection}{0pt}{\baselineskip}{1ex}

% Block-style heading for occasional sections (e.g. Broader Impacts) that should
% break out of the default runin section style.
\newcommand{\customsection}[1]{%
  \titleformat{\section}[block]{\normalfont\bfseries}{\thesection}{1em}{}[]%
  \section{#1}%
  \titleformat{\section}[runin]{\normalfont\bfseries}{\thesection}{1em}{}[:]%
}

\bibliographystyle{unsrtnat}
\hypersetup{hidelinks,colorlinks=false,urlcolor=black}
\hypersetup{draft}
\setpapersize{USletter}
\setmarginsrb{1in}{1in}{1in}{1in}{0pt}{0mm}{0pt}{0mm}
\pretolerance=5000
\tolerance=9000
\graphicspath{{images/}}

\newcommand{\pseudodot}{{\lower 2.4pt\hbox{$\cdot$}}}

\begin{document}
\pagestyle{empty}  %turn this back on at the end for nsf
```

### Section order

**1. Goals tcolorbox** (no section heading before it)

Open with a tcolorbox summarizing the project around its RQs:

```latex
\begin{tcolorbox}[colback=top!55, colframe=black, boxrule=1pt, coltext=black]
\textbf{Project goals:}
[2-4 sentences. State the framework or system being proposed. Name each RQ with \textbf{RQ1}, \textbf{RQ2} etc. and the PI(s) responsible. End with the defining intellectual contribution -- what makes this not just building a system but advancing generalizable knowledge.]
\end{tcolorbox}
```

**2. Opening wrapfigure** (right-aligned, 0.45 or 0.5 textwidth)

```latex
\begin{wrapfigure}{r}{0.45\textwidth}
\vspace{-0.4cm}
% TODO FIGURE: [Describe what the figure should show -- the framework architecture,
%   the key coupling or tradeoff, the closed-loop structure. Be specific about
%   what visual would make the intellectual contribution immediately legible
%   to a reviewer skimming the page.]
\includegraphics[width=0.45\textwidth]{images/images.png}
\captionsetup{justification=centering,singlelinecheck=false,font=small}
\vspace{-0.9cm}
\caption{[Caption.]}
\label{fig:framework}
\vspace{-0.4cm}
\end{wrapfigure}
```

**3. \section{Status quo}**

Three paragraphs:
- Para 1: National-scale problem. What is the situation across the US (or globally) that motivates this work? Start general. Do NOT name the pilot sites here.
- Para 2: The fundamental difficulty. If there are multiple coupled scales or dimensions to the problem, name them and explain why they cannot be solved independently. This is where the core intellectual tension lives.
- Para 3: Gap in existing tools/methods and program alignment. What do existing approaches miss? End with a sentence explicitly connecting to NSF program priorities using language from the call.

Add a second wrapfigure in the status quo section illustrating the problem (same format as above).

**4. \subsection{Intellectual merit}** (inside the Status quo section)

List RQs as an itemize with \textbf{RQ1 (PI names):} format. Follow with a paragraph explaining how the RQs couple and why their integration is the primary contribution. End with the RQ-to-RO mapping sentence: "RQ1 is addressed through [RO1 and RO2]; RQ2 is addressed through [RO3]." (adjust as appropriate).

**5. Table 1** (ltablex, 4 columns, 3 rows max)

```latex
\begingroup
\footnotesize
\begin{tabularx}{\textwidth}{|X|X|X|X|}
\caption{Summary of research gaps, objectives, approaches, and outcomes\label{tab:research_summary}}\\
\hline
\rowcolor{mycmykcolor}
\textbf{Research Gaps} & \textbf{Objectives} & \textbf{Approaches} & \textbf{Outcomes}\\
\hline
\endfirsthead
...
```

Gaps column: knowledge gaps only. Use "it is not known...", "not characterized", "not established". Never "no framework exists" or "no tool does X".

Objectives column: bold RO label + brief description + PI names in parens.

**6. \section{Current state-of-the-art}**

Opening paragraph (3-4 sentences) situating the technical domains and framing the integration gap. Then one \subsection per domain. Then \subsection{Gap summary}.

Each domain subsection body is a stub:
```
Add content here, see comment below
% firstname: [detailed guidance on what literature to cover, what the
%   limitation to highlight is, what 3-5 papers to start with]
```

Gap summary paragraph is written prose (not a stub) -- it synthesizes the gaps and points to Table 1.

**7. \section{Pilot sites and preliminary work}**

Opening sentence introducing the validation context. Then stubs:
```
% firstname: [paragraph describing PI's preliminary results -- prior work on
%   X, Y, Z that establishes feasibility]
```

One stub per PI.

**8. \section{Research plan}**

Opening paragraph: "The research plan is organized around [N] research objectives corresponding to the [N] research questions. [RO1 description + PI(s) + subtask count]. [RO2 description + PI + subtask count]. [RO3 description + PI(s)]."

For each RO, use the matching per-RO color (`roonecol` for RO1, `rootwocol` for RO2,
`roothreecol` for RO3, defined in the preamble) -- these same colors are reused for
that RO's group in the Gantt chart in Section 10:

```latex
\begin{tcolorbox}[colback=roonecol!55,colframe=black,boxrule=1pt,coltext=black,
  left=1mm,right=1mm,top=1mm,bottom=1mm]
\textbf{Research Objective N (RON, lead(s): Lastname \& Lastname): Title.}
\end{tcolorbox}
```

Followed by 2-3 sentences explaining how this RO addresses its RQ and what the coupling or novelty is.

For each subtask:
```
\textbf{Subtask N.M: Title (lead: Lastname).}
2-3 sentences of prose describing what will be done and why it is the right approach.

% firstname: [specific questions about methodology, formalism, platform, or
%   design choices that the PI needs to fill in]
```

At the end of each RO's subtasks (before the next tcolorbox):
```
\textbf{Key outcomes and evaluation:} Add after subtasks are written.
```

**9. \customsection{Broader Impacts}**

Use `\customsection{Broader Impacts}` (defined in the preamble) instead of
`\section{}` for this heading -- it breaks out of the runin section style for this
one section. Four paragraphs of written prose:
- Para 1: How the framework transforms access or practice for the target community
- Para 2: Generalizability beyond the pilot domain
- Para 3: Program alignment
- Para 4: Graduate student training (name each student, PI, and focus)

Then subsections:
- \subsection{Potential for transformative impact} -- 3 sentences of prose
- \subsection{Education and broadening participation} -- BESURE/WISER/MURE for Penn State PIs; `% firstname:` comment for other institutions' programs; broadening participation stub
- \subsection{Open science and transferability} -- prose specifying GitHub + MIT license + data repository

**10. \section{Project timeline and evaluation}**

Written prose (not a stub). State project duration, parallel/sequential structure of ROs by year, and 5-6 numbered KPIs corresponding to each RO and the human-AI collaboration work. Reference the Gantt chart as `Fig.~\ref{fig:gantt}` and its numbered milestones.

Follow the prose with a Gantt chart figure built with `pgfgantt` (do not use an
`\includegraphics` image for the timeline). One `\ganttgroup` per RO, using that
RO's color (`roonecol`/`rootwocol`/`roothreecol`, matching the tcolorbox colors
from Section 8), with `\ganttbar` rows per subtask and `\ganttmilestone` markers
numbered to match the KPIs/milestones referenced in the prose:

```latex
\begin{figure}[H]
\centering
\resizebox{0.85\textwidth}{!}{%
\begin{ganttchart}[
  hgrid,
  vgrid=false,
  x unit=2.6mm,
  y unit title=5mm,
  y unit chart=4.8mm,
  title/.style={fill=lightgray, draw=black, font=\scriptsize\bfseries},
  title label font=\scriptsize\bfseries,
  bar label font=\scriptsize,
  group label font=\scriptsize\bfseries,
  bar height=0.55,
  group height=0.3,
  bar top shift=0.225,
  bar label node/.append style={align=right, text width=4.2cm},
  group label node/.append style={align=right, text width=4.2cm},
  milestone label font=\tiny,
  milestone label node/.append style={text width=0pt, text=white},
]{1}{36}
%--- title rows
\gantttitle{Year 1}{12}\gantttitle{Year 2}{12}\gantttitle{Year 3}{12} \\
\gantttitle{Q1}{3}\gantttitle{Q2}{3}\gantttitle{Q3}{3}\gantttitle{Q4}{3}%
\gantttitle{Q1}{3}\gantttitle{Q2}{3}\gantttitle{Q3}{3}\gantttitle{Q4}{3}%
\gantttitle{Q1}{3}\gantttitle{Q2}{3}\gantttitle{Q3}{3}\gantttitle{Q4}{3} \\
%--- RO1
\ganttgroup[
  group/.append style={fill=roonecol, draw=roonecol!70!black},
  group label node/.append style={text=roonecol!70!black}
]{RO1}{1}{18}
  \ganttmilestone[milestone/.append style={fill=roonecol!60!black, draw=roonecol!40!black, shape=rectangle, rounded corners=1pt, inner sep=6pt, label={[font=\tiny\bfseries,text=white,inner sep=0pt]center:1}}]{}{18} \\
\ganttbar[bar/.append style={fill=roonecol!55, draw=roonecol!80}]{1.1 [Subtask title]}{1}{12} \\
\ganttbar[bar/.append style={fill=roonecol!55, draw=roonecol!80}]{1.2 [Subtask title]}{1}{12} \\
\ganttbar[bar/.append style={fill=roonecol!55, draw=roonecol!80}]{1.3 [Subtask title]}{6}{18} \\
%--- RO2
\ganttgroup[
  group/.append style={fill=rootwocol, draw=rootwocol!70!black},
  group label node/.append style={text=rootwocol!70!black}
]{RO2}{1}{24}
  \ganttmilestone[milestone/.append style={fill=rootwocol!60!black, draw=rootwocol!40!black, shape=rectangle, rounded corners=1pt, inner sep=6pt, label={[font=\tiny\bfseries,text=white,inner sep=0pt]center:2}}]{}{24} \\
\ganttbar[bar/.append style={fill=rootwocol!55, draw=rootwocol!80}]{2.1 [Subtask title]}{1}{12} \\
\ganttbar[bar/.append style={fill=rootwocol!55, draw=rootwocol!80}]{2.2 [Subtask title]}{12}{24} \\
%--- RO3
\ganttgroup[
  group/.append style={fill=roothreecol, draw=roothreecol!70!black},
  group label node/.append style={text=roothreecol!70!black}
]{RO3}{12}{36}
  \ganttmilestone[milestone/.append style={fill=roothreecol!60!black, draw=roothreecol!40!black, shape=rectangle, rounded corners=1pt, inner sep=6pt, label={[font=\tiny\bfseries,text=white,inner sep=0pt]center:3}}]{}{30}
  \ganttmilestone[milestone/.append style={fill=roothreecol!60!black, draw=roothreecol!40!black, shape=rectangle, rounded corners=1pt, inner sep=6pt, label={[font=\tiny\bfseries,text=white,inner sep=0pt]center:4}}]{}{36} \\
\ganttbar[bar/.append style={fill=roothreecol!55, draw=roothreecol!80}]{3.1 [Subtask title]}{12}{24} \\
\ganttbar[bar/.append style={fill=roothreecol!55, draw=roothreecol!80}]{3.2 [Subtask title]}{24}{36}
\end{ganttchart}%
}
\caption{Project timeline and Gantt chart. Numbered rectangles denote the
chronological sequence of key performance indicators (KPIs) and project
milestones.}
\label{fig:gantt}
\end{figure}
```

Adjust the `{1}{36}` project-month range, `\gantttitle` Year/Quarter spans, each
`\ganttgroup`'s start/end month, and the per-RO `\ganttbar` rows to match the
project's actual duration and number of ROs/subtasks.

**11. \section{Results from prior NSF Support}**

For each PI: `\noindent\textbf{PI Lastname:}` followed by a comment stub:
```
% firstname: add prior NSF support in this format:
%   (a) award number, dollar amount, dates
%   (b) title
%   (c) intellectual merit (2-3 sentences), broader impacts (2-3 sentences)
%   (d) publications (cite key list)
%   (e) publicly shared datasets
%   (f) renewal status
```

---

## Critical style rules

**No em dashes.** Never use `---`. Use a comma, colon, semicolon, or rephrase the sentence. This is non-negotiable -- em dashes do not appear anywhere in the output.

**Comments use lowercase first name only.** The format is `% firstname: question or note`. Use the PI's first name, lowercase, no colon before the name, no TODO or QUESTION labels. This is how the PIs will find their action items in the document. Examples:
- `% becca: describe the knowledge representation formalism here`
- `% ilya: what simulation platform will you use for layout evaluation?`
- `% jess: how will you recruit stakeholders for the user studies?`

**Knowledge gaps, not tool gaps.** Every gap statement in Table 1 and in the intellectual merit section must describe missing scientific knowledge, not a missing artifact. "It is not known how X affects Y" is correct. "No framework exists for X" is not.

**xxx for unknown quantities.** Use `xxx` inline when a specific number or detail is not yet known: "xxx pilot sites", "xxx graduate researchers", "deployed at xxx facilities".

**SOTA stubs, not generated literature.** Do not write the literature review paragraphs. The PIs know the literature; you do not know their citations. Write the section headers and detailed `% firstname:` guidance comments, then `Add content here, see comment below`.

---

## summary.tex

Structure:
```latex
\documentclass[11pt]{article}
\usepackage{nopageno}
\setcounter{secnumdepth}{1}
\usepackage[margin=1in]{geometry}
\begin{document}
\pagestyle{empty}

\vspace{-0.3cm}
\subsection{Overview}
\vspace{-0.3cm}
[Opening sentence names all PIs with institution and role. 
Then 2-3 sentences on the national problem. 
Then one sentence per thrust/RO describing the proposed approach.
End with the defining contribution.]

\vspace{-0.5cm}
\subsection{Intellectual Merit}
\vspace{-0.3cm}
[One paragraph per RQ, stating what is not known and what the project will establish.
End with the integration argument: what makes the combination novel beyond any single contribution.]

\vspace{-0.5cm}
\subsection{Broader Impacts}
\vspace{-0.3cm}
[Who benefits, how the framework generalizes, student training, open-source release.]

\end{document}
```

No URLs, no hyperlinks, no em dashes. ~1 page.

---

## mentoringPlan.tex

Opening paragraph: name each graduate researcher, their PI, institution, and research focus (RO assignment).

Then one `\noindent \textbf{Section:}` block per topic:
- Regular one-on-one meetings
- Cross-disciplinary co-mentoring (describe what each student learns from the other PIs' groups)
- Industry and stakeholder engagement
- Career counseling and professional development (list relevant conferences for each PI's domain)
- Training in grant proposal and scholarly communication
- Teaching and mentoring skill development
- Undergraduate research involvement (BESURE/WISER/MURE for Penn State; `% firstname:` for other institutions)
- Collaboration and diversity training
- Responsible professional practices

Use `% firstname:` comments for institution-specific programs and for details the PI needs to confirm.

---

## DMP2.tex

Use runin section formatting (same titleformat as Research.tex).

Sections:
1. **Roles and Responsibilities**: Lead PI (Napolitano or whoever is named as lead) has primary responsibility. Each co-PI is secondary custodian for their data stream. Name the streams.

2. **Expected Data and Formats**: Itemized list. Each item: bold data type label, 1-2 sentences describing content, then "Formats: [list]". Include one item per major data category (AI pipeline code/outputs, experimental data, user study data, pilot deployment data, dissemination materials). Add `% firstname:` comments where format needs PI confirmation.

3. **Access, Sharing, and Reuse Policies**: GitHub + MIT license for code. DesignSafe-CI or Open Science Framework for data. Shared within 12 months of collection or upon publication. Identifiable human subjects data restricted to project personnel.

4. **Reproducibility**: Git version control, Docker/Conda environments, code to reproduce all analyses.

5. **Data Storage, Preservation and Backup**: Penn State ICDS-ACI for Penn State PIs. `% firstname:` for other institutions' storage resources.

6. **Ethics and Privacy**: IRB compliance for human subjects. Anonymization before sharing. Data use agreements for industry partners. `% firstname:` on IRB lead institution question.

---

## biblio.bib

Stub entries only -- do not invent citations. Create placeholder entries for each citation key used in the tex files, with a comment explaining what the citation should be:

```bibtex
@misc{placeholder_key,
  author = {PLACEHOLDER},
  title  = {PLACEHOLDER: [description of what this citation should be]},
  year   = {XXXX},
  note   = {Replace with real citation}
}
```

---

## Final check before writing files

Before generating, confirm:
- No em dashes anywhere in the output
- All gaps in Table 1 use knowledge gap framing
- SOTA subsections are stubs with `% firstname:` guidance
- Pilot sites section is a stub
- Prior NSF support section is a stub
- Each RO section ends with "Key outcomes and evaluation: Add after subtasks are written."
- All comments use `% firstname:` format (lowercase, first name only)
- `xxx` used for all unknown quantities
- Each RO tcolorbox uses its matching color (`roonecol`/`rootwocol`/`roothreecol`)
- Project timeline section includes a `pgfgantt` Gantt chart (Fig.~\ref{fig:gantt}), not a placeholder image
- Broader Impacts heading uses `\customsection{Broader Impacts}`

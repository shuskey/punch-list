# Punch List — Technical Specification

**Version**: 2.2
**Status**: Released
**Author**: Scott Huskey
**Date**: 2026-04-16

---

## 1. Purpose and Problem Statement

AI-assisted development has made it possible for a single developer to run five to seven projects in parallel. Agents handle deep implementation work; the developer operates at a higher level — directing, reviewing, deciding. The bottleneck is no longer writing code.

**The bottleneck is context switching.**

Every move between projects requires: mentally shelving the current context, navigating to the right ticket system, finding the right epic, opening a new issue, filling in fields, finding the local directory, confirming the right branch, and re-orienting to where work left off. High enough friction that developers skip it. Bugs never get filed. Insights evaporate.

**Punch List greases the skids for context switching — both entering and exiting a project.**

Core proposition: *stay in Claude, stay in flow, let the system handle the overhead.*

> "Hey Claude, add a bug to Project B: the login page times out after 30 seconds." Done. Never left Project A.

---

## 2. Design Philosophy

### Thin Skills, Rich Orchestration

No monolithic UI. Seven focused Claude Code skills — each a lightweight connector between Claude and the tools already in use (GitHub, the local filesystem). Claude orchestrates across them. More capable than a heavy UI, far easier to evolve.

### Lifecycle-First, Not Org-Chart-First

Unlike traditional project trackers that organize around ownership ("who is responsible?"), Punch List organizes around state ("where is this project in its life?"). The board answers: *What does it take to get this to the next step?*

### Human-in-the-Loop Handoffs

No autonomous state transitions. The human always decides when to advance, redirect, or move. Agents execute within a state; humans decide when the state changes.

### Context Travels with the Card

Artifacts, update notes, and history move with the project regardless of state direction. Nothing is lost on backward moves.

### Retirement Is Intentional

Nothing disappears passively. G3 Retired is the only true exit.

---

## 3. Architecture Overview

```text
Developer
    │
    │  slash commands (/pl-*)
    ▼
Claude Code (CLI / IDE Extension)
    │                    │
    │ invokes            │ invokes
    ▼                    ▼
PL Skills            PL Registry (~/.punch-list/)
~/.claude/skills/    ├── registry.json
symlinked from       └── projects/<slug>/
repo                     └── config.json
    │                           │
    │ reads/writes              │
    └───────────────────────────┘
    │
    ├──────────────────────────┐──────────────────────────┐
    ▼                          ▼                          ▼
GitHub Issues              GitHub Repo             Local Filesystem
gh CLI                     skills source + PRs     Project working dirs
create & list issues       linked in config.json   Claude Code / Cursor
```

### Three-Layer Design

| Layer | What | Where |
| ----- | ---- | ----- |
| Skills | Claude Code slash commands | `~/.claude/skills/` → symlinked from repo |
| Registry | Local JSON state | `~/.punch-list/` |
| External | GitHub Issues, filesystem | `gh` CLI + local paths |

---

## 4. The Registry

All state lives at `~/.punch-list/`. Owned and written by the PL skills. Never shared; no server.

### 4.1 Directory Structure

```text
~/.punch-list/
├── registry.json              # Master project index
└── projects/
    └── <slug>/
        └── config.json        # Per-project metadata
```

### 4.2 `registry.json`

```json
{
  "version": "1.0",
  "createdAt": "2026-04-09",
  "projects": [
    {
      "slug": "punch-list",
      "name": "Punch List",
      "state": "D",
      "description": "A lifecycle-first registry so audacious it needed its own state model."
    }
  ]
}
```

Registry entries contain only display fields. All operational data (`githubRepo`, `localDirectory`, `subDirectory`, `swimLane`, `updateNotes`) lives exclusively in the per-project config — this prevents the two from drifting out of sync.

| Field | Type | Description |
|-------|------|-------------|
| `slug` | string | Unique identifier |
| `name` | string | Display name |
| `state` | `"A"`–`"G"` | Lifecycle state — duplicated here for fast listing without reading configs |
| `description` | string | One-line project description |

### 4.3 `projects/<slug>/config.json`

```json
{
  "name": "Punch List",
  "slug": "punch-list",
  "description": "A lifecycle-first registry so audacious it needed its own state model.",
  "state": "D",
  "swimLane": null,
  "githubRepo": "https://github.com/shuskey/punch-list",
  "subDirectory": null,
  "localDirectory": null,
  "updateNotes": "Ready to use! Please create tickets here to drive improvements!",
  "createdAt": "2026-04-09",
  "updatedAt": "2026-04-15"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `state` | `"A"`–`"G"` | Lifecycle state (see Section 5) |
| `swimLane` | `"internal"` \| `"customer"` \| null | Future: drives gate strictness |
| `githubRepo` | string? | GitHub repo URL — issues on this repo are the project's tickets |
| `subDirectory` | string? | Subdirectory within the repo and local directory |
| `localDirectory` | string? | Absolute path to local working directory |
| `updateNotes` | string? | Free-form notes on where work was left off and what's next |

---

## 5. The 7-State Lifecycle

```text
A ──► B ──► C ──► D ──► E ──► F ──► G
      ▲     │     │
      └─────┘     │  (projects can move backward — history is preserved)
            └─────┘
```

| State | Label | Mnemonic | When to be here |
|-------|-------|----------|-----------------|
| **A** | Ideation | Aspiring | Idea captured, not yet scoped |
| **B** | Defining | Building | Spec in progress, track assigned |
| **C** | Proving | Crystallizing | Prototype / PoC / in review |
| **D** | Delivering | Dispatching | Active development and staging |
| **E** | Evolving | Elevating | In production, iterating |
| **F** | Sustaining | Fortifying | Stable, in maintenance |
| **G** | Sunsetting | Graduating | Deprecating through retirement |

### Future Sub-States (Designed, Not Yet Built)

Each state will expand to 3–5 sub-states. Examples:

- **B**: B1 Structuring → B2 Spec Drafting → B3 Track Assigned → B4 Spec Ready
- **C**: C1 Prototyping → C2 Demonstrating → C3 In Review → C4 Needs Rework → C5 Approved
- **D**: D1 Planned → D2 In Progress → D3 In Staging → D4 Launched

Sub-states tell you not just *which column* a project is in, but *exactly where it stands* and *what the next action is*.

## The 23 Sub-States

Sub-states are the granular positions within each state. Format: `[Letter][Number] Name`

```text
A1 Spark
A2 Captured
A3 Conversing

B1 Structuring
B2 Spec drafting
B3 Spec ready

C1 Prototyping
C2 Demonstrating
C3 In review
C4 Needs rework
C5 Approved

D1 Planned
D2 In progress
D3 In staging
D4 Launched

E1 In production
E2 Iterating
E3 Needs attention

F1 Stable
F2 Maintained
F3 Under review

G1 Deprecating
G2 Decommissioning
G3 Retired
```

---

## 6. Skills Reference

Seven Claude Code skills, installed as symlinks from the repo to `~/.claude/skills/`. Edits to skills in the repo are live immediately — no reinstall needed.

### 6.1 `/pl-init`

**Purpose**: One-time setup of `~/.punch-list/`. Idempotent — safe to re-run.

**Flow**:

1. Check for existing registry — if found, report and stop
2. Create `~/.punch-list/projects/` directory
3. Write `registry.json`

**Writes**: `~/.punch-list/registry.json`

---

### 6.2 `/pl-create-project`

**Purpose**: Interactive creation of a new project card.

**Flow**:

1. Prompt: project name → auto-generate slug
2. Generate creative description (AI suggestion; accept / regenerate / rewrite)
3. Optionally collect: GitHub repo URL, subdirectory, local directory, initial state
4. Write `projects/<slug>/config.json`, update `registry.json`

---

### 6.3 `/pl-list-projects`

**Purpose**: Display all tracked projects grouped by state.

**Output format**:
- 5+ projects: grouped by state header
- Fewer: flat list with column headers

**Columns**: Name | [State] Label | GitHub (yes/no) | Local (yes/no)

No external calls are made by this skill.

---

### 6.4 `/pl-project <slug>`

**Purpose**: Full detail card for a single project.

**Displays**:
- Core metadata: name, slug, state, paths, config location
- **Update Notes**: free-form progress/next-steps from the card
- **Open Issues**: open GitHub issues from the project's repo (via `gh issue list`)

**GitHub call** (if `githubRepo` is set):

```bash
gh issue list --repo <owner/repo> --state open --json number,title,labels,state --limit 50
```

**Offers**: Update notes editing at end of display.

---

### 6.5 `/pl-create-ticket`

**Purpose**: Create a new GitHub issue on the project's repo.

**Flow**:

1. List projects that have a `githubRepo` set; user selects one
2. Choose issue type: Bug, Feature, Task, Story
3. Enter title (required) and body (optional)
4. Run `gh issue create --repo <owner/repo> --title "..." --label "<type>" --body "..."`
5. Display summary card: issue number, type, label, title, repo URL, issue URL

**Issue type → label mapping**:

| Type    | Label        |
|---------|--------------|
| Bug     | `bug`        |
| Feature | `enhancement`|
| Task    | `task`       |
| Story   | `story`      |

---

### 6.6 `/pl-claude <slug>`

**Purpose**: Launch Claude Code at the project's local working directory.

**Path computation**: `localDirectory` + optional `subDirectory`

**Implementation**: AppleEvent / osascript opens Terminal and runs `claude` CLI at the resolved path.

**Checks**: Detects if a Claude Code session is already running at that path; offers to launch another or cancel.

---

### 6.7 `/pl-cursor <slug>`

**Purpose**: Launch Cursor at the project's local working directory.

**Implementation**: `cursor --reuse-window <resolved-path>`

---

## 7. GitHub Issues Integration

All ticketing is done via the `gh` CLI against the GitHub repo stored in each project's `githubRepo` field. The repo is the project — there is no separate epic or ticketing reference. Issues live natively on the repo.

### 7.1 Issue Types

GitHub Issues has no native type concept. Types are represented as labels:

| Punch List Type | GitHub Label | Notes |
|-----------------|-------------|-------|
| Bug | `bug` | GitHub default label |
| Feature | `enhancement` | GitHub default label |
| Task | `task` | Custom label — created on first use if missing |
| Story | `story` | Custom label — created on first use if missing |

### 7.2 Key `gh` Commands

**Create an issue**:

```bash
gh issue create \
  --repo "<owner/repo>" \
  --title "<title>" \
  --label "<label>" \
  --body "<body>"
```

**List open issues**:

```bash
gh issue list \
  --repo "<owner/repo>" \
  --state open \
  --json number,title,labels,state \
  --limit 50
```

**Derive `owner/repo`** from `githubRepo` URL by stripping `https://github.com/`.

### 7.3 Adding a Different Provider

If a future provider is needed (Linear, Jira, ClickUp, etc.), the four ticketing-aware skills to update are: `/pl-init`, `/pl-create-project`, `/pl-project`, `/pl-create-ticket`. No changes needed to: `/pl-list-projects`, `/pl-claude`, `/pl-cursor`.

---

## 8. Installation

### 8.1 Prerequisites

- Claude Code CLI installed
- `gh` CLI installed and authenticated (`gh auth login`)

### 8.2 Install Steps

```bash
# Clone or pull the repo
git clone https://github.com/shuskey/punch-list
cd punch-list

# Install skills (symlinks)
./install-skills.sh

# Initialize the registry
# (in any Claude Code session)
/pl-init
```

`install-skills.sh` creates:

```text
~/.claude/skills/<name>  →  ~/.agents/skills/<name>  →  /repo/skills/<name>
```

Edits to skills in the repo are live immediately. Re-run with `--force` to replace existing links.

---

## 9. What Is and Isn't Built (Phase One vs. Full Vision)

### Phase One — Shipped

| Feature | Status |
|---------|--------|
| 7-state lifecycle registry | Done |
| `/pl-init` | Done |
| `/pl-create-project` | Done |
| `/pl-list-projects` | Done |
| `/pl-project` (with update notes + open GitHub issues) | Done |
| `/pl-create-ticket` (GitHub Issues via gh CLI) | Done |
| `/pl-claude`, `/pl-cursor` | Done |
| `updateNotes` field on project cards | Done |

### Immediate Next Steps

| Feature | Priority | Description |
|---------|----------|-------------|
| Sub-state support | High | Surface A1–G3 in list and project views |
| Cross-project ticket capture | High | File a bug in any project without leaving the current one |
| `/pl-board` morning view | Medium | All projects with state, last-updated, and one-line "what's next" |
| Context jump (branch + active ticket) | Medium | `/pl-claude` opens right branch and surfaces active ticket |

### Full Vision (Designed, Not Yet Built)

| Feature | Description |
|---------|-------------|
| 23 sub-states | Full A1–G3 sub-state model with gate enforcement |
| Swim lanes | Internal vs. Customer classification; drives gate strictness |
| Approval governance | Cost/Risk/Impact assessment; Lightweight vs. Formal track |
| Approval matrix | Per-discipline sign-off routing (Eng, Security, QA, UI/UX, DevOps, Product, etc.) |
| `spec-governance` integration | C3 gate invokes spec-governance agent; auto-populates sign-off table |
| Chutes and ladders | Any backward move preserves history and flags re-confirmation needs |
| Agent envelope | Structured briefing with goal ancestry, frozen history, skills, and DoD for dispatching agents from a card |
| Four context pillars | Claude, GitHub Issues, GitHub repo, Production — activating progressively as projects mature |
| Bidirectional sync | Issue state changes flow back to registry; registry state changes push to GitHub |
| Visual board UI | 7-column kanban with filters, card detail views, full CRUD |

---

## 10. Data Model Summary

### Fields by Lifecycle Phase

| Field | Set at | Used by |
|-------|--------|---------|
| `name`, `slug`, `description` | Create | All display skills |
| `state` | Create / update | `/pl-list-projects`, `/pl-project` |
| `githubRepo` | Create (optional) | `/pl-project`, `/pl-create-ticket` |
| `subDirectory` | Create (optional) | `/pl-project` |
| `localDirectory` | Create (optional) | `/pl-claude`, `/pl-cursor` |
| `updateNotes` | Create / edit | `/pl-project` |
| `swimLane` | Future | Future governance skills |

---

## 11. Open Questions

1. **Named approvers vs. disciplines** — The Approval Matrix defines which disciplines sign off, but not specific individuals. How should named approvers be configured per project?

2. **Long-lead urgency signals** — Vendor security reviews and DevSecOps requests take weeks. Flag on the card, a sub-state, or a separate workflow?

3. **AI/ML governance path** — No dedicated AI capability review section. First-class discipline or checklist item within an existing discipline?

4. **Data classification tiers** — Public / Internal / Confidential / Restricted not yet modeled. Required for Formal governance track?

5. **Demo environment modeling** — No mechanism to track staging environments per card. In scope?

---

## 12. File Map

```text
punch-list/
├── README.md                    # Quick start, overview, architecture diagram
├── install-skills.sh            # Symlink installer
├── assets/
│   └── architecture.drawio      # Technical architecture diagram
├── docs/
│   └── spec.md                  # This file
└── skills/
    ├── pl-init/SKILL.md
    ├── pl-create-project/SKILL.md
    ├── pl-list-projects/SKILL.md
    ├── pl-project/SKILL.md
    ├── pl-create-ticket/SKILL.md
    ├── pl-claude/SKILL.md
    └── pl-cursor/SKILL.md
```

---

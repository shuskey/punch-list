---
name: pl-list-projects
description: "Use when the user wants to list projects, see their Punch List board, view project status, or check what projects are being tracked."
---

# PL List Projects — Display the Project Registry

Show all tracked projects in the current Punch List with their state and status indicators.

## Gate Check

Run:
```bash
python punchlist.py config show --json
```

If it exits non-zero or `state.json` does not exist, tell the user:
> Punch List is not initialized yet. Run `/pl-init` first.

Then stop.

## Load Data

Run:
```bash
python punchlist.py project list --json
```

Parse the JSON output. Key fields per project entry:
- `slug`, `name`, `state` — identity
- `isCurrent` — true for the current project (show 👉)
- `configMissing` — true if config.json was missing (show `[!]`)
- `checklistSummary` — `{ listCount, completedItems, totalItems }`
- `githubRepo`, `githubVisibility` — for GitHub column
- `localDirectory` — for Local column
- `nextStep` — shown as indented `→` line if set

Top-level fields: `listName`, `currentProject`.

## Display the Board

**Header**: When there are multiple punch lists (check via `python punchlist.py list show --json`), prefix with list name:
```
Punch List: <listName> — <count> projects
```
Otherwise:
```
Punch List — <count> projects
```

Group by state if 5 or more projects. Show column headers right-aligned over last three columns:

```
Punch List: Home Projects — 10 projects     Checklists  GitHub    Local

[A] Ideation
👉 Home Remodel                              1 checklist  no         no
   Tune Upgrade                                           no         no

[D] Delivering
   Punch List                                             🌐        yes
    → ** Push code to Repo
```

**Column details**:
- **Name**: prefix with `👉 ` if `isCurrent`, otherwise `   `. Append `[!]` if `configMissing`.
- **Checklists**: `N checklist` / `N checklists` if `checklistSummary.listCount > 0`, else blank.
- **GitHub**:
  - `githubVisibility === "public"` → `🌐`
  - `githubVisibility === "private"` → `🔒`
  - `githubRepo` set, visibility null → `yes`
  - no repo → `no`
- **Local**: `yes` if `localDirectory` set, else `no`
- **Next Step**: indented `→ <nextStep>` line below the project row if set.

## State Labels Reference

| State | Label |
|-------|-------|
| A | Ideation |
| B | Defining |
| C | Proving |
| D | Delivering |
| E | Evolving |
| F | Sustaining |
| G | Sunsetting |

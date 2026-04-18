---
name: pl-project
description: "Use when the user wants to view details of a specific Punch List project. Invoke with a project name or slug (e.g., /pl-project punch-list)."
---

# PL Project — Show Project Detail Card

Display the full detail card for a single tracked project, including open GitHub issues.

## Resolve the Project

If an argument was provided, find the matching slug from:
```bash
python ~/.punch-list/punchlist.py project list --json
```
Match against `slug` (exact) or `name` (case-insensitive, partial). If no match, show available projects and stop.

If no argument, use the current project (the CLI will default to it automatically).

## Load and Set Current

Run:
```bash
python ~/.punch-list/punchlist.py project show <slug> --set-current --json
```

This returns the full config plus `checklistSummary` array, and records the project as current in the registry.

## Fetch GitHub Issues (if repo is set)

If `githubRepo` is set in the response, extract `owner/repo` and run:
```bash
gh issue list --repo "<owner/repo>" --state open --json number,title,labels,state --limit 50
```

## Display Detail Card

```
  Name:      <name>
  Slug:      <slug>
  State:     [<letter>] <label>
  GitHub:    <githubRepo or "—">
  SubDir:    <subDirectory or "—">
  Local Dir: <localDirectory or "—">
```

### Next Step
```
Next Step:
  <nextStep or "(none — ...)">
```

### Update Notes
```
Update Notes:
  <updateNotes or "(none — ...)">
```

### Checklists

If `checklistSummary` has entries with items, display each. Prefix current checklist (`isCurrent: true`) with `👉 `:
```
Checklists:
👉 Home Remodel Tasks      2 items (0 done)   ← current
   Stuff We Can Do         1 item
  (use /pl-checklist <slug> to manage)
```

If no checklists with items, show nothing.

### Open Issues

If `githubRepo` set, display issues from `gh` output grouped by first label. If no repo, display:
```
Open Issues:
  No GitHub repo configured for this project.
```

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

---
name: pl-project
description: "Use when the user wants to view details of a specific Punch List project. Invoke with a project name or slug (e.g., /pl-project punch-list)."
---

# PL Project — Show Project Detail Card

Display the full detail card for a single tracked project, including open GitHub issues.

## Gate Check

Read `~/.punch-list/registry.json`. If it does not exist, tell the user:

> Punch List is not initialized yet. Run `/pl-init` first.

Then stop.

## Resolve the Project

The user provides a project name or slug as the argument (e.g., `/pl-project punch-list` or `/pl-project My Cool Project`).

Search the `projects` array in the registry for a match:
- Compare the argument against each project's `slug` (exact, case-insensitive)
- Also compare against each project's `name` (case-insensitive, partial match acceptable)

If no match is found, display:

> No project found matching "<argument>".
>
> Available projects:
> - <slug> — <name>
> - ...

Then stop.

## Load Config

Read `~/.punch-list/projects/<slug>/config.json`.

If the file is missing or invalid JSON, display:

> Project "<name>" found in registry but config is missing or corrupt.
> Expected: `~/.punch-list/projects/<slug>/config.json`

Then stop.

## Fetch GitHub Issues (if repo is set)

If `githubRepo` is set in the config, extract the `owner/repo` from the URL and run:

```bash
gh issue list --repo "<owner/repo>" --state open --json number,title,labels,state --limit 50
```

Parse the JSON output to list open issues grouped by label type.

If `githubRepo` is not set, skip this step and note it in the display.

## Display Detail Card

```
  Name:      <name>
  Slug:      <slug>
  State:     [<letter>] <label>
  GitHub:    <githubRepo or "—">
  SubDir:    <subDirectory or "—">
  Local Dir: <localDirectory or "—">
  Config:    ~/.punch-list/projects/<slug>/config.json
```

### Update Notes

Display the `updateNotes` field prominently after the core card, under its own heading:

```
Update Notes:
  <updateNotes text>
```

If `updateNotes` is null or empty, display:

```
Update Notes:
  (none — use option below to add notes about where you left off and what's next)
```

### Open Issues

If `githubRepo` is set, display all open issues from the `gh issue list` output:

```
Open Issues: (<count>)
  #<number>  [<label>]  <title>
  #<number>  [<label>]  <title>
```

Group by the first label on each issue if labels are present. If an issue has no labels, show it under `(unlabeled)`.

If there are no open issues, display:

```
Open Issues:
  (none — all issues are closed or no issues exist)
```

If `githubRepo` is not set, display:

```
Open Issues:
  No GitHub repo configured for this project.
```

## Offer to Update Notes

After displaying the full card, always ask:

> Would you like to update the notes for **<name>**?
> - **Yes** — write new notes
> - **No** — done

If the user chooses **Yes**, ask:

> Enter your update notes (what you just did, what's coming up next):

Accept their free-form text. Then update `~/.punch-list/projects/<slug>/config.json`:
- Set `updateNotes` to the entered text
- Set `updatedAt` to today's date (YYYY-MM-DD)

Write the updated config back using the Write tool. Confirm with:

> Notes saved for **<name>**.

If the user chooses **No**, simply end.

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

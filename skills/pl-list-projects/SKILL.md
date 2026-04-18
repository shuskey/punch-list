---
name: pl-list-projects
description: "Use when the user wants to list projects, see their Punch List board, view project status, or check what projects are being tracked."
---

# PL List Projects — Display the Project Registry

Show all tracked projects in the current Punch List with their state and status indicators.

## Gate Check & Migration

Read `~/.punch-list/state.json`.

**If it exists**: parse it, set `currentList` from the `currentList` field. All paths resolve under `~/.punch-list/lists/<currentList>/`. Proceed.

**If it does not exist**: check for old single-list layout by reading `~/.punch-list/registry.json`.

- **Old layout found**: perform one-time migration:
  1. Run:
     ```bash
     mkdir -p ~/.punch-list/lists/default
     cp ~/.punch-list/registry.json ~/.punch-list/lists/default/registry.json
     cp -r ~/.punch-list/projects ~/.punch-list/lists/default/projects
     ```
  2. Write `~/.punch-list/state.json`:
     ```json
     {
       "version": "1.0",
       "currentList": "default",
       "lists": [{ "slug": "default", "name": null, "createdAt": "<today YYYY-MM-DD>" }]
     }
     ```
  3. Inform the user:
     > Migrated Punch List to multi-list layout. Your existing projects are in the **default** list. Use `/pl-lists` to rename it or add more lists.
  4. Set `currentList` = `"default"` and continue.

- **Neither exists**: tell the user:
  > Punch List is not initialized yet. Run `/pl-init` first.
  
  Then stop.

## Behavior

### 1. Read the registry

Read `~/.punch-list/lists/<currentList>/registry.json` and parse the `projects` array and `currentProject` field.

If the array is empty, display:

> **Punch List** — 0 projects
>
> No projects yet. Use `/pl-create-project` to add one.

Then stop.

**Resolve current project**: If `currentProject` is set in the registry, use that slug. If not set or the slug doesn't match any project, default to the first project in the array. Do not write back to the registry at display time — only update `currentProject` when the user explicitly changes it (e.g., via `/pl-project`).

### 2. Load each project's config and checklists

For each entry in `projects`, read `~/.punch-list/lists/<currentList>/projects/<slug>/config.json`.

If a config file is missing or contains invalid JSON, show that project with a warning indicator:

```text
  <name>                   [?] Config missing            no   no
```

Also attempt to read `~/.punch-list/lists/<currentList>/projects/<slug>/checklists.json`. If it exists, count the total number of items across all lists (items arrays). If the file is missing or all lists are empty, the checklist count is 0.

### 3. Display the board

**Header**: When `state.lists.length > 1`, prefix the header with the current list name:

```text
Punch List: <listName> — <count> projects
```

When there is only one list:

```text
Punch List — <count> projects
```

Format output as a table:

```text
Punch List — <count> projects

  <Name padded>             [<state>] <label padded>    Checklists  GitHub  Local
    → <nextStep>
  <Name padded>             [<state>] <label padded>    Checklists  GitHub  Local
```

**Column details**:

- **Name**: Project name, left-aligned (from registry). Prefix with `👉 ` if this is the current project (slug matches `currentProject`).
- **State**: `[A]` through `[G]` with label — read from the registry entry (Ideation, Defining, Proving, Delivering, Evolving, Sustaining, Sunsetting)
- **Checklists**: Show `N checklist` / `N checklists` (counting lists with at least 1 item) only if N > 0. If zero, leave the column blank.
- **GitHub**: Determined by `githubRepo` and `githubVisibility` fields in the config:
  - `githubRepo` is null or not set → `no`
  - `githubRepo` is set and `githubVisibility` is `"public"` → `🌐`
  - `githubRepo` is set and `githubVisibility` is `"private"` → `🔒`
  - `githubRepo` is set and `githubVisibility` is null → `yes`
- **Local**: Show `yes` if `localDirectory` is set in the config, otherwise `no`
- **Next Step**: If `nextStep` is set (non-null) in the config, show it on a second indented line directly below the project row, prefixed with `→ `. If `nextStep` is null or not set, show nothing (no extra line).

### 4. Group by state (optional enhancement)

If there are 5 or more projects, group them by state with headers. Always show a column header line at the top right-aligned over the last three columns:

```
Punch List: Hobby & Photo Room — 6 projects     Checklists  GitHub    Local

[A] Ideation
👉 My Cool Project                               1 checklist  🌐         yes
    → ** Design the data model first
  Another Idea                                               no         no

[B] Defining
  Secret Sauce                                               yes        no

[D] Delivering
  Production Widget                               2 checklists 🔒         yes
    → 1 Ship the auth PR
  API Revamp                                                 yes        yes
  Docs Refresh                                               no         yes
```

For fewer than 5 projects, use the flat list format with the same column header line.

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

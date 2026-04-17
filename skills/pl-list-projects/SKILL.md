---
name: pl-list-projects
description: "Use when the user wants to list projects, see their Punch List board, view project status, or check what projects are being tracked."
---

# PL List Projects — Display the Project Registry

Show all tracked projects with their state and status indicators.

## Gate Check

First, try to read `~/.punch-list/registry.json`. If it does not exist, tell the user:

> Punch List is not initialized yet. Run `/pl-init` first.

Then stop.

## Behavior

### 1. Read the registry

Read `~/.punch-list/registry.json` and parse the `projects` array.

If the array is empty, display:

> **Punch List** — 0 projects
>
> No projects yet. Use `/pl-create-project` to add one.

Then stop.

### 2. Load each project's config

The registry contains `slug`, `name`, `state`, and `description` for fast listing. For the **GitHub** and **Local** columns, you must also read each project's config.

For each entry in `projects`, read `~/.punch-list/projects/<slug>/config.json`.

If a config file is missing or contains invalid JSON, show that project with a warning indicator instead of skipping it, using `state` from the registry entry:

```text
  <name>                   [?] Config missing     no   no
```

### 3. Display the board

Format output as a table:

```text
Punch List — <count> projects

  <Name padded>             [<state>] <label padded>    GitHub  Local
  <Name padded>             [<state>] <label padded>    GitHub  Local
```

**Column details**:

- **Name**: Project name, left-aligned (from registry)
- **State**: `[A]` through `[G]` with label — read from the registry entry (Ideation, Defining, Proving, Delivering, Evolving, Sustaining, Sunsetting)
- **GitHub**: Show `yes` if `githubRepo` is set in the config, otherwise `no`
- **Local**: Show `yes` if `localDirectory` is set in the config, otherwise `no`

### 4. Group by state (optional enhancement)

If there are 5 or more projects, group them by state with headers. Always show a column header line at the top right-aligned over the last two columns:

```
Punch List — 6 projects                          GH Repo  Local

[A] Ideation
  My Cool Project                                  yes     yes
  Another Idea                                     no      no

[B] Defining
  Secret Sauce                                     no      no

[D] Delivering
  Production Widget                                yes     yes
  API Revamp                                       yes     yes
  Docs Refresh                                     no      yes
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

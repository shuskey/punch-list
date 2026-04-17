---
name: pl-init
description: "Initialize Punch List and create the project registry. Automatically seeded with the Punch List project so you can immediately start using all features."
---

# PL Init — Initialize the Punch List Virtual Project Registry

Set up the `~/.punch-list/` directory structure and registry file. The registry is automatically seeded with one project: **Punch List itself**, so you can immediately list projects, view details, and add GitHub issues — no waiting for first setup.

## Behavior

This skill is **idempotent** — safe to run multiple times.

### Step 1: Check if already initialized

Read `~/.punch-list/registry.json` using the Read tool.

- **If it exists and contains valid JSON with a `projects` array**: Report that Punch List is already initialized. Show the project count (e.g., "Punch List is already set up with 3 projects tracked."). Done.
- **If it does not exist or is invalid**: Proceed to Step 2.

### Step 2: Create directory structure

Run these commands using Bash:

```bash
mkdir -p ~/.punch-list/projects
```

### Step 3: Create the registry file with the Punch List project

The registry is a lightweight index only — no operational fields. Use the Write tool to create `~/.punch-list/registry.json` with this content:

```json
{
  "version": "1.0",
  "createdAt": "<today's date in YYYY-MM-DD format>",
  "projects": [
    {
      "slug": "punch-list",
      "name": "Punch List",
      "state": "D",
      "description": "Agentic workflow coordination that implements a human-as-general-contractor model."
    }
  ]
}
```

### Step 4: Create the Punch List project config file

The config is the source of truth for all project details. Use the Write tool to create `~/.punch-list/projects/punch-list/config.json` with this content:

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
  "createdAt": "<today's date in YYYY-MM-DD format>",
  "updatedAt": "<today's date in YYYY-MM-DD format>"
}
```

### Step 5: Confirm success

Tell the user:

> Punch List initialized at `~/.punch-list/`
>
> - Registry: `~/.punch-list/registry.json`
> - Projects directory: `~/.punch-list/projects/`
>
> Your first project is ready: **Punch List** itself (state D). You can immediately:
> - Use `/pl-list-projects` to see all projects
> - Use `/pl-project punch-list` to view this project's details
> - Use `/pl-create-ticket` to add GitHub issues
>
> Use `/pl-create-project` to add more projects.

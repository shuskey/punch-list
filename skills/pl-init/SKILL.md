---
name: pl-init
description: "Initialize Punch List and create the project registry. Automatically seeded with the Punch List project so you can immediately start using all features."
---

# PL Init — Initialize the Punch List Virtual Project Registry

Set up the `~/.punch-list/` directory structure, state file, and default list. The default list is seeded with one project: **Punch List itself**.

## Behavior

This skill is **idempotent** — safe to run multiple times.

### Step 1: Check if already initialized

Read `~/.punch-list/state.json`.

- **If it exists and contains valid JSON with a `currentList` field**: Report that Punch List is already initialized. Show the list count and current list name (e.g., "Punch List is already set up with 2 lists, currently on **Hobby**."). Done.
- **If it does not exist**: proceed to Step 2.

### Step 2: Migration check (old single-list layout)

Read `~/.punch-list/registry.json`.

**If it exists** (old layout): perform one-time migration:

1. Run:
   ```bash
   mkdir -p ~/.punch-list/lists/default
   cp ~/.punch-list/registry.json ~/.punch-list/lists/default/registry.json
   cp -r ~/.punch-list/projects ~/.punch-list/lists/default/projects
   ```
2. Write `~/.punch-list/state.json` using the Write tool:
   ```json
   {
     "version": "1.0",
     "currentList": "default",
     "lists": [
       { "slug": "default", "name": null, "createdAt": "<today YYYY-MM-DD>" }
     ]
   }
   ```
3. Tell the user:
   > Migrated Punch List to multi-list layout. Your existing projects are now in the **default** list (unnamed). Use `/pl-lists` to rename it or add more lists.

Done — do not proceed to fresh init.

**If it does not exist**: proceed to Step 3 (fresh init).

### Step 3: Create directory structure

```bash
mkdir -p ~/.punch-list/lists/default/projects/punch-list
```

### Step 4: Write state.json

Use the Write tool to create `~/.punch-list/state.json`:

```json
{
  "version": "1.0",
  "currentList": "default",
  "lists": [
    { "slug": "default", "name": null, "createdAt": "<today YYYY-MM-DD>" }
  ]
}
```

### Step 5: Write the default list registry

Use the Write tool to create `~/.punch-list/lists/default/registry.json`:

```json
{
  "version": "1.0",
  "createdAt": "<today YYYY-MM-DD>",
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

### Step 6: Write the Punch List project config

Use the Write tool to create `~/.punch-list/lists/default/projects/punch-list/config.json`:

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
  "createdAt": "<today YYYY-MM-DD>",
  "updatedAt": "<today YYYY-MM-DD>"
}
```

### Step 7: Confirm success

Tell the user:

> Punch List initialized at `~/.punch-list/`
>
> - State:         `~/.punch-list/state.json`
> - Default list:  `~/.punch-list/lists/default/`
>
> Your first project is ready: **Punch List** itself (state D). You can immediately:
> - Use `/pl-list-projects` to see all projects
> - Use `/pl-project punch-list` to view this project's details
> - Use `/pl-create-ticket` to add GitHub issues
> - Use `/pl-lists` to rename your list or add more lists
>
> Use `/pl-create-project` to add more projects.

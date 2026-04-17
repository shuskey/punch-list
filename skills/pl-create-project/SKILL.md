---
name: pl-create-project
description: "Use when the user wants to create a new project card, add a project to Punch List, or register a new project in their project registry."
---

# PL Create Project — Add a New Project to the Registry

Interactive project card creation. Walk the user through each field, write the config, and update the registry.

## Gate Check

First, try to read `~/.punch-list/registry.json`. If it does not exist, tell the user:

> Punch List is not initialized yet. Run `/pl-init` first.

Then stop. Do not proceed.

## Interactive Flow

Ask questions **one at a time** using AskUserQuestion. Do not batch questions.

### 1. Project Name (required)

Ask:
> What's the name of your project?

From the name, generate a slug: lowercase, replace spaces/special chars with hyphens, remove consecutive hyphens, trim leading/trailing hyphens. Examples:
- "My Cool Project" → `my-cool-project`
- "AI-Powered Widget 2.0!" → `ai-powered-widget-20`

Check the slug against the `projects` array in `~/.punch-list/registry.json`. If a project with that slug already exists, append `-2` (or `-3`, etc.) and inform the user of the adjusted slug.

### 2. Creative Description

Generate 1 creative, slightly whimsical description (1-2 sentences) based on the project name. Present it and ask:

> Here's a description for **<name>**:
>
> *"<generated description>"*
>
> - **Accept** this description
> - **Another** — generate a different one
> - **Custom** — write your own

If they choose "Another", generate a fresh description and present the same options again. If they choose "Custom", ask them to type their description.

### 3. GitHub Repo URL (optional)

Ask:
> GitHub repo URL? (e.g., https://github.com/org/repo) — or press Enter to skip.

This is the primary project identifier — GitHub issues on this repo are the project's tickets.

### 4. Subdirectory (optional)

Only ask this if a GitHub repo URL was provided. Ask:
> Does this project live in a subdirectory of the repo? (e.g., `my-tool`) — or press Enter to skip.

This subfolder applies equally to both the GitHub repo path and the local directory when searching for files. Store as `subDirectory`. Leave null if skipped.

### 5. Local Working Directory (optional)

Ask:
> Local working directory path? — or press Enter to skip.

If they skip, mention:
> No local directory set. You can always update this later.

Do NOT auto-create a workspace directory — just leave it as null.

### 6. Initial State

The default state is `"A"` (Ideation). Ask:

> Initial state? Default is **[A] Ideation**. Options:
>
> - **A** — Ideation
> - **B** — Defining
> - **C** — Proving
> - **D** — Delivering
> - **E** — Evolving
> - **F** — Sustaining
> - **G** — Sunsetting

Accept A through G (case-insensitive). Default to A if they just press Enter.

## Write the Project

### Create config.json

Create the directory and config file:

```bash
mkdir -p ~/.punch-list/projects/<slug>
```

Use the Write tool to create `~/.punch-list/projects/<slug>/config.json`:

```json
{
  "name": "<project name>",
  "slug": "<slug>",
  "description": "<chosen description>",
  "state": "<state letter>",
  "swimLane": null,
  "githubRepo": "<repo URL or null>",
  "subDirectory": "<subfolder name or null>",
  "localDirectory": "<path or null>",
  "updateNotes": null,
  "createdAt": "<today YYYY-MM-DD>",
  "updatedAt": "<today YYYY-MM-DD>"
}
```

Use `null` (not `"null"`) for any fields that were skipped.

### Update registry.json

The registry is a lightweight index only — no operational fields. Read the current `~/.punch-list/registry.json`, parse the JSON, append this entry to the `projects` array:

```json
{
  "slug": "<slug>",
  "name": "<project name>",
  "state": "<state letter>",
  "description": "<chosen description>"
}
```

Write the updated registry back using the Write tool.

## Display Summary

After writing both files, display a summary card:

```
Project created!

  Name:        <name>
  Slug:        <slug>
  Description: <description>
  State:       [<letter>] <label>
  GitHub:      <url or "—">
  SubDir:      <subfolder or "—">
  Local Dir:   <path or "—">
  Notes:       (none yet — use /pl-project <slug> to add update notes)
  Config:      ~/.punch-list/projects/<slug>/config.json
```

## State Labels Reference

Use these labels when displaying states:

| State | Label |
|-------|-------|
| A | Ideation |
| B | Defining |
| C | Proving |
| D | Delivering |
| E | Evolving |
| F | Sustaining |
| G | Sunsetting |

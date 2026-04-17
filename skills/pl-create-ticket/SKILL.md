---
name: pl-create-ticket
description: "Use when the user wants to create a GitHub issue under a Punch List project. Invoke with an optional project slug or name (e.g., /pl-create-ticket my-project)."
---

# PL Create Ticket — Create a GitHub Issue for a PL Project

Creates a GitHub issue on the repo associated with a Punch List project.

## Gate Check

Read `~/.punch-list/registry.json`. If it does not exist, tell the user:

> Punch List is not initialized yet. Run `/pl-init` first.

Then stop.

## Interactive Flow

Ask questions **one at a time** using AskUserQuestion.

### 1. Select PL Project

Read `~/.punch-list/registry.json` and present the list of projects that have a `githubRepo` set in their config. Load each project's `~/.punch-list/projects/<slug>/config.json` to check.

If no projects have a GitHub repo, tell the user:

> None of your Punch List projects have a GitHub repo set. Add one via `/pl-project` first.

Then stop.

Present the eligible projects as options. If the user invoked the skill with a project slug or name argument, pre-select it and skip this question.

### 2. Issue Type

Ask:

> What type of issue?
> - **Bug** — something broken (applies `bug` label)
> - **Feature** — new capability (applies `enhancement` label)
> - **Task** — work item (applies `task` label)
> - **Story** — user story (applies `story` label)

### 3. Title

Ask:
> Title for this issue?

### 4. Body (optional)

Ask:
> Add a description/body? (or press Enter to skip)

If skipped, leave body empty.

## Derive Repo Reference

From the project's `githubRepo` URL (e.g., `https://github.com/org/repo`), extract the `owner/repo` portion for use with `gh` commands.

If `subDirectory` is set in the project config, note it in the issue body if provided, but it does not affect the repo reference.

## Create the Issue

Use the Bash tool to run:

```bash
gh issue create \
  --repo "<owner/repo>" \
  --title "<title>" \
  --label "<label>" \
  --body "<body or empty string>"
```

**Label mapping:**

| Type    | Label        |
|---------|--------------|
| Bug     | `bug`        |
| Feature | `enhancement`|
| Task    | `task`       |
| Story   | `story`      |

If the label does not exist on the repo, `gh` will prompt to create it. In that case, proceed — let `gh` handle the label creation interactively, or omit `--label` and note to the user that the label may need to be created manually.

Capture the output of `gh issue create` — it returns the issue URL on success.

## Display Summary

```
Issue created!

  Number:  #<number>
  Type:    <type>
  Label:   <label>
  Title:   <title>
  Repo:    <githubRepo>
  Status:  Open
  URL:     <url from gh output>
```

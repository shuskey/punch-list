---
name: pl-cursor
description: "Use when the user wants to open a Punch List project in Cursor. Invoke with a project name or slug (e.g., /pl-cursor punch-list)."
---

# PL Cursor — Launch Cursor for a Project

Open the local directory for a Punch List project in Cursor.

## Gate Check

Read `~/.punch-list/registry.json`. If it does not exist, tell the user:

> Punch List is not initialized yet. Run `/pl-init` first.

Then stop.

## Resolve the Project

The user provides a project name or slug as the argument.

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

## Compute Effective Path

- If `localDirectory` is null or not set, display:

  > No local directory configured for this project.

  Then stop.

- If `subDirectory` is set: effective path = `<localDirectory>/<subDirectory>`
- Otherwise: effective path = `<localDirectory>`

## Detect OS

Run:

```bash
uname -s
```

Use the output to determine the platform:
- `Darwin` → macOS
- `Linux` → Linux
- `MINGW*`, `MSYS*`, or `CYGWIN*` → Windows (Git Bash / MSYS2)

## Launch Cursor

The `cursor` CLI is cross-platform and handles opening or reusing a window on all platforms. Run it first regardless of OS:

```bash
cursor --reuse-window "<effective-path>"
```

`--reuse-window` reuses an existing Cursor window if one is open for that path, or opens a new one.

### Bring Cursor to front (OS-specific)

**macOS** — the `cursor` CLI does not always raise the window, so activate via AppleScript:

```bash
osascript -e 'tell application "Cursor" to activate'
```

**Linux** — no additional step needed; the `cursor` CLI raises the window.

**Windows** — no additional step needed; the `cursor` CLI raises the window.

## Report Result

> Opened `<effective-path>` in Cursor.

Report any errors from the bash commands to the user.

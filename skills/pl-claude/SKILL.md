---
name: pl-claude
description: "Use when the user wants to open a Punch List project in Claude Code. Invoke with a project name or slug (e.g., /pl-claude punch-list)."
---

# PL Claude — Launch Claude Code for a Project

Open a new terminal session running Claude Code at the local directory for a Punch List project.

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

## Resolve the Project

The user provides a project name or slug as the argument.

Search the `projects` array in `~/.punch-list/lists/<currentList>/registry.json` for a match:
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

Read `~/.punch-list/lists/<currentList>/projects/<slug>/config.json`.

If the file is missing or invalid JSON, display:

> Project "<name>" found in registry but config is missing or corrupt.
> Expected: `~/.punch-list/lists/<currentList>/projects/<slug>/config.json`

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

## Detect Existing Session

**macOS / Linux:**

```bash
lsof -a -c "claude" -d cwd -n 2>/dev/null | grep "<effective-path>"
```

If a match is found, inform the user:

> Claude Code is already running at `<effective-path>`.

Then use AskUserQuestion to offer:
1. Launch another instance anyway
2. Cancel

If cancelled, stop.

**Windows:**

`lsof` is not available. Run a best-effort check:

```bash
tasklist 2>/dev/null | grep -i "claude"
```

If claude appears to be running, inform the user:

> Claude Code appears to be running (cannot verify directory on Windows).

Then use AskUserQuestion to offer:
1. Launch anyway
2. Cancel

If cancelled, stop.

## Launch Claude Code

### macOS

```bash
osascript -e 'tell application "Terminal"
  activate
  do script "cd <effective-path> && claude"
end tell'
```

`activate` brings Terminal to the foreground first to avoid AppleEvent error -10000.

### Linux

Try terminal emulators in order:

```bash
if command -v gnome-terminal &>/dev/null; then
  gnome-terminal -- bash -c "cd '<effective-path>' && claude; exec bash" &
elif command -v xterm &>/dev/null; then
  xterm -e "cd '<effective-path>' && claude" &
else
  echo "No supported terminal emulator found (tried gnome-terminal, xterm)."
fi
```

### Windows

Convert the path to Windows format first (Git Bash paths use forward slashes):

```bash
win_path="$(cygpath -w "<effective-path>" 2>/dev/null || echo "<effective-path>")"
```

Then launch using Windows Terminal (`wt`) if available, otherwise fall back to `cmd.exe`:

```bash
if cmd.exe /c where wt &>/dev/null 2>&1; then
  cmd.exe /c start wt -d "$win_path" bash -c "claude"
else
  cmd.exe /c start "" cmd.exe /k "cd /d \"$win_path\" && claude"
fi
```

## Report Result

> Launched Claude Code at `<effective-path>`.

Report any errors from the bash commands to the user.

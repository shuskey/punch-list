---
name: pl-lists
description: "Use when the user wants to manage Punch Lists — create, switch, rename, or delete lists. Invoke with an optional sub-command and argument: switch, create [name], rename <slug>, delete <slug>."
---

# PL Lists — Manage Punch Lists

Manage multiple Punch Lists: create new ones, switch the active list, rename, or delete.

## Gate Check

Run:
```bash
python ~/.punch-list/punchlist.py list show --json
```

If it exits non-zero, tell the user:
> Punch List is not initialized yet. Run `/pl-init` first.

Then stop.

## Always Display Lists First

Parse JSON output. Display with 👉 on the current list (`isCurrent: true`). Do **not** show slugs:

```
Punch Lists — <count> lists

👉 <name or "(unnamed)">   (<N> projects)    ← current
   <name or "(unnamed)">   (<N> projects)
```

## Dispatch

- `switch` → **Switch** action
- `create [name]` → **Create** action
- `rename <slug>` → **Rename** action
- `delete <slug>` → **Delete** action
- no argument → **Main Menu**

## Main Menu

Use AskUserQuestion:
> What would you like to do?
> - **Switch** — change the active list
> - **Create** — add a new list
> - **Rename** — rename a list
> - **Delete** — remove a list

---

## Switch Action

If only one list exists, tell the user and stop.

Present all lists with AskUserQuestion (👉 on current). On selection:

```bash
python ~/.punch-list/punchlist.py config set-list <slug>
```

Confirm: `Switched to **<name>**. All Punch List commands now operate on this list.`

---

## Create Action

If name not supplied as argument, ask: `Name for the new Punch List?`

Generate slug: lowercase, spaces/special chars → hyphens, no consecutive hyphens, trim edges. If slug collides with existing, append `-2`, `-3`, etc.

If only one list exists and it has `name: null`, ask the user to name it first:
> Your current list is unnamed. Give it a name before adding a second list.

```bash
python ~/.punch-list/punchlist.py list rename <current-slug> "<new-name>"
```

Then create:
```bash
python ~/.punch-list/punchlist.py list create <slug> "<name>"
```

Offer to switch:
> **<name>** created (0 projects). Switch to it now?

If yes:
```bash
python ~/.punch-list/punchlist.py config set-list <slug>
```

Confirm: `Created **<name>** (\`<slug>\`). <Now active. | Current list unchanged — still on **<name>**.>`

---

## Rename Action

If no slug supplied, ask which list via AskUserQuestion.

Ask: `New name for **<name>**?`

```bash
python ~/.punch-list/punchlist.py list rename <slug> "<new-name>"
```

Confirm: `Renamed to **<new name>**. Slug \`<slug>\` is unchanged.`

---

## Delete Action

If no slug supplied, ask which list via AskUserQuestion.

If only one list, refuse and stop.

Check project count from `list show --json`. If > 0:
> **<name>** contains <N> project(s). This will permanently delete the list and all its project configs.
> Type the list name exactly to confirm:

Use AskUserQuestion to collect input. If it doesn't match (case-insensitive), cancel and stop.

If the list being deleted is active, ask which list to switch to first:
```bash
python ~/.punch-list/punchlist.py config set-list <other-slug>
```

Then delete:
```bash
python ~/.punch-list/punchlist.py list delete <slug> --force
```

Confirm: `Deleted **<name>**. <Now active on **<new current>**.>`

---
name: pl-checklist
description: "Use when the user wants to view or manage checklists for a Punch List project — add items, mark complete, delete, reorder, or clear completed. Invoke with an optional project slug (e.g., /pl-checklist punch-list)."
---

# PL Checklist — Manage Project Checklists

Interactive checklist manager for a Punch List project.

## Resolve the Project

If invoked with a slug or name argument, resolve it:
```bash
python ~/.punch-list/punchlist.py project list --json
```
Match against `slug` (exact) or `name` (case-insensitive, partial). If no match, show available projects and stop.

If no argument, the CLI defaults to the current project automatically — pass no `--project-slug`.

Set `PROJECT_SLUG` to the resolved slug (or omit from CLI calls to use the default).

## Load Checklist Data

```bash
python ~/.punch-list/punchlist.py checklist lists --project-slug <slug> --json
```

Returns `{ projectSlug, currentList, lists: [{ id, name, totalItems, completedItems, isCurrent }] }`.

## Main Menu

If no lists exist (empty `lists` array), skip to **New List** flow.

Display all lists. Prefix current list (`isCurrent`) with `👉 `:

```
Checklists — <project name>

👉 [1] Home Remodel Tasks  (2 items)     ← current
       □ Bottom Out on Button. Budget.
       □ Engage with Mountain Home Remodelers

   [2] Stuff We Can Do Ourselves  (1 item)
       □ Update Master Bathroom Shower

──────────────────────────────
  [N] New list
  [Q] Quit
```

To show items, run:
```bash
python ~/.punch-list/punchlist.py checklist show <list-id> --project-slug <slug> --json
```

Items format:
- Incomplete: `□ <text>  ×<quantity>`
- Complete: `✓ <text>  (done)`

Ask:
> Select a list number to manage, [N] for new list, or [Q] to quit.

## Manage a List

Set this list as current:
```bash
python ~/.punch-list/punchlist.py checklist set-current <list-id> --project-slug <slug>
```

Show:
```
<list name> — <count> items

  [1] □ <text>
  [2] ✓ <text>  (done)

──────────────────────────────
  [A] Add item
  [C] Clear all completed
  [U] Up/Down — reorder an item
  [R] Rename this list
  [D] Delete this list
  [B] Back
```

Ask:
> Action? (item number to toggle/delete, or a letter)

### Toggle / Delete Item

If user enters an item number, ask:
> [1] Mark complete  [2] Delete item  [3] Cancel

**Mark complete** (toggle):
```bash
python ~/.punch-list/punchlist.py checklist toggle <item-id> --project-slug <slug>
```

**Delete item**:
```bash
python ~/.punch-list/punchlist.py checklist delete-item <item-id> --project-slug <slug>
```

### Add Item

Ask: `Item text?`  
Ask: `Quantity? (e.g., "2 lbs", "3") — or press Enter to skip.`

```bash
python ~/.punch-list/punchlist.py checklist add "<text>" [--quantity "<qty>"] --project-slug <slug> --list-id <list-id>
```

### Clear All Completed

Get completed items from:
```bash
python ~/.punch-list/punchlist.py checklist show <list-id> --project-slug <slug> --json
```

Count items where `completed: true`. Confirm:
> Clear <N> completed items? [Y/N]

If confirmed, call for each completed item:
```bash
python ~/.punch-list/punchlist.py checklist delete-item <item-id> --project-slug <slug>
```

### Reorder

Ask: `Which item number to move?`  
Ask: `[U] Move up  [D] Move down`

Convert to 1-based new position (up = current position - 1, down = current position + 1).

```bash
python ~/.punch-list/punchlist.py checklist reorder <item-id> <new-position> --list-id <list-id> --project-slug <slug>
```

### Rename List

Ask: `New name for this list?`

```bash
python ~/.punch-list/punchlist.py checklist rename-list <list-id> "<new-name>" --project-slug <slug>
```

### Delete List

Ask: `Delete "<name>" and all its items? [Y/N]`

If confirmed:
```bash
python ~/.punch-list/punchlist.py checklist delete-list <list-id> --force --project-slug <slug>
```

## New List Flow

Ask: `Name for the new list?`

```bash
python ~/.punch-list/punchlist.py checklist create-list "<name>" --set-current --project-slug <slug>
```

Then immediately enter **Manage a List** for the new list (re-fetch data first).

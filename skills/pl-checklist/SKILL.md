---
name: pl-checklist
description: "Use when the user wants to view or manage checklists for a Punch List project — add items, mark complete, delete, reorder, or clear completed. Invoke with an optional project slug (e.g., /pl-checklist punch-list)."
---

# PL Checklist — Manage Project Checklists

Interactive checklist manager for a Punch List project. Checklists are stored as local JSON files and only shown when they have items.

## Gate Check & Migration

Read `~/.punch-list/state.json`.

**If it exists**: parse it, set `currentList` from the `currentList` field. All paths resolve under `~/.punch-list/lists/<currentList>/`. Proceed.

**If it does not exist**: tell the user:
> Punch List is not initialized yet. Run `/pl-init` first.

Then stop.

## Data File

Checklists for a project live at:
```
~/.punch-list/lists/<currentList>/projects/<slug>/checklists.json
```

Schema:
```json
{
  "version": "1.0",
  "lists": [
    {
      "id": "<short-uuid>",
      "name": "My List",
      "createdAt": "YYYY-MM-DD",
      "items": [
        {
          "id": "<short-uuid>",
          "text": "Item text",
          "quantity": null,
          "completed": false,
          "order": 0
        }
      ]
    }
  ]
}
```

- `id`: 8-character hex string generated via `date +%s%N | md5sum | head -c 8` or similar
- `quantity`: optional string (e.g., `"2 lbs"`, `"3"`) — null if not set
- `order`: integer starting at 0, controls display order within the list

If `checklists.json` does not exist, treat it as `{ "version": "1.0", "lists": [] }`.

## Resolve the Project

If the skill was invoked with an argument (slug or name), resolve it against `~/.punch-list/lists/<currentList>/registry.json`. Match by slug (exact) or name (case-insensitive, partial).

If no argument, ask:
> Which project? (type slug or name)

If no match found, show available projects and stop.

## Main Menu

Display all checklists for the project. If none exist, skip to **New List** flow.

```
Checklists — <project name>

  [1] Costco Run  (3 items, 1 done)
      □ Milk  ×2 gallons
      □ Eggs
      ✓ Bread  (done)

  [2] Weekend Tasks  (2 items)
      □ Mow lawn
      □ Fix fence

──────────────────────────────
  [N] New list
  [Q] Quit
```

Display format per item:
- Incomplete: `□ <text>  ×<quantity>` (quantity omitted if null)
- Complete: `✓ <text>  (done)`

Ask:
> Select a list number to manage, [N] for new list, or [Q] to quit.

## Manage a List

When the user selects a list, show:

```
<list name> — <count> items

  [1] □ Milk  ×2 gallons
  [2] □ Eggs
  [3] ✓ Bread  (done)

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

### Toggle Complete

If the user enters an item number, ask:
> [1] Mark complete  [2] Delete item  [3] Cancel

- **Mark complete**: set `completed: true`. If already complete, set `completed: false` (toggle).
- **Delete item**: remove the item from the array, renumber `order` values.

### Add Item

Ask (one at a time):
> Item text?

Then:
> Quantity? (e.g., "2 lbs", "3") — or press Enter to skip.

Append to items array with `completed: false` and `order` = current max + 1.

### Clear All Completed

Remove all items where `completed: true`. Confirm first:
> Clear <N> completed items? [Y/N]

### Reorder

Ask:
> Which item number to move?

Then:
> [U] Move up  [D] Move down

Swap `order` values with the adjacent item. Re-display the list.

### Rename List

Ask:
> New name for this list?

Update `name` field.

### Delete List

Ask:
> Delete "<name>" and all its items? [Y/N]

If confirmed, remove the list from the array.

## New List Flow

Ask:
> Name for the new list? (e.g., "Costco Run", "Weekend Tasks")

Create a new list entry with a generated `id`, today's date, and empty `items` array. Then immediately enter **Manage a List** for it.

## Saving

After every mutating operation, write the full updated `checklists.json` back using the Write tool. Create the file if it doesn't exist.

## Display from pl-project

When `pl-project` loads a project, it should check for `checklists.json`. If it exists and has any list with items, show:

```
Checklists:
  Costco Run      3 items (1 done)
  Weekend Tasks   2 items
  (use /pl-checklist <slug> to manage)
```

If `checklists.json` is missing or all lists are empty, show nothing.

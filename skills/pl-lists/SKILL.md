---
name: pl-lists
description: "Use when the user wants to manage Punch Lists — create, switch, rename, or delete lists. Invoke with an optional sub-command and argument: switch, create [name], rename <slug>, delete <slug>."
---

# PL Lists — Manage Punch Lists

Manage multiple Punch Lists: create new ones, switch the active list, rename, or delete.

## Gate Check

Read `~/.punch-list/state.json`. If it does not exist, tell the user:

> Punch List is not initialized yet. Run `/pl-init` first.

Then stop.

Parse `state.json`. Extract `currentList` and `lists` array.

## Always display the list first

Before any action, read project counts and display all lists. For each entry in `state.lists`, read `~/.punch-list/lists/<slug>/registry.json` and count the `projects` array. If a registry is missing, show `?`.

Display with 👉 pointing to the current list. Do **not** show the slug:

```
Punch Lists — <count> lists

👉 <name or "(unnamed)">   (<N> projects)    ← current
   <name or "(unnamed)">   (<N> projects)
```

## Dispatch

Determine which action to take based on the argument:

- `/pl-lists switch` → run **Switch** action
- `/pl-lists create [name]` → run **Create** action (name is optional pre-supply)
- `/pl-lists rename <slug>` → run **Rename** action
- `/pl-lists delete <slug>` → run **Delete** action
- `/pl-lists` with no argument → show **Main Menu**

## Main Menu

Use AskUserQuestion to present:

> What would you like to do?
> - **Switch** — change the active list
> - **Create** — add a new list
> - **Rename** — rename a list
> - **Delete** — remove a list

Default-highlighted: **Switch**.

Route to the corresponding action below.

---

## Switch Action

If there is only one list, tell the user:

> You only have one Punch List. Use `/pl-lists create` to add another.

Then stop.

Before presenting the picker, read each list's `~/.punch-list/lists/<slug>/registry.json` and count the `projects` array (show `?` if missing).

Present all entries in `state.lists` using AskUserQuestion (arrow-key style), with the current list pre-selected:

> Select a Punch List to make active:
> - 👉 <name or "(unnamed)"> (<N> projects)   ← current
> - <name or "(unnamed)"> (<N> projects)
> ...

Do **not** show the slug. Use 👉 only on the currently active list.

On selection:
1. Update `currentList` to the chosen slug in `state.json`.
2. Write the updated `state.json`.
3. Confirm:
   > Switched to **<name or slug>**. All Punch List commands now operate on this list.

---

## Create Action

### Get the name

If a name was supplied as an argument, use it. Otherwise ask:

> Name for the new Punch List?

Generate a slug: lowercase, spaces/special chars → hyphens, no consecutive hyphens, trim leading/trailing hyphens. Check slug is unique in `state.lists`; if collision, append `-2`, `-3`, etc.

### Name the existing list first (if this is the 2nd list)

If `state.lists.length === 1` and that entry has `name: null`:

Ask:

> Your current list is unnamed. Give it a name before adding a second list.
> Name for the current list (`<slug>`)? [default: **Initial List**]

If the user presses Enter without typing, use `"Initial List"` as the name (slug: `initial-list`).

Accept input, update the existing entry's `name` in `state.lists`, and write `state.json` before continuing.

### Create the list

1. Run:
   ```bash
   mkdir -p ~/.punch-list/lists/<new-slug>/projects
   ```
2. Use the Write tool to create `~/.punch-list/lists/<new-slug>/registry.json`:
   ```json
   {
     "version": "1.0",
     "createdAt": "<today YYYY-MM-DD>",
     "projects": []
   }
   ```
3. Append to `state.lists`:
   ```json
   { "slug": "<slug>", "name": "<name>", "createdAt": "<today YYYY-MM-DD>" }
   ```
4. Write the updated `state.json`.

### Offer to switch

Ask:

> **<name>** created (0 projects). Switch to it now?
> - **Yes** — make it the active list
> - **No** — stay on current list

If Yes: update `currentList` in `state.json` and write it.

Confirm:
> Created **<name>** (`<slug>`). <"Now active." or "Current list unchanged — still on **<currentListName>**.">

---

## Rename Action

If no slug was supplied as argument, present all lists with AskUserQuestion and ask which to rename.

Prompt:

> New name for **<current name or slug>**?

Update the `name` field for the matching entry in `state.lists`. Slug is unchanged. Write updated `state.json`.

Confirm:
> Renamed to **<new name>**. Slug `<slug>` is unchanged.

---

## Delete Action

If no slug was supplied as argument, present all lists with AskUserQuestion and ask which to delete.

### Cannot delete the last list

If `state.lists.length === 1`, refuse:

> You only have one Punch List. You cannot delete it.

Then stop.

### Count projects

Read `~/.punch-list/lists/<slug>/registry.json`. Count the `projects` array.

### Confirm if list has projects

If `projects.length > 0`:

Tell the user:

> **<name>** contains <N> project(s). This will permanently delete the list and all its project configs.
> Type the list name exactly to confirm:

Use AskUserQuestion to collect their input. If the typed value does not match the list name (case-insensitive), cancel:

> Deletion cancelled — name did not match.

Then stop.

### Handle deleting the active list

If the slug matches `currentList`, ask:

> **<name>** is your active list. Select a list to switch to:
> - <other list names>
> ...

Set `currentList` to the chosen slug before deleting.

### Perform deletion

1. Run:
   ```bash
   rm -rf ~/.punch-list/lists/<slug>
   ```
2. Remove the matching entry from `state.lists`.
3. Write updated `state.json`.

Confirm:
> Deleted **<name>**. <"Now active on **<new current>**." if the active list changed.>

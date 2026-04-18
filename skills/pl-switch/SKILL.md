---
name: pl-switch
description: "Use when the user wants to switch the active Punch List. Shortcut for /pl-lists switch."
---

# PL Switch — Switch Active Punch List

Shortcut for `/pl-lists switch`. Changes which Punch List all subsequent commands operate on.

## Gate Check

Read `~/.punch-list/state.json`. If it does not exist, tell the user:

> Punch List is not initialized yet. Run `/pl-init` first.

Then stop.

Parse `state.json`. Extract `currentList` and `lists` array.

## Single-list guard

If `state.lists.length === 1`, tell the user:

> You only have one Punch List (<name or "unnamed">). Nothing to switch to.
> Use `/pl-lists create` to add another list.

Then stop.

## Switch

Present all entries in `state.lists` using AskUserQuestion (arrow-key style), with the current list pre-selected:

> Select a Punch List to make active:
> - <name or "(unnamed — <slug>)"> ← current
> - <name or "(unnamed — <slug>)">
> ...

On selection:
1. Update `currentList` to the chosen slug in `state.json`.
2. Write the updated `state.json`.
3. Confirm:
   > Switched to **<name or slug>**. All Punch List commands now operate on this list.

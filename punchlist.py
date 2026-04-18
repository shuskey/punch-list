#!/usr/bin/env python3
"""punchlist.py — Punch List CLI data layer"""

import json
import secrets
import shutil
import sys
from datetime import date
from pathlib import Path
from typing import Optional

import typer

# Ensure UTF-8 output on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

# ── App setup ─────────────────────────────────────────────────────────────────

app = typer.Typer(no_args_is_help=True)
config_app = typer.Typer(no_args_is_help=True, help="Global state commands")
list_app = typer.Typer(no_args_is_help=True, help="Punch list commands")
project_app = typer.Typer(no_args_is_help=True, help="Project commands")
checklist_app = typer.Typer(no_args_is_help=True, help="Checklist commands")

app.add_typer(config_app, name="config")
app.add_typer(list_app, name="list")
app.add_typer(project_app, name="project")
app.add_typer(checklist_app, name="checklist")

# ── Constants ─────────────────────────────────────────────────────────────────

DEFAULT_DATA_DIR = Path.home() / ".punch-list"
TODAY = date.today().isoformat()

STATE_LABELS = {
    "A": "Ideation", "B": "Defining", "C": "Proving",
    "D": "Delivering", "E": "Evolving", "F": "Sustaining", "G": "Sunsetting",
}

# ── Global state ──────────────────────────────────────────────────────────────

_data_dir: Path = DEFAULT_DATA_DIR


@app.callback()
def main(
    data_dir: Optional[Path] = typer.Option(None, "--data-dir", help="Override base data directory"),
):
    global _data_dir
    if data_dir:
        _data_dir = data_dir


# ── I/O helpers ───────────────────────────────────────────────────────────────

def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        typer.echo(f"Error: file not found: {path}", err=True)
        raise typer.Exit(2)
    except json.JSONDecodeError as e:
        typer.echo(f"Error: corrupt JSON in {path}: {e}", err=True)
        raise typer.Exit(2)


def write_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)


def gen_id() -> str:
    return secrets.token_hex(4)


def out(data, as_json: bool, human_fn):
    if as_json:
        typer.echo(json.dumps(data, indent=2))
    else:
        human_fn()


# ── Resolution helpers ────────────────────────────────────────────────────────

def state_path() -> Path:
    return _data_dir / "state.json"


def read_state() -> dict:
    return read_json(state_path())


def write_state(state: dict):
    write_json(state_path(), state)


def resolve_list_slug(override: Optional[str] = None) -> str:
    if override:
        return override
    state = read_state()
    slug = state.get("currentList")
    if not slug:
        typer.echo("Error: no current list set. Use 'config set-list <slug>'.", err=True)
        raise typer.Exit(1)
    return slug


def registry_path(list_slug: str) -> Path:
    return _data_dir / "lists" / list_slug / "registry.json"


def read_registry(list_slug: str) -> dict:
    return read_json(registry_path(list_slug))


def write_registry(list_slug: str, registry: dict):
    write_json(registry_path(list_slug), registry)


def resolve_project_slug(list_slug: str, override: Optional[str] = None) -> str:
    if override:
        return override
    registry = read_registry(list_slug)
    slug = registry.get("currentProject")
    if slug:
        return slug
    projects = registry.get("projects", [])
    if projects:
        return projects[0]["slug"]
    typer.echo("Error: no projects in this list.", err=True)
    raise typer.Exit(1)


def config_path(list_slug: str, project_slug: str) -> Path:
    return _data_dir / "lists" / list_slug / "projects" / project_slug / "config.json"


def read_config(list_slug: str, project_slug: str) -> dict:
    return read_json(config_path(list_slug, project_slug))


def write_config(list_slug: str, project_slug: str, cfg: dict):
    write_json(config_path(list_slug, project_slug), cfg)


def checklists_path(list_slug: str, project_slug: str) -> Path:
    return _data_dir / "lists" / list_slug / "projects" / project_slug / "checklists.json"


def read_checklists(list_slug: str, project_slug: str) -> dict:
    path = checklists_path(list_slug, project_slug)
    if not path.exists():
        return {"version": "1.0", "currentList": None, "lists": []}
    return read_json(path)


def write_checklists(list_slug: str, project_slug: str, data: dict):
    write_json(checklists_path(list_slug, project_slug), data)


def resolve_checklist_id(cl_data: dict, override: Optional[str] = None) -> Optional[str]:
    if override:
        return override
    current = cl_data.get("currentList")
    if current:
        return current
    for lst in cl_data.get("lists", []):
        if lst.get("items"):
            return lst["id"]
    return None


def find_list_entry(state: dict, slug: str) -> Optional[dict]:
    return next((e for e in state.get("lists", []) if e["slug"] == slug), None)


def find_project_entry(registry: dict, slug: str) -> Optional[dict]:
    return next((p for p in registry.get("projects", []) if p["slug"] == slug), None)


def find_checklist(cl_data: dict, list_id: str) -> Optional[dict]:
    return next((l for l in cl_data.get("lists", []) if l["id"] == list_id), None)


def find_item_in_data(cl_data: dict, item_id: str) -> Optional[tuple]:
    """Returns (list, item) or None."""
    for lst in cl_data.get("lists", []):
        for item in lst.get("items", []):
            if item["id"] == item_id:
                return lst, item
    return None


def checklist_summary(cl_data: dict) -> dict:
    lists = cl_data.get("lists", [])
    list_count = sum(1 for l in lists if l.get("items"))
    total = sum(len(l.get("items", [])) for l in lists)
    completed = sum(
        sum(1 for i in l.get("items", []) if i.get("completed"))
        for l in lists
    )
    return {"listCount": list_count, "completedItems": completed, "totalItems": total}


# ── config commands ───────────────────────────────────────────────────────────

@config_app.command("show")
def config_show(as_json: bool = typer.Option(False, "--json")):
    """Show global state."""
    state = read_state()
    if as_json:
        typer.echo(json.dumps(state, indent=2))
        return
    current = state.get("currentList", "(none)")
    entry = find_list_entry(state, current)
    name = entry["name"] if entry else "(unknown)"
    typer.echo(f"Data directory : {_data_dir}")
    typer.echo(f"Current list   : {current} ({name})")
    typer.echo(f"Version        : {state.get('version', '?')}")


@config_app.command("set-list")
def config_set_list(slug: str, as_json: bool = typer.Option(False, "--json")):
    """Set the current active list."""
    state = read_state()
    entry = find_list_entry(state, slug)
    if not entry:
        typer.echo(f"Error: list '{slug}' not found.", err=True)
        raise typer.Exit(1)
    state["currentList"] = slug
    write_state(state)
    out(
        {"ok": True, "currentList": slug, "name": entry["name"]},
        as_json,
        lambda: typer.echo(f"Current list set to: {slug} ({entry['name']})"),
    )


# ── list commands ─────────────────────────────────────────────────────────────

@list_app.command("show")
def list_show(as_json: bool = typer.Option(False, "--json")):
    """Show all punch lists with project counts."""
    state = read_state()
    current = state.get("currentList")
    result = []
    for entry in state.get("lists", []):
        slug = entry["slug"]
        rp = registry_path(slug)
        count: object = "?"
        if rp.exists():
            try:
                count = len(json.loads(rp.read_text(encoding="utf-8")).get("projects", []))
            except Exception:
                pass
        result.append({**entry, "projectCount": count, "isCurrent": slug == current})

    if as_json:
        typer.echo(json.dumps({"currentList": current, "lists": result}, indent=2))
        return

    typer.echo(f"\n  {'':3} {'SLUG':<22} {'NAME':<38} {'PROJECTS':>8}  CREATED")
    for r in result:
        marker = ">" if r["isCurrent"] else " "
        typer.echo(
            f"  {marker}  {r['slug']:<22} {r.get('name') or '(unnamed)':<38}"
            f" {str(r['projectCount']):>8}  {r.get('createdAt', '')}"
        )


@list_app.command("create")
def list_create(
    slug: str,
    name: str,
    set_current: bool = typer.Option(False, "--set-current"),
    as_json: bool = typer.Option(False, "--json"),
):
    """Create a new punch list."""
    state = read_state()
    if find_list_entry(state, slug):
        typer.echo(f"Error: list '{slug}' already exists.", err=True)
        raise typer.Exit(3)
    entry = {"slug": slug, "name": name, "createdAt": TODAY}
    state["lists"].append(entry)
    if set_current:
        state["currentList"] = slug
    write_state(state)
    write_registry(slug, {"version": "1.0", "createdAt": TODAY, "currentProject": None, "projects": []})
    (_data_dir / "lists" / slug / "projects").mkdir(parents=True, exist_ok=True)
    out(
        {"ok": True, "slug": slug, "name": name, "setCurrent": set_current},
        as_json,
        lambda: typer.echo(f"Created list: {slug} ({name})"),
    )


@list_app.command("rename")
def list_rename(slug: str, new_name: str, as_json: bool = typer.Option(False, "--json")):
    """Rename a punch list."""
    state = read_state()
    entry = find_list_entry(state, slug)
    if not entry:
        typer.echo(f"Error: list '{slug}' not found.", err=True)
        raise typer.Exit(1)
    entry["name"] = new_name
    write_state(state)
    out(
        {"ok": True, "slug": slug, "name": new_name},
        as_json,
        lambda: typer.echo(f"Renamed list {slug} to: {new_name}"),
    )


@list_app.command("delete")
def list_delete(
    slug: str,
    force: bool = typer.Option(False, "--force"),
    as_json: bool = typer.Option(False, "--json"),
):
    """Delete a punch list."""
    state = read_state()
    if len(state.get("lists", [])) <= 1:
        msg = "Cannot delete the only list."
        out({"ok": False, "error": msg}, as_json, lambda: typer.echo(f"Error: {msg}", err=True))
        raise typer.Exit(1)
    entry = find_list_entry(state, slug)
    if not entry:
        typer.echo(f"Error: list '{slug}' not found.", err=True)
        raise typer.Exit(1)
    rp = registry_path(slug)
    project_count = 0
    if rp.exists():
        try:
            project_count = len(json.loads(rp.read_text(encoding="utf-8")).get("projects", []))
        except Exception:
            pass
    if project_count > 0 and not force:
        msg = f"List has {project_count} projects. Use --force to delete."
        out({"ok": False, "error": msg, "projectCount": project_count}, as_json,
            lambda: typer.echo(f"Error: {msg}", err=True))
        raise typer.Exit(1)
    state["lists"] = [e for e in state["lists"] if e["slug"] != slug]
    if state.get("currentList") == slug:
        state["currentList"] = state["lists"][0]["slug"] if state["lists"] else None
    write_state(state)
    list_dir = _data_dir / "lists" / slug
    if list_dir.exists():
        shutil.rmtree(list_dir)
    out({"ok": True, "slug": slug}, as_json, lambda: typer.echo(f"Deleted list: {slug}"))


# ── project commands ──────────────────────────────────────────────────────────

@project_app.command("list")
def project_list(
    list_slug: Optional[str] = typer.Option(None, "--list-slug"),
    state_filter: Optional[str] = typer.Option(None, "--state"),
    as_json: bool = typer.Option(False, "--json"),
):
    """List all projects in the current list."""
    ls = resolve_list_slug(list_slug)
    registry = read_registry(ls)
    projects = registry.get("projects", [])
    current_project = registry.get("currentProject") or (projects[0]["slug"] if projects else None)

    state_data = read_state()
    list_entry = find_list_entry(state_data, ls)
    list_name = list_entry["name"] if list_entry else ls

    if state_filter:
        projects = [p for p in projects if p.get("state") == state_filter.upper()]

    result = []
    for p in projects:
        slug = p["slug"]
        cp = config_path(ls, slug)
        cfg: dict = {}
        config_missing = False
        if cp.exists():
            try:
                cfg = json.loads(cp.read_text(encoding="utf-8"))
            except Exception:
                config_missing = True
        else:
            config_missing = True

        cl_data = read_checklists(ls, slug)
        summary = checklist_summary(cl_data)

        result.append({
            "slug": slug,
            "name": p.get("name", slug),
            "state": p.get("state", "?"),
            "description": p.get("description", ""),
            "githubRepo": cfg.get("githubRepo"),
            "githubVisibility": cfg.get("githubVisibility"),
            "localDirectory": cfg.get("localDirectory"),
            "nextStep": cfg.get("nextStep"),
            "updateNotes": cfg.get("updateNotes"),
            "createdAt": cfg.get("createdAt", ""),
            "updatedAt": cfg.get("updatedAt", ""),
            "isCurrent": slug == current_project,
            "configMissing": config_missing,
            "checklistSummary": summary,
        })

    if as_json:
        typer.echo(json.dumps({
            "listSlug": ls, "listName": list_name,
            "currentProject": current_project, "projects": result,
        }, indent=2))
        return

    typer.echo(f"\nList: {list_name}\n")
    hr = "\u2500"
    typer.echo(f"  {'':3} {'NAME':<32} {'ST':2}  {'CHECKLISTS':>14}  {'GITHUB':>8}  {'LOC':>3}  NEXT STEP")
    typer.echo(f"  {hr*3} {hr*32} {hr*2}  {hr*14}  {hr*8}  {hr*3}  {hr*30}")
    for r in result:
        marker = "👉" if r["isCurrent"] else "  "
        warn = "[!]" if r["configMissing"] else "   "
        s = r["checklistSummary"]
        cl_str = (
            f"{s['listCount']} list{'s' if s['listCount'] != 1 else ''} "
            f"({s['completedItems']}/{s['totalItems']})"
        ) if s["listCount"] > 0 else ""
        gh = r["githubVisibility"] or ("yes" if r["githubRepo"] else "no")
        local = "yes" if r["localDirectory"] else "no"
        next_s = (r["nextStep"] or "")[:30]
        typer.echo(
            f"  {marker} {warn} {r['name']:<32} {r['state']:2}  {cl_str:>14}  {gh:>8}  {local:>3}  {next_s}"
        )
        if r.get("nextStep"):
            pass  # already shown inline


@project_app.command("show")
def project_show(
    slug: Optional[str] = typer.Argument(None),
    list_slug: Optional[str] = typer.Option(None, "--list-slug"),
    set_current: bool = typer.Option(False, "--set-current"),
    as_json: bool = typer.Option(False, "--json"),
):
    """Show full detail for a project."""
    ls = resolve_list_slug(list_slug)
    ps = resolve_project_slug(ls, slug)
    cfg = read_config(ls, ps)
    cl_data = read_checklists(ls, ps)

    if set_current:
        registry = read_registry(ls)
        if registry.get("currentProject") != ps:
            registry["currentProject"] = ps
            write_registry(ls, registry)

    current_lid = cl_data.get("currentList")
    cl_lists = []
    for lst in cl_data.get("lists", []):
        if not lst.get("items"):
            continue
        total = len(lst["items"])
        done = sum(1 for i in lst["items"] if i.get("completed"))
        cl_lists.append({
            "id": lst["id"], "name": lst["name"],
            "totalItems": total, "completedItems": done,
            "isCurrent": lst["id"] == current_lid,
        })

    if as_json:
        typer.echo(json.dumps({**cfg, "checklistSummary": cl_lists}, indent=2))
        return

    state_label = STATE_LABELS.get(cfg.get("state", ""), "Unknown")
    typer.echo(f"\nPROJECT: {cfg.get('name', ps)}")
    typer.echo("─" * 52)
    typer.echo(f"  Slug        : {ps}")
    typer.echo(f"  State       : [{cfg.get('state','?')}] {state_label}")
    typer.echo(f"  GitHub      : {cfg.get('githubRepo') or '—'}")
    typer.echo(f"  Visibility  : {cfg.get('githubVisibility') or '—'}")
    typer.echo(f"  Local Dir   : {cfg.get('localDirectory') or '—'}")
    typer.echo(f"  Next Step   : {cfg.get('nextStep') or '(none)'}")
    typer.echo(f"  Notes       : {cfg.get('updateNotes') or '(none)'}")
    typer.echo(f"  Created     : {cfg.get('createdAt','')}")
    typer.echo(f"  Updated     : {cfg.get('updatedAt','')}")
    if cl_lists:
        typer.echo("\nChecklists:")
        for cl in cl_lists:
            marker = "👉" if cl["isCurrent"] else "  "
            typer.echo(f"  {marker} {cl['name']}  ({cl['completedItems']}/{cl['totalItems']} complete)")


@project_app.command("create")
def project_create(
    slug: str,
    name: str,
    description: Optional[str] = typer.Option(None, "--description"),
    state: str = typer.Option("A", "--state"),
    github_repo: Optional[str] = typer.Option(None, "--github-repo"),
    github_visibility: Optional[str] = typer.Option(None, "--github-visibility"),
    local_directory: Optional[str] = typer.Option(None, "--local-directory"),
    next_step: Optional[str] = typer.Option(None, "--next-step"),
    set_current: bool = typer.Option(False, "--set-current"),
    list_slug: Optional[str] = typer.Option(None, "--list-slug"),
    as_json: bool = typer.Option(False, "--json"),
):
    """Create a new project."""
    ls = resolve_list_slug(list_slug)
    registry = read_registry(ls)
    if find_project_entry(registry, slug):
        typer.echo(f"Error: project '{slug}' already exists in list '{ls}'.", err=True)
        raise typer.Exit(3)
    registry["projects"].append({
        "slug": slug, "name": name, "state": state, "description": description or "",
    })
    if set_current:
        registry["currentProject"] = slug
    write_registry(ls, registry)
    write_config(ls, slug, {
        "name": name, "slug": slug, "description": description or "",
        "state": state, "swimLane": None,
        "githubRepo": github_repo, "githubVisibility": github_visibility,
        "subDirectory": None, "localDirectory": local_directory,
        "updateNotes": None, "nextStep": next_step,
        "createdAt": TODAY, "updatedAt": TODAY,
    })
    write_checklists(ls, slug, {"version": "1.0", "currentList": None, "lists": []})
    out(
        {"ok": True, "slug": slug, "name": name, "listSlug": ls},
        as_json,
        lambda: typer.echo(f"Created project: {slug} ({name}) in list: {ls}"),
    )


@project_app.command("update")
def project_update(
    slug: str,
    name: Optional[str] = typer.Option(None, "--name"),
    description: Optional[str] = typer.Option(None, "--description"),
    state: Optional[str] = typer.Option(None, "--state"),
    github_repo: Optional[str] = typer.Option(None, "--github-repo"),
    github_visibility: Optional[str] = typer.Option(None, "--github-visibility"),
    local_directory: Optional[str] = typer.Option(None, "--local-directory"),
    next_step: Optional[str] = typer.Option(None, "--next-step"),
    update_notes: Optional[str] = typer.Option(None, "--update-notes"),
    clear_next_step: bool = typer.Option(False, "--clear-next-step"),
    clear_update_notes: bool = typer.Option(False, "--clear-update-notes"),
    list_slug: Optional[str] = typer.Option(None, "--list-slug"),
    as_json: bool = typer.Option(False, "--json"),
):
    """Update a project's fields."""
    ls = resolve_list_slug(list_slug)
    cfg = read_config(ls, slug)
    updated: list[str] = []

    def set_field(key, val):
        if val is not None:
            cfg[key] = val
            updated.append(key)

    set_field("name", name)
    set_field("description", description)
    set_field("state", state)
    set_field("githubRepo", github_repo)
    set_field("githubVisibility", github_visibility)
    set_field("localDirectory", local_directory)
    set_field("nextStep", next_step)
    set_field("updateNotes", update_notes)
    if clear_next_step:
        cfg["nextStep"] = None
        updated.append("nextStep")
    if clear_update_notes:
        cfg["updateNotes"] = None
        updated.append("updateNotes")

    if not updated:
        typer.echo("Error: no fields specified to update.", err=True)
        raise typer.Exit(1)

    cfg["updatedAt"] = TODAY
    write_config(ls, slug, cfg)

    # Sync denormalized fields to registry
    if {"name", "state", "description"} & set(updated):
        registry = read_registry(ls)
        entry = find_project_entry(registry, slug)
        if entry:
            if "name" in updated: entry["name"] = cfg["name"]
            if "state" in updated: entry["state"] = cfg["state"]
            if "description" in updated: entry["description"] = cfg["description"]
            write_registry(ls, registry)

    out(
        {"ok": True, "slug": slug, "updatedFields": list(set(updated))},
        as_json,
        lambda: typer.echo(f"Updated project: {slug}"),
    )


@project_app.command("set-current")
def project_set_current(
    slug: str,
    list_slug: Optional[str] = typer.Option(None, "--list-slug"),
    as_json: bool = typer.Option(False, "--json"),
):
    """Set the current project."""
    ls = resolve_list_slug(list_slug)
    registry = read_registry(ls)
    entry = find_project_entry(registry, slug)
    if not entry:
        typer.echo(f"Error: project '{slug}' not found in list '{ls}'.", err=True)
        raise typer.Exit(1)
    registry["currentProject"] = slug
    write_registry(ls, registry)
    out(
        {"ok": True, "slug": slug, "name": entry["name"]},
        as_json,
        lambda: typer.echo(f"Current project set to: {slug} ({entry['name']})"),
    )


@project_app.command("delete")
def project_delete(
    slug: str,
    force: bool = typer.Option(False, "--force"),
    list_slug: Optional[str] = typer.Option(None, "--list-slug"),
    as_json: bool = typer.Option(False, "--json"),
):
    """Delete a project."""
    ls = resolve_list_slug(list_slug)
    registry = read_registry(ls)
    entry = find_project_entry(registry, slug)
    if not entry:
        typer.echo(f"Error: project '{slug}' not found.", err=True)
        raise typer.Exit(1)
    cl_data = read_checklists(ls, slug)
    item_count = sum(len(l.get("items", [])) for l in cl_data.get("lists", []))
    if item_count > 0 and not force:
        msg = f"Project has {item_count} checklist items. Use --force to delete."
        out({"ok": False, "error": msg, "itemCount": item_count}, as_json,
            lambda: typer.echo(f"Error: {msg}", err=True))
        raise typer.Exit(1)
    registry["projects"] = [p for p in registry["projects"] if p["slug"] != slug]
    if registry.get("currentProject") == slug:
        remaining = registry["projects"]
        registry["currentProject"] = remaining[0]["slug"] if remaining else None
    write_registry(ls, registry)
    project_dir = _data_dir / "lists" / ls / "projects" / slug
    if project_dir.exists():
        shutil.rmtree(project_dir)
    out({"ok": True, "slug": slug}, as_json, lambda: typer.echo(f"Deleted project: {slug}"))


# ── checklist commands ────────────────────────────────────────────────────────

@checklist_app.command("lists")
def checklist_lists(
    project_slug: Optional[str] = typer.Option(None, "--project-slug"),
    list_slug: Optional[str] = typer.Option(None, "--list-slug"),
    as_json: bool = typer.Option(False, "--json"),
):
    """Show all checklist lists for the current project."""
    ls = resolve_list_slug(list_slug)
    ps = resolve_project_slug(ls, project_slug)
    cl_data = read_checklists(ls, ps)
    current_id = cl_data.get("currentList")
    result = []
    for lst in cl_data.get("lists", []):
        items = lst.get("items", [])
        done = sum(1 for i in items if i.get("completed"))
        result.append({
            "id": lst["id"], "name": lst["name"],
            "totalItems": len(items), "completedItems": done,
            "isCurrent": lst["id"] == current_id,
        })
    if as_json:
        typer.echo(json.dumps({"projectSlug": ps, "currentList": current_id, "lists": result}, indent=2))
        return
    hr = "\u2500"
    typer.echo(f"\n  {'':2} {'ID':<10} {'NAME':<30} {'ITEMS':>6}  {'DONE':>5}")
    typer.echo(f"  {hr*2} {hr*10} {hr*30} {hr*6}  {hr*5}")
    for r in result:
        marker = ">" if r["isCurrent"] else " "
        typer.echo(f"  {marker}  {r['id']:<10} {r['name']:<30} {r['totalItems']:>6}  {r['completedItems']:>5}")


@checklist_app.command("show")
def checklist_show(
    list_id: Optional[str] = typer.Argument(None),
    project_slug: Optional[str] = typer.Option(None, "--project-slug"),
    list_slug: Optional[str] = typer.Option(None, "--list-slug"),
    as_json: bool = typer.Option(False, "--json"),
):
    """Show items in a checklist list."""
    ls = resolve_list_slug(list_slug)
    ps = resolve_project_slug(ls, project_slug)
    cl_data = read_checklists(ls, ps)
    lid = list_id or resolve_checklist_id(cl_data)
    if not lid:
        typer.echo("Error: no checklists found.", err=True)
        raise typer.Exit(1)
    lst = find_checklist(cl_data, lid)
    if not lst:
        typer.echo(f"Error: checklist '{lid}' not found.", err=True)
        raise typer.Exit(1)
    items = sorted(lst.get("items", []), key=lambda i: i.get("order", 0))
    done = sum(1 for i in items if i.get("completed"))
    if as_json:
        typer.echo(json.dumps({
            "projectSlug": ps, "listId": lid, "listName": lst["name"],
            "currentList": cl_data.get("currentList"),
            "completedCount": done, "totalCount": len(items), "items": items,
        }, indent=2))
        return
    typer.echo(f"\nCHECKLIST: {lst['name']}  [{done}/{len(items)} complete]")
    typer.echo("─" * 52)
    for i, item in enumerate(items, 1):
        mark = "x" if item.get("completed") else " "
        qty = f"  ×{item['quantity']}" if item.get("quantity") else ""
        typer.echo(f"  {i:2}. [{mark}] {item['text']}{qty}  (id:{item['id']})")


@checklist_app.command("create-list")
def checklist_create_list(
    name: str,
    set_current: bool = typer.Option(False, "--set-current"),
    project_slug: Optional[str] = typer.Option(None, "--project-slug"),
    list_slug: Optional[str] = typer.Option(None, "--list-slug"),
    as_json: bool = typer.Option(False, "--json"),
):
    """Create a new checklist list."""
    ls = resolve_list_slug(list_slug)
    ps = resolve_project_slug(ls, project_slug)
    cl_data = read_checklists(ls, ps)
    new_id = gen_id()
    cl_data["lists"].append({"id": new_id, "name": name, "createdAt": TODAY, "items": []})
    if set_current:
        cl_data["currentList"] = new_id
    write_checklists(ls, ps, cl_data)
    out(
        {"ok": True, "id": new_id, "name": name, "setCurrent": set_current},
        as_json,
        lambda: typer.echo(f"Created checklist: {name} [id: {new_id}]"),
    )


@checklist_app.command("set-current")
def checklist_set_current(
    list_id: str,
    project_slug: Optional[str] = typer.Option(None, "--project-slug"),
    list_slug: Optional[str] = typer.Option(None, "--list-slug"),
    as_json: bool = typer.Option(False, "--json"),
):
    """Set the active checklist list."""
    ls = resolve_list_slug(list_slug)
    ps = resolve_project_slug(ls, project_slug)
    cl_data = read_checklists(ls, ps)
    lst = find_checklist(cl_data, list_id)
    if not lst:
        typer.echo(f"Error: checklist '{list_id}' not found.", err=True)
        raise typer.Exit(1)
    cl_data["currentList"] = list_id
    write_checklists(ls, ps, cl_data)
    out(
        {"ok": True, "id": list_id, "name": lst["name"]},
        as_json,
        lambda: typer.echo(f"Current checklist set to: {lst['name']} [{list_id}]"),
    )


@checklist_app.command("rename-list")
def checklist_rename_list(
    list_id: str,
    new_name: str,
    project_slug: Optional[str] = typer.Option(None, "--project-slug"),
    list_slug: Optional[str] = typer.Option(None, "--list-slug"),
    as_json: bool = typer.Option(False, "--json"),
):
    """Rename a checklist list."""
    ls = resolve_list_slug(list_slug)
    ps = resolve_project_slug(ls, project_slug)
    cl_data = read_checklists(ls, ps)
    lst = find_checklist(cl_data, list_id)
    if not lst:
        typer.echo(f"Error: checklist '{list_id}' not found.", err=True)
        raise typer.Exit(1)
    lst["name"] = new_name
    write_checklists(ls, ps, cl_data)
    out(
        {"ok": True, "id": list_id, "name": new_name},
        as_json,
        lambda: typer.echo(f"Renamed checklist to: {new_name}"),
    )


@checklist_app.command("delete-list")
def checklist_delete_list(
    list_id: str,
    force: bool = typer.Option(False, "--force"),
    project_slug: Optional[str] = typer.Option(None, "--project-slug"),
    list_slug: Optional[str] = typer.Option(None, "--list-slug"),
    as_json: bool = typer.Option(False, "--json"),
):
    """Delete a checklist list."""
    ls = resolve_list_slug(list_slug)
    ps = resolve_project_slug(ls, project_slug)
    cl_data = read_checklists(ls, ps)
    lst = find_checklist(cl_data, list_id)
    if not lst:
        typer.echo(f"Error: checklist '{list_id}' not found.", err=True)
        raise typer.Exit(1)
    item_count = len(lst.get("items", []))
    if item_count > 0 and not force:
        msg = f"List has {item_count} items. Use --force to delete."
        out({"ok": False, "error": msg, "itemCount": item_count}, as_json,
            lambda: typer.echo(f"Error: {msg}", err=True))
        raise typer.Exit(1)
    cl_data["lists"] = [l for l in cl_data["lists"] if l["id"] != list_id]
    if cl_data.get("currentList") == list_id:
        remaining = cl_data["lists"]
        cl_data["currentList"] = remaining[0]["id"] if remaining else None
    write_checklists(ls, ps, cl_data)
    out({"ok": True, "id": list_id}, as_json, lambda: typer.echo(f"Deleted checklist: {lst['name']}"))


@checklist_app.command("add")
def checklist_add(
    text: str,
    quantity: Optional[str] = typer.Option(None, "--quantity"),
    list_id: Optional[str] = typer.Option(None, "--list-id"),
    project_slug: Optional[str] = typer.Option(None, "--project-slug"),
    list_slug: Optional[str] = typer.Option(None, "--list-slug"),
    as_json: bool = typer.Option(False, "--json"),
):
    """Add an item to a checklist."""
    ls = resolve_list_slug(list_slug)
    ps = resolve_project_slug(ls, project_slug)
    cl_data = read_checklists(ls, ps)
    lid = list_id or resolve_checklist_id(cl_data)
    if not lid:
        typer.echo("Error: no checklist found. Create one first with 'checklist create-list'.", err=True)
        raise typer.Exit(1)
    lst = find_checklist(cl_data, lid)
    if not lst:
        typer.echo(f"Error: checklist '{lid}' not found.", err=True)
        raise typer.Exit(1)
    items = lst.get("items", [])
    max_order = max((i.get("order", 0) for i in items), default=-1)
    new_id = gen_id()
    item = {"id": new_id, "text": text, "quantity": quantity, "completed": False, "order": max_order + 1}
    items.append(item)
    lst["items"] = items
    write_checklists(ls, ps, cl_data)
    out({"ok": True, **item}, as_json, lambda: typer.echo(f"Added item [{new_id}]: {text}"))


@checklist_app.command("toggle")
def checklist_toggle(
    item_id: str,
    project_slug: Optional[str] = typer.Option(None, "--project-slug"),
    list_slug: Optional[str] = typer.Option(None, "--list-slug"),
    as_json: bool = typer.Option(False, "--json"),
):
    """Toggle an item's completed state."""
    ls = resolve_list_slug(list_slug)
    ps = resolve_project_slug(ls, project_slug)
    cl_data = read_checklists(ls, ps)
    result = find_item_in_data(cl_data, item_id)
    if not result:
        typer.echo(f"Error: item '{item_id}' not found.", err=True)
        raise typer.Exit(1)
    _, item = result
    item["completed"] = not item["completed"]
    write_checklists(ls, ps, cl_data)
    mark = "x" if item["completed"] else " "
    out(
        {"ok": True, "id": item_id, "completed": item["completed"]},
        as_json,
        lambda: typer.echo(f"  [{mark}] {item['text']}"),
    )


@checklist_app.command("complete")
def checklist_complete(
    item_id: str,
    project_slug: Optional[str] = typer.Option(None, "--project-slug"),
    list_slug: Optional[str] = typer.Option(None, "--list-slug"),
    as_json: bool = typer.Option(False, "--json"),
):
    """Mark an item complete."""
    _set_completed(item_id, True, project_slug, list_slug, as_json)


@checklist_app.command("uncomplete")
def checklist_uncomplete(
    item_id: str,
    project_slug: Optional[str] = typer.Option(None, "--project-slug"),
    list_slug: Optional[str] = typer.Option(None, "--list-slug"),
    as_json: bool = typer.Option(False, "--json"),
):
    """Mark an item incomplete."""
    _set_completed(item_id, False, project_slug, list_slug, as_json)


def _set_completed(item_id: str, completed: bool, project_slug, list_slug, as_json):
    ls = resolve_list_slug(list_slug)
    ps = resolve_project_slug(ls, project_slug)
    cl_data = read_checklists(ls, ps)
    result = find_item_in_data(cl_data, item_id)
    if not result:
        typer.echo(f"Error: item '{item_id}' not found.", err=True)
        raise typer.Exit(1)
    _, item = result
    item["completed"] = completed
    write_checklists(ls, ps, cl_data)
    mark = "x" if completed else " "
    out(
        {"ok": True, "id": item_id, "completed": completed},
        as_json,
        lambda: typer.echo(f"  [{mark}] {item['text']}"),
    )


@checklist_app.command("update-item")
def checklist_update_item(
    item_id: str,
    text: Optional[str] = typer.Option(None, "--text"),
    quantity: Optional[str] = typer.Option(None, "--quantity"),
    clear_quantity: bool = typer.Option(False, "--clear-quantity"),
    project_slug: Optional[str] = typer.Option(None, "--project-slug"),
    list_slug: Optional[str] = typer.Option(None, "--list-slug"),
    as_json: bool = typer.Option(False, "--json"),
):
    """Update an item's text or quantity."""
    ls = resolve_list_slug(list_slug)
    ps = resolve_project_slug(ls, project_slug)
    cl_data = read_checklists(ls, ps)
    result = find_item_in_data(cl_data, item_id)
    if not result:
        typer.echo(f"Error: item '{item_id}' not found.", err=True)
        raise typer.Exit(1)
    _, item = result
    if text is not None: item["text"] = text
    if quantity is not None: item["quantity"] = quantity
    if clear_quantity: item["quantity"] = None
    write_checklists(ls, ps, cl_data)
    out(
        {"ok": True, "id": item_id, "text": item["text"], "quantity": item["quantity"]},
        as_json,
        lambda: typer.echo(f"Updated item [{item_id}]: {item['text']}"),
    )


@checklist_app.command("delete-item")
def checklist_delete_item(
    item_id: str,
    project_slug: Optional[str] = typer.Option(None, "--project-slug"),
    list_slug: Optional[str] = typer.Option(None, "--list-slug"),
    as_json: bool = typer.Option(False, "--json"),
):
    """Delete an item from a checklist."""
    ls = resolve_list_slug(list_slug)
    ps = resolve_project_slug(ls, project_slug)
    cl_data = read_checklists(ls, ps)
    result = find_item_in_data(cl_data, item_id)
    if not result:
        typer.echo(f"Error: item '{item_id}' not found.", err=True)
        raise typer.Exit(1)
    lst, item = result
    lst["items"] = [i for i in lst["items"] if i["id"] != item_id]
    for idx, i in enumerate(sorted(lst["items"], key=lambda x: x.get("order", 0))):
        i["order"] = idx
    write_checklists(ls, ps, cl_data)
    out({"ok": True, "id": item_id}, as_json, lambda: typer.echo(f"Deleted item [{item_id}]: {item['text']}"))


@checklist_app.command("reorder")
def checklist_reorder(
    item_id: str,
    new_position: int,
    list_id: Optional[str] = typer.Option(None, "--list-id"),
    project_slug: Optional[str] = typer.Option(None, "--project-slug"),
    list_slug: Optional[str] = typer.Option(None, "--list-slug"),
    as_json: bool = typer.Option(False, "--json"),
):
    """Move an item to a new 1-based position within its list."""
    ls = resolve_list_slug(list_slug)
    ps = resolve_project_slug(ls, project_slug)
    cl_data = read_checklists(ls, ps)
    lid = list_id or resolve_checklist_id(cl_data)
    lst = find_checklist(cl_data, lid) if lid else None
    if not lst:
        typer.echo("Error: checklist not found.", err=True)
        raise typer.Exit(1)
    items = sorted(lst.get("items", []), key=lambda i: i.get("order", 0))
    idx = next((i for i, it in enumerate(items) if it["id"] == item_id), None)
    if idx is None:
        typer.echo(f"Error: item '{item_id}' not found.", err=True)
        raise typer.Exit(1)
    item = items.pop(idx)
    new_idx = max(0, min(new_position - 1, len(items)))
    items.insert(new_idx, item)
    for i, it in enumerate(items):
        it["order"] = i
    lst["items"] = items
    write_checklists(ls, ps, cl_data)
    out(
        {"ok": True, "id": item_id, "newOrder": new_idx},
        as_json,
        lambda: typer.echo(f"Moved item to position {new_position}: {item['text']}"),
    )


if __name__ == "__main__":
    app()

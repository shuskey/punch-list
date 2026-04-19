#!/usr/bin/env python3
"""Punch List Web Server — serves the React board UI and REST API."""

import json
import subprocess
import sys
import webbrowser
import threading
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory

PUNCHLIST = Path.home() / ".punch-list" / "punchlist.py"
HERE = Path(__file__).parent

app = Flask(__name__)


@app.errorhandler(Exception)
def handle_exception(e):
    from werkzeug.exceptions import HTTPException
    code = e.code if isinstance(e, HTTPException) else 500
    return jsonify({"error": str(e)}), code


def run_pl(*args):
    """Call punchlist.py with --json. Returns (data_dict, http_status_int)."""
    cmd = [sys.executable, str(PUNCHLIST), *args, "--json"]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    stdout = r.stdout.strip()
    if stdout:
        try:
            data = json.loads(stdout)
        except ValueError:
            return {"error": stdout}, 500
        return data, (400 if r.returncode != 0 else 200)
    if r.returncode != 0:
        return {"error": r.stderr.strip() or "command failed"}, 500
    return {}, 200


# ── Static ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(HERE, "index.html")


# ── List ──────────────────────────────────────────────────────────────────────

@app.route("/api/list")
def get_list():
    data, status = run_pl("list", "show")
    return jsonify(data), status


@app.route("/api/list/switch", methods=["POST"])
def switch_list():
    slug = (request.json or {}).get("slug", "")
    if not slug:
        return jsonify({"error": "slug required"}), 400
    data, status = run_pl("config", "set-list", slug)
    return jsonify(data), status


# ── Projects ─────────────────────────────────────────────────────────────────

@app.route("/api/projects")
def list_projects():
    data, status = run_pl("project", "list")
    return jsonify(data), status


@app.route("/api/projects/<slug>")
def show_project(slug):
    data, status = run_pl("project", "show", slug)
    return jsonify(data), status


@app.route("/api/projects", methods=["POST"])
def create_project():
    d = request.json or {}
    args = ["project", "create", d["slug"], d["name"]]
    if d.get("description"):      args += ["--description", d["description"]]
    if d.get("state"):            args += ["--state", d["state"]]
    if d.get("githubRepo"):       args += ["--github-repo", d["githubRepo"]]
    if d.get("githubVisibility"): args += ["--github-visibility", d["githubVisibility"]]
    if d.get("localDirectory"):   args += ["--local-directory", d["localDirectory"]]
    if d.get("nextStep"):         args += ["--next-step", d["nextStep"]]
    data, status = run_pl(*args)
    return jsonify(data), status


@app.route("/api/projects/<slug>", methods=["PATCH"])
def update_project(slug):
    d = request.json or {}
    args = ["project", "update", slug]
    if "name" in d:              args += ["--name", d["name"]]
    if "description" in d:       args += ["--description", d["description"]]
    if "state" in d:             args += ["--state", d["state"]]
    if "githubRepo" in d:
        if d["githubRepo"]:      args += ["--github-repo", d["githubRepo"]]
    if "githubVisibility" in d:
        if d["githubVisibility"]: args += ["--github-visibility", d["githubVisibility"]]
    if "localDirectory" in d:
        if d["localDirectory"]:  args += ["--local-directory", d["localDirectory"]]
    if "nextStep" in d:
        if d["nextStep"]:        args += ["--next-step", d["nextStep"]]
        else:                    args += ["--clear-next-step"]
    if "updateNotes" in d:
        if d["updateNotes"]:     args += ["--update-notes", d["updateNotes"]]
        else:                    args += ["--clear-update-notes"]
    data, status = run_pl(*args)
    return jsonify(data), status


@app.route("/api/projects/<slug>", methods=["DELETE"])
def delete_project(slug):
    args = ["project", "delete", slug]
    if request.args.get("force") == "true":
        args += ["--force"]
    data, status = run_pl(*args)
    return jsonify(data), status


@app.route("/api/projects/<slug>/set-current", methods=["POST"])
def set_current(slug):
    data, status = run_pl("project", "set-current", slug)
    return jsonify(data), status


# ── Checklists ────────────────────────────────────────────────────────────────

@app.route("/api/projects/<slug>/checklists")
def list_checklists(slug):
    data, status = run_pl("checklist", "lists", "--project-slug", slug)
    return jsonify(data), status


@app.route("/api/projects/<slug>/checklists", methods=["POST"])
def create_checklist(slug):
    d = request.json or {}
    args = ["checklist", "create-list", d["name"], "--project-slug", slug, "--set-current"]
    data, status = run_pl(*args)
    return jsonify(data), status


@app.route("/api/projects/<slug>/checklists/<list_id>")
def show_checklist(slug, list_id):
    data, status = run_pl("checklist", "show", list_id, "--project-slug", slug)
    return jsonify(data), status


@app.route("/api/projects/<slug>/checklists/<list_id>", methods=["DELETE"])
def delete_checklist(slug, list_id):
    args = ["checklist", "delete-list", list_id, "--project-slug", slug]
    if request.args.get("force") == "true":
        args += ["--force"]
    data, status = run_pl(*args)
    return jsonify(data), status


@app.route("/api/projects/<slug>/checklists/<list_id>/items", methods=["POST"])
def add_item(slug, list_id):
    d = request.json or {}
    args = ["checklist", "add", d["text"], "--list-id", list_id, "--project-slug", slug]
    if d.get("quantity"):
        args += ["--quantity", d["quantity"]]
    data, status = run_pl(*args)
    return jsonify(data), status


@app.route("/api/projects/<slug>/checklists/<list_id>/items/<item_id>/toggle", methods=["POST"])
def toggle_item(slug, list_id, item_id):
    data, status = run_pl("checklist", "toggle", item_id, "--project-slug", slug)
    return jsonify(data), status


@app.route("/api/projects/<slug>/checklists/<list_id>/items/<item_id>", methods=["PATCH"])
def update_item(slug, list_id, item_id):
    d = request.json or {}
    args = ["checklist", "update-item", item_id, "--project-slug", slug]
    if "text" in d:
        args += ["--text", d["text"]]
    data, status = run_pl(*args)
    return jsonify(data), status


@app.route("/api/projects/<slug>/checklists/<list_id>/items/<item_id>", methods=["DELETE"])
def delete_item(slug, list_id, item_id):
    data, status = run_pl("checklist", "delete-item", item_id, "--project-slug", slug)
    return jsonify(data), status


@app.route("/api/projects/<slug>/checklists/<list_id>/items/<item_id>/reorder", methods=["POST"])
def reorder_item(slug, list_id, item_id):
    position = str((request.json or {}).get("position", 1))
    data, status = run_pl("checklist", "reorder", item_id, position,
                          "--list-id", list_id, "--project-slug", slug)
    return jsonify(data), status


# ── Launch ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    url = "http://localhost:5000"
    threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    print(f"\nPunch List  ->  {url}\n")
    app.run(port=5000, debug=False)

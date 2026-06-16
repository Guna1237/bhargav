import json
import os
import uuid
import random
import string
from datetime import datetime

_ROOT = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(_ROOT, "data")


def _path(filename):
    os.makedirs(DATA_DIR, exist_ok=True)
    return os.path.join(DATA_DIR, filename)


def _load(filename):
    p = _path(filename)
    if not os.path.exists(p):
        return {}
    with open(p, "r") as f:
        return json.load(f)


def _save(filename, data):
    with open(_path(filename), "w") as f:
        json.dump(data, f, indent=2, default=str)


def _gen_code(existing_codes):
    while True:
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if code not in existing_codes:
            return code


# ── Projects ──────────────────────────────────────────────────────────────────

def create_project(title, description, timeline, team_size):
    projects = _load("projects.json")
    codes = {p["code"] for p in projects.values()}
    pid = str(uuid.uuid4())
    code = _gen_code(codes)
    projects[pid] = {
        "id": pid,
        "code": code,
        "title": title,
        "description": description,
        "timeline": timeline,
        "team_size": int(team_size),
        "analysis": None,
        "questions": [],
        "workspace": {"workstreams": [], "assignments": {}},
        "integrations": {"github": {}, "drive": {}, "calendar": {}},
        "created_at": datetime.now().isoformat(),
    }
    _save("projects.json", projects)
    return pid, code


def get_project(pid):
    return _load("projects.json").get(pid)


def get_project_by_code(code):
    for p in _load("projects.json").values():
        if p["code"] == code.upper().strip():
            return p
    return None


def update_project(pid, **fields):
    projects = _load("projects.json")
    if pid in projects:
        projects[pid].update(fields)
        _save("projects.json", projects)


def set_analysis(pid, analysis, questions):
    update_project(pid, analysis=analysis, questions=questions)


def set_workspace(pid, workspace):
    update_project(pid, workspace=workspace)


def set_integration(pid, key, data):
    projects = _load("projects.json")
    if pid in projects:
        projects[pid]["integrations"][key] = data
        _save("projects.json", projects)


# ── Responses ─────────────────────────────────────────────────────────────────

def save_response(project_id, respondent, answers):
    responses = _load("responses.json")
    rid = str(uuid.uuid4())
    responses[rid] = {
        "id": rid,
        "project_id": project_id,
        "respondent": respondent,
        "answers": answers,
        "submitted_at": datetime.now().isoformat(),
    }
    _save("responses.json", responses)
    return rid


def get_responses(project_id):
    all_r = _load("responses.json")
    return sorted(
        [r for r in all_r.values() if r["project_id"] == project_id],
        key=lambda r: r["submitted_at"],
    )


def respondent_exists(project_id, name):
    return any(
        r["respondent"].lower() == name.lower()
        for r in get_responses(project_id)
    )


# ── Scores ────────────────────────────────────────────────────────────────────

def save_scores(project_id, pci_data, ths_data=None):
    scores = _load("scores.json")
    existing = scores.get(project_id, {})
    scores[project_id] = {
        "project_id": project_id,
        "pci": pci_data,
        "ths": ths_data if ths_data is not None else existing.get("ths"),
        "updated_at": datetime.now().isoformat(),
    }
    _save("scores.json", scores)


def save_ths(project_id, ths_data):
    scores = _load("scores.json")
    existing = scores.get(project_id, {})
    existing["ths"] = ths_data
    existing["project_id"] = project_id
    existing["updated_at"] = datetime.now().isoformat()
    scores[project_id] = existing
    _save("scores.json", scores)


def get_scores(project_id):
    return _load("scores.json").get(project_id)

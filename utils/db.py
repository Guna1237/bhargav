import sqlite3
import json
import uuid
import random
import string
from datetime import datetime

DB_PATH = "squadsync.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            code TEXT UNIQUE,
            title TEXT,
            brief TEXT,
            timeline TEXT,
            team_size INTEGER,
            summary TEXT,
            workstreams TEXT,
            questions TEXT,
            created_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS responses (
            id TEXT PRIMARY KEY,
            project_id TEXT,
            respondent TEXT,
            answers TEXT,
            submitted_at TEXT,
            FOREIGN KEY (project_id) REFERENCES projects (id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS pci_results (
            id TEXT PRIMARY KEY,
            project_id TEXT UNIQUE,
            group_alignment REAL,
            priority_alignment REAL,
            role_clarity REAL,
            skill_coverage REAL,
            tool_cohesion REAL,
            pci_score REAL,
            gaps TEXT,
            discussion_topics TEXT,
            recommendations TEXT,
            calculated_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def _generate_code(conn):
    c = conn.cursor()
    while True:
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        c.execute("SELECT id FROM projects WHERE code = ?", (code,))
        if not c.fetchone():
            return code


def create_project(title, brief, timeline, team_size, summary, workstreams, questions):
    conn = sqlite3.connect(DB_PATH)
    try:
        project_id = str(uuid.uuid4())
        code = _generate_code(conn)
        conn.execute(
            """INSERT INTO projects
               (id, code, title, brief, timeline, team_size, summary, workstreams, questions, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                project_id, code, title, brief, timeline, int(team_size),
                summary,
                json.dumps(workstreams),
                json.dumps(questions),
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        return project_id, code
    finally:
        conn.close()


def get_project_by_code(code):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute("SELECT * FROM projects WHERE code = ?", (code.upper(),)).fetchone()
        if not row:
            return None
        p = dict(row)
        p["workstreams"] = json.loads(p["workstreams"]) if p["workstreams"] else []
        p["questions"] = json.loads(p["questions"]) if p["questions"] else []
        return p
    finally:
        conn.close()


def save_response(project_id, respondent, answers):
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "INSERT INTO responses (id, project_id, respondent, answers, submitted_at) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), project_id, respondent, json.dumps(answers), datetime.now().isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def get_responses(project_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT * FROM responses WHERE project_id = ? ORDER BY submitted_at", (project_id,)
        ).fetchall()
        result = []
        for row in rows:
            r = dict(row)
            r["answers"] = json.loads(r["answers"])
            result.append(r)
        return result
    finally:
        conn.close()


def respondent_exists(project_id, name):
    conn = sqlite3.connect(DB_PATH)
    try:
        row = conn.execute(
            "SELECT id FROM responses WHERE project_id = ? AND lower(respondent) = lower(?)",
            (project_id, name),
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def save_pci(project_id, scores, gaps, discussion_topics, recommendations):
    overall = (
        scores["group_alignment"] * 0.25
        + scores["priority_alignment"] * 0.25
        + scores["role_clarity"] * 0.20
        + scores["skill_coverage"] * 0.15
        + scores["tool_cohesion"] * 0.15
    )
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("DELETE FROM pci_results WHERE project_id = ?", (project_id,))
        conn.execute(
            """INSERT INTO pci_results
               (id, project_id, group_alignment, priority_alignment, role_clarity,
                skill_coverage, tool_cohesion, pci_score, gaps, discussion_topics, recommendations, calculated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(uuid.uuid4()), project_id,
                scores["group_alignment"], scores["priority_alignment"],
                scores["role_clarity"], scores["skill_coverage"], scores["tool_cohesion"],
                round(overall, 1),
                json.dumps(gaps),
                json.dumps(discussion_topics),
                json.dumps(recommendations),
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        return round(overall, 1)
    finally:
        conn.close()


def get_pci(project_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute("SELECT * FROM pci_results WHERE project_id = ?", (project_id,)).fetchone()
        if not row:
            return None
        r = dict(row)
        r["gaps"] = json.loads(r["gaps"])
        r["discussion_topics"] = json.loads(r["discussion_topics"])
        r["recommendations"] = json.loads(r["recommendations"])
        return r
    finally:
        conn.close()

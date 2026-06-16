import os
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from utils.db import (
    init_db, create_project, get_project_by_code,
    save_response, get_responses, respondent_exists,
    save_pci, get_pci,
)

init_db()

st.set_page_config(
    page_title="SquadSync",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
#MainMenu, footer, header { visibility: hidden; }
.stApp { background: #ffffff; }
.block-container { max-width: 680px; padding: 2.5rem 1.5rem 6rem; }

/* Typography */
h1 {
    font-size: 1.45rem !important;
    font-weight: 700 !important;
    color: #0a0a0a !important;
    letter-spacing: -0.025em !important;
    margin-bottom: 0.25rem !important;
}
h2 {
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    color: #0a0a0a !important;
    margin-bottom: 0.25rem !important;
}
h3 {
    font-size: 0.875rem !important;
    font-weight: 600 !important;
    color: #0a0a0a !important;
}
p { font-size: 0.875rem !important; color: #555 !important; line-height: 1.65 !important; }
label { font-size: 0.875rem !important; color: #0a0a0a !important; font-weight: 500 !important; }
li { font-size: 0.875rem !important; color: #555 !important; }

/* Buttons — all dark */
.stButton > button,
.stFormSubmitButton > button {
    background: #0a0a0a !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 4px !important;
    padding: 0.45rem 1.2rem !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.01em !important;
    transition: background 0.15s !important;
}
.stButton > button:hover,
.stFormSubmitButton > button:hover {
    background: #2a2a2a !important;
    border: none !important;
    color: #fff !important;
}
.stButton > button:focus,
.stFormSubmitButton > button:focus {
    box-shadow: 0 0 0 2px #0a0a0a !important;
}

/* Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input {
    border: 1px solid #d0d0d0 !important;
    border-radius: 4px !important;
    font-size: 0.875rem !important;
    color: #0a0a0a !important;
    background: #fff !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #0a0a0a !important;
    box-shadow: none !important;
    outline: none !important;
}

/* Select slider */
div[data-testid="stSlider"] > div > div > div > div[role="slider"] {
    background: #0a0a0a !important;
    border: 2px solid #0a0a0a !important;
}

/* Radio */
.stRadio > div { gap: 0.5rem !important; }
.stRadio label { font-weight: 400 !important; color: #333 !important; }

/* Divider */
hr {
    border: none !important;
    border-top: 1px solid #e8e8e8 !important;
    margin: 1.25rem 0 !important;
}

/* Info/error boxes */
.stAlert { border-radius: 4px !important; font-size: 0.85rem !important; }

/* Spinner */
.stSpinner > div { border-top-color: #0a0a0a !important; }

/* Code blocks */
code { font-size: 0.85rem !important; }
</style>
""", unsafe_allow_html=True)


# ── Streamlit version compat ──────────────────────────────────────────────────
def _rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()


# ── Session helpers ───────────────────────────────────────────────────────────
def go(page, **kwargs):
    st.session_state["page"] = page
    for k, v in kwargs.items():
        st.session_state[k] = v
    _rerun()


def s(key, default=None):
    return st.session_state.get(key, default)


# ── Reusable UI components ────────────────────────────────────────────────────
def topbar(sub=None):
    cols = st.columns([1, 6])
    with cols[0]:
        if st.button("← Back", key="topbar_back"):
            go("home")
    with cols[1]:
        label = f"SquadSync · {sub}" if sub else "SquadSync"
        st.markdown(
            f"<p style='color:#999;font-size:0.78rem;margin:0.4rem 0 0'>{label}</p>",
            unsafe_allow_html=True,
        )
    st.divider()


def pci_hero(score):
    if score >= 75:
        color, label = "#16a34a", "Strong cohesion"
    elif score >= 55:
        color, label = "#d97706", "Moderate cohesion — some gaps"
    else:
        color, label = "#dc2626", "Low cohesion — alignment needed before execution"

    st.markdown(f"""
<div style="border:1px solid #e0e0e0;border-radius:6px;padding:1.25rem 1.5rem;margin:0.75rem 0 1.25rem">
    <div style="font-size:0.68rem;text-transform:uppercase;letter-spacing:0.07em;color:#999;margin-bottom:0.3rem">
        Project Cohesion Index
    </div>
    <div style="font-size:2.8rem;font-weight:700;color:{color};line-height:1;margin-bottom:0.6rem">
        {score:.0f}<span style="font-size:1rem;font-weight:400;color:#bbb"> / 100</span>
    </div>
    <div style="background:#f0f0f0;height:5px;border-radius:3px;margin-bottom:0.6rem">
        <div style="background:{color};height:5px;border-radius:3px;width:{score}%"></div>
    </div>
    <div style="font-size:0.8rem;color:#666">{label}</div>
</div>
""", unsafe_allow_html=True)


def dim_bar(label, score, weight):
    if score >= 75:
        color = "#16a34a"
    elif score >= 55:
        color = "#d97706"
    else:
        color = "#dc2626"
    st.markdown(f"""
<div style="margin-bottom:0.8rem">
    <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:0.22rem">
        <span style="font-size:0.82rem;color:#333">
            {label}
            <span style="color:#bbb;font-size:0.72rem;margin-left:4px">{weight}</span>
        </span>
        <span style="font-size:0.82rem;font-weight:600;color:{color}">{score:.0f}</span>
    </div>
    <div style="background:#f0f0f0;height:4px;border-radius:2px">
        <div style="background:{color};height:4px;border-radius:2px;width:{score}%"></div>
    </div>
</div>
""", unsafe_allow_html=True)


def code_box(code, label="Project code — share this with your team"):
    st.markdown(f"""
<div style="border:1.5px solid #0a0a0a;border-radius:6px;padding:1rem 1.25rem;margin:0.5rem 0 1.25rem;display:inline-block;min-width:200px">
    <div style="font-size:0.68rem;text-transform:uppercase;letter-spacing:0.07em;color:#999;margin-bottom:0.2rem">
        {label}
    </div>
    <div style="font-size:2rem;font-weight:700;color:#0a0a0a;letter-spacing:0.18em">{code}</div>
</div>
""", unsafe_allow_html=True)


def section(title):
    st.markdown(f"**{title}**")


def bullet_list(items):
    for item in items:
        st.markdown(
            f"<p style='margin:0.1rem 0 0.1rem 0;color:#444'>— {item}</p>",
            unsafe_allow_html=True,
        )
    st.write("")


def numbered_list(items):
    for i, item in enumerate(items, 1):
        st.markdown(
            f"<p style='margin:0.15rem 0;color:#444'>{i}.&nbsp; {item}</p>",
            unsafe_allow_html=True,
        )
    st.write("")


# ── Pages ─────────────────────────────────────────────────────────────────────
def page_home():
    st.markdown(
        "<p style='font-size:0.78rem;color:#999;margin-bottom:0.25rem'>SquadSync</p>",
        unsafe_allow_html=True,
    )
    st.title("Project cohesion for temporary teams")
    st.write(
        "Align your team on goals, responsibilities, and priorities — "
        "before execution begins."
    )
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Create a project", use_container_width=True):
            go("create")
    with col2:
        if st.button("Join a project", use_container_width=True):
            go("join")

    st.write("")
    if st.button("View team dashboard", use_container_width=True):
        go("dashboard_entry")


def page_create():
    topbar("New project")
    st.title("Create a project")
    st.write("Enter your project details. The AI will analyze the brief and generate alignment questions for your team.")
    st.write("")

    with st.form("create_form"):
        title = st.text_input("Project name", placeholder="e.g. AI Healthcare Triage System")
        brief = st.text_area(
            "Project brief",
            placeholder="Describe the problem you're solving, the key deliverables, timeline constraints, and any relevant context. The more specific, the better the questions.",
            height=160,
        )
        col1, col2 = st.columns(2)
        with col1:
            timeline = st.text_input("Timeline", placeholder="e.g. 24 hours, 2 weeks")
        with col2:
            team_size = st.number_input("Team size", min_value=2, max_value=20, value=4, step=1)

        submitted = st.form_submit_button("Analyze and create project")

    if submitted:
        errors = []
        if not title.strip():
            errors.append("Project name is required.")
        if not brief.strip() or len(brief.strip()) < 30:
            errors.append("Brief must be at least 30 characters.")
        if not timeline.strip():
            errors.append("Timeline is required.")
        if errors:
            for e in errors:
                st.error(e)
            return

        if not os.getenv("OPENAI_API_KEY", "").strip():
            st.error("OPENAI_API_KEY is not set. Copy .env.example to .env and add your free key from openrouter.ai")
            return

        with st.spinner("Analyzing project brief and generating questions…"):
            try:
                from utils.ai_engine import analyze_project, generate_questions

                analysis = analyze_project(title.strip(), brief.strip(), timeline.strip(), int(team_size))
                questions = generate_questions(
                    title.strip(), brief.strip(), timeline.strip(),
                    int(team_size), analysis.get("workstreams", []),
                )

                project_id, code = create_project(
                    title.strip(), brief.strip(), timeline.strip(), int(team_size),
                    analysis.get("summary", ""),
                    analysis.get("workstreams", []),
                    questions,
                )

                go(
                    "created",
                    project_code=code,
                    project_id=project_id,
                    project_analysis=analysis,
                    project_questions=questions,
                    project_title=title.strip(),
                )
            except Exception as exc:
                st.error(f"Error: {exc}")


def page_created():
    code = s("project_code", "")
    analysis = s("project_analysis", {})
    questions = s("project_questions", [])
    title = s("project_title", "Your project")

    topbar("Project created")
    code_box(code)

    st.title(title)

    if analysis.get("summary"):
        st.write(analysis["summary"])

    st.divider()

    col1, col2 = st.columns(2)

    if analysis.get("workstreams"):
        with col1:
            section("Suggested workstreams")
            bullet_list(analysis["workstreams"])

    if analysis.get("risks"):
        with col2:
            section("Key risks")
            bullet_list(analysis["risks"])

    st.markdown(
        f"<p style='color:#666;font-size:0.82rem'>"
        f"<strong>{len(questions)}</strong> alignment questions generated and ready.</p>",
        unsafe_allow_html=True,
    )
    st.write("")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Answer as team leader", use_container_width=True):
            project = get_project_by_code(code)
            go("questionnaire", project=project, questionnaire_name="")
    with col2:
        if st.button("Skip to dashboard", use_container_width=True):
            project = get_project_by_code(code)
            go("dashboard", project=project)


def page_join():
    topbar("Join")
    st.title("Join a project")
    st.write("Enter the project code you received from your team leader.")
    st.write("")

    with st.form("join_form"):
        code = st.text_input("Project code", placeholder="e.g. ABC123", max_chars=6)
        name = st.text_input("Your name", placeholder="e.g. Alice")
        submitted = st.form_submit_button("Continue")

    if submitted:
        if not code.strip() or not name.strip():
            st.error("Both project code and your name are required.")
            return

        project = get_project_by_code(code.strip().upper())
        if not project:
            st.error(f"No project found with code {code.strip().upper()}. Check and try again.")
            return

        if respondent_exists(project["id"], name.strip()):
            st.warning(
                f"A response from **{name.strip()}** already exists for this project. "
                "Submit again only if you want to replace your answers."
            )

        go("questionnaire", project=project, questionnaire_name=name.strip())


def page_questionnaire():
    project = s("project")
    name = s("questionnaire_name", "")

    if not project:
        go("home")
        return

    questions = project.get("questions", [])
    if not questions:
        st.error("No questions found for this project. Contact the project leader.")
        return

    topbar(f"{project['title']} · {project['code']}")

    if name:
        st.title(f"Hi {name}")
    else:
        st.title("Alignment questionnaire")

    st.write(
        "Answer each question based on your current understanding. "
        "There are no right or wrong answers — honest responses improve the cohesion analysis."
    )
    st.divider()

    with st.form("questionnaire_form"):
        answers = {}

        for i, q in enumerate(questions):
            qid = str(q.get("id", i + 1))
            st.markdown(f"**{i + 1}. {q['question']}**")

            q_type = q.get("type", "open")

            if q_type == "scale":
                val = st.select_slider(
                    f"scale_{qid}",
                    options=[1, 2, 3, 4, 5],
                    value=3,
                    format_func=lambda x: {1: "1 — Not at all", 2: "2", 3: "3 — Somewhat", 4: "4", 5: "5 — Very much"}.get(x, str(x)),
                    label_visibility="collapsed",
                )
                answers[qid] = str(val)

            elif q_type == "choice" and q.get("options"):
                val = st.radio(
                    f"choice_{qid}",
                    options=q["options"],
                    label_visibility="collapsed",
                    horizontal=len(q["options"]) <= 3,
                )
                answers[qid] = val or ""

            else:
                val = st.text_area(
                    f"open_{qid}",
                    placeholder=q.get("placeholder", "Your answer…"),
                    height=90,
                    label_visibility="collapsed",
                    key=f"ta_{qid}",
                )
                answers[qid] = val

            st.write("")

        if not name:
            st.divider()
            name_input = st.text_input("Your name", placeholder="Enter your name before submitting")
        else:
            name_input = name

        st.write("")
        submitted = st.form_submit_button("Submit responses")

    if submitted:
        final_name = name_input.strip() if name_input else ""
        if not final_name:
            st.error("Please enter your name.")
            return

        missing = []
        for i, q in enumerate(questions):
            qid = str(q.get("id", i + 1))
            if q.get("type", "open") == "open" and not answers.get(qid, "").strip():
                missing.append(i + 1)

        if missing:
            st.error(f"Please answer question{'s' if len(missing) > 1 else ''}: {', '.join(map(str, missing))}")
            return

        save_response(project["id"], final_name, answers)
        go(
            "submitted",
            submitted_project_code=project["code"],
            submitted_project_title=project["title"],
        )


def page_submitted():
    code = s("submitted_project_code", "")
    title = s("submitted_project_title", "the project")

    st.write("")
    st.title("Responses recorded")
    st.write(f"Your answers for **{title}** have been saved.")
    st.write(
        "The team leader can view the Project Cohesion Index once enough team members have responded."
    )

    st.write("")
    code_box(code, label="Project code")

    st.write("")
    if st.button("Back to home"):
        go("home")


def page_dashboard_entry():
    topbar("Dashboard")
    st.title("View team dashboard")
    st.write("Enter the project code to view PCI scores and recommendations.")
    st.write("")

    with st.form("dash_entry_form"):
        code = st.text_input("Project code", placeholder="e.g. ABC123", max_chars=6)
        submitted = st.form_submit_button("View dashboard")

    if submitted:
        if not code.strip():
            st.error("Enter a project code.")
            return
        project = get_project_by_code(code.strip().upper())
        if not project:
            st.error(f"No project found with code {code.strip().upper()}.")
            return
        go("dashboard", project=project)


def page_dashboard():
    project = s("project")
    if not project:
        go("home")
        return

    topbar(project["code"])

    responses = get_responses(project["id"])
    questions = project.get("questions", [])
    n = len(responses)
    team_size = project.get("team_size", 0)

    # Header row
    col_title, col_refresh = st.columns([5, 1])
    with col_title:
        st.title(project["title"])
    with col_refresh:
        st.write("")
        if st.button("↻", help="Refresh responses"):
            _rerun()

    if project.get("summary"):
        st.write(project["summary"])

    # Response counter
    pct = int((n / team_size * 100)) if team_size else 0
    st.markdown(
        f"<p style='color:#999;font-size:0.8rem;margin:0'>"
        f"{n} of {team_size} expected responses · {pct}% participation</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    if n == 0:
        st.info("No responses yet. Share the project code with your team.")
        return

    if n < 2:
        st.info("Need at least 2 responses to calculate PCI.")
        st.write("")
        section("Respondents")
        for r in responses:
            st.markdown(f"— {r['respondent']}")
        return

    # ── PCI calculation ──────────────────────────────────────────────────────
    pci_data = get_pci(project["id"])

    if not os.getenv("OPENAI_API_KEY", "").strip():
        st.warning("OPENAI_API_KEY not set — cannot calculate PCI.")
    else:
        btn_label = "Recalculate PCI" if pci_data else "Calculate PCI"
        if st.button(btn_label):
            with st.spinner("Analyzing team responses…"):
                try:
                    from utils.ai_engine import calculate_pci as ai_pci

                    result = ai_pci(project["title"], project["brief"], questions, responses)
                    raw_scores = result.get("scores", {})

                    dims = ["group_alignment", "priority_alignment", "role_clarity", "skill_coverage", "tool_cohesion"]
                    scores = {d: float(raw_scores.get(d, 70)) for d in dims}

                    save_pci(
                        project["id"],
                        scores,
                        result.get("alignment_gaps", []),
                        result.get("discussion_topics", []),
                        result.get("recommendations", []),
                    )
                    pci_data = get_pci(project["id"])
                    _rerun()
                except Exception as exc:
                    st.error(f"Error: {exc}")

    # ── PCI display ──────────────────────────────────────────────────────────
    if pci_data:
        pci_hero(pci_data["pci_score"])

        if pci_data.get("calculated_at"):
            try:
                dt = datetime.fromisoformat(pci_data["calculated_at"])
                st.markdown(
                    f"<p style='color:#bbb;font-size:0.72rem;margin-top:-0.75rem;margin-bottom:1rem'>"
                    f"Calculated {dt.strftime('%b %d at %H:%M')}</p>",
                    unsafe_allow_html=True,
                )
            except Exception:
                pass

        section("Dimension breakdown")
        dim_bar("Group Alignment", pci_data["group_alignment"], "25%")
        dim_bar("Priority Alignment", pci_data["priority_alignment"], "25%")
        dim_bar("Role Clarity", pci_data["role_clarity"], "20%")
        dim_bar("Skill Coverage", pci_data["skill_coverage"], "15%")
        dim_bar("Tool Cohesion", pci_data["tool_cohesion"], "15%")

        st.divider()

        if pci_data.get("gaps"):
            section("Alignment gaps")
            bullet_list(pci_data["gaps"])

        if pci_data.get("discussion_topics"):
            section("Recommended discussion topics")
            numbered_list(pci_data["discussion_topics"])

        if pci_data.get("recommendations"):
            section("Action items")
            bullet_list(pci_data["recommendations"])

        st.divider()

    # ── Respondents ──────────────────────────────────────────────────────────
    section(f"Respondents ({n})")
    for r in responses:
        try:
            dt = datetime.fromisoformat(r["submitted_at"])
            time_str = dt.strftime("%b %d, %H:%M")
        except Exception:
            time_str = ""

        suffix = (
            f"&nbsp;<span style='color:#bbb;font-size:0.75rem'>· {time_str}</span>"
            if time_str else ""
        )
        st.markdown(
            f"<p style='margin:0.15rem 0;color:#333;font-size:0.875rem'>— {r['respondent']}{suffix}</p>",
            unsafe_allow_html=True,
        )


# ── Router ────────────────────────────────────────────────────────────────────
ROUTES = {
    "home": page_home,
    "create": page_create,
    "created": page_created,
    "join": page_join,
    "questionnaire": page_questionnaire,
    "submitted": page_submitted,
    "dashboard_entry": page_dashboard_entry,
    "dashboard": page_dashboard,
}

current = st.session_state.get("page", "home")
ROUTES.get(current, page_home)()

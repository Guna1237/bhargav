import streamlit as st
from dotenv import load_dotenv
load_dotenv()

from services.common import inject_css, sidebar_project
from services.data_service import (
    get_project, get_project_by_code, save_response, respondent_exists,
)

st.set_page_config(page_title="Alignment — SquadSync", layout="centered", initial_sidebar_state="expanded")
inject_css()
sidebar_project()

st.markdown("<p style='font-size:0.78rem;color:#9ca3af'>SquadSync · Alignment</p>", unsafe_allow_html=True)

# ── Load project ──────────────────────────────────────────────────────────────
pid = st.session_state.get("project_id")
project = get_project(pid) if pid else None

if not project:
    st.title("Join a project")
    st.write("Enter the project code to access the alignment questions.")
    with st.form("join_form"):
        code = st.text_input("Project code", max_chars=6, placeholder="e.g. ABC123")
        name = st.text_input("Your name", placeholder="e.g. Alice")
        ok = st.form_submit_button("Continue")
    if ok:
        if not code.strip() or not name.strip():
            st.error("Both fields are required.")
        else:
            p = get_project_by_code(code.strip())
            if not p:
                st.error("No project found with code {}.".format(code.strip().upper()))
            else:
                st.session_state["project_id"] = p["id"]
                st.session_state["respondent_name"] = name.strip()
                from services.common import _rerun
                _rerun()
    st.stop()

questions = project.get("questions", [])
if not questions:
    st.warning("No questions for this project yet. The leader needs to complete project creation first.")
    st.stop()

# ── Respondent name ───────────────────────────────────────────────────────────
preset_name = st.session_state.get("respondent_name", "")

st.title("Alignment questionnaire")
st.write(
    "**{}** — answer each question based on your current understanding. "
    "Honest responses improve the cohesion analysis.".format(project["title"])
)
st.markdown(
    "<p style='color:#9ca3af;font-size:0.8rem'>{} questions · ~5 minutes</p>".format(len(questions)),
    unsafe_allow_html=True,
)
st.divider()

with st.form("questionnaire_form"):
    if not preset_name:
        respondent = st.text_input("Your name", placeholder="Enter your name")
    else:
        respondent = preset_name
        st.markdown(
            "<p style='font-size:0.875rem;color:#6b7280;margin-bottom:0.5rem'>Answering as <strong>{}</strong></p>".format(preset_name),
            unsafe_allow_html=True,
        )

    answers = {}
    for i, q in enumerate(questions):
        qid = str(q.get("id", i + 1))
        st.write("")
        st.markdown(
            "<p style='font-size:0.875rem;font-weight:600;color:#0f0f0f;margin-bottom:0.2rem'>"
            "{}/{}. {}</p>".format(i + 1, len(questions), q["question"]),
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='font-size:0.72rem;color:#9ca3af;margin-top:-0.2rem;margin-bottom:0.4rem'>"
            "{}</p>".format(q.get("dimension", "").replace("_", " ").title()),
            unsafe_allow_html=True,
        )

        q_type = q.get("type", "open")

        if q_type == "slider":
            val = st.select_slider(
                "q_{}".format(qid),
                options=[1, 2, 3, 4, 5],
                value=3,
                format_func=lambda x: {
                    1: "1 — Not at all", 2: "2", 3: "3 — Somewhat", 4: "4", 5: "5 — Completely"
                }.get(x, str(x)),
                label_visibility="collapsed",
            )
            answers[qid] = str(val)

        elif q_type == "mcq" and q.get("options"):
            val = st.radio(
                "q_{}".format(qid),
                options=q["options"],
                label_visibility="collapsed",
                horizontal=len(q["options"]) <= 3,
            )
            answers[qid] = val or ""

        else:
            val = st.text_area(
                "q_{}".format(qid),
                placeholder=q.get("placeholder", "Your answer…"),
                height=85,
                label_visibility="collapsed",
                key="ta_{}".format(qid),
            )
            answers[qid] = val

    st.write("")
    submitted = st.form_submit_button("Submit responses")

if submitted:
    final_name = (respondent or "").strip()
    if not final_name:
        st.error("Enter your name before submitting.")
        st.stop()

    missing = [
        i + 1 for i, q in enumerate(questions)
        if q.get("type", "open") == "open"
        and not answers.get(str(q.get("id", i + 1)), "").strip()
    ]
    if missing:
        st.error("Please answer question{}: {}".format(
            "s" if len(missing) > 1 else "",
            ", ".join(map(str, missing)),
        ))
        st.stop()

    save_response(project["id"], final_name, answers)
    st.session_state["respondent_name"] = final_name

    st.success("Responses recorded for {}.".format(final_name))
    st.info("The team leader can view the PCI Dashboard once more responses are in.")
    st.markdown(
        "<p style='font-size:0.875rem'>Project code: "
        "<strong style='letter-spacing:0.1em'>{}</strong></p>".format(project["code"]),
        unsafe_allow_html=True,
    )

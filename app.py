import streamlit as st
from dotenv import load_dotenv
load_dotenv()

from services.common import inject_css, sidebar_project, _rerun
from services.data_service import get_project_by_code

st.set_page_config(page_title="SquadSync", layout="centered", initial_sidebar_state="expanded")
inject_css()
sidebar_project()

# ── Brand ─────────────────────────────────────────────────────────────────────
st.markdown(
    "<p style='font-size:0.78rem;color:#9ca3af;margin-bottom:0.1rem'>SquadSync</p>",
    unsafe_allow_html=True,
)
st.title("Project cohesion for temporary teams")
st.write(
    "Align your team on goals, responsibilities, and priorities before execution begins. "
    "Measure cohesion. Get AI-powered recommendations."
)

st.divider()

# ── Create vs Join ─────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    st.markdown("**New project**")
    st.write("Start a project, invite your team, and get an AI analysis of your brief.")
    st.markdown("Use **Create Project** in the sidebar →")

with col2:
    st.markdown("**Join a project**")
    st.write("Have a project code? Enter it below to load the project and answer alignment questions.")

    with st.form("join_form"):
        code = st.text_input("Project code", placeholder="e.g. ABC123", max_chars=6)
        name = st.text_input("Your name", placeholder="e.g. Alice")
        joined = st.form_submit_button("Load project")

    if joined:
        if not code.strip():
            st.error("Enter a project code.")
        else:
            project = get_project_by_code(code.strip())
            if not project:
                st.error("No project found with code {}.".format(code.strip().upper()))
            else:
                st.session_state["project_id"] = project["id"]
                if name.strip():
                    st.session_state["respondent_name"] = name.strip()
                st.success("Loaded: {}".format(project["title"]))
                st.info("Go to **Alignment** in the sidebar to answer the questions.")

st.divider()

# ── Active project indicator ───────────────────────────────────────────────────
pid = st.session_state.get("project_id")
if pid:
    from services.data_service import get_project
    project = get_project(pid)
    if project:
        st.markdown("**Active project**")
        st.markdown(
            "<p style='margin:0;font-size:0.875rem'><strong>{}</strong> &nbsp;"
            "<span style='color:#9ca3af;letter-spacing:0.1em'>{}</span></p>".format(
                project["title"], project["code"]
            ),
            unsafe_allow_html=True,
        )
        responses_count = len(__import__("services.data_service", fromlist=["get_responses"]).get_responses(pid))
        st.markdown(
            "<p style='color:#9ca3af;font-size:0.8rem;margin-top:0.25rem'>"
            "{} of {} responses received</p>".format(responses_count, project["team_size"]),
            unsafe_allow_html=True,
        )

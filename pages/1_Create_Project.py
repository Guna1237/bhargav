import streamlit as st
from dotenv import load_dotenv
load_dotenv()

from services.common import inject_css, sidebar_project, code_box
from services.data_service import create_project, set_analysis, get_project
from services.openai_service import analyze_project, generate_questions

st.set_page_config(page_title="Create Project — SquadSync", layout="centered", initial_sidebar_state="expanded")
inject_css()
sidebar_project()

st.markdown("<p style='font-size:0.78rem;color:#9ca3af'>SquadSync · Create Project</p>", unsafe_allow_html=True)
st.title("Create a project")
st.write("Describe your project. The AI will analyze the brief and generate alignment questions for your team.")
st.divider()

with st.form("create_form"):
    title = st.text_input("Project name", placeholder="e.g. AI Healthcare Triage System")
    description = st.text_area(
        "Project description",
        placeholder=(
            "Describe the problem you're solving, what you need to build, "
            "key constraints, and any relevant context. More detail → better questions."
        ),
        height=160,
    )
    col1, col2 = st.columns(2)
    with col1:
        timeline = st.text_input("Timeline", placeholder="e.g. 24 hours, 2 weeks")
    with col2:
        team_size = st.number_input("Expected team size", min_value=2, max_value=20, value=4, step=1)

    submitted = st.form_submit_button("Analyze and create project")

if submitted:
    errors = []
    if not title.strip():
        errors.append("Project name is required.")
    if not description.strip() or len(description.strip()) < 30:
        errors.append("Description must be at least 30 characters.")
    if not timeline.strip():
        errors.append("Timeline is required.")
    for e in errors:
        st.error(e)

    if not errors:
        with st.spinner("Analyzing project brief…"):
            try:
                pid, code = create_project(
                    title.strip(), description.strip(),
                    timeline.strip(), int(team_size),
                )
                analysis = analyze_project(title.strip(), description.strip(), timeline.strip(), int(team_size))
                questions = generate_questions(
                    title.strip(), description.strip(), timeline.strip(),
                    int(team_size), analysis.get("workstreams", []),
                )
                set_analysis(pid, analysis, questions)
                st.session_state["project_id"] = pid
                st.session_state.pop("respondent_name", None)

                st.success("Project created.")
                code_box(code)
                st.info("Share this code with your team. Go to **Project Analysis** in the sidebar to review the AI output.")

            except Exception as exc:
                st.error("Error: {}".format(exc))

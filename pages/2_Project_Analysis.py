import streamlit as st
from dotenv import load_dotenv
load_dotenv()

from services.common import inject_css, sidebar_project, require_project, bullet_list, code_box

st.set_page_config(page_title="Project Analysis — SquadSync", layout="centered", initial_sidebar_state="expanded")
inject_css()
sidebar_project()

project = require_project()
analysis = project.get("analysis") or {}
questions = project.get("questions") or []

st.markdown("<p style='font-size:0.78rem;color:#9ca3af'>SquadSync · Project Analysis</p>", unsafe_allow_html=True)
st.title(project["title"])
code_box(project["code"])

if not analysis:
    st.warning("No AI analysis yet. Go to **Create Project** and submit your project brief.")
    st.stop()

# ── Summary ───────────────────────────────────────────────────────────────────
st.write(analysis.get("summary", ""))
st.divider()

# ── Four cards in two columns ─────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Suggested workstreams**")
    for ws in analysis.get("workstreams", []):
        st.markdown(
            "<div style='border:1px solid #e5e7eb;border-radius:4px;padding:0.6rem 0.85rem;margin-bottom:0.5rem;"
            "font-size:0.85rem;color:#0f0f0f'>{}</div>".format(ws),
            unsafe_allow_html=True,
        )
    st.write("")

    st.markdown("**Deliverables**")
    bullet_list(analysis.get("deliverables", []))

with col2:
    st.markdown("**Suggested roles**")
    for role in analysis.get("suggested_roles", []):
        st.markdown(
            "<div style='border:1px solid #e5e7eb;border-radius:4px;padding:0.6rem 0.85rem;margin-bottom:0.5rem;"
            "font-size:0.85rem;color:#0f0f0f'>{}</div>".format(role),
            unsafe_allow_html=True,
        )
    st.write("")

    st.markdown("**Risks**")
    for risk in analysis.get("risks", []):
        st.markdown(
            "<p style='margin:0.15rem 0;font-size:0.875rem'>"
            "<span style='color:#dc2626;font-weight:600'>&#9650;</span> {}</p>".format(risk),
            unsafe_allow_html=True,
        )

st.divider()

# ── Questions preview ──────────────────────────────────────────────────────────
if questions:
    st.markdown("**{} alignment questions generated**".format(len(questions)))
    st.write("Team members can join with the project code and answer these questions.")
    with st.expander("Preview questions"):
        for i, q in enumerate(questions, 1):
            st.markdown(
                "<p style='margin:0.4rem 0;font-size:0.875rem'><strong>{}</strong>. {}"
                " <span style='color:#9ca3af;font-size:0.75rem'>[{}]</span></p>".format(
                    i, q["question"], q.get("dimension", "")
                ),
                unsafe_allow_html=True,
            )
else:
    st.warning("No questions generated. Re-create the project to trigger question generation.")

st.write("")
st.write("Next: go to **Alignment** in the sidebar to answer the questions as the team leader.")

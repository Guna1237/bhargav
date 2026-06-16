import streamlit as st
from dotenv import load_dotenv
load_dotenv()

from services.common import inject_css, sidebar_project, require_project, score_color
from services.data_service import get_responses, set_workspace

st.set_page_config(page_title="Workspace — SquadSync", layout="centered", initial_sidebar_state="expanded")
inject_css()
sidebar_project()

project = require_project()
analysis = project.get("analysis") or {}
workspace = project.get("workspace") or {"workstreams": [], "assignments": {}}
responses = get_responses(project["id"])
team_members = [r["respondent"] for r in responses]
suggested_ws = analysis.get("workstreams", [])

st.markdown("<p style='font-size:0.78rem;color:#9ca3af'>SquadSync · Workspace</p>", unsafe_allow_html=True)
st.title("Workspace")
st.write("Assign ownership to workstreams. Changes are saved automatically.")
st.divider()

if not team_members:
    st.info("No team members have submitted responses yet. Share the project code so your team can complete alignment.")

# ── Workstreams ───────────────────────────────────────────────────────────────
# Build current workstream list (start with saved, or populate from AI suggestions)
current_ws = workspace.get("workstreams") or []
if not current_ws and suggested_ws:
    current_ws = [{"name": ws, "description": "", "owner": ""} for ws in suggested_ws]

assignments = workspace.get("assignments", {})

st.markdown("**Workstreams**")
st.markdown(
    "<p style='font-size:0.8rem;color:#9ca3af;margin-top:-0.5rem'>"
    "Suggested by AI · edit names and assign owners</p>",
    unsafe_allow_html=True,
)
st.write("")

member_options = ["Unassigned"] + team_members
updated_ws = []

for i, ws in enumerate(current_ws):
    with st.expander(ws.get("name", "Workstream {}".format(i + 1)), expanded=True):
        col1, col2 = st.columns([3, 2])
        with col1:
            name = st.text_input(
                "Name", value=ws.get("name", ""), key="ws_name_{}".format(i),
                label_visibility="collapsed",
            )
            desc = st.text_input(
                "Description (optional)", value=ws.get("description", ""),
                placeholder="What does this workstream cover?",
                key="ws_desc_{}".format(i),
            )
        with col2:
            owner = st.selectbox(
                "Owner",
                options=member_options,
                index=member_options.index(ws.get("owner", "Unassigned"))
                if ws.get("owner", "Unassigned") in member_options else 0,
                key="ws_owner_{}".format(i),
            )
        updated_ws.append({"name": name, "description": desc, "owner": owner})

st.write("")

# ── Add custom workstream ──────────────────────────────────────────────────────
with st.expander("+ Add workstream"):
    with st.form("add_ws_form"):
        new_name = st.text_input("Workstream name", placeholder="e.g. Data Pipeline")
        new_desc = st.text_input("Description", placeholder="Optional")
        add_ok = st.form_submit_button("Add")
    if add_ok and new_name.strip():
        updated_ws.append({"name": new_name.strip(), "description": new_desc.strip(), "owner": "Unassigned"})

st.divider()

# ── Save ──────────────────────────────────────────────────────────────────────
if st.button("Save workspace", use_container_width=False):
    new_workspace = {
        "workstreams": updated_ws,
        "assignments": {ws["name"]: ws["owner"] for ws in updated_ws if ws["owner"] != "Unassigned"},
    }
    set_workspace(project["id"], new_workspace)
    st.success("Workspace saved.")

# ── Summary view ──────────────────────────────────────────────────────────────
if updated_ws:
    st.divider()
    st.markdown("**Ownership map**")
    for ws in updated_ws:
        owner = ws.get("owner", "Unassigned")
        badge_color = "#f3f4f6" if owner == "Unassigned" else "#dcfce7"
        text_color = "#6b7280" if owner == "Unassigned" else "#15803d"
        st.markdown(
            "<div style='display:flex;justify-content:space-between;align-items:center;"
            "padding:0.6rem 0;border-bottom:1px solid #f3f4f6'>"
            "<span style='font-size:0.875rem;color:#0f0f0f'>{}</span>"
            "<span style='font-size:0.78rem;padding:0.2rem 0.6rem;border-radius:3px;"
            "background:{};color:{}'>{}</span>"
            "</div>".format(ws["name"], badge_color, text_color, owner),
            unsafe_allow_html=True,
        )

import streamlit as st
from dotenv import load_dotenv
load_dotenv()

from services.common import (
    inject_css, sidebar_project, require_project,
    pci_hero, dim_bar, bullet_list, numbered_list, score_color, _rerun,
)
from services.data_service import get_responses, get_scores, save_scores
from services.pci_service import LABELS, build_pci_record
from datetime import datetime

st.set_page_config(page_title="PCI Dashboard — SquadSync", layout="centered", initial_sidebar_state="expanded")
inject_css()
sidebar_project()

project = require_project()
responses = get_responses(project["id"])
questions = project.get("questions", [])
scores_record = get_scores(project["id"])
pci_data = scores_record.get("pci") if scores_record else None

n = len(responses)
team_size = project.get("team_size", 0)

st.markdown("<p style='font-size:0.78rem;color:#9ca3af'>SquadSync · PCI Dashboard</p>", unsafe_allow_html=True)

col_title, col_btn = st.columns([4, 1])
with col_title:
    st.title(project["title"])
with col_btn:
    st.write("")
    if st.button("↻ Refresh"):
        _rerun()

pct = int(n / team_size * 100) if team_size else 0
st.markdown(
    "<p style='color:#9ca3af;font-size:0.8rem;margin:0'>"
    "{} of {} responses · {}% participation</p>".format(n, team_size, pct),
    unsafe_allow_html=True,
)
st.divider()

if n == 0:
    st.info("No responses yet. Share the project code with your team.")
    st.stop()

if n < 2:
    st.info("Need at least 2 responses to calculate PCI.")
    st.markdown("**Respondents so far**")
    for r in responses:
        st.markdown("— {}".format(r["respondent"]))
    st.stop()

# ── Calculate PCI ─────────────────────────────────────────────────────────────
btn_label = "Recalculate PCI" if pci_data else "Calculate PCI"
if st.button(btn_label):
    with st.spinner("Analyzing {} responses…".format(n)):
        try:
            from services.openai_service import calculate_pci
            ai_result = calculate_pci(
                project["title"], project["description"], questions, responses
            )
            pci_data = build_pci_record(ai_result)
            save_scores(project["id"], pci_data)
            _rerun()
        except Exception as exc:
            st.error("Error: {}".format(exc))

if not pci_data:
    st.write("Click **Calculate PCI** above to generate the cohesion analysis.")
    st.stop()

# ── PCI Score ─────────────────────────────────────────────────────────────────
pci_hero(pci_data["pci_score"])

if scores_record and scores_record.get("updated_at"):
    try:
        dt = datetime.fromisoformat(scores_record["updated_at"])
        st.markdown(
            "<p style='color:#d1d5db;font-size:0.72rem;margin-top:-0.75rem;margin-bottom:1rem'>"
            "Calculated {}</p>".format(dt.strftime("%b %d at %H:%M")),
            unsafe_allow_html=True,
        )
    except Exception:
        pass

# ── Dimension Breakdown ────────────────────────────────────────────────────────
st.markdown("**Dimension breakdown**")
for key, (label, weight) in LABELS.items():
    dim_bar(label, pci_data["scores"].get(key, 0), weight)

st.divider()

# ── Gaps + Topics + Recommendations ───────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    if pci_data.get("alignment_gaps"):
        st.markdown("**Alignment gaps**")
        bullet_list(pci_data["alignment_gaps"])

    if pci_data.get("recommendations"):
        st.markdown("**Action items**")
        bullet_list(pci_data["recommendations"])

with col2:
    if pci_data.get("discussion_topics"):
        st.markdown("**Discussion topics**")
        numbered_list(pci_data["discussion_topics"])

st.divider()

# ── Respondents ───────────────────────────────────────────────────────────────
st.markdown("**Respondents ({}/{})**".format(n, team_size))
for r in responses:
    try:
        dt = datetime.fromisoformat(r["submitted_at"])
        ts = dt.strftime("%b %d, %H:%M")
    except Exception:
        ts = ""
    st.markdown(
        "<p style='margin:0.15rem 0;font-size:0.875rem;color:#374151'>&#8212; {}"
        "<span style='color:#d1d5db;font-size:0.75rem;margin-left:8px'>{}</span></p>".format(
            r["respondent"], ts
        ),
        unsafe_allow_html=True,
    )

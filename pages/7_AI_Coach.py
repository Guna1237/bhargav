import streamlit as st
from dotenv import load_dotenv
load_dotenv()

from services.common import inject_css, sidebar_project, require_project, bullet_list, numbered_list, _rerun
from services.data_service import get_scores, save_scores

st.set_page_config(page_title="AI Coach — SquadSync", layout="centered", initial_sidebar_state="expanded")
inject_css()
sidebar_project()

project = require_project()
scores_record = get_scores(project["id"])
pci_data = (scores_record or {}).get("pci")
ths_data = (scores_record or {}).get("ths")
coach_data = (scores_record or {}).get("coach")
integrations = project.get("integrations", {})

st.markdown("<p style='font-size:0.78rem;color:#9ca3af'>SquadSync · AI Coach</p>", unsafe_allow_html=True)
st.title("AI Coach")
st.write("Synthesized insights from your cohesion index, health score, and tool activity.")
st.divider()

if not pci_data:
    st.warning("Calculate the PCI first on the **PCI Dashboard** page.")
    st.stop()

# ── Generate ───────────────────────────────────────────────────────────────────
btn_label = "Regenerate coaching report" if coach_data else "Generate coaching report"
if st.button(btn_label):
    with st.spinner("Generating coaching report…"):
        try:
            signals = {}
            if integrations.get("github"):
                gh = integrations["github"]
                signals["github"] = {
                    "commits": gh.get("commit_count"),
                    "contributors": gh.get("contributor_count"),
                    "open_issues": gh.get("open_issues"),
                    "concentration": (
                        "{} has the majority of commits".format(
                            gh["contributor_breakdown"][0]["login"]
                        ) if gh.get("contributor_breakdown") else "N/A"
                    ),
                }
            if integrations.get("drive"):
                dr = integrations["drive"]
                signals["drive"] = {
                    "files": dr.get("file_count"),
                    "recent_edits": dr.get("recent_edits"),
                    "contributors": dr.get("contributor_count"),
                }
            if integrations.get("calendar"):
                cal = integrations["calendar"]
                signals["calendar"] = {
                    "upcoming_events": cal.get("upcoming_events"),
                    "has_review_meeting": cal.get("has_review_meeting"),
                    "has_deadline": cal.get("has_deadline"),
                }

            from services.openai_service import generate_coach
            coach_data = generate_coach(
                project["title"], pci_data, ths_data, signals
            )

            updated = scores_record or {}
            updated["coach"] = coach_data
            updated["project_id"] = project["id"]
            from services.data_service import _load, _save
            scores = _load("scores.json")
            scores[project["id"]] = updated
            _save("scores.json", scores)
            _rerun()

        except Exception as exc:
            st.error("Error: {}".format(exc))

if not coach_data:
    st.write("Click **Generate coaching report** above.")
    st.stop()

# ── Summary ────────────────────────────────────────────────────────────────────
if coach_data.get("summary"):
    st.markdown(
        "<div style='border-left:3px solid #0f0f0f;padding:0.75rem 1rem;margin-bottom:1.25rem;"
        "background:#fafafa;border-radius:0 4px 4px 0'>"
        "<p style='margin:0;font-size:0.9rem;color:#0f0f0f;line-height:1.65'>{}</p>"
        "</div>".format(coach_data["summary"]),
        unsafe_allow_html=True,
    )

st.divider()

col1, col2 = st.columns(2)

with col1:
    if coach_data.get("risks"):
        st.markdown("**Risks**")
        for risk in coach_data["risks"]:
            st.markdown(
                "<p style='margin:0.25rem 0;font-size:0.875rem'>"
                "<span style='color:#dc2626;font-weight:600'>&#9650;</span> {}</p>".format(risk),
                unsafe_allow_html=True,
            )
        st.write("")

    if coach_data.get("strengths"):
        st.markdown("**Strengths**")
        for s in coach_data["strengths"]:
            st.markdown(
                "<p style='margin:0.25rem 0;font-size:0.875rem'>"
                "<span style='color:#16a34a;font-weight:600'>&#10003;</span> {}</p>".format(s),
                unsafe_allow_html=True,
            )
        st.write("")

with col2:
    if coach_data.get("recommendations"):
        st.markdown("**Recommendations**")
        numbered_list(coach_data["recommendations"])

    if coach_data.get("discussion_topics"):
        st.markdown("**Discussion topics**")
        numbered_list(coach_data["discussion_topics"])

st.divider()

# ── Score summary row ──────────────────────────────────────────────────────────
from services.common import score_color, score_label
col1, col2, col3 = st.columns(3)

def _mini_score(col, label, score):
    c = score_color(score) if score else "#9ca3af"
    col.markdown(
        "<div style='border:1px solid #e5e7eb;border-radius:4px;padding:0.75rem;text-align:center'>"
        "<div style='font-size:0.68rem;text-transform:uppercase;letter-spacing:0.06em;color:#9ca3af'>{}</div>"
        "<div style='font-size:1.5rem;font-weight:700;color:{}'>{}</div>"
        "</div>".format(label, c, "{:.0f}".format(score) if score else "—"),
        unsafe_allow_html=True,
    )

_mini_score(col1, "PCI", pci_data.get("pci_score"))
_mini_score(col2, "THS", ths_data.get("ths_score") if ths_data else None)
_mini_score(col3, "Responses", len(__import__("services.data_service", fromlist=["get_responses"]).get_responses(project["id"])))

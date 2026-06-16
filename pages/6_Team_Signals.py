import streamlit as st
from dotenv import load_dotenv
load_dotenv()

from services.common import inject_css, sidebar_project, require_project, dim_bar, score_color, _rerun
from services.data_service import get_responses, get_scores, set_integration, save_ths
from services.ths_service import calculate_ths

st.set_page_config(page_title="Team Signals — SquadSync", layout="centered", initial_sidebar_state="expanded")
inject_css()
sidebar_project()

project = require_project()
responses = get_responses(project["id"])
scores_record = get_scores(project["id"])
integrations = project.get("integrations", {})

st.markdown("<p style='font-size:0.78rem;color:#9ca3af'>SquadSync · Team Signals</p>", unsafe_allow_html=True)
st.title("Team Signals")
st.write("Connect external tools to build the Team Health Score (THS).")
st.divider()

# ── GitHub ────────────────────────────────────────────────────────────────────
st.markdown("### Development Health")
gh_data = integrations.get("github", {})

with st.expander("GitHub — {}".format("Connected" if gh_data else "Not connected"), expanded=not gh_data):
    with st.form("github_form"):
        from services.common import get_secret
        gh_url = st.text_input(
            "Repository URL",
            value=gh_data.get("repo_url", ""),
            placeholder="https://github.com/owner/repo",
        )
        gh_token = st.text_input(
            "GitHub Token (optional — for private repos / higher rate limits)",
            value="",
            type="password",
            placeholder="ghp_...",
        )
        gh_ok = st.form_submit_button("Connect GitHub")

    if gh_ok and gh_url.strip():
        with st.spinner("Fetching GitHub data…"):
            try:
                from services.github_service import get_repo_stats
                token = gh_token.strip() or get_secret("GITHUB_TOKEN")
                stats = get_repo_stats(gh_url.strip(), token or None)
                stats["repo_url"] = gh_url.strip()
                set_integration(project["id"], "github", stats)
                st.success("GitHub connected.")
                _rerun()
            except Exception as exc:
                st.error("GitHub error: {}".format(exc))

if gh_data:
    cols = st.columns(4)
    metrics = [
        ("Commits", gh_data.get("commit_count", 0)),
        ("Contributors", gh_data.get("contributor_count", 0)),
        ("Open PRs", gh_data.get("open_prs", 0)),
        ("Open Issues", gh_data.get("open_issues", 0)),
    ]
    for col, (label, val) in zip(cols, metrics):
        col.metric(label, val)

    if gh_data.get("contributor_breakdown"):
        st.write("")
        st.markdown("**Contribution distribution**")
        total_contrib = sum(c["contributions"] for c in gh_data["contributor_breakdown"])
        for c in gh_data["contributor_breakdown"]:
            pct = c["contributions"] / max(total_contrib, 1) * 100
            st.markdown(
                "<div style='margin-bottom:0.5rem'>"
                "<div style='display:flex;justify-content:space-between;font-size:0.82rem;margin-bottom:0.2rem'>"
                "<span>{}</span><span style='color:#6b7280'>{} commits ({:.0f}%)</span></div>"
                "<div style='background:#f3f4f6;height:4px;border-radius:2px'>"
                "<div style='background:#0f0f0f;height:4px;border-radius:2px;width:{:.0f}%'></div></div>"
                "</div>".format(c["login"], c["contributions"], pct, pct),
                unsafe_allow_html=True,
            )

st.divider()

# ── Google Drive ──────────────────────────────────────────────────────────────
st.markdown("### Documentation Health")
drive_data = integrations.get("drive", {})

with st.expander("Google Drive — {}".format("Connected" if drive_data else "Not connected"), expanded=not drive_data):
    st.write("Requires a Google Cloud API key with the Drive API enabled and a **public** shared folder.")
    with st.form("drive_form"):
        folder_url = st.text_input(
            "Drive folder URL or ID",
            value=drive_data.get("folder_url", ""),
            placeholder="https://drive.google.com/drive/folders/FOLDER_ID",
        )
        gapi_key = st.text_input(
            "Google API Key",
            value="",
            type="password",
            placeholder="AIza...",
        )
        drive_ok = st.form_submit_button("Connect Drive")

    if drive_ok and folder_url.strip():
        with st.spinner("Fetching Drive data…"):
            try:
                folder_id = folder_url.strip().rstrip("/").split("/")[-1].split("?")[0]
                api_key = gapi_key.strip() or get_secret("GOOGLE_API_KEY")
                from services.drive_service import get_folder_stats
                stats = get_folder_stats(folder_id, api_key)
                stats["folder_url"] = folder_url.strip()
                set_integration(project["id"], "drive", stats)
                st.success("Drive connected.")
                _rerun()
            except Exception as exc:
                st.error("Drive error: {}".format(exc))

if drive_data:
    cols = st.columns(3)
    cols[0].metric("Files", drive_data.get("file_count", 0))
    cols[1].metric("Contributors", drive_data.get("contributor_count", 0))
    cols[2].metric("Recent edits (48h)", drive_data.get("recent_edits", 0))

st.divider()

# ── Google Calendar ───────────────────────────────────────────────────────────
st.markdown("### Planning Health")
cal_data = integrations.get("calendar", {})

with st.expander("Google Calendar — {}".format("Connected" if cal_data else "Not connected"), expanded=not cal_data):
    st.write("Requires a **public** Google Calendar and a Google API key with the Calendar API enabled.")
    with st.form("cal_form"):
        cal_id = st.text_input(
            "Calendar ID",
            value=cal_data.get("calendar_id", ""),
            placeholder="yourname@group.calendar.google.com",
        )
        cal_api_key = st.text_input(
            "Google API Key",
            value="",
            type="password",
            placeholder="AIza...",
        )
        cal_ok = st.form_submit_button("Connect Calendar")

    if cal_ok and cal_id.strip():
        with st.spinner("Fetching Calendar data…"):
            try:
                api_key = cal_api_key.strip() or get_secret("GOOGLE_API_KEY")
                from services.calendar_service import get_calendar_events
                stats = get_calendar_events(cal_id.strip(), api_key)
                stats["calendar_id"] = cal_id.strip()
                set_integration(project["id"], "calendar", stats)
                st.success("Calendar connected.")
                _rerun()
            except Exception as exc:
                st.error("Calendar error: {}".format(exc))

if cal_data:
    cols = st.columns(3)
    cols[0].metric("Upcoming events", cal_data.get("upcoming_events", 0))
    cols[1].metric("Has review meeting", "Yes" if cal_data.get("has_review_meeting") else "No")
    cols[2].metric("Has deadline", "Yes" if cal_data.get("has_deadline") else "No")

    if cal_data.get("events"):
        st.write("")
        st.markdown("**Upcoming (14 days)**")
        for e in cal_data["events"][:6]:
            badge = {"deadline": "#fee2e2", "review": "#fef3c7", "meeting": "#f3f4f6"}[e["type"]]
            st.markdown(
                "<div style='display:flex;justify-content:space-between;padding:0.4rem 0;"
                "border-bottom:1px solid #f3f4f6;font-size:0.85rem'>"
                "<span>{}</span>"
                "<span style='background:{};padding:0.1rem 0.5rem;border-radius:3px;font-size:0.75rem'>{}</span>"
                "</div>".format(e["title"], badge, e["date"]),
                unsafe_allow_html=True,
            )

st.divider()

# ── THS Calculation ───────────────────────────────────────────────────────────
st.markdown("### Team Health Score")

if st.button("Calculate THS"):
    with st.spinner("Calculating…"):
        ths = calculate_ths(
            responses=responses,
            team_size=project.get("team_size", len(responses)),
            github=integrations.get("github") or None,
            drive=integrations.get("drive") or None,
            calendar=integrations.get("calendar") or None,
        )
        save_ths(project["id"], ths)
        _rerun()

ths_data = (scores_record or {}).get("ths")
if ths_data:
    color = score_color(ths_data["ths_score"])
    st.markdown("""
<div style="border:1px solid #e5e7eb;border-radius:6px;padding:1.25rem 1.5rem;margin:0.75rem 0 1rem">
    <div style="font-size:0.68rem;text-transform:uppercase;letter-spacing:0.07em;color:#9ca3af;margin-bottom:0.25rem">
        Team Health Score
    </div>
    <div style="font-size:2.5rem;font-weight:700;color:{color};line-height:1;margin-bottom:0.5rem">
        {score:.0f}<span style="font-size:1rem;font-weight:400;color:#d1d5db"> / 100</span>
    </div>
</div>
""".format(color=color, score=ths_data["ths_score"]), unsafe_allow_html=True)

    components = ths_data.get("components", {})
    dim_bar("Participation", components.get("participation", 0), "30%")
    dim_bar("Contribution Activity", components.get("contribution_activity", 0), "30%")
    dim_bar("Ownership Activity", components.get("ownership_activity", 0), "20%")
    dim_bar("Workspace Activity", components.get("workspace_activity", 0), "20%")

    if ths_data.get("signals"):
        st.write("")
        st.markdown("**Signals detected**")
        for sig in ths_data["signals"]:
            st.markdown(
                "<p style='margin:0.2rem 0;font-size:0.875rem'>"
                "<span style='color:#d97706'>&#9650;</span> {}</p>".format(sig),
                unsafe_allow_html=True,
            )

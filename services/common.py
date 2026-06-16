import os
import streamlit as st


def inject_css():
    css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "styles.css")
    with open(css_path) as f:
        st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)


def get_secret(key, default=""):
    """Read from st.secrets first, then env, then .env file."""
    try:
        val = st.secrets.get(key, "")
        if val:
            return val.strip().strip('"').strip("'")
    except Exception:
        pass
    val = os.getenv(key, default).strip().strip('"').strip("'")
    # Fix Python 3.7 dotenv stripping 'sk' prefix from OpenAI keys
    if val.startswith("-"):
        val = "sk" + val
    return val


def sidebar_project():
    """Show active project badge in sidebar."""
    pid = st.session_state.get("project_id")
    if not pid:
        return
    from services.data_service import get_project
    project = get_project(pid)
    if not project:
        return
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Active project")
    st.sidebar.markdown(
        "<p style='font-weight:600;color:#0f0f0f;margin:0'>{}</p>".format(project["title"]),
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(
        "<p style='font-size:1.1rem;font-weight:700;letter-spacing:0.15em;color:#0f0f0f;margin:0.2rem 0 0'>{}</p>".format(project["code"]),
        unsafe_allow_html=True,
    )


def require_project():
    """Return project dict or stop page with a prompt."""
    pid = st.session_state.get("project_id")
    if not pid:
        st.warning("No project loaded. Go to **Create Project** or enter a project code on the home page.")
        st.stop()
    from services.data_service import get_project
    project = get_project(pid)
    if not project:
        st.warning("Project not found. It may have been cleared.")
        st.stop()
    return project


def score_color(score):
    if score >= 75:
        return "#16a34a"
    if score >= 55:
        return "#d97706"
    return "#dc2626"


def score_label(score):
    if score >= 75:
        return "Strong"
    if score >= 55:
        return "Moderate"
    return "Needs attention"


def pci_hero(score):
    color = score_color(score)
    label = "Strong cohesion" if score >= 75 else "Moderate cohesion — gaps identified" if score >= 55 else "Low cohesion — alignment needed before execution"
    st.markdown("""
<div style="border:1px solid #e5e7eb;border-radius:6px;padding:1.5rem;margin:0.75rem 0 1.25rem">
    <div style="font-size:0.68rem;text-transform:uppercase;letter-spacing:0.07em;color:#9ca3af;margin-bottom:0.3rem">
        Project Cohesion Index
    </div>
    <div style="font-size:2.75rem;font-weight:700;color:{color};line-height:1;margin-bottom:0.6rem">
        {score:.0f}<span style="font-size:1rem;font-weight:400;color:#d1d5db"> / 100</span>
    </div>
    <div style="background:#f3f4f6;height:5px;border-radius:3px;margin-bottom:0.6rem">
        <div style="background:{color};height:5px;border-radius:3px;width:{score}%"></div>
    </div>
    <div style="font-size:0.8rem;color:#6b7280">{label}</div>
</div>
""".format(color=color, score=score, label=label), unsafe_allow_html=True)


def dim_bar(label, score, weight):
    color = score_color(score)
    st.markdown("""
<div style="margin-bottom:0.9rem">
    <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:0.22rem">
        <span style="font-size:0.82rem;color:#374151">
            {label}
            <span style="color:#d1d5db;font-size:0.72rem;margin-left:4px">{weight}</span>
        </span>
        <span style="font-size:0.82rem;font-weight:600;color:{color}">{score:.0f}</span>
    </div>
    <div style="background:#f3f4f6;height:4px;border-radius:2px">
        <div style="background:{color};height:4px;border-radius:2px;width:{score}%"></div>
    </div>
</div>
""".format(label=label, weight=weight, color=color, score=score), unsafe_allow_html=True)


def code_box(code, label="Project code — share this with your team"):
    st.markdown("""
<div style="border:1.5px solid #0f0f0f;border-radius:6px;padding:1rem 1.25rem;display:inline-block;margin:0.5rem 0 1.25rem">
    <div style="font-size:0.68rem;text-transform:uppercase;letter-spacing:0.07em;color:#9ca3af;margin-bottom:0.2rem">{label}</div>
    <div style="font-size:2rem;font-weight:700;color:#0f0f0f;letter-spacing:0.18em">{code}</div>
</div>
""".format(label=label, code=code), unsafe_allow_html=True)


def bullet_list(items):
    for item in items:
        st.markdown(
            "<p style='margin:0.15rem 0;color:#4b5563'>&#8212; {}</p>".format(item),
            unsafe_allow_html=True,
        )
    st.write("")


def numbered_list(items):
    for i, item in enumerate(items, 1):
        st.markdown(
            "<p style='margin:0.15rem 0;color:#4b5563'>{}.&nbsp; {}</p>".format(i, item),
            unsafe_allow_html=True,
        )
    st.write("")


def info_card(title, value, sub=None):
    sub_html = "<div style='font-size:0.78rem;color:#6b7280;margin-top:0.2rem'>{}</div>".format(sub) if sub else ""
    st.markdown("""
<div style="border:1px solid #e5e7eb;border-radius:6px;padding:1rem 1.25rem">
    <div style="font-size:0.68rem;text-transform:uppercase;letter-spacing:0.07em;color:#9ca3af;margin-bottom:0.2rem">{title}</div>
    <div style="font-size:1.5rem;font-weight:700;color:#0f0f0f">{value}</div>
    {sub}
</div>
""".format(title=title, value=value, sub=sub_html), unsafe_allow_html=True)


def _rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

def calculate_ths(responses, team_size, github=None, drive=None, calendar=None):
    # Participation (30%): responses / expected team size
    n = len(responses)
    expected = max(team_size, 1)
    participation = min(100.0, n / expected * 100)

    # Contribution Activity (30%): GitHub commit distribution
    if github and github.get("contributor_breakdown"):
        contribs = [c["contributions"] for c in github["contributor_breakdown"]]
        total = sum(contribs)
        if total > 0:
            top = max(contribs)
            concentration = top / total
            # High concentration = low score (work bottlenecked to one person)
            contribution_activity = max(20.0, 100.0 - concentration * 80)
        else:
            contribution_activity = 40.0
    else:
        contribution_activity = participation  # fallback to participation proxy

    # Ownership Activity (20%): from workspace assignments
    if drive and drive.get("contributor_count", 0) > 1:
        ownership_activity = min(100.0, drive["contributor_count"] / expected * 90)
    else:
        ownership_activity = 50.0

    # Workspace Activity (20%): calendar meetings + drive edits
    workspace_activity = 50.0
    if calendar and calendar.get("upcoming_events", 0) > 0:
        workspace_activity = min(100.0, 50 + calendar["upcoming_events"] * 10)
    if drive and drive.get("recent_edits", 0) > 0:
        workspace_activity = min(100.0, workspace_activity + drive["recent_edits"] * 5)

    ths = (
        participation * 0.30
        + contribution_activity * 0.30
        + ownership_activity * 0.20
        + workspace_activity * 0.20
    )

    signals = []
    if participation < 60:
        signals.append("Only {:.0f}% of the team has responded to alignment questions.".format(participation))
    if github and github.get("contributor_breakdown"):
        contribs = [c["contributions"] for c in github["contributor_breakdown"]]
        if contribs:
            top_pct = max(contribs) / max(sum(contribs), 1) * 100
            if top_pct > 60:
                top_name = github["contributor_breakdown"][0]["login"]
                signals.append("{:.0f}% of commits are from one contributor ({}).".format(top_pct, top_name))
    if drive and drive.get("file_count", 0) == 0:
        signals.append("No files found in the connected Drive folder.")
    if calendar and calendar.get("upcoming_events", 0) == 0:
        signals.append("No upcoming meetings or milestones found in the calendar.")

    return {
        "ths_score": round(ths, 1),
        "components": {
            "participation": round(participation, 1),
            "contribution_activity": round(contribution_activity, 1),
            "ownership_activity": round(ownership_activity, 1),
            "workspace_activity": round(workspace_activity, 1),
        },
        "signals": signals,
    }

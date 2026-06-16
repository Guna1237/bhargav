WEIGHTS = {
    "group_alignment": 0.25,
    "priority_alignment": 0.25,
    "role_clarity": 0.20,
    "skill_coverage": 0.15,
    "tool_cohesion": 0.15,
}

LABELS = {
    "group_alignment": ("Group Alignment", "25%"),
    "priority_alignment": ("Priority Alignment", "25%"),
    "role_clarity": ("Role Clarity", "20%"),
    "skill_coverage": ("Skill Coverage", "15%"),
    "tool_cohesion": ("Tool Cohesion", "15%"),
}


def calculate_overall(scores):
    return round(sum(scores.get(k, 0) * w for k, w in WEIGHTS.items()), 1)


def build_pci_record(ai_result):
    raw = ai_result.get("scores", {})
    dims = list(WEIGHTS.keys())
    scores = {d: float(raw.get(d, 70)) for d in dims}
    overall = calculate_overall(scores)
    return {
        "pci_score": overall,
        "scores": scores,
        "alignment_gaps": ai_result.get("alignment_gaps", []),
        "discussion_topics": ai_result.get("discussion_topics", []),
        "recommendations": ai_result.get("recommendations", []),
    }

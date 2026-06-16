import os
import json
import requests

BASE_URL = "https://api.openai.com/v1/chat/completions"
MODEL = "gpt-4o-mini"


def _chat(messages, temperature=0.4):
    api_key = os.getenv("OPENAI_API_KEY", "").strip().strip('"').strip("'")
    # Python 3.7 dotenv strips 'sk' from keys starting with sk- — restore it
    if api_key.startswith("-"):
        api_key = "sk" + api_key
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set. Add it to your .env file.")

    try:
        resp = requests.post(
            BASE_URL,
            headers={
                "Authorization": "Bearer " + api_key,
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": messages,
                "response_format": {"type": "json_object"},
                "temperature": temperature,
            },
            timeout=60,
        )
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Cannot reach api.openai.com — check your internet connection.")
    except requests.exceptions.Timeout:
        raise RuntimeError("Request timed out after 60s. Try again.")

    if not resp.ok:
        body = resp.text[:400]
        raise RuntimeError("OpenAI error {}: {}".format(resp.status_code, body))

    data = resp.json()

    if "error" in data:
        raise RuntimeError("OpenAI: {}".format(data["error"].get("message", str(data["error"]))))

    if not data.get("choices"):
        raise RuntimeError("Unexpected response: {}".format(str(data)[:300]))

    return json.loads(data["choices"][0]["message"]["content"])


def analyze_project(title, brief, timeline, team_size):
    return _chat(
        [
            {
                "role": "user",
                "content": (
                    "Analyze this project brief and return JSON.\n\n"
                    "Project: {title}\n"
                    "Brief: {brief}\n"
                    "Timeline: {timeline}\n"
                    "Team size: {team_size}\n\n"
                    "Return exactly this JSON structure:\n"
                    '{{\n'
                    '  "summary": "2-3 sentences describing what the project involves and its core challenge",\n'
                    '  "workstreams": ["workstream 1", "workstream 2", "workstream 3", "workstream 4"],\n'
                    '  "risks": ["risk 1", "risk 2", "risk 3"],\n'
                    '  "deliverables": ["deliverable 1", "deliverable 2", "deliverable 3"]\n'
                    "}}\n\n"
                    "Be specific to this project. Max 4 workstreams. Risks must be concrete."
                ).format(title=title, brief=brief, timeline=timeline, team_size=team_size),
            }
        ],
        temperature=0.4,
    )


def generate_questions(title, brief, timeline, team_size, workstreams):
    ws = ", ".join(workstreams) if workstreams else "not specified"
    result = _chat(
        [
            {
                "role": "user",
                "content": (
                    "Generate exactly 8 alignment questions for this project team.\n\n"
                    "Project: {title}\n"
                    "Brief: {brief}\n"
                    "Timeline: {timeline}\n"
                    "Team size: {team_size}\n"
                    "Suggested workstreams: {ws}\n\n"
                    "Questions must be specific to THIS project, not generic.\n"
                    "They should reveal real alignment gaps between team members.\n\n"
                    "Return JSON:\n"
                    '{{\n'
                    '  "questions": [\n'
                    '    {{\n'
                    '      "id": 1,\n'
                    '      "question": "question text specific to this project",\n'
                    '      "type": "open",\n'
                    '      "dimension": "group_alignment",\n'
                    '      "placeholder": "e.g. a short example answer"\n'
                    '    }}\n'
                    "  ]\n"
                    "}}\n\n"
                    "Question types:\n"
                    '- "open": free text\n'
                    '- "scale": 1-5 rating\n'
                    '- "choice": multiple choice (add "options": ["A", "B", "C"])\n\n'
                    "Required order:\n"
                    "1. group_alignment (open) - understanding of core problem\n"
                    "2. group_alignment (open) - what success looks like\n"
                    "3. priority_alignment (open) - what to build first and why\n"
                    "4. priority_alignment (choice, 3 options) - highest-risk decision\n"
                    "5. role_clarity (open) - specific contribution this person will make\n"
                    "6. role_clarity (scale) - how clear is your role\n"
                    "7. skill_coverage (open) - specific skills they bring\n"
                    "8. tool_cohesion (choice, 3-4 options) - preferred communication style\n\n"
                    "Every question must reference specific aspects of THIS project."
                ).format(title=title, brief=brief, timeline=timeline, team_size=team_size, ws=ws),
            }
        ],
        temperature=0.5,
    )
    return result.get("questions", [])


def calculate_pci(project_title, project_brief, questions, responses):
    blocks = []
    for r in responses:
        lines = ["Respondent: " + r["respondent"]]
        for i, q in enumerate(questions):
            qid = str(q.get("id", i + 1))
            answer = r["answers"].get(qid, r["answers"].get(str(i), "No answer"))
            q_type = q.get("type", "open")
            if q_type == "scale":
                lines.append("  [{}] {}\n  Answer: {}/5".format(q["dimension"], q["question"], answer))
            else:
                lines.append("  [{}] {}\n  Answer: {}".format(q["dimension"], q["question"], answer))
        blocks.append("\n".join(lines))

    return _chat(
        [
            {
                "role": "user",
                "content": (
                    "Analyze team alignment responses and calculate the Project Cohesion Index.\n\n"
                    "Project: {title}\n"
                    "Brief: {brief}\n\n"
                    "Team responses:\n{responses}\n\n"
                    "Score each dimension 0-100 based on actual response content:\n"
                    "- group_alignment: consistency in understanding project goals\n"
                    "- priority_alignment: agreement on what to build first\n"
                    "- role_clarity: how clearly each person knows their role\n"
                    "- skill_coverage: whether collective skills cover project needs\n"
                    "- tool_cohesion: alignment on communication preferences\n\n"
                    "Return JSON:\n"
                    '{{\n'
                    '  "scores": {{\n'
                    '    "group_alignment": <0-100>,\n'
                    '    "priority_alignment": <0-100>,\n'
                    '    "role_clarity": <0-100>,\n'
                    '    "skill_coverage": <0-100>,\n'
                    '    "tool_cohesion": <0-100>\n'
                    "  }},\n"
                    '  "alignment_gaps": ["specific gap 1", "specific gap 2"],\n'
                    '  "discussion_topics": ["topic 1", "topic 2", "topic 3"],\n'
                    '  "recommendations": ["action 1", "action 2", "action 3"]\n'
                    "}}\n\n"
                    "Be specific — cite actual respondent differences, not generic advice."
                ).format(
                    title=project_title,
                    brief=project_brief,
                    responses="\n\n---\n\n".join(blocks),
                ),
            }
        ],
        temperature=0.3,
    )

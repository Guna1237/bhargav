import os
import json
import requests

_BASE = "https://api.openai.com/v1/chat/completions"
_MODEL = "gpt-4o-mini"
_PROMPTS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")


def _prompt(name, **kwargs):
    with open(os.path.join(_PROMPTS, name)) as f:
        return f.read().format(**kwargs)


def _key():
    from services.common import get_secret
    return get_secret("OPENAI_API_KEY")


def _chat(prompt, temperature=0.4):
    api_key = _key()
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set in .streamlit/secrets.toml or .env")

    try:
        resp = requests.post(
            _BASE,
            headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
            json={
                "model": _MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
                "temperature": temperature,
            },
            timeout=60,
        )
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Cannot reach api.openai.com — check your connection.")
    except requests.exceptions.Timeout:
        raise RuntimeError("Request timed out. Try again.")

    if not resp.ok:
        raise RuntimeError("OpenAI error {}: {}".format(resp.status_code, resp.text[:300]))

    data = resp.json()
    if "error" in data:
        raise RuntimeError(data["error"].get("message", str(data["error"])))
    if not data.get("choices"):
        raise RuntimeError("No response from OpenAI: {}".format(str(data)[:200]))

    return json.loads(data["choices"][0]["message"]["content"])


def analyze_project(title, description, timeline, team_size):
    return _chat(_prompt(
        "project_analysis.txt",
        title=title, description=description,
        timeline=timeline, team_size=team_size,
    ))


def generate_questions(title, description, timeline, team_size, workstreams):
    ws = ", ".join(workstreams) if workstreams else "not specified"
    result = _chat(_prompt(
        "question_generation.txt",
        title=title, description=description,
        timeline=timeline, team_size=team_size, workstreams=ws,
    ), temperature=0.5)
    return result.get("questions", [])


def calculate_pci(project_title, project_description, questions, responses):
    blocks = []
    for r in responses:
        lines = ["Respondent: " + r["respondent"]]
        for i, q in enumerate(questions):
            qid = str(q.get("id", i + 1))
            answer = r["answers"].get(qid, "No answer")
            q_type = q.get("type", "open")
            suffix = "/5" if q_type == "slider" else ""
            lines.append("  [{}] {}\n  Answer: {}{}".format(
                q.get("dimension", ""), q["question"], answer, suffix))
        blocks.append("\n".join(lines))

    return _chat(_prompt(
        "pci_analysis.txt",
        title=project_title,
        description=project_description,
        responses="\n\n---\n\n".join(blocks),
    ), temperature=0.3)


def generate_coach(project_title, pci_data, ths_data, signals):
    return _chat(_prompt(
        "recommendations.txt",
        title=project_title,
        pci_score=pci_data.get("pci_score", "N/A"),
        pci_breakdown=json.dumps(pci_data.get("scores", {}), indent=2),
        alignment_gaps="\n".join(pci_data.get("alignment_gaps", [])) or "None identified",
        ths_score=ths_data.get("ths_score", "N/A") if ths_data else "N/A",
        signals=json.dumps(signals, indent=2),
    ), temperature=0.4)

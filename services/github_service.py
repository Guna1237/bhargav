import requests


def _headers(token=None):
    h = {"Accept": "application/vnd.github.v3+json"}
    if token:
        h["Authorization"] = "token " + token.strip()
    return h


def _parse_repo(url):
    parts = url.rstrip("/").split("/")
    if "github.com" in url and len(parts) >= 2:
        return parts[-2], parts[-1]
    raise ValueError("Invalid GitHub URL. Expected: https://github.com/owner/repo")


def get_repo_stats(repo_url, token=None):
    owner, repo = _parse_repo(repo_url)
    h = _headers(token)
    base = "https://api.github.com/repos/{}/{}".format(owner, repo)

    def _get(path, params=None):
        r = requests.get(base + path, headers=h, params=params, timeout=15)
        if r.status_code == 404:
            raise ValueError("Repository not found or private. Add a GitHub token for private repos.")
        if r.status_code == 403:
            raise ValueError("GitHub rate limit hit. Add a GitHub token to increase limits.")
        return r.json() if r.ok else []

    info = _get("")
    commits = _get("/commits", {"per_page": 30})
    contributors = _get("/contributors", {"per_page": 10})
    prs_open = _get("/pulls", {"state": "open", "per_page": 20})
    prs_closed = _get("/pulls", {"state": "closed", "per_page": 20})
    issues = _get("/issues", {"state": "open", "per_page": 20})

    breakdown = []
    if isinstance(contributors, list):
        for c in contributors[:5]:
            breakdown.append({
                "login": c.get("login", "unknown"),
                "contributions": c.get("contributions", 0),
            })

    return {
        "repo": "{}/{}".format(owner, repo),
        "commit_count": len(commits) if isinstance(commits, list) else 0,
        "contributor_count": len(contributors) if isinstance(contributors, list) else 0,
        "open_prs": len(prs_open) if isinstance(prs_open, list) else 0,
        "closed_prs": len(prs_closed) if isinstance(prs_closed, list) else 0,
        "open_issues": info.get("open_issues_count", 0) if isinstance(info, dict) else 0,
        "last_push": info.get("pushed_at", "") if isinstance(info, dict) else "",
        "contributor_breakdown": breakdown,
    }

import requests


def get_folder_stats(folder_id, api_key):
    """
    Fetch public Google Drive folder metadata using the Drive API v3.
    folder_id: the ID from the Drive URL (after /folders/)
    api_key: Google Cloud API key with Drive API enabled
    """
    if not api_key:
        raise ValueError("Google API key required. Enable the Drive API in Google Cloud Console.")

    url = "https://www.googleapis.com/drive/v3/files"
    params = {
        "q": "'{}' in parents".format(folder_id),
        "fields": "files(id,name,modifiedTime,owners,lastModifyingUser)",
        "key": api_key,
        "pageSize": 50,
    }

    try:
        r = requests.get(url, params=params, timeout=15)
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Cannot reach Google APIs.")

    if not r.ok:
        body = r.json()
        msg = body.get("error", {}).get("message", r.text[:200])
        raise RuntimeError("Drive API error: {}".format(msg))

    files = r.json().get("files", [])

    contributors = set()
    for f in files:
        user = f.get("lastModifyingUser", {})
        name = user.get("displayName") or user.get("emailAddress")
        if name:
            contributors.add(name)

    # Recent edits: files modified in last 48h
    from datetime import datetime, timedelta
    cutoff = (datetime.utcnow() - timedelta(hours=48)).isoformat() + "Z"
    recent = [f for f in files if f.get("modifiedTime", "") >= cutoff]

    return {
        "file_count": len(files),
        "contributor_count": len(contributors),
        "contributors": list(contributors),
        "recent_edits": len(recent),
        "files": [{"name": f["name"], "modified": f.get("modifiedTime", "")} for f in files[:10]],
    }

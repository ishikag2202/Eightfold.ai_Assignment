import requests


def extract(username):
    """Extract candidate fields from a public GitHub profile via REST API."""
    if not username:
        return {}
    try:
        profile_resp = requests.get(
            f"https://api.github.com/users/{username}", timeout=5
        )
        if profile_resp.status_code != 200:
            print(f"[github_extractor] user not found or API error: {profile_resp.status_code}")
            return {}
        profile = profile_resp.json()

        repos_resp = requests.get(
            f"https://api.github.com/users/{username}/repos?per_page=30", timeout=5
        )
        repos = repos_resp.json() if repos_resp.status_code == 200 else []

        languages = set()
        if isinstance(repos, list):
            for repo in repos:
                if repo.get("language"):
                    languages.add(repo["language"])

        return {
            "full_name": (profile.get("name") or "").strip(),
            "headline": profile.get("bio") or None,
            "location_raw": profile.get("location") or None,
            "links": {"github": profile.get("html_url", "")},
            "skills": list(languages),
            "_source": "github_api",
        }
    except requests.RequestException as e:
        print(f"[github_extractor] request failed: {e}")
        return {}
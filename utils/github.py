"""GitHub API utilities for fetching repository data."""

import re
from datetime import datetime

import requests


def extract_repo_info(url: str) -> tuple[str, str] | None:
    """Extract owner and repo name from GitHub URL.
    
    Args:
        url: GitHub repository URL
        
    Returns:
        Tuple of (owner, repo) or None if URL is invalid
    """
    match = re.match(r"https?://github\.com/([^/]+)/([^/]+)/?", url)
    if match:
        return match.group(1), match.group(2)
    return None


def fetch_repo_data(owner: str, repo: str, token: str | None = None) -> dict | None:
    """Fetch repository data from GitHub API.
    
    Args:
        owner: Repository owner/organization
        repo: Repository name
        token: Optional GitHub API token for authentication
        
    Returns:
        Dictionary with repository data or None if fetch failed
    """
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # Fetch main repo data
    repo_url = f"https://api.github.com/repos/{owner}/{repo}"
    response = requests.get(repo_url, headers=headers, timeout=30)
    if response.status_code != 200:
        print(f"Failed to fetch {owner}/{repo}: {response.status_code}")
        return None

    data = response.json()

    # Fetch latest release for version and updated_at
    releases_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    release_response = requests.get(releases_url, headers=headers, timeout=30)
    version = "-"
    updated_at = "-"
    if release_response.status_code == 200:
        release_data = release_response.json()
        version = release_data.get("tag_name", "-")
        published_at = release_data.get("published_at", "")
        if published_at:
            dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            updated_at = dt.strftime("%Y-%m-%d")

    return {
        "name": data.get("name", repo),
        "full_name": data.get("full_name", f"{owner}/{repo}"),
        "url": data.get("html_url", f"https://github.com/{owner}/{repo}"),
        "description": data.get("description") or "-",
        "stars": data.get("stargazers_count", 0),
        "version": version,
        "updated_at": updated_at,
        "topics": data.get("topics", []),
    }

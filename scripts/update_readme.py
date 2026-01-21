#!/usr/bin/env python3
"""Scrape GitHub repository data and update README with a markdown table."""

import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path

import requests


def extract_repo_info(url: str) -> tuple[str, str] | None:
    """Extract owner and repo name from GitHub URL."""
    match = re.match(r"https?://github\.com/([^/]+)/([^/]+)/?", url)
    if match:
        return match.group(1), match.group(2)
    return None


def fetch_repo_data(owner: str, repo: str, token: str | None = None) -> dict | None:
    """Fetch repository data from GitHub API."""
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


def generate_markdown_table(repos: list[dict]) -> str:
    """Generate a markdown table from repository data."""
    # Filter out entries without full data (only have url)
    complete_repos = [r for r in repos if "stars" in r]
    
    if not complete_repos:
        return "_No repositories found._"

    # Sort by stars descending
    repos = sorted(complete_repos, key=lambda x: x["stars"], reverse=True)

    lines = [
        "| Repository | Description | ⭐ Stars | Version | Updated |",
        "|------------|-------------|-------|---------|---------|",
    ]

    for repo in repos:
        name_link = f"<a href=\"{repo['url']}\" target=\"_blank\">{repo['name']}</a>"
        description = repo["description"][:80] + "..." if len(repo["description"]) > 80 else repo["description"]
        stars = f"{repo['stars']:,}"
        lines.append(f"| {name_link} | {description} | {stars} | {repo['version']} | {repo['updated_at']} |")

    return "\n".join(lines)


def update_readme(table: str) -> None:
    """Update README.md with the generated table."""
    readme_path = "README.md"

    header = "# awesome-scraping\n\nA curated list of awesome scraping tools and libraries.\n\n"
    content = header + "## Repositories\n\n" + table + "\n"

    with open(readme_path, "w") as f:
        f.write(content)

    print(f"Updated {readme_path}")


def backup_urls_json() -> None:
    """Move current urls.json to history directory with timestamp suffix."""
    urls_path = Path("urls.json")
    history_dir = Path("history")
    
    if not urls_path.exists():
        print("No urls.json found to backup")
        return
    
    history_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = history_dir / f"urls_{timestamp}.json"
    
    shutil.move(urls_path, backup_path)
    print(f"Moved urls.json to {backup_path}")


def update_urls_json(repos: list[dict]) -> None:
    """Write updated repository data to urls.json."""
    urls_path = Path("urls.json")
    
    with open(urls_path, "w") as f:
        json.dump(repos, f, indent=4)
    
    print(f"Created new {urls_path} with {len(repos)} repositories")


def main() -> None:
    """Main function to orchestrate the scraping and README update."""
    token = os.environ.get("GITHUB_TOKEN")

    # Load URLs from urls.json
    with open("urls.json") as f:
        urls_data = json.load(f)

    # Backup current urls.json to history
    backup_urls_json()

    repos = []
    for item in urls_data:
        url = item.get("url", "")
        repo_info = extract_repo_info(url)
        if not repo_info:
            print(f"Invalid GitHub URL: {url}")
            continue

        owner, repo = repo_info
        print(f"Fetching data for {owner}/{repo}...")
        data = fetch_repo_data(owner, repo, token)
        if data:
            repos.append(data)
        else:
            # Keep original entry if fetch failed
            repos.append(item)

    # Write updated urls.json with fetched data
    update_urls_json(repos)

    # Generate table and update README
    table = generate_markdown_table(repos)
    update_readme(table)


if __name__ == "__main__":
    main()

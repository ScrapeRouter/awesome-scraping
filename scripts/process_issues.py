# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "requests",
# ]
# ///
"""Process GitHub issues to add new URLs to urls.json."""

import json
import os
import re
from pathlib import Path

import requests

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_REPOSITORY = os.environ["GITHUB_REPOSITORY"]
GITHUB_API = "https://api.github.com"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

# Pattern to match GitHub repo URLs
GITHUB_URL_PATTERN = re.compile(
    r"add\s+(https://github\.com/[\w.-]+/[\w.-]+)",
    re.IGNORECASE,
)


def load_urls() -> list[dict]:
    """Load existing URLs from urls.json."""
    urls_path = Path("urls.json")
    if urls_path.exists():
        return json.loads(urls_path.read_text())
    return []


def save_urls(urls: list[dict]) -> None:
    """Save URLs to urls.json."""
    urls_path = Path("urls.json")
    urls_path.write_text(json.dumps(urls, indent=4) + "\n")


def get_existing_urls(urls_data: list[dict]) -> set[str]:
    """Extract all URLs from the urls data, normalized."""
    existing = set()
    for item in urls_data:
        url = item.get("url", "").rstrip("/").lower()
        if url:
            existing.add(url)
    return existing


def normalize_url(url: str) -> str:
    """Normalize a GitHub URL for comparison."""
    return url.rstrip("/").lower()


def get_open_issues() -> list[dict]:
    """Fetch all open issues from the repository."""
    url = f"{GITHUB_API}/repos/{GITHUB_REPOSITORY}/issues"
    params = {"state": "open", "per_page": 100}
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    # Filter out pull requests (they also appear in issues endpoint)
    return [issue for issue in response.json() if "pull_request" not in issue]


def extract_github_url(issue: dict) -> str | None:
    """Extract GitHub repo URL from issue title or body."""
    title = issue.get("title", "")
    body = issue.get("body", "") or ""
    
    # Search in title first, then body
    for text in [title, body]:
        match = GITHUB_URL_PATTERN.search(text)
        if match:
            return match.group(1)
    return None


def comment_on_issue(issue_number: int, comment: str) -> None:
    """Add a comment to an issue."""
    url = f"{GITHUB_API}/repos/{GITHUB_REPOSITORY}/issues/{issue_number}/comments"
    data = {"body": comment}
    response = requests.post(url, headers=HEADERS, json=data)
    response.raise_for_status()


def close_issue(issue_number: int) -> None:
    """Close an issue."""
    url = f"{GITHUB_API}/repos/{GITHUB_REPOSITORY}/issues/{issue_number}"
    data = {"state": "closed"}
    response = requests.patch(url, headers=HEADERS, json=data)
    response.raise_for_status()


def process_issue(issue: dict, urls_data: list[dict], existing_urls: set[str]) -> bool:
    """
    Process a single issue.
    
    Returns True if a new URL was added, False otherwise.
    """
    issue_number = issue["number"]
    github_url = extract_github_url(issue)
    
    if not github_url:
        # Not an "add" issue, skip it
        return False
    
    normalized_url = normalize_url(github_url)
    
    print(f"Processing issue #{issue_number}: found URL {github_url}")
    
    if normalized_url in existing_urls:
        # Duplicate URL
        comment = (
            f"Thanks for the suggestion!\n\n"
            f"However, **{github_url}** is already in our list.\n\n"
            f"Closing this issue as a duplicate."
        )
        comment_on_issue(issue_number, comment)
        close_issue(issue_number)
        print(f"  -> Duplicate, closed issue #{issue_number}")
        return False
    
    # Add new URL
    urls_data.append({"url": github_url})
    existing_urls.add(normalized_url)
    
    comment = (
        f"Thanks for the suggestion!\n\n"
        f"**{github_url}** has been added to the list.\n\n"
        f"The README will be updated automatically."
    )
    comment_on_issue(issue_number, comment)
    close_issue(issue_number)
    print(f"  -> Added, closed issue #{issue_number}")
    return True


def main() -> None:
    """Main entry point."""
    print(f"Processing issues for {GITHUB_REPOSITORY}")
    
    urls_data = load_urls()
    existing_urls = get_existing_urls(urls_data)
    
    print(f"Loaded {len(urls_data)} existing URLs")
    
    issues = get_open_issues()
    print(f"Found {len(issues)} open issues")
    
    added_count = 0
    for issue in issues:
        if process_issue(issue, urls_data, existing_urls):
            added_count += 1
    
    if added_count > 0:
        save_urls(urls_data)
        print(f"\nAdded {added_count} new URL(s) to urls.json")
    else:
        print("\nNo new URLs added")


if __name__ == "__main__":
    main()

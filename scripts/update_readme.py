#!/usr/bin/env python3
"""Scrape GitHub repository data and update README with a markdown table."""

import os
import sys

# Add project root to path for utils import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import (
    backup_urls_json,
    extract_repo_info,
    fetch_repo_data,
    filter_blacklisted_urls,
    generate_markdown_table,
    load_blacklist,
    load_urls_json,
    update_readme,
    update_urls_json,
)
from utils.markdown import load_categories


def main() -> None:
    """Main function to orchestrate the scraping and README update."""
    token = os.environ.get("GITHUB_TOKEN")

    # Load URLs from urls.json
    urls_data = load_urls_json()

    # Load blacklist and filter out blacklisted URLs
    blacklist = load_blacklist()
    urls_data = filter_blacklisted_urls(urls_data, blacklist)

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

    # Load categories for generating category tables
    categories = load_categories()
    if categories:
        print(f"Loaded {len(categories)} categories from categories.json")
    else:
        print("No categories.json found, generating tables without categories")

    # Generate tables and update README
    tables = generate_markdown_table(repos, categories)
    update_readme(tables, categories)


if __name__ == "__main__":
    main()

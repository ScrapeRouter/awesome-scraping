"""Markdown generation utilities for README files."""


def generate_markdown_table(repos: list[dict]) -> str:
    """Generate a markdown table from repository data.
    
    Args:
        repos: List of repository dictionaries with keys:
               name, url, description, stars, version, updated_at
               
    Returns:
        Markdown-formatted table string
    """
    # Filter out entries without full data (only have url)
    complete_repos = [r for r in repos if "stars" in r]

    if not complete_repos:
        return "_No repositories found._"

    # Sort by stars descending
    sorted_repos = sorted(complete_repos, key=lambda x: x["stars"], reverse=True)

    lines = [
        "| Repository | Description | ⭐ Stars | Version | Updated |",
        "|------------|-------------|-------|---------|---------|",
    ]

    for repo in sorted_repos:
        name_link = f"<a href=\"{repo['url']}\" target=\"_blank\">{repo['name']}</a>"
        description = repo["description"][:80] + "..." if len(repo["description"]) > 80 else repo["description"]
        stars = f"{repo['stars']:,}"
        lines.append(f"| {name_link} | {description} | {stars} | {repo['version']} | {repo['updated_at']} |")

    return "\n".join(lines)


def update_readme(table: str, readme_path: str = "README.md") -> None:
    """Update README.md with the generated table.
    
    Args:
        table: Markdown table content
        readme_path: Path to README file (default: README.md)
    """
    header = "# awesome-scraping\n\nA curated list of awesome scraping tools and libraries.\n\n"
    content = header + "## Repositories\n\n" + table + "\n"

    with open(readme_path, "w") as f:
        f.write(content)

    print(f"Updated {readme_path}")

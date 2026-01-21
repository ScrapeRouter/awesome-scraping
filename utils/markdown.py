"""Markdown generation utilities for README files."""

from datetime import datetime

from dateutil.relativedelta import relativedelta


def _format_repo_row(repo: dict) -> str:
    """Format a single repository as a markdown table row."""
    name = repo['name']
    name = name.replace(' | ', ' ')
    name = name.replace('|', '')
    name_link = f"<a href=\"{repo['url']}\" target=\"_blank\">{name}</a>"
    full_description = repo["description"]
    full_description = full_description.replace(' | ', ' ')
    full_description = full_description.replace('|', '')
    description = full_description[:80] + "..." if len(full_description) > 80 else full_description
    description_with_title = f"<span title=\"{full_description}\">{description}</span>"
    stars = f"{repo['stars']:,}"
    return f"| {name_link} | {description_with_title} | {stars} | {repo['version']} | {repo['updated_at']} |"


def _build_table(repos: list[dict]) -> str:
    """Build a markdown table from a list of repos (already sorted)."""
    lines = [
        "| Repository | Description | ⭐ Stars | Version | Updated |",
        "|------------|-------------|-------|---------|---------|",
    ]
    for repo in repos:
        lines.append(_format_repo_row(repo))
    return "\n".join(lines)


def generate_markdown_table(repos: list[dict]) -> tuple[str, str]:
    """Generate markdown tables from repository data, separating active and hall of fame.
    
    Args:
        repos: List of repository dictionaries with keys:
               name, url, description, stars, version, updated_at
               
    Returns:
        Tuple of (active_table, hall_of_fame_table) markdown strings
    """
    # Filter out entries without full data (only have url)
    complete_repos = [r for r in repos if "stars" in r]

    if not complete_repos:
        return "_No repositories found._", ""

    # Calculate cutoff date (6 months ago)
    cutoff_date = datetime.now() - relativedelta(months=6)
    
    # Separate into active and hall of fame
    active_repos = []
    hall_of_fame_repos = []
    
    for repo in complete_repos:
        updated_at = repo.get("updated_at", "")
        try:
            repo_date = datetime.strptime(updated_at, "%Y-%m-%d")
            if repo_date < cutoff_date:
                hall_of_fame_repos.append(repo)
            else:
                active_repos.append(repo)
        except ValueError:
            # If date parsing fails, consider it active
            active_repos.append(repo)

    # Sort both lists by stars descending
    active_repos = sorted(active_repos, key=lambda x: x["stars"], reverse=True)
    hall_of_fame_repos = sorted(hall_of_fame_repos, key=lambda x: x["stars"], reverse=True)

    active_table = _build_table(active_repos) if active_repos else "_No active repositories found._"
    hall_of_fame_table = _build_table(hall_of_fame_repos) if hall_of_fame_repos else ""

    return active_table, hall_of_fame_table


def update_readme(tables: tuple[str, str], readme_path: str = "README.md") -> None:
    """Update README.md with the generated tables.
    
    Args:
        tables: Tuple of (active_table, hall_of_fame_table) markdown content
        readme_path: Path to README file (default: README.md)
    """
    active_table, hall_of_fame_table = tables
    
    header = "# awesome-scraping\n\nA curated list of awesome scraping tools and libraries. Human-selected repositories, information updated automatically every day.\n\n"
    content = header + "## Repositories\n\n" + active_table + "\n"
    
    if hall_of_fame_table:
        content += "\n## Hall of Fame\n\n"
        content += "_Repos that haven't been updated in the last 6 months, sorted by stars._\n\n"
        content += hall_of_fame_table + "\n"

    with open(readme_path, "w") as f:
        f.write(content)

    print(f"Updated {readme_path}")

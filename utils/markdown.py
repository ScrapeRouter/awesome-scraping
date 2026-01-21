"""Markdown generation utilities for README files."""

from datetime import datetime

from dateutil.relativedelta import relativedelta


def _format_repo_row(repo: dict) -> str:
    """Format a single repository as a markdown table row."""
    name = repo['name']
    name = name.replace(' | ', ' ')
    name = name.replace('|', '')
    name_link = f"<a href=\"{repo['url']}\" target=\"_blank\">{name}</a>"
    version = repo['version']
    repo_cell = f"{name_link}<br><sub>{version}</sub>" if version else name_link
    full_description = repo["description"]
    full_description = full_description.replace(' | ', ' ')
    full_description = full_description.replace('|', '')
    description = full_description[:80] + "..." if len(full_description) > 80 else full_description
    description_with_title = f"<span title=\"{full_description}\">{description}</span>"
    stars = f"{repo['stars']:,}"
    return f"| {repo_cell} | {description_with_title} | {stars} | {repo['updated_at']} |"


def _build_table(repos: list[dict]) -> str:
    """Build a markdown table from a list of repos (already sorted)."""
    lines = [
        "| Repository | Description | ⭐ Stars | Updated |",
        "|------------|-------------|------:|---------|",
    ]
    for repo in repos:
        lines.append(_format_repo_row(repo))
    return "\n".join(lines)


def generate_markdown_table(repos: list[dict]) -> tuple[str, str, str]:
    """Generate markdown tables from repository data, separating active, hall of fame, and artefacts.
    
    Args:
        repos: List of repository dictionaries with keys:
               name, url, description, stars, version, updated_at
               
    Returns:
        Tuple of (active_table, hall_of_fame_table, artefacts_table) markdown strings
    """
    # Filter out entries without full data (only have url)
    complete_repos = [r for r in repos if "stars" in r]

    if not complete_repos:
        return "_No repositories found._", "", ""

    # Calculate cutoff dates
    cutoff_6_months = datetime.now() - relativedelta(months=6)
    cutoff_1_year = datetime.now() - relativedelta(years=1)
    
    # Separate into active, hall of fame, and artefacts
    active_repos = []
    hall_of_fame_repos = []
    artefacts_repos = []
    
    for repo in complete_repos:
        updated_at = repo.get("updated_at", "")
        try:
            repo_date = datetime.strptime(updated_at, "%Y-%m-%d")
            if repo_date < cutoff_1_year:
                artefacts_repos.append(repo)
            elif repo_date < cutoff_6_months:
                hall_of_fame_repos.append(repo)
            else:
                active_repos.append(repo)
        except ValueError:
            # If date parsing fails, consider it active
            active_repos.append(repo)

    # Sort all lists by stars descending
    active_repos = sorted(active_repos, key=lambda x: x["stars"], reverse=True)
    hall_of_fame_repos = sorted(hall_of_fame_repos, key=lambda x: x["stars"], reverse=True)
    artefacts_repos = sorted(artefacts_repos, key=lambda x: x["stars"], reverse=True)

    active_table = _build_table(active_repos) if active_repos else "_No active repositories found._"
    hall_of_fame_table = _build_table(hall_of_fame_repos) if hall_of_fame_repos else ""
    artefacts_table = _build_table(artefacts_repos) if artefacts_repos else ""

    return active_table, hall_of_fame_table, artefacts_table


def update_readme(tables: tuple[str, str, str], readme_path: str = "README.md") -> None:
    """Update README.md with the generated tables.
    
    Args:
        tables: Tuple of (active_table, hall_of_fame_table, artefacts_table) markdown content
        readme_path: Path to README file (default: README.md)
    """
    active_table, hall_of_fame_table, artefacts_table = tables
    
    header = "# awesome-scraping\n\nA curated list of awesome scraping tools and libraries. Human-selected repositories, information updated automatically every day.\n\n"
    content = header + "## Repositories\n\n" + active_table + "\n"
    
    if hall_of_fame_table:
        content += "\n## Hall of Fame\n\n"
        content += "_Repos that haven't been updated in the last 6 months, sorted by stars._\n\n"
        content += hall_of_fame_table + "\n"

    if artefacts_table:
        content += "\n## Artefacts\n\n"
        content += "_Repos that haven't been updated in over a year, sorted by stars._\n\n"
        content += artefacts_table + "\n"

    with open(readme_path, "w") as f:
        f.write(content)

    print(f"Updated {readme_path}")

"""Markdown generation utilities for README files."""

import json
from pathlib import Path


def _format_repo_row(repo: dict) -> str:
    """Format a single repository as a markdown table row."""
    name = repo['name']
    name = name.replace(' | ', ' ')
    name = name.replace('|', '')
    name_link = f"<a href=\"{repo['url']}\" target=\"_blank\">{name}</a>"
    version = repo.get('version', '')
    repo_cell = f"{name_link}<br><sub>{version}</sub>" if version else name_link
    full_description = repo.get("description", "")
    full_description = full_description.replace(' | ', ' ')
    full_description = full_description.replace('|', '')
    description = full_description[:80] + "..." if len(full_description) > 80 else full_description
    description_with_title = f"<span title=\"{full_description}\">{description}</span>"
    stars = f"{repo['stars']:,}"
    updated_at = repo.get('updated_at', '-')
    return f"| {repo_cell} | {description_with_title} | {stars} | {updated_at} |"


def _build_table(repos: list[dict]) -> str:
    """Build a markdown table from a list of repos (already sorted)."""
    lines = [
        "| Repository | Description | ⭐Stars | Updated |",
        "|------------|-------------|------:|---------|",
    ]
    for repo in repos:
        lines.append(_format_repo_row(repo))
    return "\n".join(lines)


def load_categories(categories_path: str = "categories.json") -> dict:
    """Load categories from JSON file.
    
    Args:
        categories_path: Path to categories.json file
        
    Returns:
        Dictionary with category data or empty dict if file doesn't exist
    """
    path = Path(categories_path)
    if not path.exists():
        return {}
    
    with open(path, "r") as f:
        return json.load(f)


def get_categorized_repo_names(categories: dict) -> set[str]:
    """Get set of all repo names that have been categorized.
    
    Args:
        categories: Categories dictionary from categories.json
        
    Returns:
        Set of repo names
    """
    names = set()
    for cat_data in categories.values():
        for repo in cat_data.get("repos", []):
            names.add(repo["name"])
    return names


# Categories to exclude from README output entirely
EXCLUDED_CATEGORIES = {"rejected"}

# Special categories that appear at the end of README (in order)
END_CATEGORIES = ["hall_of_fame", "artefacts"]


def generate_category_tables(categories: dict, repos: list[dict]) -> dict[str, str]:
    """Generate markdown tables for each category.
    
    Args:
        categories: Categories dictionary from categories.json
        repos: List of all repos with full data from urls.json
        
    Returns:
        Dictionary mapping category_id to markdown table string
    """
    # Build a lookup from repo name to full repo data
    repo_lookup = {r["name"]: r for r in repos if "stars" in r}
    
    tables = {}
    for cat_id, cat_data in categories.items():
        # Skip excluded categories (like "rejected") and end categories
        if cat_id in EXCLUDED_CATEGORIES or cat_id in END_CATEGORIES:
            continue
        
        cat_repos = cat_data.get("repos", [])
        if not cat_repos:
            continue
        
        # Enrich category repos with full data from urls.json (for version, updated_at)
        enriched_repos = []
        for cat_repo in cat_repos:
            name = cat_repo["name"]
            if name in repo_lookup:
                # Merge: use urls.json data but keep categories from categories.json
                merged = {**repo_lookup[name], "categories": cat_repo.get("categories", [])}
                enriched_repos.append(merged)
            else:
                # Fallback to category repo data
                enriched_repos.append(cat_repo)
        
        # Sort by stars descending
        enriched_repos = sorted(enriched_repos, key=lambda x: x.get("stars", 0), reverse=True)
        
        tables[cat_id] = _build_table(enriched_repos)
    
    return tables


def generate_end_category_tables(categories: dict, repos: list[dict]) -> dict[str, str]:
    """Generate markdown tables for end categories (hall_of_fame, artefacts).
    
    Args:
        categories: Categories dictionary from categories.json
        repos: List of all repos with full data from urls.json
        
    Returns:
        Dictionary mapping category_id to markdown table string
    """
    # Build a lookup from repo name to full repo data
    repo_lookup = {r["name"]: r for r in repos if "stars" in r}
    
    tables = {}
    for cat_id in END_CATEGORIES:
        if cat_id not in categories:
            continue
        
        cat_data = categories[cat_id]
        cat_repos = cat_data.get("repos", [])
        if not cat_repos:
            continue
        
        # Enrich category repos with full data from urls.json
        enriched_repos = []
        for cat_repo in cat_repos:
            name = cat_repo["name"]
            if name in repo_lookup:
                merged = {**repo_lookup[name], "categories": cat_repo.get("categories", [])}
                enriched_repos.append(merged)
            else:
                enriched_repos.append(cat_repo)
        
        # Sort by stars descending
        enriched_repos = sorted(enriched_repos, key=lambda x: x.get("stars", 0), reverse=True)
        
        tables[cat_id] = _build_table(enriched_repos)
    
    return tables


def generate_markdown_table(repos: list[dict], categories: dict | None = None) -> tuple[str, dict[str, str], dict[str, str]]:
    """Generate markdown tables from repository data.
    
    Args:
        repos: List of repository dictionaries with keys:
               name, url, description, stars, version, updated_at
        categories: Optional categories dict. If provided, generates category tables
                   and puts uncategorized repos in a separate table.
               
    Returns:
        Tuple of (uncategorized_table, category_tables, end_category_tables)
        category_tables is a dict mapping category_id to table string
        end_category_tables is a dict for hall_of_fame and artefacts
    """
    # Filter out entries without full data (only have url)
    complete_repos = [r for r in repos if "stars" in r]

    if not complete_repos:
        return "_No repositories found._", {}, {}

    # Get categorized repo names
    categorized_names = get_categorized_repo_names(categories) if categories else set()
    
    # Generate category tables
    category_tables = generate_category_tables(categories, complete_repos) if categories else {}
    
    # Generate end category tables (hall_of_fame, artefacts)
    end_category_tables = generate_end_category_tables(categories, complete_repos) if categories else {}

    # Collect all uncategorized repos (regardless of age)
    uncategorized_repos = [
        repo for repo in complete_repos
        if repo["name"] not in categorized_names
    ]

    # Sort by stars descending
    uncategorized_repos = sorted(uncategorized_repos, key=lambda x: x["stars"], reverse=True)

    uncategorized_table = _build_table(uncategorized_repos) if uncategorized_repos else ""

    return uncategorized_table, category_tables, end_category_tables


def _generate_anchor(text: str) -> str:
    """Generate a markdown anchor from header text.
    
    Args:
        text: Header text to convert to anchor
        
    Returns:
        Anchor string (lowercase, spaces replaced with hyphens)
    """
    # Convert to lowercase and replace spaces with hyphens
    anchor = text.lower().replace(" ", "-")
    # Remove special characters except hyphens
    anchor = "".join(c for c in anchor if c.isalnum() or c == "-")
    return anchor


def update_readme(
    tables: tuple[str, dict[str, str], dict[str, str]],
    categories: dict | None = None,
    readme_path: str = "README.md"
) -> None:
    """Update README.md with the generated tables.
    
    Args:
        tables: Tuple of (uncategorized_table, category_tables, end_category_tables)
        categories: Categories dictionary for section headers/descriptions
        readme_path: Path to README file (default: README.md)
    """
    uncategorized_table, category_tables, end_category_tables = tables
    
    header = "# awesome-scraping\n\n"
    header += "A curated list of awesome scraping tools and libraries. "
    header += "Human-selected repositories, information updated automatically every day.\n\n"
    
    content = header
    
    # Build table of contents
    if categories and category_tables:
        content += "## Table of Contents\n\n"
        for cat_id, cat_data in categories.items():
            if cat_id not in category_tables:
                continue
            cat_name = cat_data.get("name", cat_id)
            anchor = _generate_anchor(cat_name)
            content += f"- [{cat_name}](#{anchor})\n"
        if uncategorized_table:
            content += "- [Uncategorized](#uncategorized)\n"
        # Add end categories to TOC
        for cat_id in END_CATEGORIES:
            if cat_id in end_category_tables and cat_id in categories:
                cat_name = categories[cat_id].get("name", cat_id)
                anchor = _generate_anchor(cat_name)
                content += f"- [{cat_name}](#{anchor})\n"
        content += "\n"
    
    # Add category sections
    if categories and category_tables:
        for cat_id, cat_data in categories.items():
            if cat_id not in category_tables:
                continue
            
            cat_name = cat_data.get("name", cat_id)
            cat_description = cat_data.get("description", "")
            # cat_best_for = cat_data.get("best_for", "")
            
            content += f"## {cat_name}\n\n"
            if cat_description:
                content += f"_{cat_description}_\n\n"
            # if cat_best_for:
            #     content += f"**Best for:** {cat_best_for}\n\n"
            content += category_tables[cat_id] + "\n\n"
    
    # Add uncategorized repos if any
    if uncategorized_table:
        content += "## Uncategorized\n\n"
        content += "_Repositories not yet categorized, sorted by stars._\n\n"
        content += uncategorized_table + "\n\n"
    
    # Add end category sections (hall_of_fame, artefacts)
    if categories and end_category_tables:
        for cat_id in END_CATEGORIES:
            if cat_id not in end_category_tables:
                continue
            
            cat_data = categories[cat_id]
            cat_name = cat_data.get("name", cat_id)
            cat_description = cat_data.get("description", "")
            
            content += f"## {cat_name}\n\n"
            if cat_description:
                content += f"_{cat_description}_\n\n"
            content += end_category_tables[cat_id] + "\n\n"

    with open(readme_path, "w") as f:
        f.write(content.rstrip() + "\n")

    print(f"Updated {readme_path}")

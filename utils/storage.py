"""Storage utilities for managing urls.json and history."""

import json
import shutil
from datetime import datetime
from pathlib import Path


def load_urls_json(urls_path: str | Path = "urls.json") -> list[dict]:
    """Load repository data from urls.json.
    
    Args:
        urls_path: Path to urls.json file
        
    Returns:
        List of repository dictionaries
    """
    with open(urls_path) as f:
        return json.load(f)


def backup_urls_json(urls_path: str | Path = "urls.json", history_dir: str | Path = "history") -> Path | None:
    """Move current urls.json to history directory with timestamp suffix.
    
    Args:
        urls_path: Path to urls.json file
        history_dir: Path to history directory
        
    Returns:
        Path to backup file or None if no backup was made
    """
    urls_path = Path(urls_path)
    history_dir = Path(history_dir)

    if not urls_path.exists():
        print("No urls.json found to backup")
        return None

    history_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = history_dir / f"urls_{timestamp}.json"

    shutil.move(urls_path, backup_path)
    print(f"Moved urls.json to {backup_path}")
    return backup_path


def update_urls_json(repos: list[dict], urls_path: str | Path = "urls.json") -> None:
    """Write updated repository data to urls.json.
    
    Args:
        repos: List of repository dictionaries
        urls_path: Path to urls.json file
    """
    urls_path = Path(urls_path)

    with open(urls_path, "w") as f:
        json.dump(repos, f, indent=4)

    print(f"Created new {urls_path} with {len(repos)} repositories")

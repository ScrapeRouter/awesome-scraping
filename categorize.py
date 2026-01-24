#!/usr/bin/env python3
"""
Categorize repos from urls.json using OpenRouter API with Gemini 2.0 Flash.
Outputs categories.json with repos sorted into categories.
"""

import base64
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv
from openrouter import OpenRouter

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
MODEL = "google/gemini-3-flash-preview"

CATEGORIES = {
    "full_featured_frameworks": {
        "name": "Full-Featured Frameworks",
        "description": "All-in-one solutions designed to handle crawling (visiting many pages) and scraping (extracting data) at scale.",
        "examples": ["Scrapy", "Crawlee", "Firecrawl", "Crawl4AI"],
        "best_for": "Large projects requiring structured data and managed workflows.",
        "repos": []
    },
    "browser_automation": {
        "name": "Browser Automation",
        "description": "Tools that control real web browsers (Chrome, Firefox, WebKit). Essential for websites that require JavaScript to render.",
        "examples": ["Puppeteer", "Playwright", "SeleniumBase", "Zendriver"],
        "best_for": "High-interactivity sites, SPAs (Single Page Apps), and bypassing simple bot detection.",
        "repos": []
    },
    "ai_llm_scrapers": {
        "name": "AI & LLM-Powered Scrapers",
        "description": "The 'new wave' of scrapers that use Large Language Models to understand page structure and extract data using natural language.",
        "examples": ["Scrapegraph-ai", "CyberScraper-2077", "HyperAgent"],
        "best_for": "Unstructured sites or when you don't want to write manual CSS/XPath selectors.",
        "repos": []
    },
    "http_clients": {
        "name": "HTTP Clients & Request Libraries",
        "description": "Lightweight tools used to fetch the raw HTML/data of a page without the overhead of a full browser.",
        "examples": ["Axios", "Httpx", "Got", "Urllib3", "Curl_cffi"],
        "best_for": "Speed, performance, and simple APIs.",
        "repos": []
    },
    "parsers_extractors": {
        "name": "Parsers & Extractors",
        "description": "Tools that take raw HTML or XML and turn it into a format your code can read (like JSON).",
        "examples": ["Cheerio", "BeautifulSoup (via lxml)", "Selectolax", "Htmlparser2"],
        "best_for": "Selecting specific elements once you already have the page source.",
        "repos": []
    },
    "evasion_fingerprinting": {
        "name": "Evasion & Fingerprinting",
        "description": "Libraries specifically designed to help scrapers look like real users and avoid being blocked.",
        "examples": ["Cloudscraper", "Camoufox", "Proxy-chain", "Fake-useragent"],
        "best_for": "Bypassing Cloudflare, Akamai, or other anti-bot services.",
        "repos": []
    },
    "data_cleaning": {
        "name": "Data Cleaning & Sanitization",
        "description": "Tools to clean up the 'messy' data you've extracted, such as stripping HTML tags or converting dates.",
        "examples": ["Bleach", "Js-xss", "Dateparser", "Price-parser", "Python-slugify"],
        "best_for": "Post-processing data before saving it to a database.",
        "repos": []
    },
    "other": {
        "name": "Other",
        "description": "Tools and libraries related to web scraping that don't fit neatly into other categories.",
        "examples": [],
        "best_for": "Miscellaneous scraping-related utilities and tools.",
        "repos": []
    },
    "rejected": {
        "name": "Rejected",
        "description": "Repositories that are NOT related to web scraping, crawling, or data extraction. This includes general-purpose libraries, unrelated tools, or repos that were miscategorized.",
        "examples": [],
        "best_for": "Filtering out irrelevant repositories.",
        "repos": []
    }
}

CATEGORY_IDS = list(CATEGORIES.keys())

README_MAX_CHARS = 1024


def fetch_readme(full_name: str) -> str:
    """Fetch the first 1024 chars of a repo's README from GitHub API."""
    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    
    url = f"https://api.github.com/repos/{full_name}/readme"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return ""
        
        data = response.json()
        content = data.get("content", "")
        encoding = data.get("encoding", "")
        
        if encoding == "base64" and content:
            decoded = base64.b64decode(content).decode("utf-8", errors="ignore")
            return decoded[:README_MAX_CHARS]
        
        return ""
    except Exception as e:
        print(f"  Failed to fetch README: {e}")
        return ""


def build_system_prompt() -> str:
    """Build the system prompt with category definitions."""
    categories_text = "\n".join([
        f"{i+1}. {cat['name']} ({cat_id})\n"
        f"   Description: {cat['description']}\n"
        f"   Examples: {', '.join(cat['examples'])}\n"
        f"   Best for: {cat['best_for']}"
        for i, (cat_id, cat) in enumerate(CATEGORIES.items())
    ])
    
    return f"""You are an expert at categorizing web scraping and data extraction tools.

Given a repository's name, description, topics, and README excerpt, classify it into one or more of the following categories.
A repo can belong to multiple categories if it fits multiple purposes.

Categories:
{categories_text}

IMPORTANT RULES:
- If a repo is related to web scraping/crawling but doesn't fit the main categories, use "other"
- If a repo is NOT related to web scraping, crawling, or data extraction at all, use "rejected"
- Every repo MUST be assigned to at least one category (including "other" or "rejected")

Respond with ONLY a JSON array of category IDs (strings) that apply to this repository.
Valid category IDs are: {json.dumps(CATEGORY_IDS)}

Example responses:
["full_featured_frameworks"]
["browser_automation", "evasion_fingerprinting"]
["http_clients"]
["parsers_extractors", "data_cleaning"]
["other"]
["rejected"]

Do not include any explanation, just the JSON array."""


def categorize_repo(repo: dict, client: OpenRouter) -> list[str]:
    """Categorize a single repo using OpenRouter API."""
    # Fetch README excerpt for additional context
    readme_excerpt = fetch_readme(repo['full_name'])
    
    user_message = f"""Repository: {repo['name']}
Full name: {repo['full_name']}
Description: {repo.get('description', 'No description')}
Topics: {', '.join(repo.get('topics', []))}"""
    
    if readme_excerpt:
        user_message += f"\n\nREADME excerpt:\n{readme_excerpt}"

    try:
        response = client.chat.send(
            model=MODEL,
            messages=[
                {"role": "system", "content": build_system_prompt()},
                {"role": "user", "content": user_message}
            ],
            temperature=0.1,
            max_tokens=200
        )
        
        content = response.choices[0].message.content.strip()
        
        # Handle potential markdown code blocks
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        
        categories = json.loads(content)
        
        # Validate categories
        valid_categories = [c for c in categories if c in CATEGORY_IDS]
        return valid_categories
        
    except json.JSONDecodeError as e:
        print(f"  JSON parse error for {repo['name']}: {e}")
        print(f"  Raw content: {content}")
        return []
    except Exception as e:
        print(f"  Error for {repo['name']}: {e}")
        return []


def load_existing_categories(path: Path) -> tuple[dict, set[str]]:
    """Load existing categories.json and return the data and set of already categorized repo names."""
    # Start with full category structure
    output = {cat_id: {**cat_data, "repos": []} for cat_id, cat_data in CATEGORIES.items()}
    categorized_names = set()
    
    if not path.exists():
        return output, categorized_names
    
    with open(path, "r") as f:
        existing = json.load(f)
    
    # Merge existing repos into output structure
    for cat_id in existing:
        if cat_id in output:
            # Use existing repos for known categories
            output[cat_id]["repos"] = existing[cat_id].get("repos", [])
        # Extract all repo names that are already categorized
        for repo in existing[cat_id].get("repos", []):
            categorized_names.add(repo["name"])
    
    return output, categorized_names


def save_categories(output: dict, path: Path) -> None:
    """Save categories to JSON file, sorted by stars within each category."""
    # Sort repos within each category by stars (descending)
    for cat_id in output:
        output[cat_id]["repos"].sort(key=lambda x: x.get("stars", 0), reverse=True)
    
    with open(path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


def main():
    if not OPENROUTER_API_KEY:
        print("Error: OPENROUTER_API_KEY not set in environment or .env file")
        return
    
    # Load repos
    urls_path = Path(__file__).parent / "urls.json"
    with open(urls_path, "r") as f:
        repos = json.load(f)
    
    print(f"Loaded {len(repos)} repos from urls.json")
    
    # Load existing categories and get already categorized repos
    output_path = Path(__file__).parent / "categories.json"
    output, already_categorized = load_existing_categories(output_path)
    
    print(f"Already categorized: {len(already_categorized)} repos")
    
    # Filter to only uncategorized repos
    repos_to_process = [r for r in repos if r["name"] not in already_categorized]
    print(f"Repos to categorize: {len(repos_to_process)}")
    
    if not repos_to_process:
        print("No new repos to categorize.")
        return
    
    # Track newly categorized repos
    newly_categorized = 0
    
    with OpenRouter(api_key=OPENROUTER_API_KEY) as client:
        for i, repo in enumerate(repos_to_process):
            print(f"[{i+1}/{len(repos_to_process)}] Categorizing: {repo['name']}")
            
            categories = categorize_repo(repo, client)
            
            # If no categories returned (LLM error), assign to "other" as fallback
            if not categories:
                categories = ["other"]
                print("  -> No categories returned (fallback to other)")
            else:
                print(f"  -> Categories: {categories}")
            
            newly_categorized += 1
            
            # Create a simplified repo entry for the output
            repo_entry = {
                "name": repo["name"],
                "full_name": repo["full_name"],
                "url": repo["url"],
                "description": repo.get("description", ""),
                "stars": repo.get("stars", 0),
                "categories": categories,
                "categorized_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Add repo to each matching category
            for cat_id in categories:
                output[cat_id]["repos"].append(repo_entry)
            
            # Save incrementally after each successful categorization
            save_categories(output, output_path)
            print("  -> Saved progress")
            
            # Small delay to avoid rate limiting
            time.sleep(0.1)
    
    print(f"\nSaved categories to {output_path}")
    
    # Print summary
    print("\n=== Summary ===")
    for cat_id, cat_data in output.items():
        print(f"{cat_data['name']}: {len(cat_data['repos'])} repos")
    
    total_in_categories = sum(len(output[cat_id]["repos"]) for cat_id in output)
    print(f"\nNewly categorized: {newly_categorized}")
    print(f"Total repos in categories: {total_in_categories}")


if __name__ == "__main__":
    main()

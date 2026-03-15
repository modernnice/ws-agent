import os
import requests
import json
from datetime import datetime, timezone
from pathlib import Path
from langchain_core.tools import tool

# ===============================
# Configuration
# ===============================
REPO_OWNER = "CCondeluci"
REPO_NAME = "WeissSchwarz-ENG-DB"
REPO_DB_PATH = "DB"
BRANCH = "master"
GITHUB_API_BASE = "https://api.github.com"
RAW_CONTENT_BASE = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}"

# Local paths
CURRENT_DIR = Path(__file__).resolve().parent
TIME_FILE = CURRENT_DIR / "time.txt"
# Assuming the data directory is relative to the project root, which is 2 levels up from here
PROJECT_ROOT = CURRENT_DIR.parent.parent
LOCAL_DB_PATH = PROJECT_ROOT / "data" / "Card_DB" / "DB"


def get_last_update_time():
    """Reads the last update time from time.txt."""
    if not TIME_FILE.exists():
        return None
    try:
        with open(TIME_FILE, "r") as f:
            content = f.read().strip()
            if not content:
                return None
            dt = datetime.fromisoformat(content)
            # Ensure timezone awareness (assume UTC if naive)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
    except Exception as e:
        print(f"Error reading time.txt: {e}")
        return None


def save_last_update_time(dt):
    """Saves the given datetime to time.txt."""
    try:
        with open(TIME_FILE, "w") as f:
            f.write(dt.isoformat())
        print(f"Updated time.txt to: {dt.isoformat()}")
    except Exception as e:
        print(f"Error writing to time.txt: {e}")


def get_commits_since(since_dt):
    """
    Fetches commits from GitHub API since the given datetime.
    Returns a list of commits sorted by date (newest first).
    """
    url = f"{GITHUB_API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/commits"
    params = {
        "path": REPO_DB_PATH,
        "sha": BRANCH,
        "since": since_dt.isoformat(),
        "per_page": 100  # Adjust as needed, pagination might be required for very long gaps
    }
    
    commits = []
    page = 1
    
    while True:
        params["page"] = page
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            batch = response.json()
            
            if not batch:
                break
                
            commits.extend(batch)
            if len(batch) < 100:
                break
            page += 1
            
        except requests.RequestException as e:
            print(f"Error fetching commits: {e}")
            return []
            
    return commits


def get_commit_details(commit_sha):
    """Fetches details of a specific commit to see changed files."""
    url = f"{GITHUB_API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/commits/{commit_sha}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching commit details for {commit_sha}: {e}")
        return None


def download_file(remote_path, local_path):
    """Downloads a file from the raw GitHub content."""
    url = f"{RAW_CONTENT_BASE}/{remote_path}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # Ensure directory exists
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(local_path, "wb") as f:
            f.write(response.content)
        print(f"Downloaded: {remote_path} -> {local_path}")
        return True
    except requests.RequestException as e:
        print(f"Error downloading {remote_path}: {e}")
        return False


def perform_upgrade():
    """
    Main logic to perform the incremental upgrade.
    """
    # 1. Get last update time
    last_update = get_last_update_time()
    if not last_update:
        print("No previous update time found in time.txt. Cannot perform incremental update.")
        print("Please ensure card_upgrade_check.py has been run or time.txt is initialized.")
        return "Failed: Missing time.txt or invalid format."

    print(f"Checking for updates since: {last_update.isoformat()}")

    # 2. Get commits since last update
    commits = get_commits_since(last_update)
    if not commits:
        print("No new commits found.")
        return "No updates available."

    print(f"Found {len(commits)} commits to process.")

    # 3. Process commits to find changed files
    # We process from oldest to newest to simulate the history, 
    # BUT for file content, we only need the latest version.
    # So we can collect all changed files and just download their current HEAD version.
    
    changed_files = set()
    removed_files = set()
    
    # Iterate through all commits to gather all touched files
    for commit in commits:
        sha = commit['sha']
        details = get_commit_details(sha)
        if not details:
            continue
            
        for file in details.get('files', []):
            filename = file['filename']
            status = file['status']
            
            # Filter only files in the target DB directory and are JSON
            if not filename.startswith(REPO_DB_PATH) or not filename.endswith('.json'):
                continue
                
            if status == 'removed':
                removed_files.add(filename)
                if filename in changed_files:
                    changed_files.remove(filename)
            else:
                # added, modified, renamed, etc.
                changed_files.add(filename)
                if filename in removed_files:
                    removed_files.remove(filename)

    print(f"Files to update/add: {len(changed_files)}")
    print(f"Files to remove: {len(removed_files)}")

    if not changed_files and not removed_files:
        # Just update the timestamp if no relevant files were changed
        latest_commit_date_str = commits[0]['commit']['committer']['date']
        latest_dt = datetime.fromisoformat(latest_commit_date_str.replace("Z", "+00:00"))
        save_last_update_time(latest_dt)
        return "Timestamp updated (no relevant file changes)."

    # 4. Apply changes
    # Remove files
    for remote_path in removed_files:
        # remote_path is like "DB/file.json"
        # we need to map it to local path
        # remove "DB/" prefix if present to join correctly, or just use name
        relative_path = Path(remote_path).name
        local_file = LOCAL_DB_PATH / relative_path
        
        if local_file.exists():
            try:
                local_file.unlink()
                print(f"Removed: {local_file}")
            except OSError as e:
                print(f"Error removing {local_file}: {e}")

    # Download/Update files
    for remote_path in changed_files:
        relative_path = Path(remote_path).name
        local_file = LOCAL_DB_PATH / relative_path
        download_file(remote_path, local_file)

    # 5. Update time.txt to the latest commit time
    # The commits list is sorted by date (newest first) by default from GitHub API
    latest_commit_date_str = commits[0]['commit']['committer']['date']
    latest_dt = datetime.fromisoformat(latest_commit_date_str.replace("Z", "+00:00"))
    
    save_last_update_time(latest_dt)
    
    return f"Successfully updated {len(changed_files)} files and removed {len(removed_files)} files."


@tool
def upgrade_card_db() -> str:
    """
    Executes the incremental update of the Card Database.
    It checks for commits since the last update time, downloads new/modified JSON files,
    removes deleted files, and updates the local time record.
    Returns a status message describing the result.
    """
    return perform_upgrade()


if __name__ == "__main__":
    # Test run
    result = perform_upgrade()
    print(f"Result: {result}")

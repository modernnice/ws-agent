import requests
from datetime import datetime, timezone
from pathlib import Path
from langchain_core.tools import tool

# ===============================
# Configuration
# ===============================
REPO_OWNER = "CCondeluci"
REPO_NAME = "WeissSchwarz-ENG-DB"
REPO_PATH = "DB"
BRANCH = "master"
GITHUB_API_BASE = "https://api.github.com"

TIME_FILE = Path(__file__).resolve().parent / "time.txt"


# ===============================
# Read local time.txt
# ===============================
def get_last_update_time():
    if not TIME_FILE.exists():
        return None
    try:
        with open(TIME_FILE, "r") as f:
            content = f.read().strip()
            dt = datetime.fromisoformat(content)

            # 如果是 naive，默认视为 UTC
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            return dt
    except Exception:
        return None


# ===============================
# Get latest commit time from GitHub (DB folder only)
# ===============================
def get_remote_latest_time():
    url = f"{GITHUB_API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/commits"
    params = {
        "path": REPO_PATH,
        "sha": BRANCH,
        "per_page": 1
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        commits = response.json()

        if not commits:
            return None

        latest_commit_date_str = commits[0]['commit']['committer']['date']
        return datetime.fromisoformat(latest_commit_date_str.replace("Z", "+00:00"))

    except requests.RequestException:
        return None


# ===============================
# Logic Function (Internal)
# ===============================
def _check_card_db_status_impl() -> dict:
    """
    Internal implementation of check_card_db_status logic.
    """
    local_time = get_last_update_time()
    remote_time = get_remote_latest_time()

    return {
        "local_last_sync_time": local_time.isoformat() if local_time else None,
        "remote_latest_commit_time": remote_time.isoformat() if remote_time else None
    }


# ===============================
# Tool Function (Exposed to Agent)
# ===============================
@tool
def check_card_db_status() -> dict:
    """
    查询 Weiss Schwarz GitHub DB 目录的最新更新时间，
    以及本地 time.txt 记录的上次同步时间。
    """
    return _check_card_db_status_impl()


if __name__ == "__main__":
    # Call the implementation directly, bypassing the Tool wrapper
    result = _check_card_db_status_impl()
    local_time = result.get("local_last_sync_time")
    remote_time = result.get("remote_latest_commit_time")
    local_dt = datetime.fromisoformat(local_time) if local_time else None
    remote_dt = datetime.fromisoformat(remote_time) if remote_time else None
    print("===== Weiss Schwarz DB Status =====")
    print(f"Local last sync time (time.txt): {local_time}")
    print(f"Remote DB latest commit time: {remote_time}")
    if local_dt is None or remote_dt is None:
        print("Status check failed.")
    elif remote_dt > local_dt:
        print("Remote DB has updates available.")
    else:
        print("Local DB is up to date.")

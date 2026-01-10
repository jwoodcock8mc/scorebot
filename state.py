import json
from pathlib import Path
from datetime import date

MAX_DAILY_POSTS = 8  # stay safely below 10

STATE_FILE = Path("state.json")

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def can_post(state):
    today = str(date.today())

    if state.get("last_post_day") != today:
        state["last_post_day"] = today
        state["daily_posts"] = 0

    return state["daily_posts"] < MAX_DAILY_POSTS

def record_post(state):
    state["daily_posts"] += 1


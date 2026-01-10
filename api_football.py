import requests
from config import API_FOOTBALL_KEY, API_FOOTBALL_HOST, NORWICH_TEAM_ID

HEADERS = {
    "X-RapidAPI-Key": API_FOOTBALL_KEY,
    "X-RapidAPI-Host": API_FOOTBALL_HOST,
}

BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"

def get_live_fixture():
    """Return live Norwich City fixture or None."""
    r = requests.get(
        f"{BASE_URL}/fixtures",
        headers=HEADERS,
        params={"team": NORWICH_TEAM_ID, "live": "all"},
        timeout=10,
    )
    data = r.json()
    return data["response"][0] if data["response"] else None

def get_fixture_events(fixture_id):
    r = requests.get(
        f"{BASE_URL}/fixtures/events",
        headers=HEADERS,
        params={"fixture": fixture_id},
        timeout=10,
    )
    return r.json()["response"]

def get_fixture_lineups(fixture_id):
    r = requests.get(
        f"{BASE_URL}/fixtures/lineups",
        headers=HEADERS,
        params={"fixture": fixture_id},
        timeout=10,
    )
    return r.json()["response"]

import time
import requests
from config import API_FOOTBALL_KEY, API_FOOTBALL_HOST, NORWICH_TEAM_ID

BASE_URL = " https://v3.football.api-sports.io/"

HEADERS = {
    "X-RapidAPI-Key": API_FOOTBALL_KEY,
    "X-RapidAPI-Host": API_FOOTBALL_HOST,
}

# -------------------------
# Internal helper
# -------------------------

def _safe_get(endpoint, params=None):
    """
    Safe API-Football GET.
    Always returns a list.
    Backs off on rate limits.
    """
    url = f"{BASE_URL}{endpoint}"

    try:
        r = requests.get(
            url,
            headers=HEADERS,
            params=params or {},
            timeout=10,
        )

        if r.status_code == 429:
            print(
                f"API-Football RATE LIMITED (429) on {endpoint}. "
                "Backing off 10 minutes.",
                flush=True,
            )
            time.sleep(600)
            return []

        if r.status_code != 200:
            print(
                f"API-Football HTTP error {r.status_code} on {endpoint}",
                flush=True,
            )
            return []

        data = r.json()

        if data.get("errors"):
            print(
                f"API-Football API error on {endpoint}: {data['errors']}",
                flush=True,
            )
            return []

        response = data.get("response")
        if not isinstance(response, list):
            print(
                f"API-Football malformed response on {endpoint}",
                flush=True,
            )
            return []

        return response

    except requests.exceptions.Timeout:
        print(f"API-Football timeout on {endpoint}", flush=True)
        return []

    except requests.exceptions.RequestException as e:
        print(f"API-Football request failed: {e}", flush=True)
        return []

    except ValueError as e:
        print(f"API-Football JSON decode failed: {e}", flush=True)
        return []


# -------------------------
# Public API
# -------------------------

def get_live_fixture():
    """
    Return live Norwich City fixture dict, or None.
    """
    fixtures = _safe_get(
        "/fixtures",
        params={
            "team": NORWICH_TEAM_ID,
            "live": "all",
        },
    )

    for f in fixtures:
        teams = f.get("teams", {})
        if (
            teams.get("home", {}).get("id") == NORWICH_TEAM_ID
            or teams.get("away", {}).get("id") == NORWICH_TEAM_ID
        ):
            return f

    return None


def get_fixture_events(fixture_id):
    if not fixture_id:
        return []

    return _safe_get(
        "/fixtures/events",
        params={"fixture": fixture_id},
    )


def get_fixture_lineups(fixture_id):
    if not fixture_id:
        return []

    return _safe_get(
        "/fixtures/lineups",
        params={"fixture": fixture_id},
    )

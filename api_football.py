import requests
from config import API_FOOTBALL_KEY, API_FOOTBALL_HOST, NORWICH_TEAM_ID

BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"

HEADERS = {
    "X-RapidAPI-Key": API_FOOTBALL_KEY,
    "X-RapidAPI-Host": API_FOOTBALL_HOST,
}

# -------------------------
# Internal helper
# -------------------------

def _safe_get(endpoint, params=None):
    """
    Perform a safe API-Football GET request.
    Always returns a list (possibly empty).
    Never raises KeyError.
    """
    url = f"{BASE_URL}{endpoint}"

    try:
        r = requests.get(
            url,
            headers=HEADERS,
            params=params or {},
            timeout=10,
        )

        # HTTP-level error (4xx / 5xx)
        if r.status_code != 200:
            print(
                f"API-Football HTTP error {r.status_code} on {endpoint}",
                flush=True,
            )
            return []

        data = r.json()

        # API-level error
        if "errors" in data and data["errors"]:
            print(
                f"API-Football API error on {endpoint}: {data['errors']}",
                flush=True,
            )
            return []

        response = data.get("response")

        if not isinstance(response, list):
            print(
                f"API-Football malformed response on {endpoint}: {data}",
                flush=True,
            )
            return []

        return response

    except requests.exceptions.Timeout:
        print(f"API-Football timeout on {endpoint}", flush=True)
        return []

    except requests.exceptions.RequestException as e:
        print(f"API-Football request failed on {endpoint}: {e}", flush=True)
        return []

    except ValueError as e:
        print(f"API-Football JSON decode failed on {endpoint}: {e}", flush=True)
        return []


# -------------------------
# Public API
# -------------------------

def get_live_fixture():
    """
    Return the live Norwich City fixture dict, or None if not live.
    """
    fixtures = _safe_get(
        "/fixtures",
        params={
            "team": NORWICH_TEAM_ID,
            "live": "all",
        },
    )

    if not fixtures:
        return None

    # API-Football can return multiple live fixtures (rare, but possible)
    for fixture in fixtures:
        teams = fixture.get("teams", {})
        home_id = teams.get("home", {}).get("id")
        away_id = teams.get("away", {}).get("id")

        if home_id == NORWICH_TEAM_ID or away_id == NORWICH_TEAM_ID:
            return fixture

    return None


def get_fixture_events(fixture_id):
    """
    Return a list of events for a fixture.
    Always returns a list (possibly empty).
    """
    if not fixture_id:
        return []

    return _safe_get(
        "/fixtures/events",
        params={"fixture": fixture_id},
    )


def get_fixture_lineups(fixture_id):
    """
    Return a list of lineups for a fixture.
    Always returns a list (possibly empty).
    """
    if not fixture_id:
        return []

    return _safe_get(
        "/fixtures/lineups",
        params={"fixture": fixture_id},
    )

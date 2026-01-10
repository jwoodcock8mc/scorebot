import time
from api_football import get_live_fixture, get_fixture_events
from bluesky import login, post
from state import load_state, save_state
from config import LIVE_POLL_SECONDS

login()
state = load_state()

print("Norwich City Bluesky bot started")

while True:
    try:
        fixture = get_live_fixture()

        if not fixture:
            time.sleep(300)
            continue

        fixture_id = fixture["fixture"]["id"]
        status = fixture["fixture"]["status"]["short"]

        home = fixture["teams"]["home"]["name"]
        away = fixture["teams"]["away"]["name"]

        goals_home = fixture["goals"]["home"]
        goals_away = fixture["goals"]["away"]

        match_key = str(fixture_id)
        state.setdefault(match_key, {
            "posted_events": [],
            "status": None
        })

        # --- HT / FT detection ---
        if status != state[match_key]["status"]:
            if status == "HT":
                post(f"⏸ HT: {home} {goals_home}–{goals_away} {away}\n\n#NCFC")
            if status == "FT":
                post(f"🏁 FT: {home} {goals_home}–{goals_away} {away}\n\nUp the Canaries 💛💚\n#NCFC")
            state[match_key]["status"] = status

        # --- Event detection ---
        events = get_fixture_events(fixture_id)

        for e in events:
            minute = e["time"]["elapsed"]
            team = e["team"]["name"]
            player = e["player"]["name"]
            event_type = e["type"]
            detail = e["detail"]

            event_id = f"{event_type}:{detail}:{minute}:{player}"

            if event_id in state[match_key]["posted_events"]:
                continue

            # Goals
            if event_type == "Goal":
                score = f"{home} {goals_home}–{goals_away} {away}"
                post(f"⚽ GOAL!\n\n{score}\n{player} ({minute}')\n\n#NCFC")

            # Yellow cards
            elif detail == "Yellow Card":
                post(f"🟨 Yellow card\n\n{player} ({minute}')\n{home} vs {away}\n\n#NCFC")

            # Red cards
            elif detail == "Red Card":
                post(f"🟥 RED CARD\n\n{player} ({minute}')\n{home} vs {away}\n\n#NCFC")

            state[match_key]["posted_events"].append(event_id)

        save_state(state)
        time.sleep(LIVE_POLL_SECONDS)

    except Exception as e:
        print("Error:", e)
        time.sleep(60)

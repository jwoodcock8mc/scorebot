print("BOT.PY LOADED", flush=True)

import time
from datetime import date

from api_football import (
    get_live_fixture,
    get_fixture_events,
    get_fixture_lineups,
)

from bluesky import login, safe_post
from state import load_state, save_state
from config import BLUESKY_HANDLE, BLUESKY_APP_PASSWORD


# -------------------------
# Helpers
# -------------------------

def high_signal_only(state):
    """Suppress low-signal posts when close to daily limit."""
    return state.get("daily_posts", 0) >= 6

def today():
    return str(date.today())


# -------------------------
# Main
# -------------------------

def main():
    print("ENTERED MAIN()", flush=True)

    # ---- Startup ----
    print("Logging in to Bluesky...", flush=True)
    login(BLUESKY_HANDLE, BLUESKY_APP_PASSWORD)
    print("Bluesky login OK", flush=True)

    state = load_state()
    print("State loaded", flush=True)

    print("Norwich City Bluesky bot started (final version)", flush=True)

    POLL_COUNT = 0

    # ---- Main loop ----
    POLL_COUNT = 0

while True:
    try:
        print("Polling API-Football", flush=True)
        fixture_data = get_live_fixture()

        # Log raw API response
        print("API-Football raw response:", fixture_data, flush=True)

        # Check if we have a live fixture
        if not fixture_data.get("response") or len(fixture_data["response"]) == 0:
            print("No live fixture found, sleeping 300s", flush=True)
            time.sleep(300)
            continue

        fixture = fixture_data["response"][0]

        # -------------------------
        # Extract match info safely
        # -------------------------
        fixture_id = fixture.get("fixture", {}).get("id")
        status = fixture.get("fixture", {}).get("status", {}).get("short", "NS")
        minute = fixture.get("fixture", {}).get("status", {}).get("elapsed") or 0

        home = fixture.get("teams", {}).get("home", {}).get("name", "Home")
        away = fixture.get("teams", {}).get("away", {}).get("name", "Away")

        goals_home = fixture.get("goals", {}).get("home", 0)
        goals_away = fixture.get("goals", {}).get("away", 0)
        score = (goals_home, goals_away)

        venue = fixture.get("fixture", {}).get("venue", {}).get("name", "Unknown Venue")
        referee = fixture.get("fixture", {}).get("referee", "")
        weather = fixture.get("fixture", {}).get("weather")

        match_key = str(fixture_id)

        state.setdefault(match_key, {
            "last_score": None,
            "last_status": None,
            "last_event_minute": 0,
            "lineups_posted": False,
            "kickoff_posted": False,
        })

        match_state = state[match_key]

        # -------------------------
        # Lineups
        # -------------------------
        if not match_state["lineups_posted"] and status in ("NS", "1H"):
            print("Checking lineups", flush=True)
            lineups_data = get_fixture_lineups(fixture_id)

            # Safety: make sure data exists
            if not lineups_data or len(lineups_data) == 0:
                print("No lineups returned, skipping", flush=True)
            else:
                for team in lineups_data:
                    if team.get("team", {}).get("name") == home:
                        formation = team.get("formation", "Unknown")

                        starters = []
                        for p in team.get("startXI", []):
                            player = p.get("player", {})
                            name = player.get("name", "Unknown")
                            if player.get("captain"):
                                name += " ©"
                            starters.append(name)

                        lineup_text = "\n".join(starters)

                        ref = safe_post(
                            f"📋 Norwich City XI ({formation})\n\n"
                            f"{lineup_text}\n\n#NCFC",
                            state
                        )

                        match_state["lineups_posted"] = True
                        save_state(state)

                        # Bench as reply
                        if ref and not high_signal_only(state):
                            bench = [p.get("player", {}).get("name", "Unknown") for p in team.get("substitutes", [])]
                            bench_text = "\n".join(bench)

                            safe_post(
                                f"🪑 Bench\n\n{bench_text}",
                                state
                            )
                        break

        # -------------------------
        # Status changes
        # -------------------------
        if status != match_state["last_status"]:
            print(f"Status change: {status}", flush=True)

            # Kickoff
            if status == "1H" and not match_state["kickoff_posted"]:
                extras = []
                if referee:
                    extras.append(f"Referee: {referee}")
                if weather:
                    extras.append(f"Weather: {weather}")

                extra_text = "\n".join(extras)

                safe_post(
                    f"🟢 KICKOFF\n\n"
                    f"{home} vs {away}\n"
                    f"{venue}\n\n"
                    f"{extra_text}\n\n#NCFC",
                    state
                )

                match_state["kickoff_posted"] = True
                save_state(state)

            # Half-time
            elif status == "HT" and not high_signal_only(state):
                safe_post(
                    f"⏸ HT: {home} {goals_home}–{goals_away} {away}\n\n#NCFC",
                    state
                )

            # Full-time
            elif status == "FT":
                safe_post(
                    f"🏁 FT: {home} {goals_home}–{goals_away} {away}\n\n"
                    f"Up the Canaries 💛💚\n#NCFC",
                    state
                )
                save_state(state)
                time.sleep(600)
                continue

            match_state["last_status"] = status

        # -------------------------
        # Event fetching
        # -------------------------
        fetch_events = False
        if match_state["last_score"] and score != match_state["last_score"]:
            fetch_events = True
        if status in ("1H", "2H") and POLL_COUNT % 3 == 0:
            fetch_events = True
        if minute >= 80:
            fetch_events = True

        if fetch_events:
            print("Fetching events", flush=True)
            events_data = get_fixture_events(fixture_id)

            # Safety check
            if not events_data or len(events_data) == 0:
                print("No events returned, skipping", flush=True)
            else:
                for e in events_data:
                    e_minute = e.get("time", {}).get("elapsed") or 0
                    if e_minute <= match_state["last_event_minute"]:
                        continue

                    team_name = e.get("team", {}).get("name", "")
                    player_name = e.get("player", {}).get("name", "Unknown")
                    event_type = e.get("type", "")
                    detail = e.get("detail", "")

                    scoreline = f"{home} {goals_home}–{goals_away} {away}"

                    # Goals
                    if event_type == "Goal":
                        text = (f"⚽ GOAL!\n\n{scoreline}\n{player_name} ({e_minute}')\n\n#NCFC"
                                if team_name == home else
                                f"😕 Goal conceded\n\n{scoreline}\n{player_name} ({e_minute}')\n\n#NCFC")
                        safe_post(text, state)

                    # Red card
                    elif detail == "Red Card":
                        safe_post(
                            f"🟥 RED CARD\n\n{player_name} ({e_minute}')\n"
                            f"{home} vs {away}\n\n#NCFC",
                            state
                        )

                    # Yellow card
                    elif detail == "Yellow Card" and not high_signal_only(state):
                        safe_post(
                            f"🟨 Yellow card\n\n{player_name} ({e_minute}')\n"
                            f"{home} vs {away}\n\n#NCFC",
                            state
                        )

                    # Substitution
                    elif event_type == "subst" and detail == "Substitution" and team_name == home:
                        off_player = player_name
                        on_player = e.get("assist", {}).get("name", "Unknown")
                        safe_post(
                            f"🔄 Substitution ({e_minute}')\n\nOn: {on_player}\nOff: {off_player}\n\n#NCFC",
                            state
                        )

                    match_state["last_event_minute"] = max(
                        match_state["last_event_minute"],
                        e_minute
                    )

        match_state["last_score"] = score
        save_state(state)

        # -------------------------
        # Dynamic polling
        # -------------------------
        if status in ("1H", "2H"):
            sleep_time = 45 if minute >= 80 else 60
        elif status == "HT":
            sleep_time = 180
        else:
            sleep_time = 300

        POLL_COUNT += 1
        print(f"Sleeping {sleep_time}s", flush=True)
        time.sleep(sleep_time)

    except Exception as e:
        print("ERROR in main loop:", e, flush=True)
        time.sleep(60)



if __name__ == "__main__":
    main()

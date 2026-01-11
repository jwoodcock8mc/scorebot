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
    while True:
        try:
            print("Polling API-Football", flush=True)

            fixture = get_live_fixture()

            # No live Norwich match
            if not fixture:
                print("No live Norwich match", flush=True)
                time.sleep(300)
                continue

            fixture_id = fixture["fixture"]["id"]
            status = fixture["fixture"]["status"]["short"]
            minute = fixture["fixture"]["status"]["elapsed"] or 0

            home = fixture["teams"]["home"]["name"]
            away = fixture["teams"]["away"]["name"]

            goals_home = fixture["goals"]["home"]
            goals_away = fixture["goals"]["away"]
            score = (goals_home, goals_away)

            venue = fixture["fixture"]["venue"]["name"]
            referee = fixture["fixture"]["referee"]
            weather = fixture["fixture"].get("weather")

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

                lineups = get_fixture_lineups(fixture_id)

                for team in lineups:
                    if team["team"]["name"] == home:
                        formation = team["formation"]

                        starters = []
                        for p in team["startXI"]:
                            name = p["player"]["name"]
                            if p["player"].get("captain"):
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

                        # Bench reply
                        if ref and not high_signal_only(state):
                            bench = [p["player"]["name"] for p in team["substitutes"]]
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
            # Event fetching logic
            # -------------------------
            fetch_events = False

            if match_state["last_score"] and score != match_state["last_score"]:
                fetch_events = True

            if status in ("1H", "2H") and POLL_COUNT % 3 == 0:
                fetch_events = True

            if minute >= 80:
                fetch_events = True

            # -------------------------
            # Events
            # -------------------------
            if fetch_events:
                print("Fetching events", flush=True)
                events = get_fixture_events(fixture_id)

                for e in events:
                    e_minute = e["time"]["elapsed"] or 0

                    if e_minute <= match_state["last_event_minute"]:
                        continue

                    team = e["team"]["name"]
                    player = e["player"]["name"]
                    event_type = e["type"]
                    detail = e["detail"]

                    scoreline = f"{home} {goals_home}–{goals_away} {away}"

                    if event_type == "Goal":
                        if team == home:
                            text = f"⚽ GOAL!\n\n{scoreline}\n{player} ({e_minute}')\n\n#NCFC"
                        else:
                            text = f"😕 Goal conceded\n\n{scoreline}\n{player} ({e_minute}')\n\n#NCFC"
                        safe_post(text, state)

                    elif detail == "Red Card":
                        safe_post(
                            f"🟥 RED CARD\n\n{player} ({e_minute}')\n"
                            f"{home} vs {away}\n\n#NCFC",
                            state
                        )

                    elif detail == "Yellow Card" and not high_signal_only(state):
                        safe_post(
                            f"🟨 Yellow card\n\n{player} ({e_minute}')\n"
                            f"{home} vs {away}\n\n#NCFC",
                            state
                        )

                    elif (
                        event_type == "subst"
                        and detail == "Substitution"
                        and team == home
                    ):
                        off_player = e["player"]["name"]
                        on_player = e["assist"]["name"]

                        safe_post(
                            f"🔄 Substitution ({e_minute}')\n\n"
                            f"On: {on_player}\n"
                            f"Off: {off_player}\n\n#NCFC",
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

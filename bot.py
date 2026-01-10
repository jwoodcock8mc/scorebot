import time
from api_football import get_live_fixture, get_fixture_events, get_fixture_lineups
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
    		"last_score": None,
		"last_status": None,
		"last_event_minute": 0,
		"lineups_posted": False,
		"kickoff_posted": False
	})

	# -------------------------
	# Lineups (once per match)
	# -------------------------
	if not match_state["lineups_posted"] and status in ("NS", "1H"):
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

            	    post_ref = post(
    			f"📋 Norwich City XI ({formation})\n\n"
		        f"{lineup_text}\n\n#NCFC"
		    )
		    
		    bench = [p["player"]["name"] for p in team["substitutes"]]

		    bench_text = "\n".join(bench)

		    reply(
    			f"🪑 Bench\n\n{bench_text}",
			parent_uri=post_ref.uri,
			parent_cid=post_ref.cid
		    )

            	    match_state["lineups_posted"] = True
            	    break


        # --- Kickoff ---

	referee = fixture["fixture"]["referee"]
	weather = fixture["fixture"].get("weather")
	
	extras = []
	if referee:
	    extras.append(f"Referee: {referee}")
	if weather:
	    extras.append(f"Weather: {weather}")

	extra_text = "\n".join(extras)

	post(
	    f"🟢 KICKOFF\n\n"
	    f"{home} vs {away}\n"
	    f"{venue}\n\n"
	    f"{extra_text}\n\n#NCFC"
	)


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

import os
from dotenv import load_dotenv

load_dotenv()

# API-Football
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
API_FOOTBALL_HOST = "api-football-v1.p.rapidapi.com"

# Norwich City team ID in API-Football
NORWICH_TEAM_ID = 71   # confirmed API-Football ID

# League ID for EFL Championship
CHAMPIONSHIP_LEAGUE_ID = 40

# Bluesky
BLUESKY_HANDLE = os.getenv("BLUESKY_HANDLE")
BLUESKY_APP_PASSWORD = os.getenv("BLUESKY_APP_PASSWORD")

# Polling
LIVE_POLL_SECONDS = 45

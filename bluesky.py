from atproto import Client
from atproto_client.exceptions import RequestException
import time

client = Client()

def login(handle, password):
    client.login(handle, password)

def safe_post(text, state):
    from state import can_post, record_post, save_state

    if not can_post(state):
        print("Post skipped: daily Bluesky limit reached")
        return None

    try:
        ref = client.send_post(text)
        record_post(state)
        save_state(state)
        return ref

    except RequestException as e:
        if "RateLimitExceeded" in str(e):
            print("Bluesky rate limit exceeded — sleeping 24h")
            time.sleep(86400)
            return None
        raise

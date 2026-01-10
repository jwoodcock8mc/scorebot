from atproto import Client
from config import BLUESKY_HANDLE, BLUESKY_APP_PASSWORD

client = Client()

def login():
    client.login(BLUESKY_HANDLE, BLUESKY_APP_PASSWORD)

def post(text):
    return client.send_post(text)

def reply(text, parent_uri, parent_cid):
    client.send_post(
        text=text,
        reply_to={
            "root": {"uri": parent_uri, "cid": parent_cid},
            "parent": {"uri": parent_uri, "cid": parent_cid},
        }
    )


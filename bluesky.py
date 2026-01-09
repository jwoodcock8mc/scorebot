from atproto import Client
from config import BLUESKY_HANDLE, BLUESKY_APP_PASSWORD

client = Client()

def login():
    client.login(BLUESKY_HANDLE, BLUESKY_APP_PASSWORD)

def post(text):
    client.send_post(text)

import requests
import os
import json

LAST_RELEASE_FILE = "last_release.json"

# ✅ Load secrets
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

DISCORD_ROLE_ID = "1342206955745317005"  # Notification Role

ARTIST_ID = "4pqIwzgTlrlpRqHvWvNtVd"

# ✅ Function: Get Spotify API Token
def get_spotify_token():
    url = "https://accounts.spotify.com/api/token"
    response = requests.post(url, data={
        "grant_type": "client_credentials",
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET
    }, headers={"Content-Type": "application/x-www-form-urlencoded"})
    return response.json().get("access_token")

# ✅ Function: Check for new releases
def check_new_release():
    token = get_spotify_token()
    url = f"https://api.spotify.com/v1/artists/{ARTIST_ID}/albums?include_groups=single,album&limit=1"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)
    data = response.json()

    if "items" in data and data["items"]:
        latest = data["items"][0]
        return latest["name"], latest["release_date"], latest["external_urls"]["spotify"], latest["images"][0]["url"]
    return None, None, None, None

# ✅ Function: Load last release from file
def load_last_release():
    if os.path.exists(LAST_RELEASE_FILE):
        with open(LAST_RELEASE_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return None
    return None

# ✅ Function: Save last release to file
def save_last_release(album_name):
    with open(LAST_RELEASE_FILE, "w") as f:
        json.dump({"last_release": album_name}, f)

# 🔥 Function: Send Discord notification
def send_discord_notification(album_name, release_date, spotify_url, cover_url):
    message = f"<@&{DISCORD_ROLE_ID}> 🔥 **New Surreal.wav Release!** 🎧"
    embed = {
        "content": message,
        "embeds": [{
            "title": album_name,
            "description": f"📅 **Release Date:** {release_date}\n🔗 **[Listen on Spotify]({spotify_url})**",
            "color": 16711680,
            "thumbnail": {"url": cover_url}
        }]
    }

    requests.post(DISCORD_WEBHOOK_URL, json=embed, headers={"Content-Type": "application/json"})

# ✅ Load last release and compare
last_saved = load_last_release()
album_name, release_date, spotify_url, cover_url = check_new_release()

if album_name and (not last_saved or last_saved.get("last_release") != album_name):
    print(f"🎉 New release found: {album_name}")
    send_discord_notification(album_name, release_date, spotify_url, cover_url)
    save_last_release(album_name)  # ✅ Save the new release to prevent duplicates
else:
    print("😴 No new releases found.")

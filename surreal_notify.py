import requests
import os
import json
from urllib.parse import urlparse

# ---------- Konfiguration ----------
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
LAST_RELEASE_FILE = "last_release.json"

# ---------- Datenbank ----------
def load_releases():
    try:
        with open(LAST_RELEASE_FILE, "r") as f:
            return json.load(f).get("releases", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_release(release_id):
    releases = load_releases()
    if release_id not in releases:
        releases.append(release_id)
        with open(LAST_RELEASE_FILE, "w") as f:
            json.dump({"releases": releases}, f, indent=2)

# ---------- Spotify API ----------
def get_spotify_token():
    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
    )
    return response.json().get("access_token")

def fetch_latest_release():
    token = get_spotify_token()
    if not token:
        return None
    
    response = requests.get(
        "https://api.spotify.com/v1/artists/4pqIwzgTlrlpRqHvWvNtVd/albums?include_groups=single,album&limit=1",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    data = response.json()
    if data.get("items"):
        latest = data["items"][0]
        return {
            "id": latest["id"],
            "name": latest["name"],
            "date": latest["release_date"],
            "url": latest["external_urls"]["spotify"],
            "cover": latest["images"][0]["url"] if latest["images"] else ""
        }
    return None

# ---------- Notifications ----------
def send_discord(release):
    if not DISCORD_WEBHOOK_URL:
        return
    
    embed = {
        "content": f"🔥 **Neuer Release!** {release['name']}",
        "embeds": [{
            "title": release["name"],
            "url": release["url"],
            "thumbnail": {"url": release["cover"]}
        }]
    }
    requests.post(DISCORD_WEBHOOK_URL, json=embed)

def send_telegram(release):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    
    keyboard = {"inline_keyboard": [[{"text": "🎵 Spotify", "url": release["url"]}]]}
    
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "photo": release["cover"],
            "caption": f"🔥 *{release['name']}*\n📅 {release['date']}",
            "parse_mode": "Markdown",
            "reply_markup": json.dumps(keyboard)
        }
    )

# ---------- Hauptlogik ----------
if __name__ == "__main__":
    latest_release = fetch_latest_release()
    if latest_release:
        existing_releases = load_releases()
        
        if latest_release["id"] not in existing_releases:
            send_discord(latest_release)
            send_telegram(latest_release)
            save_release(latest_release["id"])

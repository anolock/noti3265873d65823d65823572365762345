import requests
import os
import json
from urllib.parse import urlparse

# Konfiguration
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
PROMOTION_CODE = os.getenv("PROMOTION_CODE")
DISCORD_ROLE_ID = "1342206955745317005"
DB_FILE = "releases_db.json"

# Datenbank
def load_database():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f).get("processed", [])
    except:
        return []

def update_database(release_id):
    db = {"processed": load_database()}
    if release_id not in db["processed"]:
        db["processed"].append(release_id)
        with open(DB_FILE, "w") as f:
            json.dump(db, f, indent=2)

# Spotify API
def get_spotify_release():
    # Get Access Token
    token_response = requests.post(
        "https://accounts.spotify.com/api/token",
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
        data={"grant_type": "client_credentials"}
    )
    
    if token_response.status_code != 200:
        return None

    access_token = token_response.json().get("access_token")
    
    # Get Latest Release
    releases_response = requests.get(
        "https://api.spotify.com/v1/artists/4pqIwzgTlrlpRqHvWvNtVd/albums",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"include_groups": "single,album", "limit": 1}
    )
    
    if releases_response.status_code != 200:
        return None

    latest = releases_response.json().get("items", [{}])[0]
    return {
        "id": latest.get("id"),
        "name": latest.get("name"),
        "date": latest.get("release_date"),
        "url": latest.get("external_urls", {}).get("spotify"),
        "cover": latest.get("images", [{}])[0].get("url")
    }

# Benachrichtigungen
def send_discord(release):
    requests.post(
        DISCORD_WEBHOOK_URL,
        json={
            "content": f"<@&{DISCORD_ROLE_ID}> 🔥 New Surreal.wav Release! 🎧",
            "embeds": [{
                "title": release["name"],
                "description": f"📅 {release['date']}\n🔗 [Listen on Spotify]({release['url']})",
                "color": 16711680,
                "thumbnail": {"url": release["cover"]}
            }]
        }
    )

def send_telegram(release):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "photo": release["cover"],
            "caption": (
                f"🔥 *New Surreal.wav Release!* 🎧\n\n"
                f"🎵 **{release['name']}**\n"
                f"📅 {release['date']}\n"
                f"[Listen on Spotify]({release['url']})"
            ),
            "parse_mode": "Markdown"
        }
    )

# Manuelle Promotion
def process_telegram_commands():
    updates = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates").json()
    for update in updates.get("result", []):
        if "message" in update and update["message"].get("text", "").startswith("/promote"):
            parts = update["message"]["text"].split()
            if len(parts) == 3 and parts[1] == PROMOTION_CODE:
                url = parts[2]
                release_id = urlparse(url).path.split("/")[-1]
                if release_id not in load_database():
                    release_data = {
                        "id": release_id,
                        "name": "MANUAL RELEASE",
                        "date": "2025-02-20",
                        "url": url,
                        "cover": "https://i.scdn.co/image/ab67616d0000b273..."
                    }
                    send_discord(release_data)
                    send_telegram(release_data)
                    update_database(release_id)

# Hauptlogik
if __name__ == "__main__":
    process_telegram_commands()
    
    latest_release = get_spotify_release()
    if latest_release and latest_release["id"] not in load_database():
        send_discord(latest_release)
        send_telegram(latest_release)
        update_database(latest_release["id"])

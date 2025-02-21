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
PROMOTION_CODE = os.getenv("PROMOTION_CODE")
DISCORD_ROLE_ID = "1342206955745317005"
DATABASE_FILE = "processed_releases.json"

# ---------- Datenbank (Workflow-sicher) ----------
def load_database():
    try:
        with open(DATABASE_FILE, "r") as f:
            return json.load(f).get("releases", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_to_database(release_id):
    releases = load_database()
    if release_id not in releases:
        releases.append(release_id)
        with open(DATABASE_FILE, "w") as f:
            json.dump({"releases": releases}, f, indent=2)

# ---------- Spotify Check (Einmal pro Run) ----------
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
        album = data["items"][0]
        return {
            "id": album["id"],
            "name": album["name"],
            "date": album["release_date"],
            "url": album["external_urls"]["spotify"],
            "cover": album["images"][0]["url"] if album["images"] else ""
        }
    return None

# ---------- Notifications (Formatiert) ----------
def send_discord(release):
    embed = {
        "content": f"<@&{DISCORD_ROLE_ID}> 🔔・Notification・🔥 New Surreal.wav Release! 🎧",
        "embeds": [{
            "title": release["name"],
            "description": f"📅 **Release Date**: {release['date']}\n🔗 [Listen on Spotify]({release['url']})",
            "color": 16711680,
            "thumbnail": {"url": release["cover"]}
        }]
    }
    requests.post(DISCORD_WEBHOOK_URL, json=embed)

def send_telegram(release):
    message = (
        "🔥 *New Surreal.wav Release!* 🎧\n\n"
        f"🎵 *{release['name']}*\n"
        f"📅 *Release Date*: {release['date']}\n"
        f"🔗 [Listen on Spotify]({release['url']})"
    )
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "photo": release["cover"],
            "caption": message,
            "parse_mode": "Markdown"
        }
    )

# ---------- Manuelle Promotion (Code-geschützt) ----------
def process_commands():
    response = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates").json()
    for update in response.get("result", []):
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
                        "cover": "https://example.com/cover.jpg"  # Manuell anpassen
                    }
                    send_discord(release_data)
                    send_telegram(release_data)
                    save_to_database(release_id)

# ---------- Hauptlogik (Kein Loop!) ----------
if __name__ == "__main__":
    process_commands()  # Verarbeite manuelle Befehle
    latest_release = fetch_latest_release()  # Einmaliger Check
    if latest_release and latest_release["id"] not in load_database():
        send_discord(latest_release)
        send_telegram(latest_release)
        save_to_database(latest_release["id"])

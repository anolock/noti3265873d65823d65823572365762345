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
DATABASE_FILE = "surreal_db.json"

# ---------- Atomic Database ----------
def load_database():
    try:
        with open(DATABASE_FILE, "r") as f:
            return json.load(f).get("processed", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def update_database(release_id):
    db = {"processed": load_database()}
    if release_id not in db["processed"]:
        db["processed"].append(release_id)
        with open(DATABASE_FILE, "w") as f:
            json.dump(db, f, indent=2, ensure_ascii=False)

# ---------- Notification Templates ----------
def send_discord_alert(release):
    payload = {
        "content": f"<@&{DISCORD_ROLE_ID}> 🔔・Notification・🔥 New Surreal.wav Release! 🎧",
        "embeds": [{
            "title": release["name"],
            "description": f"📅 **Release Date**: {release['date']}\n🔗 [Listen on Spotify]({release['url']})",
            "color": 16711680,
            "thumbnail": {"url": release["cover"]}
        }]
    }
    requests.post(DISCORD_WEBHOOK_URL, json=payload)

def send_telegram_alert(release):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "photo": release["cover"],
            "caption": (
                f"🔥 *New Surreal.wav Release!* 🎧\n\n"
                f"🎵 **{release['name']}**\n"
                f"📅 {release['date']}\n"
                f"[SPOTIFY]({release['url']})"
            ),
            "parse_mode": "Markdown"
        }
    )

# ---------- Core Logic ----------
def spotify_check():
    token = requests.post(
        "https://accounts.spotify.com/api/token",
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
        data={"grant_type": "client_credentials"}
    ).json().get("access_token")

    if token:
        response = requests.get(
            "https://api.spotify.com/v1/artists/4pqIwzgTlrlpRqHvWvNtVd/albums?include_groups=single,album&limit=1",
            headers={"Authorization": f"Bearer {token}"}
        )
        album = response.json().get("items", [{}])[0]
        return {
            "id": album.get("id"),
            "name": album.get("name"),
            "date": album.get("release_date"),
            "url": album.get("external_urls", {}).get("spotify"),
            "cover": album.get("images", [{}])[0].get("url")
        } if album.get("id") else None

def process_commands():
    updates = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates").json()
    for update in updates.get("result", []):
        if "/promote" in update.get("message", {}).get("text", ""):
            parts = update["message"]["text"].split()
            if len(parts) == 3 and parts[1] == PROMOTION_CODE:
                url = parts[2]
                release_id = urlparse(url).path.split("/")[-1]
                if release_id not in load_database():
                    update_database(release_id)
                    send_discord_alert({
                        "name": "MANUAL RELEASE",
                        "date": "2025-02-20",
                        "url": url,
                        "cover": "https://i.scdn.co/image/ab67616d0000b273..."
                    })
                    send_telegram_alert({
                        "name": "MANUAL RELEASE",
                        "date": "2025-02-20",
                        "url": url,
                        "cover": "https://i.scdn.co/image/ab67616d0000b273..."
                    })

if __name__ == "__main__":
    process_commands()
    latest = spotify_check()
    if latest and latest["id"] not in load_database():
        send_discord_alert(latest)
        send_telegram_alert(latest)
        update_database(latest["id"])

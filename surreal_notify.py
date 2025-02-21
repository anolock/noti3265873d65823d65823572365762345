import requests
import os
import json
import time
from urllib.parse import urlparse

# ---------- Konfiguration ----------
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
DISCORD_ROLE_ID = "1342206955745317005"  # Anpassen!
LAST_RELEASE_FILE = "last_release.json"

# ---------- Debugging ----------
print("🚀 Initialisiere Bot...")
print(f"🔍 Discord-Webhook: {'✅' if DISCORD_WEBHOOK_URL else '❌'}")
print(f"🔍 Telegram-Token: {'✅' if TELEGRAM_BOT_TOKEN else '❌'}")

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
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        return None
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
    
    # Hole die NEUESTEN Releases (nicht den ersten Eintrag!)
    url = "https://api.spotify.com/v1/artists/4pqIwzgTlrlpRqHvWvNtVd/albums?include_groups=single,album&limit=1"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
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
    except Exception as e:
        print(f"❌ Spotify-Fehler: {str(e)}")
    return None

# ---------- Notifications ----------
def send_discord(release):
    if not DISCORD_WEBHOOK_URL:
        return
    
    embed = {
        "content": f"<@&{DISCORD_ROLE_ID}> 🔥 **Neuer Release!**",
        "embeds": [{
            "title": release["name"],
            "url": release["url"],
            "description": f"📅 {release['date']}",
            "color": 0xFF0000,
            "thumbnail": {"url": release["cover"]}
        }]
    }
    requests.post(DISCORD_WEBHOOK_URL, json=embed)

def send_telegram(release):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    
    # Alles in EINER Nachricht: Bild + Text + Button
    keyboard = {"inline_keyboard": [[{"text": "🎵 Auf Spotify hören", "url": release["url"]}]]}
    
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

# ---------- Telegram Commands ----------
def process_telegram_commands():
    if not TELEGRAM_BOT_TOKEN:
        return
    
    updates = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates").json()
    for update in updates.get("result", []):
        if "message" in update and update["message"].get("text", "").startswith("/release"):
            text = update["message"]["text"]
            parts = text.split()
            if len(parts) == 3 and parts[1] == "4852":  # Code: 4852
                spotify_url = parts[2]
                album_id = urlparse(spotify_url).path.split("/")[-1]
                
                if album_id in load_releases():
                    requests.post(
                        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                        data={"chat_id": update["message"]["chat"]["id"], "text": "❌ Release existiert bereits!"}
                    )
                else:
                    # Füge manuell hinzu und sende sofort
                    save_release(album_id)
                    release = fetch_latest_release()
                    if release and release["id"] == album_id:
                        send_discord(release)
                        send_telegram(release)
                        requests.post(
                            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                            data={"chat_id": update["message"]["chat"]["id"], "text": "✅ Release gesendet!"}
                        )

# ---------- Hauptlogik ----------
if __name__ == "__main__":
    process_telegram_commands()  # Zuerst manuelle Befehle
    
    latest_release = fetch_latest_release()
    if latest_release and latest_release["id"] not in load_releases():
        print(f"🎉 Neuer Release: {latest_release['name']}")
        send_discord(latest_release)
        send_telegram(latest_release)
        save_release(latest_release["id"])
    else:
        print("😴 Keine neuen Releases.")

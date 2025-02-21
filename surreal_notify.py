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
DISCORD_ROLE_ID = "1342206955745317005"
DB_FILE = "processed_releases.json"
LAST_UPDATE_FILE = "last_telegram_update.txt"
PROMO_CODE = "4852"

# Datenbank
def load_db():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f).get("processed", [])
    except:
        return []

def save_to_db(release_id):
    current = load_db()
    if release_id not in current:
        current.append(release_id)
        with open(DB_FILE, "w") as f:
            json.dump({"processed": current}, f, indent=2)

# Telegram Update-Tracking
def get_last_update_id():
    try:
        with open(LAST_UPDATE_FILE, "r") as f:
            return int(f.read().strip())
    except:
        return 0

def save_last_update_id(update_id):
    with open(LAST_UPDATE_FILE, "w") as f:
        f.write(str(update_id))

# Spotify API
def get_track_details(track_id):
    token = requests.post(
        "https://accounts.spotify.com/api/token",
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
        data={"grant_type": "client_credentials"}
    ).json().get("access_token")

    response = requests.get(
        f"https://api.spotify.com/v1/tracks/{track_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        track = response.json()
        return {
            "id": track["id"],
            "name": track["name"],
            "artist": track["artists"][0]["name"],
            "url": track["external_urls"]["spotify"],
            "cover": track["album"]["images"][0]["url"]
        }
    return None

# Benachrichtigungen
def send_alert(release):
    # Discord
    requests.post(
        DISCORD_WEBHOOK_URL,
        json={
            "content": f"<@&{DISCORD_ROLE_ID}> 🔥 Neuer Surreal.wav Release! 🎧",
            "embeds": [{
                "title": release["name"],
                "description": f"🎤 {release['artist']}\n🔗 [Auf Spotify hören]({release['url']})",
                "color": 16711680,
                "thumbnail": {"url": release["cover"]}
            }]
        }
    )

    # Telegram
    keyboard = {
        "inline_keyboard": [[{
            "text": "🎵 Jetzt streamen", 
            "url": release["url"]
        }]]
    }
    
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "photo": release["cover"],
            "caption": f"🔥 *{release['name']}*\n🎤 {release['artist']}",
            "parse_mode": "Markdown",
            "reply_markup": json.dumps(keyboard)
        }
    )

# Telegram-Befehle verarbeiten
def process_commands():
    last_processed_id = get_last_update_id()
    new_max_id = last_processed_id
    
    response = requests.get(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates",
        params={"offset": last_processed_id + 1}
    )
    
    for update in response.json().get("result", []):
        update_id = update["update_id"]
        new_max_id = max(new_max_id, update_id)
        
        if "message" in update and update["message"]["text"].startswith("/r "):
            parts = update["message"]["text"].split()
            if len(parts) == 3 and parts[1] == PROMO_CODE:
                track_url = parts[2]
                try:
                    track_id = urlparse(track_url).path.split("/")[-1]
                    existing = load_db()
                    
                    if track_id not in existing:
                        track_data = get_track_details(track_id)
                        if track_data:
                            send_alert(track_data)
                            save_to_db(track_id)
                            requests.post(
                                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                                json={"chat_id": update["message"]["chat"]["id"], "text": "✅ Release gesendet!"}
                            )
                        else:
                            requests.post(
                                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                                json={"chat_id": update["message"]["chat"]["id"], "text": "❌ Ungültiger Spotify-Link!"}
                            )
                    else:
                        requests.post(
                            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                            json={"chat_id": update["message"]["chat"]["id"], "text": "⚠️ Release wurde bereits gesendet!"}
                        )
                except:
                    requests.post(
                        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                        json={"chat_id": update["message"]["chat"]["id"], "text": "❌ Fehlerhafte Eingabe!"}
                    )
    
    save_last_update_id(new_max_id)

# Automatische Spotify-Checks
def check_artist_releases():
    token = requests.post(
        "https://accounts.spotify.com/api/token",
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
        data={"grant_type": "client_credentials"}
    ).json().get("access_token")

    response = requests.get(
        "https://api.spotify.com/v1/artists/4pqIwzgTlrlpRqHvWvNtVd/albums",
        headers={"Authorization": f"Bearer {token}"},
        params={"include_groups": "single,album", "limit": 1}
    )
    
    if response.status_code == 200:
        latest_album = response.json()["items"][0]
        return {
            "id": latest_album["id"],
            "name": latest_album["name"],
            "artist": "Surreal.wav",
            "url": latest_album["external_urls"]["spotify"],
            "cover": latest_album["images"][0]["url"]
        }
    return None

# Hauptlogik
if __name__ == "__main__":
    process_commands()
    
    latest = check_artist_releases()
    if latest and latest["id"] not in load_db():
        send_alert(latest)
        save_to_db(latest["id"])

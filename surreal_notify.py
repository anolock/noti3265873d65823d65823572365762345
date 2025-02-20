import requests
import os
import time

# ✅ Debugging: Zeige ALLE Secrets (NICHT in den Logs von GitHub sichtbar)
def debug_secrets():
    print("DEBUGGING ENVIRONMENT VARIABLES:")
    secrets = [
        "DISCORD_WEBHOOK_URL",
        "SPOTIFY_CLIENT_ID",
        "SPOTIFY_CLIENT_SECRET",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID"
    ]
    for secret in secrets:
        value = os.getenv(secret)
        if value is None:
            print(f"⚠️ {secret} is MISSING! Check your GitHub Secrets.")
        else:
            print(f"✅ {secret} is loaded.")

debug_secrets()  # 🛠️ Debug direkt beim Start

# ✅ Lade Secrets aus Umgebungsvariablen mit Fallbacks
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 🚨 Falls ein wichtiges Secret fehlt → Loggen & in Warteschleife gehen
critical_secrets = {
    "DISCORD_WEBHOOK_URL": DISCORD_WEBHOOK_URL,
    "SPOTIFY_CLIENT_ID": SPOTIFY_CLIENT_ID,
    "SPOTIFY_CLIENT_SECRET": SPOTIFY_CLIENT_SECRET,
    "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
    "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID,
}

for key, value in critical_secrets.items():
    if value is None:
        print(f"❌ ERROR: {key} is missing! The bot cannot run.")
        while True:
            print("⏳ Waiting for environment variables to be set...")
            time.sleep(300)  # Wartet 5 Minuten und checkt dann erneut

# ✅ Spotify Artist ID für Surreal.wav
ARTIST_ID = "4pqIwzgTlrlpRqHvWvNtVd"

# 🔥 Funktion: Spotify API Access Token abrufen
def get_spotify_token():
    url = "https://accounts.spotify.com/api/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET
    }
    response = requests.post(url, headers=headers, data=data)
    return response.json().get("access_token")

# 🔥 Funktion: Checken, ob neuer Release verfügbar ist
def check_new_release():
    token = get_spotify_token()
    url = f"https://api.spotify.com/v1/artists/{ARTIST_ID}/albums?include_groups=single,album&limit=1"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)
    data = response.json()

    if "items" in data and data["items"]:
        latest_release = data["items"][0]
        album_name = latest_release["name"]
        release_date = latest_release["release_date"]
        spotify_url = latest_release["external_urls"]["spotify"]
        cover_url = latest_release["images"][0]["url"]

        return album_name, release_date, spotify_url, cover_url
    return None, None, None, None

# 🔥 Funktion: Discord Nachricht senden
def send_discord_notification(message, album_name=None, release_date=None, spotify_url=None, cover_url=None):
    embed = {"content": message, "embeds": []}

    if album_name:
        embed["embeds"].append({
            "title": album_name,
            "description": f"📅 **Release Date:** {release_date}\n🔗 **[Listen on Spotify]({spotify_url})**",
            "color": 16711680,
            "thumbnail": {"url": cover_url}
        })

    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=embed, headers=headers)
        if response.status_code == 204:
            print("✅ Discord notification sent successfully.")
        else:
            print(f"⚠️ Discord notification failed! HTTP {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error sending Discord notification: {e}")

# 🔥 Funktion: Telegram Nachricht senden
def send_telegram_notification(message, cover_url=None):
    try:
        # 1️⃣ Nachricht senden
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        response = requests.post(url, data=data)

        if response.status_code == 200:
            print("✅ Telegram message sent successfully.")
        else:
            print(f"⚠️ Telegram message failed! HTTP {response.status_code} - {response.text}")

        # 2️⃣ Falls es ein Cover-Bild gibt, separat senden
        if cover_url:
            url_photo = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
            data_photo = {"chat_id": TELEGRAM_CHAT_ID, "photo": cover_url}
            requests.post(url_photo, data=data_photo)
    except Exception as e:
        print(f"❌ Error sending Telegram notification: {e}")

# ✅ Einmalige "Bot aktiviert"-Nachricht senden
send_discord_notification("🚀 **SurrealBot is now active!** I'm monitoring new releases. 🎶")
send_telegram_notification("🚀 **SurrealBot is now active!** I'm monitoring new releases. 🎶")

# ✅ Letzter Release-Name speichern
last_release = None

while True:
    try:
        album_name, release_date, spotify_url, cover_url = check_new_release()

        # ✅ Falls neuer Release → Nachricht senden
        if album_name and album_name != last_release:
            send_discord_notification("🔥 **New Surreal.wav Release!** 🎧", album_name, release_date, spotify_url, cover_url)
            telegram_msg = f"🔥 **New Surreal.wav Release!** 🎧\n📅 {release_date}\n🔗 [Listen on Spotify]({spotify_url})"
            send_telegram_notification(telegram_msg, cover_url)
            last_release = album_name  # Letzten Release speichern

    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    print("⏳ Sleeping for 5 minutes...")
    time.sleep(300)  # Warten bevor erneuter Check

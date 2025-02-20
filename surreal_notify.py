import requests
import os
import time

# ✅ Debugging: Zeige ALLE Secrets (außer sensible Daten) an
print("DEBUGGING ENVIRONMENT VARIABLES:")
print("DISCORD_WEBHOOK_URL:", os.getenv("DISCORD_WEBHOOK_URL"))
print("SPOTIFY_CLIENT_ID:", os.getenv("SPOTIFY_CLIENT_ID"))
print("SPOTIFY_CLIENT_SECRET:", os.getenv("SPOTIFY_CLIENT_SECRET"))
print("TELEGRAM_BOT_TOKEN:", os.getenv("TELEGRAM_BOT_TOKEN"))
print("TELEGRAM_CHAT_ID:", os.getenv("TELEGRAM_CHAT_ID"))

# ✅ Lade die Secrets korrekt
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "NOT_FOUND")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "NOT_FOUND")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "NOT_FOUND")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "NOT_FOUND")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "NOT_FOUND")

# ✅ Debugging: Prüfe, ob Secrets geladen wurden
print("\nAFTER LOADING SECRETS:")
print("DISCORD_WEBHOOK_URL:", DISCORD_WEBHOOK_URL)
print("SPOTIFY_CLIENT_ID:", SPOTIFY_CLIENT_ID)
print("SPOTIFY_CLIENT_SECRET:", SPOTIFY_CLIENT_SECRET)
print("TELEGRAM_BOT_TOKEN:", TELEGRAM_BOT_TOKEN)
print("TELEGRAM_CHAT_ID:", TELEGRAM_CHAT_ID)



# ✅ Spotify Artist ID für Surreal.wav
ARTIST_ID = "4pqIwzgTlrlpRqHvWvNtVd"

# ✅ API Keys (aus GitHub Secrets)
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 🔥 Funktion: Spotify API Access Token abrufen
def get_spotify_token():
    url = "https://accounts.spotify.com/api/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
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

# 🔥 Funktion: Discord Nachricht senden (MIT EMBEDDING)
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
    requests.post(DISCORD_WEBHOOK_URL, json=embed, headers=headers)

# 🔥 Funktion: Telegram Nachricht senden (OHNE EMBEDDING)
def send_telegram_notification(message, cover_url=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, data=data)

    # Falls es ein Cover-Bild gibt, separat senden
    if cover_url:
        url_photo = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        data_photo = {"chat_id": TELEGRAM_CHAT_ID, "photo": cover_url}
        requests.post(url_photo, data=data_photo)

# ✅ Einmalige "Bot aktiviert"-Nachricht senden
send_discord_notification("🚀 **SurrealBot aktiviert!** Ich überwache neue Releases. 🎶")
send_telegram_notification("🚀 **SurrealBot aktiviert!** Ich überwache neue Releases. 🎶")

# ✅ Letzter Release-Name speichern
last_release = None

while True:
    album_name, release_date, spotify_url, cover_url = check_new_release()

    # ✅ Falls neuer Release → Nachricht senden
    if album_name and album_name != last_release:
        # Discord Nachricht (mit Rich Embedding)
        send_discord_notification("🔥 **Neuer Surreal.wav Release!** 🎧", album_name, release_date, spotify_url, cover_url)

        # Telegram Nachricht (nur Text + separates Bild)
        telegram_msg = f"🔥 **Neuer Surreal.wav Release!** 🎧\n📅 {release_date}\n🔗 [Spotify]({spotify_url})"
        send_telegram_notification(telegram_msg, cover_url)

        last_release = album_name  # Letzten Release speichern

    # ⏳ Warten, bevor der nächste Check startet (5 Minuten)
    time.sleep(300)

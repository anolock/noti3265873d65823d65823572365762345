import requests
import os
import json
import time  # ✅ WICHTIG für die 5-Minuten-Pause

# ✅ Lade Secrets aus GitHub Actions
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

DISCORD_ROLE_ID = "1342206955745317005"  # Discord-Rolle für Ping

# ✅ Fehlerprüfung für fehlende Secrets
missing_secrets = [k for k, v in {
    "DISCORD_WEBHOOK_URL": DISCORD_WEBHOOK_URL,
    "SPOTIFY_CLIENT_ID": SPOTIFY_CLIENT_ID,
    "SPOTIFY_CLIENT_SECRET": SPOTIFY_CLIENT_SECRET,
    "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
    "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID
}.items() if not v]

if missing_secrets:
    print(f"❌ ERROR: Missing secrets: {', '.join(missing_secrets)}")
    exit(1)

# ✅ Spotify Artist ID für Surreal.wav
ARTIST_ID = "4pqIwzgTlrlpRqHvWvNtVd"

# 🔥 Funktion: Hole Spotify API Token
def get_spotify_token():
    url = "https://accounts.spotify.com/api/token"
    response = requests.post(url, data={
        "grant_type": "client_credentials",
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET
    }, headers={"Content-Type": "application/x-www-form-urlencoded"})
    return response.json().get("access_token")

# 🔥 Funktion: Prüfe auf neue Releases
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

# 🔥 Funktion: Discord-Benachrichtigung
def send_discord_notification(album_name, release_date, spotify_url, cover_url):
    message = f"<@&{DISCORD_ROLE_ID}> 🔥 **New Surreal.wav Release!** 🎧"
    embed = {
        "content": message,
        "embeds": [{
            "title": album_name,
            "description": f"📅 **Release Date:** {release_date}\n🔗 **[Listen on Spotify]({spotify_url})**",
            "color": 16711680,  # Rot
            "thumbnail": {"url": cover_url}
        }]
    }
    
    requests.post(DISCORD_WEBHOOK_URL, json=embed, headers={"Content-Type": "application/json"})

# 🔥 Funktion: Telegram-Benachrichtigung mit Button
def send_telegram_notification(album_name, release_date, spotify_url, cover_url):
    print("📢 Sending Telegram notification...")

    base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    
    # 📸 Bild mit Caption
    message_text = (
        f"🔥 **New Surreal.wav Release!** 🎧\n\n"
        f"🎵 *{album_name}*\n"
        f"📅 **Release Date:** {release_date}"
    )

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "photo": cover_url,
        "caption": message_text,
        "parse_mode": "Markdown"
    }
    
    response = requests.post(f"{base_url}/sendPhoto", data=payload)
    
    if response.status_code == 200:
        print("✅ Telegram image + caption sent successfully!")
    else:
        print(f"⚠️ Telegram image upload failed: {response.text}")

    # 🎶 Inline-Button zu Spotify
    keyboard = {
        "inline_keyboard": [[{"text": "🎶 Listen on Spotify", "url": spotify_url}]]
    }

    button_payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "reply_markup": json.dumps(keyboard),
        "text": "⬇️ Click below to stream 🎶"
    }
    
    response = requests.post(f"{base_url}/sendMessage", data=button_payload)
    
    if response.status_code == 200:
        print("✅ Telegram button sent successfully!")
    else:
        print(f"⚠️ Telegram button failed: {response.text}")

# ✅ Start Loop (läuft dauerhaft)
while True:
    print("🔄 Running release check loop...")
    
    album_name, release_date, spotify_url, cover_url = check_new_release()

    if album_name:
        last_release_file = "last_release.txt"

        if os.path.exists(last_release_file):
            with open(last_release_file, "r") as f:
                last_release = f.read().strip()
        else:
            last_release = None

        if album_name != last_release:
            print(f"🎉 New release found: {album_name}")

            send_discord_notification(album_name, release_date, spotify_url, cover_url)
            send_telegram_notification(album_name, release_date, spotify_url, cover_url)

            with open(last_release_file, "w") as f:
                f.write(album_name)
        else:
            print("😴 No new releases found.")

    # 🕒 Warte 5 Minuten, bevor erneut geprüft wird
    time.sleep(300)

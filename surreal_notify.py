import os
import requests
import time

# ✅ Debugging: Zeige ALLE Secrets
print("DEBUGGING ENVIRONMENT VARIABLES:")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "MISSING_WEBHOOK")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "MISSING_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "MISSING_SECRET")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "MISSING_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "MISSING_CHAT")

print("DISCORD_WEBHOOK_URL:", DISCORD_WEBHOOK_URL)
print("SPOTIFY_CLIENT_ID:", SPOTIFY_CLIENT_ID)
print("SPOTIFY_CLIENT_SECRET:", SPOTIFY_CLIENT_SECRET)
print("TELEGRAM_BOT_TOKEN:", TELEGRAM_BOT_TOKEN)
print("TELEGRAM_CHAT_ID:", TELEGRAM_CHAT_ID)

# 🔥 Sicherstellen, dass alle Secrets geladen wurden
if "MISSING_" in DISCORD_WEBHOOK_URL:
    raise ValueError("❌ DISCORD_WEBHOOK_URL is missing! Check your GitHub Secrets.")

if "MISSING_" in TELEGRAM_BOT_TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN is missing! Check your GitHub Secrets.")

if "MISSING_" in TELEGRAM_CHAT_ID:
    raise ValueError("❌ TELEGRAM_CHAT_ID is missing! Check your GitHub Secrets.")

# ✅ Falls alles passt → Starte normalen Code
print("✅ All environment variables loaded successfully.")

# 🔥 Function: Get Spotify API Token
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

# 🔥 Function: Check for New Releases
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

# 🔥 Function: Send Discord Notification
def send_discord_notification(album_name, release_date, spotify_url, cover_url):
    embed = {
        "content": "**New Surreal.wav Release!** 🎧",
        "embeds": [
            {
                "title": album_name,
                "description": f"📅 **Release Date:** {release_date}\n🔗 **[Listen on Spotify]({spotify_url})**",
                "color": 16711680,
                "thumbnail": {"url": cover_url}
            }
        ]
    }
    
    headers = {"Content-Type": "application/json"}
    requests.post(DISCORD_WEBHOOK_URL, json=embed, headers=headers)

# 🔥 Function: Send Telegram Notification in 3 Messages
def send_telegram_notification(album_name, release_date, spotify_url, cover_url):
    base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

    # 1️⃣ Send Title
    requests.post(f"{base_url}/sendMessage", data={"chat_id": TELEGRAM_CHAT_ID, "text": f"🔥 **{album_name}**"})

    # 2️⃣ Send Cover Image
    requests.post(f"{base_url}/sendPhoto", data={"chat_id": TELEGRAM_CHAT_ID, "photo": cover_url})

    # 3️⃣ Send Details (Artist, Release Date, Spotify Link)
    details_text = f"📅 **Release Date:** {release_date}\n🔗 **[Listen on Spotify]({spotify_url})**"
    requests.post(f"{base_url}/sendMessage", data={"chat_id": TELEGRAM_CHAT_ID, "text": details_text})

# ✅ Send "Bot Activated" Message
send_discord_notification("SurrealBot is now active!", "I'm monitoring new releases.", "", "")
send_telegram_notification("SurrealBot is now active!", "", "", "")

# ✅ Store Last Release Name
last_release = None

# ✅ Check for New Releases (Runs Once)
album_name, release_date, spotify_url, cover_url = check_new_release()

if album_name and album_name != last_release:
    print(f"🔥 New release detected: {album_name} ({release_date})")

    send_discord_notification(album_name, release_date, spotify_url, cover_url)
    send_telegram_notification(album_name, release_date, spotify_url, cover_url)

    last_release = album_name
else:
    print("🔍 No new release found.")

print("✅ Script finished.")

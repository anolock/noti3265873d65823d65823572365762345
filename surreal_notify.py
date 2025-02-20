import requests
import os
import time

# ✅ Debugging: Check if environment variables are loaded
print("🚀 DEBUG: Checking environment variables...")

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "MISSING_WEBHOOK")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "MISSING_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "MISSING_SECRET")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "MISSING_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "MISSING_CHAT")

DISCORD_ROLE_ID = "1342206955745317005"  # Deine Discord-Rollen-ID für Notifications

# 🔥 Make sure all secrets are present
if "MISSING" in [DISCORD_WEBHOOK_URL, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]:
    raise ValueError("❌ ERROR: One or more GitHub Secrets are missing! Check your repository settings.")

print("✅ Environment variables loaded successfully!")

# ✅ Surreal.wav’s Spotify Artist ID
ARTIST_ID = "4pqIwzgTlrlpRqHvWvNtVd"

# 🔥 Function: Get Spotify API Access Token
def get_spotify_token():
    print("🔄 Fetching new Spotify API token...")
    url = "https://accounts.spotify.com/api/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET
    }
    response = requests.post(url, headers=headers, data=data)
    return response.json().get("access_token")

# 🔥 Function: Check for New Releases
def check_new_release():
    print("🔍 Checking for new releases...")
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

# 🔥 Function: Send Discord Notification (with Role Tag)
def send_discord_notification(album_name, release_date, spotify_url, cover_url, is_startup=False):
    print("📢 Sending Discord notification...")
    
    if is_startup:
        message = "🚀 **SurrealBot is now active!** I'm monitoring new releases."
    else:
        message = f"<@&{DISCORD_ROLE_ID}> 🔥 **New Surreal.wav Release!** 🎧"

    embed = {
        "content": message,
        "embeds": [
            {
                "title": album_name if not is_startup else "SurrealBot Activated",
                "description": f"📅 **Release Date:** {release_date}\n🔗 **[Listen on Spotify]({spotify_url})**" if not is_startup else "I'm watching for new releases now.",
                "color": 16711680,  # Red
                "thumbnail": {"url": cover_url} if not is_startup else {},
            }
        ]
    }
    
    headers = {"Content-Type": "application/json"}
    response = requests.post(DISCORD_WEBHOOK_URL, json=embed, headers=headers)
    if response.status_code in [200, 204]:
        print("✅ Discord notification sent successfully!")
    else:
        print(f"⚠️ Discord notification failed: {response.text}")

# 🔥 Function: Send Telegram Notification (Better Formatting)
def send_telegram_notification(album_name, release_date, spotify_url, cover_url, is_startup=False):
    print("📢 Sending Telegram notification...")
    base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

    if is_startup:
        message_text = "🚀 **SurrealBot is now active!** I'm monitoring new releases. 🎶"
    else:
        message_text = (
            f"🔥 **New Surreal.wav Release!** 🎧\n\n"
            f"🎵 *{album_name}*\n"
            f"📅 **Release Date:** {release_date}\n"
            f"🔗 [Listen on Spotify]({spotify_url})"
        )

    response = requests.post(f"{base_url}/sendPhoto", data={"chat_id": TELEGRAM_CHAT_ID, "caption": message_text, "photo": cover_url})
    
    if response.status_code == 200:
        print("✅ Telegram notification sent successfully!")
    else:
        print(f"⚠️ Telegram notification failed: {response.text}")

# ✅ Send a one-time "Bot is active" message
if not os.path.exists("bot_active.flag"):
    print("🚀 Bot is now active! Sending initial notification...")
    send_discord_notification("SurrealBot is now active!", "", "", "", is_startup=True)
    send_telegram_notification("SurrealBot is now active!", "", "", "", is_startup=True)
    
    # Erstellt eine Datei als "Flag", damit diese Nachricht nur EINMAL kommt
    with open("bot_active.flag", "w") as f:
        f.write("Bot was started")

# ✅ Store last release name
last_release = None

# 🔁 Start checking loop
while True:
    print("🔄 Running release check loop...")
    album_name, release_date, spotify_url, cover_url = check_new_release()

    if album_name and album_name != last_release:
        print(f"🎉 New release found: {album_name}")

        # ✅ Send to Discord
        send_discord_notification(album_name, release_date, spotify_url, cover_url)

        # ✅ Send to Telegram
        send_telegram_notification(album_name, release_date, spotify_url, cover_url)

        last_release = album_name  # Save last release

    else:
        print("😴 No new releases. Sleeping for 5 minutes...")

    # ⏳ Sleep before next check
    time.sleep(300)

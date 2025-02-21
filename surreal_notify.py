import requests
import os
import json

# ✅ Load Secrets from GitHub Actions
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

DISCORD_ROLE_ID = "1342206955745317005"  # Notification Role for Discord

# ✅ Error Handling for Missing Secrets
missing_secrets = [key for key, value in {
    "DISCORD_WEBHOOK_URL": DISCORD_WEBHOOK_URL,
    "SPOTIFY_CLIENT_ID": SPOTIFY_CLIENT_ID,
    "SPOTIFY_CLIENT_SECRET": SPOTIFY_CLIENT_SECRET,
    "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
    "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID
}.items() if not value]

if missing_secrets:
    print(f"❌ ERROR: Missing secrets: {', '.join(missing_secrets)}")
    exit(1)

# ✅ Surreal.wav Spotify Artist ID
ARTIST_ID = "4pqIwzgTlrlpRqHvWvNtVd"

# 🔥 Function: Get Spotify API Token
def get_spotify_token():
    url = "https://accounts.spotify.com/api/token"
    response = requests.post(url, data={
        "grant_type": "client_credentials",
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET
    }, headers={"Content-Type": "application/x-www-form-urlencoded"})
    return response.json().get("access_token")

# 🔥 Function: Check for New Releases
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

# 🔥 Function: Send Discord Notification
def send_discord_notification(album_name, release_date, spotify_url, cover_url):
    message = f"<@&{DISCORD_ROLE_ID}> 🔥 **New Surreal.wav Release!** 🎧"
    embed = {
        "content": message,
        "embeds": [{
            "title": album_name,
            "description": f"📅 **Release Date:** {release_date}\n🔗 **[Listen on Spotify]({spotify_url})**",
            "color": 16711680,  # Red
            "thumbnail": {"url": cover_url}
        }]
    }
    
    requests.post(DISCORD_WEBHOOK_URL, json=embed, headers={"Content-Type": "application/json"})

# 🔥 Function: Send Telegram Notification with Inline Button
def send_telegram_notification(album_name, release_date, spotify_url, cover_url):
    print("📢 Sending Telegram notification...")

    base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    
    # 📸 Send image with caption (title & release date in one message)
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

    # 🔘 Add an inline button to Spotify
    keyboard = {
        "inline_keyboard": [[{"text": "🎶 Listen on Spotify", "url": spotify_url}]]
    }

    button_payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": "🎧 **Stream on Spotify**",
        "reply_markup": json.dumps(keyboard),
        "parse_mode": "Markdown"
    }
    
    response = requests.post(f"{base_url}/sendMessage", data=button_payload)
    
    if response.status_code == 200:
        print("✅ Telegram button sent successfully!")
    else:
        print(f"⚠️ Telegram button failed: {response.text}")

# ✅ Store Last Release & Prevent Reposting
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

# ✅ Manual Release Trigger via Telegram
def handle_telegram_commands():
    base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    response = requests.get(base_url)
    
    if response.status_code == 200:
        updates = response.json().get("result", [])
        for update in updates:
            message = update.get("message", {})
            text = message.get("text", "").strip()
            
            if text.startswith("/release"):
                parts = text.split()
                if len(parts) == 3 and parts[1] == "4852":
                    manual_url = parts[2]
                    print(f"📢 Manually added release: {manual_url}")

                    send_discord_notification("Manual Release", "Added manually via Telegram", manual_url, "")
                    send_telegram_notification("Manual Release", "Added manually via Telegram", manual_url, "")
                    return "✅ Manual release added successfully!"
                else:
                    return "❌ Invalid command. Use `/release 4852 [Spotify-Link]`"

handle_telegram_commands()

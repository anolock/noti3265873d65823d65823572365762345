import requests
import os
import datetime

# ✅ Surreal.wav’s Spotify Artist ID
ARTIST_ID = "4pqIwzgTlrlpRqHvWvNtVd"

# ✅ API Keys (Securely loaded from GitHub Secrets)
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# ✅ Telegram Bot API Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Set in GitHub Secrets
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # Your Telegram channel ID

# ✅ Role ID for @🔔 ⋄ Notification ⋄
ROLE_ID = "1342206955745317005"

# ✅ File to track last release and last Telegram check-in
LAST_RELEASE_FILE = "last_release.txt"
LAST_TELEGRAM_FILE = "last_telegram.txt"

# 🔥 Function to Get a Spotify API Access Token
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

# 🔥 Function to Check for New Releases
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
        cover_url = latest_release["images"][0]["url"]  # 🎨 Cover Art

        return album_name, release_date, spotify_url, cover_url

    return None, None, None, None

# 🔥 Function to Send a Discord Notification
def send_discord_notification(album_name, release_date, spotify_url, cover_url):
    embed = {
        "content": f"<@&{ROLE_ID}> 🚀 **Surreal.wav just dropped a new track!** 🎶",
        "embeds": [
            {
                "title": album_name,
                "description": f"📅 **Release Date:** {release_date}\n🔗 **[Listen on Spotify]({spotify_url})**",
                "color": 16711680,  # 🔴 Red color
                "thumbnail": {"url": cover_url}
            }
        ]
    }
    
    headers = {"Content-Type": "application/json"}
    requests.post(DISCORD_WEBHOOK_URL, json=embed, headers=headers)

# 🔥 Function to Send a Telegram Notification
def send_telegram_notification(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=data)

# ✅ Read last release from file
def get_last_release():
    if os.path.exists(LAST_RELEASE_FILE):
        with open(LAST_RELEASE_FILE, "r") as file:
            return file.read().strip()
    return None

# ✅ Save last release to file
def save_last_release(release_name):
    with open(LAST_RELEASE_FILE, "w") as file:
        file.write(release_name)

# ✅ Read last Telegram check-in timestamp
def get_last_telegram():
    if os.path.exists(LAST_TELEGRAM_FILE):
        with open(LAST_TELEGRAM_FILE, "r") as file:
            return file.read().strip()
    return None

# ✅ Save current timestamp for Telegram check-in
def save_last_telegram():
    with open(LAST_TELEGRAM_FILE, "w") as file:
        file.write(str(datetime.date.today()))

# ✅ Main Execution
if __name__ == "__main__":
    album_name, release_date, spotify_url, cover_url = check_new_release()
    last_release = get_last_release()

    # 📢 Check for new releases
    if album_name and album_name != last_release:
        send_discord_notification(album_name, release_date, spotify_url, cover_url)
        send_telegram_notification(f"🚀 **New Surreal.wav Release:** [{album_name}]({spotify_url}) 🎶")
        save_last_release(album_name)

    # 🕒 Send daily Telegram message if 24 hours have passed
    last_telegram = get_last_telegram()
    today = str(datetime.date.today())

    if last_telegram != today:
        send_telegram_notification("📢 Submit your demos at [Surreal.wav](https://www.surrealwavrecords.com) or via email: demos@surrealwavrecords.com")
        save_last_telegram()

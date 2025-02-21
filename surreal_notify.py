import requests
import os
import json
import time

# ✅ Load secrets from GitHub Actions, ensuring no crashes
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "").strip() or None
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "").strip() or None
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip() or None
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip() or None
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip() or None

DISCORD_ROLE_ID = "1342206955745317005"  # Discord role for notifications
LAST_RELEASE_FILE = "last_release.json"  # JSON file to track releases

# ✅ Ensure at least one service is available
if not DISCORD_WEBHOOK_URL and not TELEGRAM_BOT_TOKEN:
    print("❌ ERROR: No valid notification methods available (Discord or Telegram required). Exiting.")
    exit(1)

# ✅ Load last saved releases from JSON, auto-create if missing
def load_last_releases():
    if not os.path.exists(LAST_RELEASE_FILE):
        with open(LAST_RELEASE_FILE, "w") as f:
            json.dump({"releases": []}, f)
    try:
        with open(LAST_RELEASE_FILE, "r") as f:
            return json.load(f).get("releases", [])
    except json.JSONDecodeError:
        return []

# ✅ Save new release to JSON
def save_last_release(release_id):
    releases = load_last_releases()
    if release_id not in releases:
        releases.append(release_id)
        with open(LAST_RELEASE_FILE, "w") as f:
            json.dump({"releases": releases}, f)

# 🔥 Function: Get Spotify API Token
def get_spotify_token():
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        print("⚠️ WARNING: Spotify API credentials missing. Cannot check for new releases.")
        return None
    url = "https://accounts.spotify.com/api/token"
    response = requests.post(url, data={
        "grant_type": "client_credentials",
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET
    }, headers={"Content-Type": "application/x-www-form-urlencoded"})
    return response.json().get("access_token")

# 🔥 Function: Check for new releases
def check_new_release():
    token = get_spotify_token()
    if not token:
        return None, None, None, None, None

    url = f"https://api.spotify.com/v1/artists/4pqIwzgTlrlpRqHvWvNtVd/albums?include_groups=single,album&limit=1"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    data = response.json()

    if "items" in data and data["items"]:
        latest = data["items"][0]
        return latest["id"], latest["name"], latest["release_date"], latest["external_urls"]["spotify"], latest["images"][0]["url"]
    return None, None, None, None, None

# 🔥 Function: Send Discord Notification
def send_discord_notification(album_name, release_date, spotify_url, cover_url):
    if not DISCORD_WEBHOOK_URL:
        print("⚠️ WARNING: Discord webhook missing. Skipping Discord notification.")
        return

    message = f"<@&{DISCORD_ROLE_ID}> 🔥 **New Surreal.wav Release!** 🎧"
    embed = {
        "content": message,
        "embeds": [{
            "title": album_name,
            "description": f"📅 **Release Date:** {release_date}\n🔗 **[Listen on Spotify]({spotify_url})**",
            "color": 16711680,
            "thumbnail": {"url": cover_url}
        }]
    }
    
    requests.post(DISCORD_WEBHOOK_URL, json=embed, headers={"Content-Type": "application/json"})

# 🔥 Function: Send Telegram Notification
def send_telegram_notification(album_name, release_date, spotify_url, cover_url):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ WARNING: Telegram credentials missing. Skipping Telegram notification.")
        return

    base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    
    # 📸 Send image with caption
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
    
    requests.post(f"{base_url}/sendPhoto", data=payload)

    # 🎵 Add Spotify button
    keyboard = {
        "inline_keyboard": [[{"text": "🎶 Listen on Spotify", "url": spotify_url}]]
    }

    button_payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": "🎧 **Stream on Spotify**",
        "reply_markup": json.dumps(keyboard),
        "parse_mode": "Markdown"
    }
    
    requests.post(f"{base_url}/sendMessage", data=button_payload)

# 🔥 Function: Process Telegram Commands
def process_telegram_commands():
    if not TELEGRAM_BOT_TOKEN:
        return  # Skip if Telegram isn't configured

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    response = requests.get(url).json()

    if "result" in response:
        for update in response["result"]:
            if "message" in update:
                chat_id = update["message"]["chat"]["id"]
                text = update["message"].get("text", "")

                if text.startswith("/release "):
                    parts = text.split(" ")
                    if len(parts) == 3:
                        code = parts[1]  # Verification code
                        spotify_url = parts[2]

                        album_id = spotify_url.split("/")[-1].split("?")[0]

                        if album_id in load_last_releases():
                            confirmation_text = f"⚠️ Release already exists: {spotify_url}"
                        else:
                            save_last_release(album_id)
                            confirmation_text = f"✅ Release manually added: {spotify_url}"

                        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", data={
                            "chat_id": chat_id,
                            "text": confirmation_text
                        })

# ✅ Process Telegram commands before checking for releases
process_telegram_commands()

# ✅ Check for new releases
last_releases = load_last_releases()
release_id, album_name, release_date, spotify_url, cover_url = check_new_release()

if release_id and release_id not in last_releases:
    print(f"🎉 New release found: {album_name}")

    send_discord_notification(album_name, release_date, spotify_url, cover_url)
    send_telegram_notification(album_name, release_date, spotify_url, cover_url)

    save_last_release(release_id)
else:
    print("😴 No new releases found.")

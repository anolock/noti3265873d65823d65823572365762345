import requests
import os
import json

# ✅ Load secrets from GitHub Actions
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

DISCORD_ROLE_ID = "1342206955745317005"  # Discord role for notification pings
LAST_RELEASE_FILE = "last_release.json"  # File to store last release info

# ✅ Ensure required secrets are set
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

# ✅ Surreal.wav’s Spotify Artist ID
ARTIST_ID = "4pqIwzgTlrlpRqHvWvNtVd"

# ✅ Load last saved release
def load_last_release():
    if os.path.exists(LAST_RELEASE_FILE):
        with open(LAST_RELEASE_FILE, "r") as f:
            try:
                return json.load(f).get("last_release", None)
            except json.JSONDecodeError:
                return None
    return None

# ✅ Save last release
def save_last_release(release_id):
    with open(LAST_RELEASE_FILE, "w") as f:
        json.dump({"last_release": release_id}, f)

# 🔥 Function: Get Spotify API Token
def get_spotify_token():
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
    url = f"https://api.spotify.com/v1/artists/{ARTIST_ID}/albums?include_groups=single,album&limit=1"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    data = response.json()

    if "items" in data and data["items"]:
        latest = data["items"][0]
        return latest["id"], latest["name"], latest["release_date"], latest["external_urls"]["spotify"], latest["images"][0]["url"]
    return None, None, None, None, None

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

# 🔥 Function: Send Telegram Notification
def send_telegram_notification(album_name, release_date, spotify_url, cover_url):
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
                        code = parts[1]  # This should be the verification code
                        spotify_url = parts[2]

                        # Extract the Spotify album ID
                        album_id = spotify_url.split("/")[-1].split("?")[0]

                        # Manually save this as the last release (without triggering a notification)
                        save_last_release(album_id)

                        # Confirm to user
                        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", data={
                            "chat_id": chat_id,
                            "text": f"✅ Release manually added: {spotify_url}"
                        })

# ✅ Process Telegram commands before checking for releases
process_telegram_commands()

# ✅ Check for new releases
last_release = load_last_release()
release_id, album_name, release_date, spotify_url, cover_url = check_new_release()

if release_id and release_id != last_release:
    print(f"🎉 New release found: {album_name}")

    send_discord_notification(album_name, release_date, spotify_url, cover_url)
    send_telegram_notification(album_name, release_date, spotify_url, cover_url)

    save_last_release(release_id)
else:
    print("😴 No new releases found.")

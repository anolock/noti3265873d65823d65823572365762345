import requests
import os
import time
import json

# ✅ Load secrets
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

DISCORD_ROLE_ID = "1342206955745317005"  # Role ID for notifications
LAST_RELEASE_FILE = "last_release.txt"  # File to store last announced release

# ✅ Check for missing secrets
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

# 🔥 Function: Check for new releases
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

# ✅ Function: Save last release
def save_last_release(album_name):
    try:
        with open(LAST_RELEASE_FILE, "w") as f:
            f.write(album_name)
    except Exception as e:
        print(f"⚠️ ERROR: Could not save last release: {e}")

# ✅ Function: Load last release
def load_last_release():
    if os.path.exists(LAST_RELEASE_FILE):
        try:
            with open(LAST_RELEASE_FILE, "r") as f:
                return f.read().strip()
        except Exception as e:
            print(f"⚠️ ERROR: Could not read last release: {e}")
            return None
    return None

# 🔥 Function: Send Discord notification
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

# 🔥 Function: Send Telegram Notification (Now with Buttons)
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
        "text": "🎵 **Listen on Spotify** 🎶",
        "reply_markup": json.dumps(keyboard),
        "parse_mode": "Markdown"
    }

    response = requests.post(f"{base_url}/sendMessage", json=button_payload)

    if response.status_code == 200:
        print("✅ Telegram button sent successfully!")
    else:
        print(f"⚠️ Telegram button failed: {response.text}")

# ✅ Function: Send Manual Release Notification
def send_manual_release(spotify_url):
    """Handles manually triggered releases via Telegram command."""
    print("📢 Sending Manual Release notification...")

    # Fetch release details from Spotify API
    token = get_spotify_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"https://api.spotify.com/v1/albums/{spotify_url.split('/')[-1].split('?')[0]}", headers=headers)
    data = response.json()

    # Check if data is valid
    if "name" not in data or "release_date" not in data:
        print("❌ ERROR: Could not fetch album details from Spotify.")
        return
    
    album_name = data["name"]
    release_date = data["release_date"]
    cover_url = data["images"][0]["url"] if "images" in data and data["images"] else None

    # ✅ Send Discord Notification
    send_discord_notification(album_name, release_date, spotify_url, cover_url)

    # ✅ Send Telegram Notification
    send_telegram_notification(album_name, release_date, spotify_url, cover_url)

# ✅ Check for new releases & announce only if new
album_name, release_date, spotify_url, cover_url = check_new_release()

if album_name:
    last_release = load_last_release()

    if album_name != last_release:
        print(f"🎉 New release found: {album_name}")

        send_discord_notification(album_name, release_date, spotify_url, cover_url)
        send_telegram_notification(album_name, release_date, spotify_url, cover_url)

        save_last_release(album_name)  # Save the release to prevent duplicates
    else:
        print("😴 No new releases found.")

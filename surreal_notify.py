import requests
import os
import json
import re

# ✅ Load Secrets
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

DISCORD_ROLE_ID = "1342206955745317005"  # ✅ Discord role for tagging
AUTHORIZED_CODE = "4852"  # ✅ Change this to your security code

# ✅ Get Spotify API Access Token
def get_spotify_token():
    url = "https://accounts.spotify.com/api/token"
    response = requests.post(url, data={
        "grant_type": "client_credentials",
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET
    }, headers={"Content-Type": "application/x-www-form-urlencoded"})
    return response.json().get("access_token")

# ✅ Fetch Release Details from Spotify
def get_release_details(spotify_url):
    match = re.search(r"album/([a-zA-Z0-9]+)", spotify_url)
    if not match:
        return None, None, None, None

    album_id = match.group(1)
    token = get_spotify_token()
    url = f"https://api.spotify.com/v1/albums/{album_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    data = response.json()

    if "name" in data:
        return data["name"], data["release_date"], data["external_urls"]["spotify"], data["images"][0]["url"]
    
    return None, None, None, None

# ✅ Send Discord Notification
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

# ✅ Send Telegram Notification with Spotify Button
def send_telegram_notification(album_name, release_date, spotify_url, cover_url):
    base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

    # 📸 Send image with caption
    message_text = f"🔥 **New Surreal.wav Release!** 🎧\n🎵 *{album_name}*\n📅 **Release Date:** {release_date}"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "photo": cover_url,
        "caption": message_text,
        "parse_mode": "Markdown"
    }
    
    response = requests.post(f"{base_url}/sendPhoto", data=payload)
    
    if response.status_code == 200:
        print("✅ Telegram image sent successfully!")
    else:
        print(f"⚠️ Telegram image failed: {response.text}")

    # 🔘 Add Spotify Button
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

# ✅ Process Incoming Telegram Messages
def process_telegram_messages():
    base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    last_update_id = None

    while True:
        response = requests.get(f"{base_url}/getUpdates?offset={last_update_id+1 if last_update_id else ''}")
        data = response.json()

        if "result" in data and data["result"]:
            for update in data["result"]:
                last_update_id = update["update_id"]
                
                if "message" in update and "text" in update["message"]:
                    chat_id = update["message"]["chat"]["id"]
                    text = update["message"]["text"].strip()

                    if text.startswith("/release"):
                        parts = text.split(" ")
                        if len(parts) == 3 and parts[1] == AUTHORIZED_CODE:
                            spotify_url = parts[2]
                            album_name, release_date, spotify_url, cover_url = get_release_details(spotify_url)

                            if album_name:
                                send_discord_notification(album_name, release_date, spotify_url, cover_url)
                                send_telegram_notification(album_name, release_date, spotify_url, cover_url)
                                response_text = f"✅ Release **{album_name}** added successfully!"
                            else:
                                response_text = "⚠️ Invalid Spotify URL or album not found."
                        else:
                            response_text = "❌ Incorrect format. Use: `/release 4852 [Spotify-Link]`"

                        # Send response message
                        requests.post(f"{base_url}/sendMessage", data={"chat_id": chat_id, "text": response_text})

# ✅ Run Telegram Message Processing
if __name__ == "__main__":
    process_telegram_messages()

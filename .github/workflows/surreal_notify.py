import requests
import time

# ✅ Surreal.wav’s Spotify Artist ID
ARTIST_ID = "4pqIwzgTlrlpRqHvWvNtVd"

# ✅ Your Spotify API Credentials
CLIENT_ID = "7af4a6b569b544ba983b363d38e837d9"
CLIENT_SECRET = "c85b3388c9e04cada9f2f0cf5d46ce62"

# ✅ Your Discord Webhook URL (DO NOT SHARE PUBLICLY)
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1342197978516947014/IZzY-ayByZFncJhyVZT_vo_AgArelA1rIka2zdFHfNCDpu4sORojyvgZD3BuKtI4fDDo"

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
        "content": "@everyone 🚀 **Surreal.wav just dropped a new track!** 🎶",
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

# ✅ Store the Last Released Track to Prevent Duplicate Notifications
last_release = None

# ✅ Run the Script Continuously (Checks Every 5 Minutes)
while True:
    album_name, release_date, spotify_url, cover_url = check_new_release()

    if album_name and album_name != last_release:
        send_discord_notification(album_name, release_date, spotify_url, cover_url)
        last_release = album_name  # ✅ Update last release

    time.sleep(300)  # ⏳ Wait 5 minutes before checking again

import os
import json
import requests
from urllib.parse import urlparse

# Konfiguration
DISCORD_PLAYLIST_WEBHOOK2 = os.getenv("DISCORD_PLAYLIST_WEBHOOK2")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # Deine persönliche Chat-ID
TRACKED_PLAYLISTS_FILE = "tracked_playlists.json"
MILESTONES = [1000, 5000, 10000, 25000, 50000]
PROMO_CODE = "4852"

# Telegram Update-Tracking
def get_last_update_id():
    try:
        with open("last_telegram_update.txt", "r") as f:
            return int(f.read().strip())
    except:
        return 0

def save_last_update_id(update_id):
    with open("last_telegram_update.txt", "w") as f:
        f.write(str(update_id))

# Datenbank
def load_playlists():
    try:
        with open(TRACKED_PLAYLISTS_FILE, "r") as f:
            return json.load(f)
    except:
        return {"playlists": {}}

def save_playlists(data):
    with open(TRACKED_PLAYLISTS_FILE, "w") as f:
        json.dump(data, f, indent=2)

# Discord-Benachrichtigung
def send_discord_add_notification(playlist_id, name, followers, cover_url):
    requests.post(
        DISCORD_PLAYLIST_WEBHOOK2,
        json={
            "content": "🎵 **Playlist Added**",
            "embeds": [{
                "title": name,
                "description": f"🔗 [Open Playlist](https://open.spotify.com/playlist/{playlist_id})\n👥 Follower: {followers}",
                "color": 5763719,
                "thumbnail": {"url": cover_url}
            }]
        }
    )

# Telegram-Benachrichtigung
def send_telegram_message(chat_id, text):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"  # Für Links und Formatierung
        }
    )

# Playlist-Info anzeigen
def show_playlist_info(chat_id):
    data = load_playlists()
    if not data["playlists"]:
        send_telegram_message(chat_id, "❌ *No playlists tracked yet!*")
        return
    
    message = "🎵 **Tracked Playlists:**\n"
    for playlist_id, details in data["playlists"].items():
        message += f"- [{details['name']}](https://open.spotify.com/playlist/{playlist_id}) ({details['current_followers']} Follower)\n"
    
    send_telegram_message(chat_id, message)

# Playlist hinzufügen
def handle_playlist_command(url, chat_id):
    try:
        playlist_id = urlparse(url).path.split("/")[-1]
        token = requests.post(
            "https://accounts.spotify.com/api/token",
            auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
            data={"grant_type": "client_credentials"}
        ).json().get("access_token")
        
        data = load_playlists()
        
        if playlist_id in data["playlists"]:
            send_telegram_message(chat_id, "⚠️ *Playlist already tracked!*")
            return
            
        playlist = requests.get(
            f"https://api.spotify.com/v1/playlists/{playlist_id}",
            headers={"Authorization": f"Bearer {token}"}
        ).json()
        
        if "error" in playlist:
            send_telegram_message(chat_id, "❌ *Invalid playlist URL!*")
            return
        
        # Speichern und Benachrichtigungen senden
        data["playlists"][playlist_id] = {
            "name": playlist["name"],
            "current_followers": playlist["followers"]["total"],
            "cover": playlist["images"][0]["url"],
            "milestones": []
        }
        save_playlists(data)
        
        # Discord & Telegram Benachrichtigungen
        send_discord_add_notification(
            playlist_id,
            playlist["name"],
            playlist["followers"]["total"],
            playlist["images"][0]["url"]
        )
        send_telegram_message(TELEGRAM_CHAT_ID, "✅ *Playlist added to tracking!*")

    except Exception as e:
        print(f"Error: {str(e)}")
        send_telegram_message(chat_id, "❌ *Failed to add playlist!*")

# Befehle verarbeiten
def process_commands():
    last_update_id = get_last_update_id()
    new_max_id = last_update_id
    
    response = requests.get(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates",
        params={"offset": last_update_id + 1}
    )
    
    for update in response.json().get("result", []):
        update_id = update["update_id"]
        new_max_id = max(new_max_id, update_id)
        
        if "message" in update:
            text = update["message"].get("text", "")
            chat_id = update["message"]["chat"]["id"]
            
            if text.startswith("/p info"):
                show_playlist_info(chat_id)
            elif text.startswith("/p "):
                parts = text.split()
                if len(parts) == 3 and parts[1] == PROMO_CODE:
                    handle_playlist_command(parts[2], chat_id)
    
    save_last_update_id(new_max_id)

# Meilenstein-Checker
def check_milestones():
    token = requests.post(
        "https://accounts.spotify.com/api/token",
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
        data={"grant_type": "client_credentials"}
    ).json().get("access_token")
    
    data = load_playlists()
    
    for playlist_id in list(data["playlists"].keys()):
        playlist = data["playlists"][playlist_id]
        response = requests.get(
            f"https://api.spotify.com/v1/playlists/{playlist_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code != 200:
            continue
            
        current = response.json()["followers"]["total"]
        
        for milestone in MILESTONES:
            if current >= milestone and milestone not in playlist["milestones"]:
                requests.post(
                    DISCORD_PLAYLIST_WEBHOOK2,
                    json={
                        "content": f"🚀 *Playlist Milestone: {milestone} Follower!*",
                        "embeds": [{
                            "title": playlist["name"],
                            "description": f"🔗 [Open Playlist](https://open.spotify.com/playlist/{playlist_id})",
                            "color": 16711680,
                            "thumbnail": {"url": playlist["cover"]}
                        }]
                    }
                )
                playlist["milestones"].append(milestone)
        
        playlist["current_followers"] = current
    
    save_playlists(data)

if __name__ == "__main__":
    process_commands()
    check_milestones()

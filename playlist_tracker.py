import os
import json
import requests
from urllib.parse import urlparse

# Konfiguration
DISCORD_PLAYLIST_WEBHOOK2 = os.getenv("DISCORD_PLAYLIST_WEBHOOK2")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # Deine Chat-ID für private Nachrichten
TRACKED_PLAYLISTS_FILE = "tracked_playlists.json"
MILESTONES = [1000, 5000, 10000, 25000, 50000]
PROMO_CODE = "4852"

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

# Spotify API
def get_spotify_token():
    response = requests.post(
        "https://accounts.spotify.com/api/token",
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
        data={"grant_type": "client_credentials"}
    )
    return response.json().get("access_token")

def get_playlist_details(playlist_id, token):
    response = requests.get(
        f"https://api.spotify.com/v1/playlists/{playlist_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.json() if response.status_code == 200 else None

# Discord-Benachrichtigung beim Hinzufügen
def send_discord_add_notification(playlist_id, name, followers, cover_url):
    requests.post(
        DISCORD_PLAYLIST_WEBHOOK2,
        json={
            "content": "🎵 **Playlist added**",
            "embeds": [{
                "title": name,
                "description": f"🔗 [Open Playlist](https://open.spotify.com/playlist/{playlist_id})\n"
                             f"👥 **Follower:** {followers}",
                "color": 5763719,  # Grüne Farbe
                "thumbnail": {"url": cover_url}
            }]
        }
    )

# Telegram-Benachrichtigung
def send_telegram_message(chat_id, text):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json={"chat_id": chat_id, "text": text}
    )

# Playlist-Info anzeigen
def show_playlist_info(chat_id):
    data = load_playlists()
    if not data["playlists"]:
        send_telegram_message(chat_id, "❌ Keine Playlists getrackt!")
        return
    
    message = "🎵 **Getrackte Playlists:**\n"
    for playlist_id, playlist in data["playlists"].items():
        message += f"- [{playlist['name']}](https://open.spotify.com/playlist/{playlist_id}) ({playlist['current_followers']} Follower)\n"
    
    send_telegram_message(chat_id, message)

# Playlist hinzufügen
def handle_playlist_command(url, chat_id):
    try:
        playlist_id = urlparse(url).path.split("/")[-1]
        token = get_spotify_token()
        data = load_playlists()
        
        if playlist_id in data["playlists"]:
            send_telegram_message(chat_id, "⚠️ Playlist wird bereits getrackt!")
            return
            
        playlist = get_playlist_details(playlist_id, token)
        if not playlist:
            send_telegram_message(chat_id, "❌ Ungültige Playlist!")
            return
            
        # Playlist zur Datenbank hinzufügen
        data["playlists"][playlist_id] = {
            "name": playlist["name"],
            "current_followers": playlist["followers"]["total"],
            "reached_milestones": [],
            "added_notification_sent": False,  # Flag für die erste Benachrichtigung
            "cover_url": playlist["images"][0]["url"]  # Playlist-Cover speichern
        }
        save_playlists(data)

        # Discord-Benachrichtigung senden
        if not data["playlists"][playlist_id]["added_notification_sent"]:
            send_discord_add_notification(
                playlist_id,
                playlist["name"],
                playlist["followers"]["total"],
                playlist["images"][0]["url"]  # Playlist-Cover
            )
            data["playlists"][playlist_id]["added_notification_sent"] = True
            save_playlists(data)

        # Telegram-Benachrichtigung senden (nur an dich)
        send_telegram_message(TELEGRAM_CHAT_ID, "✅ Playlist added to tracking!")

    except Exception as e:
        print(f"Fehler: {str(e)}")
        send_telegram_message(chat_id, "❌ Fehler beim Hinzufügen!")

# Telegram-Befehle verarbeiten
def process_playlist_commands():
    response = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates")
    for update in response.json().get("result", []):
        if "message" in update:
            text = update["message"].get("text", "")
            chat_id = update["message"]["chat"]["id"]
            
            if text.startswith("/p "):
                parts = text.split()
                if len(parts) == 3 and parts[1] == PROMO_CODE:
                    handle_playlist_command(parts[2], chat_id)
            elif text == "/p info":
                show_playlist_info(chat_id)

# Meilenstein-Checker
def check_milestones():
    token = get_spotify_token()
    data = load_playlists()
    
    for playlist_id in list(data["playlists"].keys()):
        playlist = data["playlists"][playlist_id]
        current = get_playlist_details(playlist_id, token)["followers"]["total"]
        
        for milestone in MILESTONES:
            if current >= milestone and milestone not in playlist["reached_milestones"]:
                send_discord_milestone_alert(playlist_id, playlist["name"], milestone, playlist["cover_url"])
                playlist["reached_milestones"].append(milestone)
        
        playlist["current_followers"] = current
    
    save_playlists(data)

def send_discord_milestone_alert(playlist_id, name, milestone, cover_url):
    mention = "<@&1342206955745317005>" if milestone >= 10000 else "@here" if milestone >= 5000 else ""
    
    requests.post(
        DISCORD_PLAYLIST_WEBHOOK2,
        json={
            "content": f"{mention} 🚀 **Playlist Milestone: {milestone} Follower!**",
            "embeds": [{
                "title": name,
                "description": f"🔗 [Open Playlist](https://open.spotify.com/playlist/{playlist_id})",
                "color": 16711680,  # Rote Farbe
                "thumbnail": {"url": cover_url}
            }]
        }
    )

if __name__ == "__main__":
    process_playlist_commands()
    check_milestones()

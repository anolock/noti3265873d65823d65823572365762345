import requests
import os
import json
from urllib.parse import urlparse

# ---------- Konfiguration ----------
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
DISCORD_ROLE_ID = "1342206955745317005"  # Anpassen!
LAST_RELEASE_FILE = "last_release.json"

# ---------- Debugging ----------
def debug_log(message):
    print(f"🔍 [DEBUG] {message}")

debug_log("Initialisiere Bot...")

# ---------- Datenbank ----------
def load_releases():
    try:
        with open(LAST_RELEASE_FILE, "r") as f:
            data = json.load(f)
            debug_log(f"Geladene Releases: {data.get('releases', [])}")
            return data.get("releases", [])
    except (FileNotFoundError, json.JSONDecodeError) as e:
        debug_log(f"Datenbankfehler: {str(e)} – Neue Datenbank wird erstellt.")
        return []

def save_release(release_id):
    releases = load_releases()
    if release_id not in releases:
        releases.append(release_id)
        with open(LAST_RELEASE_FILE, "w") as f:
            json.dump({"releases": releases}, f, indent=2)
            debug_log(f"Release {release_id} gespeichert.")
    else:
        debug_log(f"Release {release_id} existiert bereits.")

# ---------- Spotify API ----------
def fetch_latest_release():
    token = get_spotify_token()
    if not token:
        return None
    
    url = "https://api.spotify.com/v1/artists/4pqIwzgTlrlpRqHvWvNtVd/albums?include_groups=single,album&limit=1"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data.get("items"):
            latest = data["items"][0]
            release_id = latest["id"]
            debug_log(f"Aktueller Release: {release_id}")
            return {
                "id": release_id,
                "name": latest["name"],
                "date": latest["release_date"],
                "url": latest["external_urls"]["spotify"],
                "cover": latest["images"][0]["url"] if latest["images"] else ""
            }
    except Exception as e:
        debug_log(f"Spotify-Fehler: {str(e)}")
    return None

# ---------- Hauptlogik ----------
if __name__ == "__main__":
    # Manuelle Befehle verarbeiten
    process_telegram_commands()
    
    # Automatische Prüfung
    latest_release = fetch_latest_release()
    if latest_release:
        existing_releases = load_releases()
        debug_log(f"Vorhandene Releases: {existing_releases}")
        
        if latest_release["id"] not in existing_releases:
            debug_log("Neuer Release gefunden – Sende Benachrichtigungen.")
            send_discord(latest_release)
            send_telegram(latest_release)
            save_release(latest_release["id"])
        else:
            debug_log("Release bereits vorhanden – Keine Aktion.")
    else:
        debug_log("Keine Releases von Spotify erhalten.")

import requests
import os
import json
from urllib.parse import urlparse

# ---------- Konfiguration ----------
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DATABASE_FILE = "processed_releases.json"  # Neue Datenbank

# ---------- Datenbank (Atomic Writing) ----------
def load_database():
    try:
        with open(DATABASE_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"releases": []}

def save_to_database(release_id):
    db = load_database()
    if release_id not in db["releases"]:
        db["releases"].append(release_id)
        with open(DATABASE_FILE, "w") as f:
            json.dump(db, f, indent=2)

# ---------- Notifications ----------
def send_discord(url):
    if not DISCORD_WEBHOOK_URL:
        return
    
    embed = {
        "content": "🔥 **NEUER RELEASE** 🔥",
        "embeds": [{
            "title": "JETZT STREAMEN!",
            "url": url,
            "color": 0xFF0000
        }]
    }
    requests.post(DISCORD_WEBHOOK_URL, json=embed)

def send_telegram(url):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": f"🔥 *NEUER RELEASE* 🔥\n[Spotify Link]({url})",
            "parse_mode": "Markdown"
        }
    )

# ---------- Telegram Command ----------
def process_commands():
    response = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates").json()
    for update in response.get("result", []):
        if "message" in update and update["message"].get("text", "").startswith("/promote"):
            url = update["message"]["text"].split()[-1]
            release_id = urlparse(url).path.split("/")[-1]
            
            if release_id not in load_database()["releases"]:
                send_discord(url)
                send_telegram(url)
                save_to_database(release_id)
                
                # Bestätigung senden
                requests.post(
                    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                    json={
                        "chat_id": update["message"]["chat"]["id"],
                        "text": "✅ Release wurde gesendet!"
                    }
                )

if __name__ == "__main__":
    process_commands()

import requests
import os
import json

# ---------- Konfiguration ----------
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DISCORD_ROLE_ID = "1342206955745317005"
DB_FILE = "processed_releases.json"

# ---------- Einfache JSON-DB ----------
def load_db():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)["releases"]
    except:
        return []

def save_to_db(release_id):
    db = {"releases": load_db()}
    if release_id not in db["releases"]:
        db["releases"].append(release_id)
        with open(DB_FILE, "w") as f:
            json.dump(db, f, indent=2)

# ---------- Notification ----------
def send_alerts(release):
    # Discord
    requests.post(
        DISCORD_WEBHOOK_URL,
        json={
            "content": f"<@&{DISCORD_ROLE_ID}> 🔔・Notification・🔥 New Release! 🎧",
            "embeds": [{
                "title": release["name"],
                "description": f"📅 {release['date']}\n🔗 [Spotify]({release['url']})",
                "color": 16711680
            }]
        }
    )
    
    # Telegram
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": f"🔥 *New Release!* 🎧\n**{release['name']}**\n📅 {release['date']}",
            "parse_mode": "Markdown"
        }
    )

# ---------- Hauptlogik ----------
def check_release():
    # Deine Spotify-Check-Logik hier
    # ...
    return latest_release  # oder None

if __name__ == "__main__":
    latest = check_release()
    if latest and latest["id"] not in load_db():
        send_alerts(latest)
        save_to_db(latest["id"])

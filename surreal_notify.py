name: Surreal Notifier

on:
  schedule:
    - cron: '*/5 * * * *'  # Alle 5 Minuten
  workflow_dispatch:

concurrency: 
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

permissions:
  contents: write

jobs:
  run:
    runs-on: ubuntu-latest
    timeout-minutes: 5

    steps:
      - name: Code auschecken
        uses: actions/checkout@v4
        with:
          persist-credentials: false
          fetch-depth: 0

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.10"

      - name: Install dependencies
        run: pip install requests

      - name: Datenbank initialisieren
        run: |
          mkdir -p db
          [ -f db/processed_releases.json ] || echo '{"processed":[]}' > db/processed_releases.json
          [ -f db/last_telegram_update.txt ] || echo "0" > db/last_telegram_update.txt

      - name: Cache laden
        uses: actions/cache@v3
        id: cache
        with:
          path: |
            db/processed_releases.json
            db/last_telegram_update.txt
          key: db-${{ hashFiles('db/processed_releases.json', 'db/last_telegram_update.txt') }}
          restore-keys: db-

      - name: Bot ausführen
        env:
          DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
          SPOTIFY_CLIENT_ID: ${{ secrets.SPOTIFY_CLIENT_ID }}
          SPOTIFY_CLIENT_SECRET: ${{ secrets.SPOTIFY_CLIENT_SECRET }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: |
          for i in {1..3}; do
            python surreal_notify.py
            if [ $? -eq 0 ]; then
              exit 0
            fi
            echo "Versuch $i fehlgeschlagen, wiederhole in 10s..."
            sleep 10
          done
          exit 1

      - name: Änderungen pushen
        if: success()
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          git config --global user.name "GitHub Bot"
          git config --global user.email "actions@github.com"
          git add db/
          git commit -m "Update: $(date +'%Y-%m-%d %H:%M:%S')" || echo "Keine Änderungen"
          git pull --rebase
          git push origin HEAD:main

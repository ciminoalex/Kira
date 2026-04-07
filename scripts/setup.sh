#!/usr/bin/env bash
set -euo pipefail

# Setup iniziale per Kira AI Assistant
# Eseguire come utente kira sulla VPS

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Kira AI Assistant — Setup ==="
echo "Directory: $PROJECT_DIR"
echo

# 1. Virtual environment
if [ ! -d "$PROJECT_DIR/.venv" ]; then
    echo "Creazione virtual environment..."
    python3.12 -m venv "$PROJECT_DIR/.venv"
fi

echo "Installazione dipendenze..."
"$PROJECT_DIR/.venv/bin/pip" install --upgrade pip
"$PROJECT_DIR/.venv/bin/pip" install -r "$PROJECT_DIR/requirements.txt"

# 2. File .env
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "Copio .env.example → .env (da compilare con le API key)"
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
    echo "IMPORTANTE: Modifica .env con le tue API key prima di avviare i servizi!"
fi

# 3. Database
echo
echo "Setup database PostgreSQL..."
echo "Esegui questi comandi manualmente se non già fatto:"
echo "  sudo -u postgres psql -c \"CREATE USER kira WITH PASSWORD 'changeme';\""
echo "  sudo -u postgres psql -c \"CREATE DATABASE kira OWNER kira;\""
echo "  psql -d kira -f $PROJECT_DIR/db/init.sql"
echo

# 4. Seed memoria
echo "Per pre-popolare la memoria di Kira:"
echo "  $PROJECT_DIR/.venv/bin/python -m scripts.seed_memory"
echo

# 5. Frontend (opzionale, per interfaccia vocale)
if [ -d "$PROJECT_DIR/frontend" ]; then
    echo "Setup frontend..."
    if command -v npm &> /dev/null; then
        cd "$PROJECT_DIR/frontend"
        if [ ! -f ".env.local" ]; then
            cp .env.local.example .env.local
            echo "IMPORTANTE: Modifica frontend/.env.local con le credenziali LiveKit!"
        fi
        npm install
        echo "Frontend pronto. Per avviare: cd frontend && npm run build && npm start"
    else
        echo "npm non trovato. Installa Node.js >= 18 per il frontend."
    fi
    echo
fi

# 6. Servizi systemd
echo "Per installare i servizi systemd:"
echo "  sudo cp $PROJECT_DIR/systemd/*.service /etc/systemd/system/"
echo "  sudo systemctl daemon-reload"
echo ""
echo "  # Fase 1: Core + Telegram"
echo "  sudo systemctl enable --now kira-agent kira-telegram"
echo ""
echo "  # Fase 3: Voce (richiede LiveKit)"
echo "  sudo systemctl enable --now livekit kira-voice"
echo

# 7. Backup database (cron)
echo "Per configurare il backup automatico del database:"
echo "  crontab -e"
echo "  # Aggiungi: 0 2 * * * $PROJECT_DIR/scripts/backup_db.sh"
echo

# 8. Tailscale (Fase 4, opzionale)
echo "Per collegare il PC fisso via Tailscale:"
echo "  curl -fsSL https://tailscale.com/install.sh | sh"
echo "  tailscale up"
echo

echo "=== Setup completato ==="

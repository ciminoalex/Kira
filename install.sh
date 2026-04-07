#!/usr/bin/env bash
###############################################################################
#  Kira AI Assistant — Installer interattivo
#
#  Uso:  chmod +x install.sh && sudo ./install.sh
#
#  Questo script:
#   1. Verifica i prerequisiti (Python 3.11+, PostgreSQL, Node.js)
#   2. Crea un utente di sistema dedicato "kira"
#   3. Installa il progetto in /home/kira/kira
#   4. Ti chiede step-by-step tutte le API key e configurazioni
#   5. Crea il database PostgreSQL (senza toccare quelli esistenti)
#   6. Installa i servizi systemd (senza interferire con altri servizi)
#   7. Configura il backup automatico del database
#
#  NOTA: Non installa/rimuove PostgreSQL, Node.js, Caddy o altri servizi.
#        Usa quelli già presenti sulla macchina.
###############################################################################
set -euo pipefail

# Colori
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

INSTALL_DIR="/home/kira/kira"
KIRA_USER="kira"

###############################################################################
# Funzioni helper
###############################################################################

info()    { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()      { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
err()     { echo -e "${RED}[ERRORE]${NC} $*"; }

ask() {
    # ask "Prompt" "default_value" → risultato in $REPLY
    local prompt="$1"
    local default="${2:-}"
    if [ -n "$default" ]; then
        read -rp "$(echo -e "${BOLD}$prompt${NC} [${default}]: ")" REPLY
        REPLY="${REPLY:-$default}"
    else
        read -rp "$(echo -e "${BOLD}$prompt${NC}: ")" REPLY
    fi
}

ask_secret() {
    # Come ask ma non mostra l'input
    local prompt="$1"
    local default="${2:-}"
    if [ -n "$default" ]; then
        read -srp "$(echo -e "${BOLD}$prompt${NC} [****]: ")" REPLY
        echo
        REPLY="${REPLY:-$default}"
    else
        read -srp "$(echo -e "${BOLD}$prompt${NC}: ")" REPLY
        echo
    fi
}

ask_yn() {
    # ask_yn "Domanda?" "y" → ritorna 0 (true) o 1 (false)
    local prompt="$1"
    local default="${2:-y}"
    local yn_hint
    if [ "$default" = "y" ]; then yn_hint="Y/n"; else yn_hint="y/N"; fi
    read -rp "$(echo -e "${BOLD}$prompt${NC} [$yn_hint]: ")" REPLY
    REPLY="${REPLY:-$default}"
    [[ "$REPLY" =~ ^[Yy] ]]
}

check_command() {
    if command -v "$1" &>/dev/null; then
        ok "$1 trovato: $(command -v "$1")"
        return 0
    else
        return 1
    fi
}

###############################################################################
# 0. Verifica root
###############################################################################

if [ "$(id -u)" -ne 0 ]; then
    err "Questo script deve essere eseguito come root (sudo ./install.sh)"
    exit 1
fi

echo
echo -e "${BOLD}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║       Kira AI Assistant — Installer v1.0         ║${NC}"
echo -e "${BOLD}╚═══════════════════════════════════════════════════╝${NC}"
echo
info "Questo installer configurerà Kira sulla tua VPS."
info "Non toccherà servizi o database già esistenti."
echo

###############################################################################
# 1. Verifica prerequisiti
###############################################################################

echo -e "${BOLD}═══ Step 1/8: Verifica prerequisiti ═══${NC}"
echo

PYTHON_CMD=""
for cmd in python3.12 python3.11 python3; do
    if check_command "$cmd"; then
        PY_VER=$($cmd --version 2>&1 | grep -oP '\d+\.\d+')
        if awk "BEGIN{exit !($PY_VER >= 3.11)}"; then
            PYTHON_CMD="$cmd"
            ok "Python $PY_VER OK (>= 3.11 richiesto)"
            break
        else
            warn "$cmd è versione $PY_VER (serve >= 3.11)"
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    err "Python 3.11+ non trovato. Installalo prima di procedere:"
    err "  sudo apt install python3.12 python3.12-venv"
    exit 1
fi

POSTGRES_OK=false
if check_command "psql"; then
    if sudo -u postgres psql -c "SELECT 1;" &>/dev/null 2>&1; then
        ok "PostgreSQL è attivo e raggiungibile"
        POSTGRES_OK=true
    else
        warn "psql trovato ma PostgreSQL non raggiungibile"
    fi
fi

if [ "$POSTGRES_OK" = false ]; then
    err "PostgreSQL non trovato o non raggiungibile."
    err "Installa e avvia PostgreSQL prima di procedere:"
    err "  sudo apt install postgresql postgresql-contrib"
    err "  sudo systemctl enable --now postgresql"
    exit 1
fi

NODE_OK=false
if check_command "node"; then
    NODE_VER=$(node --version | grep -oP '\d+' | head -1)
    if [ "$NODE_VER" -ge 18 ]; then
        ok "Node.js v$NODE_VER OK (>= 18 richiesto)"
        NODE_OK=true
    else
        warn "Node.js v$NODE_VER è troppo vecchio (serve >= 18)"
    fi
fi

if check_command "npm"; then
    ok "npm trovato"
fi

if check_command "npx"; then
    ok "npx trovato"
fi

CADDY_OK=false
if check_command "caddy"; then
    ok "Caddy trovato (reverse proxy)"
    CADDY_OK=true
else
    warn "Caddy non trovato — il frontend HTTPS andrà configurato manualmente"
fi

echo

###############################################################################
# 2. Utente di sistema
###############################################################################

echo -e "${BOLD}═══ Step 2/8: Utente di sistema ═══${NC}"
echo

if id "$KIRA_USER" &>/dev/null; then
    ok "Utente '$KIRA_USER' già esistente"
else
    info "Creo utente di sistema '$KIRA_USER'..."
    useradd -m -s /bin/bash "$KIRA_USER"
    ok "Utente '$KIRA_USER' creato"
fi

echo

###############################################################################
# 3. Installazione progetto
###############################################################################

echo -e "${BOLD}═══ Step 3/8: Installazione progetto ═══${NC}"
echo

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$SCRIPT_DIR" != "$INSTALL_DIR" ]; then
    info "Copio il progetto in $INSTALL_DIR..."
    mkdir -p "$INSTALL_DIR"
    # Copia tutto tranne .git e .venv
    rsync -a --exclude='.git' --exclude='.venv' --exclude='node_modules' \
        "$SCRIPT_DIR/" "$INSTALL_DIR/"
    chown -R "$KIRA_USER:$KIRA_USER" "$INSTALL_DIR"
    ok "Progetto copiato in $INSTALL_DIR"
else
    info "Progetto già in $INSTALL_DIR"
    chown -R "$KIRA_USER:$KIRA_USER" "$INSTALL_DIR"
fi

# Virtual environment
if [ ! -d "$INSTALL_DIR/.venv" ]; then
    info "Creo virtual environment Python..."
    sudo -u "$KIRA_USER" "$PYTHON_CMD" -m venv "$INSTALL_DIR/.venv"
    ok "Virtual environment creato"
fi

info "Installo dipendenze Python (potrebbe richiedere qualche minuto)..."
sudo -u "$KIRA_USER" "$INSTALL_DIR/.venv/bin/pip" install --quiet --upgrade pip
sudo -u "$KIRA_USER" "$INSTALL_DIR/.venv/bin/pip" install --quiet \
    -r "$INSTALL_DIR/requirements.txt"
ok "Dipendenze Python installate"

echo

###############################################################################
# 4. Configurazione — API Keys (interattivo)
###############################################################################

echo -e "${BOLD}═══ Step 4/8: Configurazione ═══${NC}"
echo
info "Ti chiederò le credenziali necessarie. Per ognuna ti spiego dove trovarla."
info "Premi Invio per saltare quelle opzionali (potrai aggiungerle dopo in .env)."
echo

ENV_FILE="$INSTALL_DIR/.env"

# Se esiste già un .env, chiedi se sovrascrivere
if [ -f "$ENV_FILE" ]; then
    if ask_yn "File .env già presente. Vuoi riconfigurarlo?"; then
        cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%s)"
        warn "Backup salvato come .env.backup.*"
    else
        ok "Mantengo il .env esistente"
        SKIP_ENV=true
    fi
fi

if [ "${SKIP_ENV:-false}" = "false" ]; then

    # ── Dominio ──
    echo -e "\n${CYAN}── Dominio e HTTPS ──${NC}"
    info "Il dominio verrà usato per il portale web e i certificati SSL (Caddy)."
    info "Esempio: kira.tuodominio.it"
    info "Prerequisiti: un record DNS A/CNAME che punta all'IP di questa VPS."
    ask "Dominio per Kira (es. kira.tuodominio.it)" ""
    KIRA_DOMAIN="$REPLY"
    if [ -n "$KIRA_DOMAIN" ]; then
        ok "Dominio: $KIRA_DOMAIN"
    else
        warn "Nessun dominio configurato. Il frontend sarà accessibile solo via IP."
    fi

    # ── Anthropic ──
    echo -e "\n${CYAN}── Anthropic (OBBLIGATORIO) ──${NC}"
    info "API key per Claude (Sonnet, Haiku, Opus)."
    info "Dove trovarla: https://console.anthropic.com/settings/keys"
    info "  1. Accedi a console.anthropic.com"
    info "  2. Settings → API Keys → Create Key"
    info "  3. Copia la chiave (inizia con sk-ant-...)"
    ask_secret "ANTHROPIC_API_KEY"
    ANTHROPIC_API_KEY="$REPLY"
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        warn "ATTENZIONE: Senza API key Anthropic, Kira non potrà funzionare!"
    fi

    # ── Database ──
    echo -e "\n${CYAN}── Database PostgreSQL ──${NC}"
    info "Kira creerà un NUOVO database e utente dedicati."
    info "I tuoi database esistenti non verranno toccati."
    ask "Nome database" "kira"
    PG_DB="$REPLY"
    ask "Utente database" "kira"
    PG_USER="$REPLY"
    ask_secret "Password database (vuoto = genera automaticamente)" ""
    PG_PASS="$REPLY"
    if [ -z "$PG_PASS" ]; then
        PG_PASS=$(openssl rand -base64 24 | tr -d '/+=')
        info "Password generata automaticamente"
    fi
    ask "Host PostgreSQL (il tuo PostgreSQL locale)" "localhost"
    PG_HOST="$REPLY"
    ask "Porta PostgreSQL" "5432"
    PG_PORT="$REPLY"

    # ── Telegram ──
    echo -e "\n${CYAN}── Telegram Bot (OBBLIGATORIO per chat) ──${NC}"
    info "Il bot Telegram è il canale principale di comunicazione con Kira."
    info "Dove trovare il token:"
    info "  1. Apri Telegram e cerca @BotFather"
    info "  2. Invia /newbot e segui le istruzioni"
    info "  3. BotFather ti darà un token tipo: 123456789:ABCdef..."
    ask_secret "TELEGRAM_BOT_TOKEN"
    TELEGRAM_TOKEN="$REPLY"
    echo
    info "Dove trovare il tuo User ID:"
    info "  1. Apri Telegram e cerca @userinfobot"
    info "  2. Invia /start — ti mostrerà il tuo ID numerico"
    info "  (Solo questo ID potrà parlare con Kira)"
    ask "Il tuo Telegram User ID (numerico)" ""
    TELEGRAM_USER_IDS="$REPLY"

    # ── Deepgram ──
    echo -e "\n${CYAN}── Deepgram STT (opzionale — per messaggi vocali) ──${NC}"
    info "Trascrizione vocale (Speech-to-Text) per messaggi audio."
    info "Dove trovarla: https://console.deepgram.com/"
    info "  1. Registrati su deepgram.com (piano free: 200$/crediti iniziali)"
    info "  2. Dashboard → API Keys → Create Key"
    ask_secret "DEEPGRAM_API_KEY (premi Invio per saltare)" ""
    DEEPGRAM_KEY="$REPLY"

    # ── ElevenLabs ──
    echo -e "\n${CYAN}── ElevenLabs TTS (opzionale — per risposte vocali) ──${NC}"
    info "Sintesi vocale (Text-to-Speech) per far parlare Kira."
    info "Dove trovarla: https://elevenlabs.io/"
    info "  1. Registrati su elevenlabs.io (piano free: 10k caratteri/mese)"
    info "  2. Profile → API Key"
    info "  3. Voice ID: Voice Library → scegli una voce → copia l'ID"
    ask_secret "ELEVENLABS_API_KEY (premi Invio per saltare)" ""
    ELEVENLABS_KEY="$REPLY"
    if [ -n "$ELEVENLABS_KEY" ]; then
        ask "ELEVENLABS_VOICE_ID (ID della voce scelta)" ""
        ELEVENLABS_VOICE="$REPLY"
    else
        ELEVENLABS_VOICE=""
    fi

    # ── Supermemory ──
    echo -e "\n${CYAN}── Supermemory (opzionale — memoria persistente) ──${NC}"
    info "Memoria a lungo termine: Kira ricorda fatti, preferenze, conversazioni."
    info "Dove trovarla: https://app.supermemory.ai/"
    info "  1. Registrati su supermemory.ai"
    info "  2. Dashboard → Settings → API Keys → Create"
    info "  3. La chiave inizia con sm_..."
    ask_secret "SUPERMEMORY_API_KEY (premi Invio per saltare)" ""
    SUPERMEMORY_KEY="$REPLY"
    ask "Container tag (isolamento memoria)" "kira_alessandro"
    SUPERMEMORY_TAG="$REPLY"

    # ── Google ──
    echo -e "\n${CYAN}── Google Gmail + Calendar (opzionale) ──${NC}"
    info "Accesso a Gmail e Google Calendar personale."
    info "Dove trovarle: https://console.cloud.google.com/"
    info "  1. Crea un progetto su Google Cloud Console"
    info "  2. Abilita le API: Gmail API e Google Calendar API"
    info "  3. Credentials → Create OAuth 2.0 Client ID (tipo: Desktop app)"
    info "  4. Scarica il JSON → troverai client_id e client_secret"
    info "  5. Per il refresh_token: usa il playground OAuth2 di Google"
    info "     https://developers.google.com/oauthplayground/"
    info "     Scopes: gmail.modify, calendar.events"
    ask "GOOGLE_CLIENT_ID (premi Invio per saltare)" ""
    GOOGLE_CID="$REPLY"
    if [ -n "$GOOGLE_CID" ]; then
        ask_secret "GOOGLE_CLIENT_SECRET" ""
        GOOGLE_CSECRET="$REPLY"
        ask_secret "GOOGLE_REFRESH_TOKEN" ""
        GOOGLE_RTOKEN="$REPLY"
    else
        GOOGLE_CSECRET=""
        GOOGLE_RTOKEN=""
    fi

    # ── Microsoft 365 ──
    echo -e "\n${CYAN}── Microsoft 365 / Outlook (opzionale) ──${NC}"
    info "Accesso a email e calendario Outlook aziendale."
    info "Dove trovarle: https://portal.azure.com/ → App registrations"
    info "  1. Azure Portal → Azure Active Directory → App registrations"
    info "  2. New registration → Nome: 'Kira AI Assistant'"
    info "  3. Supported account types: 'Single tenant'"
    info "  4. API permissions: Mail.Read, Mail.Send, Calendars.ReadWrite"
    info "  5. Copia: Application (client) ID e Directory (tenant) ID"
    info "  (Serve un admin del tenant per il consent)"
    ask "MS365_CLIENT_ID (premi Invio per saltare)" ""
    MS365_CID="$REPLY"
    if [ -n "$MS365_CID" ]; then
        ask "MS365_TENANT_ID" ""
        MS365_TID="$REPLY"
    else
        MS365_TID=""
    fi

    # ── Tavily ──
    echo -e "\n${CYAN}── Tavily (opzionale — ricerca web) ──${NC}"
    info "Permette a Kira di cercare informazioni sul web."
    info "Dove trovarla: https://tavily.com/"
    info "  1. Registrati su tavily.com (piano free: 1000 ricerche/mese)"
    info "  2. Dashboard → API Key"
    ask_secret "TAVILY_API_KEY (premi Invio per saltare)" ""
    TAVILY_KEY="$REPLY"

    # ── Claude Code ──
    echo -e "\n${CYAN}── Claude Code CLI (opzionale — task di coding) ──${NC}"
    info "Per delegare task di coding a Claude Code (usa subscription MAX)."
    info "Prerequisiti: installa con 'curl -fsSL https://claude.ai/install.sh | sh'"
    info "  poi autenticati con 'claude auth login'"
    ask "Directory di lavoro per i progetti" "/home/kira/workspace"
    CC_WORKDIR="$REPLY"

    # ── LiveKit ──
    echo -e "\n${CYAN}── LiveKit (opzionale — interfaccia vocale web) ──${NC}"
    info "Interfaccia vocale real-time via browser (WebRTC)."
    info "LiveKit server verrà installato localmente su questa VPS."
    info "Servono delle chiavi API per autenticare i client."
    if [ -n "$KIRA_DOMAIN" ]; then
        LK_URL_DEFAULT="wss://$KIRA_DOMAIN"
    else
        LK_URL_DEFAULT=""
    fi
    ask "LIVEKIT_URL (vuoto per saltare)" "$LK_URL_DEFAULT"
    LK_URL="$REPLY"
    if [ -n "$LK_URL" ]; then
        info "Puoi generare le chiavi con: livekit-server generate-keys"
        info "Oppure usa quelle di default per sviluppo (devkey/secret)"
        ask "LIVEKIT_API_KEY" "devkey"
        LK_APIKEY="$REPLY"
        ask_secret "LIVEKIT_API_SECRET" "secret"
        LK_SECRET="$REPLY"
    else
        LK_APIKEY=""
        LK_SECRET=""
    fi

    # ── Frontend Auth ──
    echo -e "\n${CYAN}── Frontend Auth ──${NC}"
    info "Password per proteggere l'accesso al portale web di Kira."
    info "Chiunque conosca l'URL potrà accedere senza questa password."
    ask_secret "Password portale web (consigliato)" ""
    FRONTEND_PASS="$REPLY"

    # ── Scheduler ──
    echo -e "\n${CYAN}── Scheduler ──${NC}"
    info "Kira ti invierà un briefing giornaliero su Telegram."
    ask "Ora del briefing mattutino (HH:MM, fuso orario Europe/Rome)" "07:30"
    BRIEFING="$REPLY"

    # ── Tailscale ──
    echo -e "\n${CYAN}── PC Fisso via Tailscale (opzionale) ──${NC}"
    info "Collega il filesystem del tuo PC fisso a Kira via Tailscale."
    info "Dove trovarlo: https://tailscale.com/"
    info "  1. Installa Tailscale sul PC fisso e sulla VPS"
    info "  2. 'tailscale up' su entrambi"
    info "  3. 'tailscale ip' sul PC fisso per ottenere l'IP (100.x.x.x)"
    ask "IP Tailscale del PC fisso (premi Invio per saltare)" ""
    TS_IP="$REPLY"

    # Scrivi il file .env
    info "Scrivo il file .env..."

    # Determina LIVEKIT_URL per .env (con dominio se fornito)
    ENV_LK_URL="$LK_URL"

    cat > "$ENV_FILE" << ENVEOF
# Kira AI Assistant — Configurazione
# Generato dall'installer il $(date '+%Y-%m-%d %H:%M:%S')

# Dominio
KIRA_DOMAIN=${KIRA_DOMAIN}

# LLM
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}

# Database
POSTGRES_HOST=${PG_HOST}
POSTGRES_PORT=${PG_PORT}
POSTGRES_DB=${PG_DB}
POSTGRES_USER=${PG_USER}
POSTGRES_PASSWORD=${PG_PASS}

# Telegram
TELEGRAM_BOT_TOKEN=${TELEGRAM_TOKEN}
TELEGRAM_ALLOWED_USER_IDS=${TELEGRAM_USER_IDS}

# STT / TTS
DEEPGRAM_API_KEY=${DEEPGRAM_KEY}
ELEVENLABS_API_KEY=${ELEVENLABS_KEY}
ELEVENLABS_VOICE_ID=${ELEVENLABS_VOICE}

# Supermemory
SUPERMEMORY_API_KEY=${SUPERMEMORY_KEY}
SUPERMEMORY_CONTAINER_TAG=${SUPERMEMORY_TAG}

# Gmail MCP (OAuth)
GOOGLE_CLIENT_ID=${GOOGLE_CID}
GOOGLE_CLIENT_SECRET=${GOOGLE_CSECRET}
GOOGLE_REFRESH_TOKEN=${GOOGLE_RTOKEN}

# Web Search
TAVILY_API_KEY=${TAVILY_KEY}

# Scheduler
BRIEFING_TIME=${BRIEFING}
REMINDER_MINUTES_BEFORE=15

# Model Routing
DEFAULT_MODEL_TIER=advanced

# Claude Code
CLAUDE_CODE_WORKDIR=${CC_WORKDIR}
CLAUDE_CODE_MAX_BUDGET=5.0
CLAUDE_CODE_TIMEOUT=300

# Microsoft 365
MS365_CLIENT_ID=${MS365_CID}
MS365_TENANT_ID=${MS365_TID}

# LiveKit
LIVEKIT_URL=${ENV_LK_URL}
LIVEKIT_API_KEY=${LK_APIKEY}
LIVEKIT_API_SECRET=${LK_SECRET}

# PC Fisso (Tailscale)
PC_TAILSCALE_IP=${TS_IP}
PC_FILESYSTEM_PORT=8765

# Frontend Auth
FRONTEND_AUTH_PASSWORD=${FRONTEND_PASS}

# Telemetria Agno
AGNO_TELEMETRY=false
ENVEOF

    chown "$KIRA_USER:$KIRA_USER" "$ENV_FILE"
    chmod 600 "$ENV_FILE"
    ok "File .env creato e protetto (chmod 600)"
fi

echo

###############################################################################
# 5. Database PostgreSQL
###############################################################################

echo -e "${BOLD}═══ Step 5/8: Database PostgreSQL ═══${NC}"
echo

# Leggi le variabili dal .env appena creato
PG_DB=$(grep '^POSTGRES_DB=' "$ENV_FILE" | cut -d= -f2)
PG_USER=$(grep '^POSTGRES_USER=' "$ENV_FILE" | cut -d= -f2)
PG_PASS=$(grep '^POSTGRES_PASSWORD=' "$ENV_FILE" | cut -d= -f2)

# Verifica se il database esiste già
if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw "$PG_DB"; then
    ok "Database '$PG_DB' già esistente — non lo tocco"
else
    info "Creo utente e database PostgreSQL..."

    # Crea utente se non esiste
    if sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$PG_USER'" | grep -q 1; then
        ok "Utente PostgreSQL '$PG_USER' già esistente"
    else
        sudo -u postgres psql -c "CREATE USER $PG_USER WITH PASSWORD '$PG_PASS';"
        ok "Utente PostgreSQL '$PG_USER' creato"
    fi

    # Crea database
    sudo -u postgres psql -c "CREATE DATABASE $PG_DB OWNER $PG_USER;"
    ok "Database '$PG_DB' creato"
fi

# Applica schema (idempotente grazie a IF NOT EXISTS)
info "Applico schema database..."
PGPASSWORD="$PG_PASS" psql -h localhost -U "$PG_USER" -d "$PG_DB" \
    -f "$INSTALL_DIR/db/init.sql" 2>/dev/null
ok "Schema applicato (reminders, notes)"

echo

###############################################################################
# 6. Frontend (opzionale)
###############################################################################

echo -e "${BOLD}═══ Step 6/8: Frontend web (opzionale) ═══${NC}"
echo

LK_URL=$(grep '^LIVEKIT_URL=' "$ENV_FILE" | cut -d= -f2)

if [ "$NODE_OK" = true ] && [ -n "$LK_URL" ]; then
    if ask_yn "Vuoi installare il frontend web (Next.js + LiveKit)?"; then
        info "Installo dipendenze frontend..."
        cd "$INSTALL_DIR/frontend"

        # Crea .env.local per il frontend
        LK_APIKEY=$(grep '^LIVEKIT_API_KEY=' "$ENV_FILE" | cut -d= -f2)
        LK_SECRET=$(grep '^LIVEKIT_API_SECRET=' "$ENV_FILE" | cut -d= -f2)
        FRONTEND_PASS=$(grep '^FRONTEND_AUTH_PASSWORD=' "$ENV_FILE" | cut -d= -f2)

        cat > "$INSTALL_DIR/frontend/.env.local" << FEOF
NEXT_PUBLIC_LIVEKIT_URL=${LK_URL}
LIVEKIT_API_KEY=${LK_APIKEY}
LIVEKIT_API_SECRET=${LK_SECRET}
FRONTEND_AUTH_PASSWORD=${FRONTEND_PASS}
FEOF

        sudo -u "$KIRA_USER" npm install --prefix "$INSTALL_DIR/frontend" 2>/dev/null
        info "Build frontend..."
        sudo -u "$KIRA_USER" npm run build --prefix "$INSTALL_DIR/frontend" 2>/dev/null
        ok "Frontend installato e buildato"
        FRONTEND_INSTALLED=true
    fi
else
    if [ "$NODE_OK" = false ]; then
        warn "Node.js >= 18 non disponibile, salto il frontend"
    elif [ -z "$LK_URL" ]; then
        warn "LiveKit non configurato, salto il frontend"
    fi
fi

cd "$INSTALL_DIR"
echo

###############################################################################
# 7. Servizi systemd
###############################################################################

echo -e "${BOLD}═══ Step 7/8: Servizi systemd ═══${NC}"
echo
info "Installo i servizi systemd per Kira."
info "Non interferisco con altri servizi già attivi."
echo

# Aggiorna i path nei file .service per riflettere l'installazione
for svc in kira-agent kira-telegram kira-voice; do
    SVCFILE="$INSTALL_DIR/systemd/${svc}.service"
    if [ -f "$SVCFILE" ]; then
        # I file .service hanno già i path /home/kira/kira, OK
        cp "$SVCFILE" "/etc/systemd/system/${svc}.service"
    fi
done

systemctl daemon-reload

# Servizi core (sempre)
if ask_yn "Avviare kira-telegram (bot Telegram)?"; then
    systemctl enable --now kira-telegram
    ok "kira-telegram avviato"
else
    systemctl enable kira-telegram
    info "kira-telegram abilitato (partirà al prossimo riavvio)"
fi

# LiveKit + Voice (opzionale)
if [ -n "$LK_URL" ]; then
    echo
    if ask_yn "Vuoi installare e avviare LiveKit + Voice Worker?"; then
        # LiveKit server
        if ! check_command "livekit-server"; then
            info "Installo LiveKit server..."
            curl -sSL https://get.livekit.io 2>/dev/null | bash 2>/dev/null
        fi

        if [ -f "$INSTALL_DIR/voice/livekit.yaml" ]; then
            cp "$INSTALL_DIR/voice/livekit.yaml" /etc/livekit.yaml
        fi

        cp "$INSTALL_DIR/systemd/livekit.service" /etc/systemd/system/
        systemctl daemon-reload
        systemctl enable --now livekit
        ok "LiveKit server avviato"

        systemctl enable --now kira-voice
        ok "kira-voice avviato"
    fi
fi

echo

###############################################################################
# 8. Finalizzazione
###############################################################################

echo -e "${BOLD}═══ Step 8/8: Finalizzazione ═══${NC}"
echo

# Crea directory workspace per Claude Code
CC_WORKDIR=$(grep '^CLAUDE_CODE_WORKDIR=' "$ENV_FILE" | cut -d= -f2)
if [ -n "$CC_WORKDIR" ]; then
    mkdir -p "$CC_WORKDIR"
    chown "$KIRA_USER:$KIRA_USER" "$CC_WORKDIR"
fi

# Crea directory backup
mkdir -p /home/kira/backups
chown "$KIRA_USER:$KIRA_USER" /home/kira/backups

# Configura backup cron
if ask_yn "Configurare backup automatico PostgreSQL (ogni notte alle 2:00)?"; then
    CRON_LINE="0 2 * * * $INSTALL_DIR/scripts/backup_db.sh"
    (crontab -u "$KIRA_USER" -l 2>/dev/null | grep -v "backup_db.sh"; echo "$CRON_LINE") \
        | crontab -u "$KIRA_USER" -
    ok "Backup cron configurato"
fi

# Seed memoria (opzionale)
SUPERMEMORY_KEY=$(grep '^SUPERMEMORY_API_KEY=' "$ENV_FILE" | cut -d= -f2)
if [ -n "$SUPERMEMORY_KEY" ]; then
    echo
    if ask_yn "Vuoi pre-popolare la memoria di Kira con i fatti iniziali?"; then
        info "Seed memoria in corso..."
        sudo -u "$KIRA_USER" bash -c "cd $INSTALL_DIR && .venv/bin/python -m scripts.seed_memory" 2>&1 || true
        ok "Seed memoria completato"
    fi
fi

# Caddy config con dominio
KIRA_DOMAIN=$(grep '^KIRA_DOMAIN=' "$ENV_FILE" | cut -d= -f2)
if [ "$CADDY_OK" = true ] && [ -n "$KIRA_DOMAIN" ]; then
    echo
    CADDY_SNIPPET="$INSTALL_DIR/Caddyfile.generated"
    info "Genero la configurazione Caddy per $KIRA_DOMAIN..."

    cat > "$CADDY_SNIPPET" << CADDYEOF
# Kira AI Assistant — Caddy config
# Aggiungere al Caddyfile principale o importare con: import $CADDY_SNIPPET

$KIRA_DOMAIN {
    # Frontend Next.js
    reverse_proxy localhost:3000

    # LiveKit WebSocket
    @livekit {
        path /rtc*
        path /livekit*
    }
    reverse_proxy @livekit localhost:7880

    # Health check
    handle /health {
        reverse_proxy localhost:8080
    }

    # Headers di sicurezza
    header {
        X-Content-Type-Options nosniff
        X-Frame-Options DENY
        Referrer-Policy strict-origin-when-cross-origin
    }
}
CADDYEOF

    ok "Caddyfile generato: $CADDY_SNIPPET"
    echo
    warn "NON sovrascrivo il Caddyfile esistente per non rompere gli altri siti."
    info "Per attivare, aggiungi al tuo Caddyfile principale:"
    info "  import $CADDY_SNIPPET"
    info "Oppure copia il contenuto in /etc/caddy/Caddyfile"
    info "Poi: sudo systemctl reload caddy"
    info ""
    info "Caddy otterrà automaticamente un certificato SSL Let's Encrypt"
    info "per $KIRA_DOMAIN (assicurati che il DNS punti a questa VPS)."
fi

echo
echo -e "${BOLD}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║          Installazione completata!                ║${NC}"
echo -e "${BOLD}╚═══════════════════════════════════════════════════╝${NC}"
echo
echo -e "  ${GREEN}Directory:${NC}     $INSTALL_DIR"
echo -e "  ${GREEN}Configurazione:${NC} $INSTALL_DIR/.env"
echo -e "  ${GREEN}Utente:${NC}        $KIRA_USER"
echo -e "  ${GREEN}Database:${NC}      $PG_DB"
if [ -n "$KIRA_DOMAIN" ]; then
echo -e "  ${GREEN}Portale web:${NC}   https://$KIRA_DOMAIN"
fi
echo

echo -e "${BOLD}Servizi installati:${NC}"
for svc in kira-telegram kira-voice livekit; do
    if systemctl is-enabled "$svc" &>/dev/null 2>&1; then
        STATUS=$(systemctl is-active "$svc" 2>/dev/null || echo "inactive")
        if [ "$STATUS" = "active" ]; then
            echo -e "  ${GREEN}●${NC} $svc  (attivo)"
        else
            echo -e "  ${YELLOW}○${NC} $svc  (abilitato, non attivo)"
        fi
    fi
done

echo
echo -e "${BOLD}Comandi utili:${NC}"
echo "  sudo journalctl -u kira-telegram -f    # Log bot Telegram"
echo "  sudo systemctl restart kira-telegram    # Riavvia bot"
echo "  sudo systemctl status kira-telegram     # Stato bot"
echo "  curl http://localhost:8080/health       # Health check"
echo
echo -e "${BOLD}Per modificare la configurazione:${NC}"
echo "  sudo nano $INSTALL_DIR/.env"
echo "  sudo systemctl restart kira-telegram"
echo

if [ -z "$(grep '^ANTHROPIC_API_KEY=' "$ENV_FILE" | cut -d= -f2)" ]; then
    warn "ANTHROPIC_API_KEY non configurata! Kira non funzionerà senza."
    warn "Modifica $INSTALL_DIR/.env e aggiungi la tua API key."
fi

echo -e "${GREEN}Kira è pronta!${NC}"

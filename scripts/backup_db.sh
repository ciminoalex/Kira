#!/usr/bin/env bash
set -euo pipefail

# Backup giornaliero del database PostgreSQL di Kira
# Configurare come cron job:
#   0 2 * * * /home/kira/kira/scripts/backup_db.sh

BACKUP_DIR="/home/kira/backups"
DB_NAME="kira"
RETENTION_DAYS=30

mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/kira_${TIMESTAMP}.sql.gz"

echo "Backup database '$DB_NAME' in corso..."

pg_dump "$DB_NAME" | gzip > "$BACKUP_FILE"

echo "Backup completato: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"

# Pulizia backup vecchi
DELETED=$(find "$BACKUP_DIR" -name "kira_*.sql.gz" -mtime +$RETENTION_DAYS -delete -print | wc -l)
if [ "$DELETED" -gt 0 ]; then
    echo "Rimossi $DELETED backup più vecchi di $RETENTION_DAYS giorni."
fi

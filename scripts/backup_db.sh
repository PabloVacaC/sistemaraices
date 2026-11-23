#!/usr/bin/env bash
# =============================================================================
# Script de Respaldo Automatizado de Base de Datos - Sistemas Raíces
# Diseñado para ejecutarse periódicamente en cron de Linux / Servidor Docker.
# =============================================================================

set -e

# Directorio base del proyecto (un nivel arriba de scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Configuración básica (o sobreescribir con variables de entorno)
CONTAINER_NAME="${RAICES_DB_CONTAINER:-raices_db}"
DB_NAME="${POSTGRES_DB:-sistemraices_db}"
DB_USER="${POSTGRES_USER:-postgres}"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_DIR/backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-15}"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/backup_${DB_NAME}_${TIMESTAMP}.sql.gz"

# Crear directorio si no existe
mkdir -p "${BACKUP_DIR}"

echo "[$(date +"%Y-%m-%d %H:%M:%S")] Iniciando respaldo de '${DB_NAME}' desde contenedor '${CONTAINER_NAME}'..."

# Ejecutar pg_dump y comprimir con gzip al vuelo
docker exec -t "${CONTAINER_NAME}" pg_dump -U "${DB_USER}" -d "${DB_NAME}" | gzip > "${BACKUP_FILE}"

FILESIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
echo "[$(date +"%Y-%m-%d %H:%M:%S")] Respaldo completado exitosamente: ${BACKUP_FILE} (${FILESIZE})"

# Limpieza automática de respaldos antiguos (> RETENTION_DAYS días)
echo "[$(date +"%Y-%m-%d %H:%M:%S")] Eliminando respaldos mayores a ${RETENTION_DAYS} días..."
find "${BACKUP_DIR}" -type f -name "backup_${DB_NAME}_*.sql.gz" -mtime "+${RETENTION_DAYS}" -exec rm -f {} \;

echo "[$(date +"%Y-%m-%d %H:%M:%S")] Rutina de respaldo finalizada."


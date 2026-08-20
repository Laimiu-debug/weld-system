#!/bin/sh
set -eu

backup_interval="${BACKUP_INTERVAL_SECONDS:-86400}"
retention_days="${BACKUP_RETENTION_DAYS:-14}"

mkdir -p /backups

while true; do
  timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
  database_file="/backups/postgres-${timestamp}.dump"
  uploads_file="/backups/uploads-${timestamp}.tar.gz"

  echo "Starting database backup ${database_file}"
  PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
    --host=postgres \
    --username="${POSTGRES_USER}" \
    --dbname="${POSTGRES_DB}" \
    --format=custom \
    --file="${database_file}.tmp"
  mv "${database_file}.tmp" "${database_file}"

  echo "Starting upload backup ${uploads_file}"
  tar -czf "${uploads_file}.tmp" -C /uploads .
  mv "${uploads_file}.tmp" "${uploads_file}"

  find /backups -type f \( -name 'postgres-*.dump' -o -name 'uploads-*.tar.gz' \) \
    -mtime "+${retention_days}" -delete

  echo "Backup completed at ${timestamp}; sleeping ${backup_interval}s"
  sleep "${backup_interval}"
done

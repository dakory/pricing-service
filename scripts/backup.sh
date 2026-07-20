#!/bin/sh
set -eu
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
export PGPASSWORD="${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}"
pg_dump -h db -U pricing -Fc pricing |
  aws s3 cp - "s3://${BACKUP_BUCKET:?BACKUP_BUCKET is required}/postgres/pricing-${timestamp}.dump" \
    --sse aws:kms \
    --sse-kms-key-id "${BACKUP_KMS_KEY_ID:?BACKUP_KMS_KEY_ID is required}"


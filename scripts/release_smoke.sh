#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-https://pricing.nicer.homes}"
EXPECTED_SHA="${2:-}"

api_version="$(curl --fail --silent --show-error "${BASE_URL}/version")"
dashboard_version="$(curl --fail --silent --show-error "${BASE_URL}/dashboard-version")"

printf 'API version: %s\n' "$api_version"
printf 'Dashboard response: %s\n' "$(printf '%s' "$dashboard_version" | head -c 80)"

if [[ -n "$EXPECTED_SHA" ]] && ! grep -Fq "$EXPECTED_SHA" <<<"$api_version"; then
  echo "API release mismatch: expected ${EXPECTED_SHA}" >&2
  exit 1
fi

if ! grep -q 'Nicer Homes\|pricing' <<<"$dashboard_version"; then
  echo "Dashboard did not return the expected application HTML" >&2
  exit 1
fi

echo "Release smoke test passed for ${BASE_URL}."

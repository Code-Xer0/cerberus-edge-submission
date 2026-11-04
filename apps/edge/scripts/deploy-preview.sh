#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
ce_host="${1:-${CERBERUS_EDGE_SSH_HOST:-}}"
ce_expected="${CERBERUS_EXPECTED_CONTAINER:?Set the privately recorded expected container ID}"
[[ "$ce_host" =~ ^[[:alnum:]][[:alnum:]_.@:-]*$ ]] || { echo 'Invalid SSH destination' >&2; exit 2; }
npm run build
ce_version="ce002-$(date -u +%Y%m%dT%H%M%SZ)"
ce_archive="/tmp/${ce_version}.tar.gz"
tar -C dist -czf "$ce_archive" .
ce_hash=$(sha256sum "$ce_archive" | cut -d ' ' -f 1)
scp -q -o BatchMode=yes -o ConnectTimeout=8 "$ce_archive" "$ce_host:/tmp/${ce_version}.tar.gz"
ssh -o BatchMode=yes -o ConnectTimeout=8 "$ce_host" bash -s -- "$ce_version" "$ce_hash" "$ce_expected" <<'REMOTE'
set -euo pipefail
version="$1"
expected_hash="$2"
expected_container="$3"
archive="/tmp/${version}.tar.gz"
base="/opt/cerberus-edge/${version}"
before=$(sudo docker inspect -f '{{.Id}}' ragnar)
[[ "$before" == "$expected_container" ]] || { echo 'Runtime identity changed; inspect before deployment' >&2; exit 3; }
[[ "$(sha256sum "$archive" | cut -d ' ' -f 1)" == "$expected_hash" ]] || exit 4
sudo mkdir -p "$base/previous" "$base/dist" "$base/rollback-check"
rollback_state=not-applicable-no-existing-preview
if sudo docker exec ragnar test -f /opt/ragnar/web/cerberus-edge-v3/index.html; then
 sudo docker cp ragnar:/opt/ragnar/web/cerberus-edge-v3/. "$base/previous/"
 sudo tar -C "$base/previous" -czf "$base/previous.tar.gz" .
 sudo tar -C "$base/rollback-check" -xzf "$base/previous.tar.gz"
 sudo cmp "$base/previous/index.html" "$base/rollback-check/index.html"
 rollback_state=passed
fi
sudo docker exec ragnar mkdir -p /opt/ragnar/web/cerberus-edge-v3
sudo tar -C "$base/dist" -xzf "$archive"
sudo docker cp "$base/dist/." ragnar:/opt/ragnar/web/cerberus-edge-v3/
local_index=$(sudo sha256sum "$base/dist/index.html" | cut -d ' ' -f 1)
remote_index=$(sudo docker exec ragnar sha256sum /opt/ragnar/web/cerberus-edge-v3/index.html | cut -d ' ' -f 1)
[[ "$local_index" == "$remote_index" ]] || exit 5
[[ "$(sudo docker inspect -f '{{.Id}}' ragnar)" == "$before" ]] || exit 6
[[ "$(sudo docker inspect -f '{{.State.Running}}' ragnar)" == 'true' ]] || exit 7
printf 'VERSION=%s\nARCHIVE_SHA256=%s\nINDEX_SHA256=%s\nCONTAINER=%s\nROLLBACK_ARTIFACT_CHECK=%s\n' "$version" "$expected_hash" "$local_index" "$before" "$rollback_state"
if [ "$rollback_state" = passed ]; then
 printf 'ROLLBACK: sudo docker cp %s/previous/. ragnar:/opt/ragnar/web/cerberus-edge-v3/\n' "$base"
else
 printf 'ROLLBACK: no preceding preview existed; default and legacy were not changed.\n'
fi
REMOTE

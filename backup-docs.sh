#!/usr/bin/env bash
set -e -o pipefail

[ -f ~/.secrets/docs.enc ] || exit 1

secret=$(grep pass: ~/.secrets/docs.enc | cut -d: -f2 | base64 -d | rev | base64 -d | rev | base64 -d)
backup_file=~/Documents/archive/Personal-$(date +%F_%H%M%S).tgz
tar zcf "${backup_file}.tmp" \
    ~/Documents/Personal/ 2>/dev/null &&
gpg2 \
  --symmetric \
  --cipher-algo AES256 \
  --compress-algo zlib \
  --no-symkey-cache \
  --pinentry-mode loopback \
  --passphrase "$secret" \
  --output "${backup_file}.gpg" \
  "${backup_file}.tmp"

#sha1sum "${backup_file}.tmp"
rm -f "${backup_file}.tmp"

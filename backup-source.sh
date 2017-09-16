#!/usr/bin/env bash
set -e -o pipefail

backup_file=~/Source/archive/Source-$(date +%F_%T).tbz2
tar jcf "${backup_file}.tmp" \
    --exclude=Source/archive \
    --exclude=\*/target/{debug,release} \
    ~/Source/ 2>/dev/null &&
  mv "${backup_file}.tmp" "$backup_file"

#!/usr/bin/env bash

tar jcf ~/Source/archive/Source-$(date +%F_%T).tbz2 \
    --exclude=Source/archive \
    --exclude=\*/target/{debug,release} \
    ~/Source/

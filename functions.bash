#!/bin/bash

function map {
  local func="$@"
  while read line; do 
    $func "$line"
  done
}

function random {
  if [[ "$@" =~ -h ]]; then
    echo "Usage: random [hight] [low]"
    return 1;
  fi

  local high="${1:-1073676289}" # RAND_MAX ^ 2
  local low="${2:-0}"

  echo $(( ($RANDOM * $RANDOM) % ($high - $low) + $low ))
}

function tz_calc {
  if [ $# -lt 1 ]; then
    echo "Usage: tz_calc <tz-dest> [<tm-str>] [<tz-orig>]"
    return 1
  fi

  local tz_dest="$1"; shift
  local tm="${1:-now}"; shift
  local tz_orig="${1:-:/etc/localtime}"; shift

  # Override timezone in tm-str if we're specifying origin
  [ "$tz_orig" != ':/etc/localtime' ] && tm=$(date -d "$tm" "+%F %T")

   TZ="$tz_dest" date -d "$(TZ="$tz_orig" date -d "$tm" "+%F %T %z")" "$@"
}

function gkill {
  kill -TERM -$(ps -p $1 -o pgid --no-headers | tr -d " ")
}

function file_data_age {
  if [ $# -lt 1 ]; then
    echo "Usage: data_age <filename> (returns the days since the data was last modified)"
    return 1
  fi
  for f in "$@"; do
    echo $f:$(( ($(date +%s) - $(stat -c %Y "$f")) / 86400 ))
  done
}

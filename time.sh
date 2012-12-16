#!/usr/bin/env bash

function spell_time {
  local hour=${1:-$(date +%_H)}; shift
  local min=${1:-$(date +%_M)}; shift
  local roundmin=$((5 * $(printf "%.0f\n" $(bc -l <<< $min/5)) % 60))

  case $roundmin in
    0) mintext="" ;;
    5|55) mintext="cinco" ;;
    10|50) mintext="diez" ;;
    15|45) mintext="cuarto" ;;
    20|40) mintext="veinte" ;;
    25|35) mintext="veinticinco" ;;
    30) mintext="media" ;;
  esac

  if [ "$mintext" ]; then
    if [ $min -le 32 ]; then
      mintext="y $mintext"
    else
      mintext="menos $mintext"
      ((hour++))
    fi
  fi

  if [ $hour -ge 20 -o $hour -eq 0 ]; then
    ampm="de la noche"
  elif [ $hour -eq 12 ]; then
    ampm="del medio dia"
  elif [ $hour -ge 13 ]; then
    ampm="de la tarde"
  else
    ampm="de la maniana"
  fi

  hour=$((hour % 12))
  [ $hour = 0 ] && hour=12

  if [ $hour -eq 1 ]; then
    hourtext="Es la una"
  else
    hourtext="Son las $hour"
  fi

  echo "$hourtext $mintext $ampm"
}

spell_time "$@" |
  festival --language spanish --tts

# vim: set sw=2 sts=2 : #

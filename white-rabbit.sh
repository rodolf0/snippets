#!/usr/bin/env bash

function speak_the_time {
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

  if [ $min -le 32 ]; then
    [ "$mintext" ] && mintext="y $mintext"
  else
    [ "$mintext" ] && mintext="menos $mintext"
    ((hour++))
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

  echo "$hourtext $mintext $ampm" |
    festival --tts --language spanish
}


function frase_del_dia {
  wget -q -O - http://www.proverbia.net/qotd.asp |
    xmlstarlet sel -t -m //item -v //item/description |
    { LC_ALL=es_AR.utf8 iconv -f UTF-8 -t ASCII//TRANSLIT; } |
    festival --tts --language spanish
}


function agenda_del_dia {
  local the_agenda=$(
    agenda --secrets /home/************gle_secrets --on $(date +%F) |
      { LC_ALL=es_AR.utf8 iconv -f UTF-8 -t ASCII//TRANSLIT; } |
      sed 's/....-..-.. //' | tr '\n' '^' | sed 's/\^/, /g')
  if [ "$the_agenda" ]; then
    { echo "Agenda para hoy,"; echo "$the_agenda"; } |
      festival --tts --language spanish
  fi
}

function tiempo_actual {
  local weather=$(wget -q -O - 'http://api.wunderground.com/api/70076******e08ba/conditions/lang:SP/q/NY/10022.xml' |
    xmlstarlet sel -t -m //current_observation -v //temp_c -o : -v //feelslike_c -o : -v //weather |
    { LC_ALL=es_AR.utf8 iconv -f UTF-8 -t ASCII//TRANSLIT; })
  local _temperatura=$(echo $weather | cut -d : -f 1 | sed 's/\..*$//')
  local _sensacion=$(echo $weather | cut -d : -f 2 | sed 's/\..*$//')
  local _tiempo=$(echo $weather | cut -d : -f 3)
  [ "${_temperatura:0:1}" = '-' ] && local signo_temp=" menos "
  [ "${_sensacion:0:1}" = '-' ] && local signo_senc=" menos "
  { cat - <<EOF
Hacen $signo_temp $_temperatura grados. $_tiempo.
EOF
  } | festival --tts --language spanish
}


function main {
  current_volume=$(amixer get Master |
    sed '/^ *Mono: Playback/!d; s/^.* Playback \([0-9]\+\) .*$/\1/')

  last_spoken_time=0
  last_spoken_agenda=0
  last_spoken_phrase=0
  last_spoken_weather=0
  while true; do
    sleep $((5 * 60))
    # only speak between 8:00am and 23:59pm
    [ $(date +%H) -ge 8 -a $(date +%H) -le 23 ] || continue

    now=$(date +%s)

    amixer set Master 54 > /dev/null

    # say clima
    if [ $((RANDOM % 30)) -eq 0 ] || \
       [ $((now - last_spoken_weather)) -gt 10800 ]; then
      tiempo_actual
      last_spoken_weather=$now
    fi

    # tell the time randomly, not more than once every 30min
    if [ $((now - last_spoken_time)) -gt 1800 ]; then
      # don't wait more than an hour and a half to tell the time
      if [ $((now - last_spoken_time)) -gt 5400 ] || \
         [ $((RANDOM % 10)) -eq 0 ]; then
        speak_the_time
        last_spoken_time=$now
      fi
    fi

    # tell the agenda for today after 8:45am once, then again after 19.30
    if [ "$last_spoken_agenda" -lt $(date -d '8:45 today' +%s) -a \
         $now -ge $(date -d '8:45 today' +%s) ] || \
       [ "$last_spoken_agenda" -lt $(date -d '19:30 today' +%s) -a \
         $now -ge $(date -d '19:30 today' +%s) ]; then
      agenda_del_dia
      last_spoken_agenda=$now
    fi

    # say a random frase
    #if [ $((RANDOM % 50)) -eq 0 ] || \
       #[ $((now - last_spoken_phrase)) -gt 14400 ]; then
      #frase_del_dia
      #last_spoken_phrase=$now
    #fi

    amixer set Master $current_volume > /dev/null
  done
}

main "$@"

# vim: set sw=2 sts=2 : #

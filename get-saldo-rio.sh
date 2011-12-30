#!/usr/bin/env bash
set -e


function get_login_tokens {
  # get login tokes: user_id_name=user_id_value:tokenfs_value
  local login_url=$(
    curl --silent --location \
         --cookie-jar $cookie_jar --cookie $cookie_jar \
         --user-agent "$user_agent" \
         $base_url/hb/html/index.jsp |
      sed '/location\.href/!d; s/^.*"\(.*\)".*$/\1/')

  local tokenfs_value=$(
    curl --silent --location \
         --cookie-jar $cookie_jar --cookie $cookie_jar \
         --user-agent "$user_agent" \
         $base_url/$login_url |
      sed '/tokenFS/!d; s/^.*value="\(.*\)".*$/\1/;')

  echo ${login_url#*\?}:$tokenfs_value
}


function build_js_context {
  local DNI="$1"            ;shift
  local PIN="$1"            ;shift
  local USR="$1"            ;shift
  local TOKENFS_VALUE="$1"  ;shift
  local LOGIN_VALUE="$1"    ;shift
  local context=$(mktemp)

  # obtener js de formato
  curl --silent --location \
       --cookie-jar $cookie_jar --cookie $cookie_jar \
       --user-agent "$user_agent" \
       $base_url/hb/javascript/formato.js \
    > $context

  # obtener js de cripto
  curl --silent --location \
       --cookie-jar $cookie_jar --cookie $cookie_jar \
       --user-agent "$user_agent" \
       $base_url/hb/javascript/cripto.js \
    >> $context

  cat >> $context <<-EOF
		
		var cr = new Cripto();
		var ct = new Date();
		var fmt = new Formato();
		print('dniOri=' + '$DNI');
		print('dni=' + cr.enc( fmt.formatDNI('$DNI')));
		print('clave=' + cr.enc(fmt.formatPIN('$PIN')));
		print('claveNueva=');
		print('claveNuevaReingreso=');
		print('usuario=' + cr.enc(fmt.formatUSR('$USR')));
		print('usuarioNuevo=');
		print('fechaNac=');
		print('usuarioVacio=' + cr.enc(fmt.formatUSR('')));
		print('claveVacia=' + cr.enc(fmt.formatPIN('')));
		print('REQID=VISMERC');
		print('DESTINATION=undefined');
		print('tv=' + 'F');
		print('accion=' + 'INICIO');
		print('prefijo=' + cr.enc(cr.getCI()));
		print('sufijo=' + cr.getCF());
		print('sinonimo=' + '0');
		print('codPregunta=' + cr.enc('000'));
		print('orden=' + cr.enc('00'));
		print('timestamp=' + cr.enc('                          '));
		print('cantOpciones=' + cr.enc('00'));
		print('codOpcion=' + cr.enc('00'));
		print('tokenFS=$TOKENFS_VALUE');
		print('cldt=' + ct.getFullYear() + "." + (ct.getMonth() + 1) +
				 "." + ct.getDate() + "." + ct. getHours() + "." +
				 ct.getMinutes() + "." + ct.getSeconds());
		print('$LOGIN_VALUE');
		EOF

  echo $context
}


function do_login {
  local DNI="$1" ;shift
  local PIN="$1" ;shift
  local USR="$1" ;shift
  # build variables
  local tokens=$(get_login_tokens)
  local context=$(build_js_context $DNI $PIN $USR "${tokens#*:}" "${tokens%:*}")
  local login_vars=$($js_interpreter $context | tr '\n' '&'; rm -f $context)

  local login_step_4=$(
    curl --silent --location \
         --cookie-jar $cookie_jar --cookie $cookie_jar \
         --user-agent "$user_agent" --referer $referer \
         --data "$login_vars" \
         $base_url/hb/html/login/procesoLogin.jsp |
      sed '/document\.location\.href/!d; s/^.*"\(.*\)".*$/\1/' |
      tail -1)

  # consumir paginas de login
  curl --silent --location \
       --cookie-jar $cookie_jar --cookie $cookie_jar \
       --user-agent "$user_agent" --referer $referer \
       --data "$login_vars" \
       $base_url/hb/html/login/$login_step_4 &>/dev/null &

  curl --silent --location \
       --cookie-jar $cookie_jar --cookie $cookie_jar \
       --user-agent "$user_agent" --referer $referer \
       --data "$login_vars" \
       $base_url/hb/html/login/bienvenida.jsp &>/dev/null &

  curl --silent --location \
       --cookie-jar $cookie_jar --cookie $cookie_jar \
       --user-agent "$user_agent" --referer $referer \
       --data "$login_vars" \
       $base_url/hb/html/common/fInicio.jsp &>/dev/null &

  # pagina de inicio que contiene el saldo
  curl --silent --location \
       --cookie-jar $cookie_jar --cookie $cookie_jar \
       --user-agent "$user_agent" --referer $referer \
       --data "$login_vars" \
       $base_url/hb/html/bienvenida/fBienvenida.jsp
}


function grep_saldo {
  awk '
    BEGIN { nTAB=0; nROW=0; nDAT=0; inTAB=0 }
    /<table[^>]*>/         { nTAB += 1; inTAB=1 }
    /<\/table>/            { nROW = 0 ; inTAB=0 }
    /<tr[^>]*>/            { nROW += 1 }
    /<\/tr>/               { nDAT = 0 }
    /<td[^>]*>/            { nDAT += 1 }
    nTAB == 8 && inTAB && nROW == 2 && nDAT == 2 { print }
  ' | sed '2!d; s/\s\+//g'
}


echo -n "DNI: " >&2; read DNI
echo -n "PIN: " >&2; read -s PIN
echo -e -n "\nUSR: " >&2; read -s USR
echo >&2

if [ "$DNI" -a "$PIN" -a "$USR" ]; then
  user_agent="Firefox/3.0.11"
  cookie_jar=$(mktemp)
  base_url="https://www.personas.santanderrio.com.ar"
  referer="www.personas.santanderrio.com.ar"
  js_interpreter=gjs

  do_login "$DNI" "$PIN" "$USR" | grep_saldo
fi
rm -f $cookie_jar

# vim: set sw=2 sts=2 : #

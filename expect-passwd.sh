#!/usr/bin/expect -f

set env(LANG) C
set password [lindex $argv 1]

spawn passwd [lindex $argv 0]

expect "Enter new UNIX password:"
sleep 0.1
send "$password\r"
expect "Retype new UNIX password:"
sleep 0.1
send "$password\r"
expect eof

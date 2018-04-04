#!/bin/sh

fb_ips() {
  # whois -h "whois.radb.net" -- '-i origin AS32934' |
  #   awk '/^route:/ {print $2}'
  cat - <<EOF
157.240.16.0/24
204.15.20.0/22
EOF
}

reroute_fb() {
  fb_ips | while read ipmask; do
    iptables -t mangle -A FORWARD \
             -i eth1.1 --source "$ipmask" -j MARK --set-mark 8
  done
  # assume 1pkt = 1.5k => 1.5mb/s
  iptables -t mangle -A FORWARD -m mark --mark 8 \
           -m limit --limit 10/second -j ACCEPT
  iptables -t mangle -A FORWARD -m mark --mark 8 -j DROP
}

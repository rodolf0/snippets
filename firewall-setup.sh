#!/usr/bin/env bash

# Insted of accepting the packect directly do accounting
ACCEPT=accounting


function reset_all {
  local filter=(INPUT FORWARD OUTPUT)
  local nat=(PREROUTING POSTROUTING OUTPUT)
  local mangle=(PREROUTING INPUT FORWARD OUTPUT POSTROUTING)

  for tab in filter nat mangle; do
    iptables -t $tab -F
    iptables -t $tab -X
    for chain in $(eval echo \${$tab[@]}); do
      iptables -t $tab -P $chain ACCEPT
    done
  done
}



function set_kernel_opts {
  echo 1 > /proc/sys/net/ipv4/ip_forward
  # Enable source address re-writing if the interface changes (used with masquerading)
  echo 1 > /proc/sys/net/ipv4/ip_dynaddr
  # Enables SYN flood protection
  echo 1 > /proc/sys/net/ipv4/tcp_syncookies
  echo 2048 > /proc/sys/net/ipv4/tcp_max_syn_backlog
  echo 2 > /proc/sys/net/ipv4/tcp_synack_retries
  echo 5 > /proc/sys/net/ipv4/tcp_syn_retries
  # Enable source-address verification to avoid spoofing
  echo 1 > /proc/sys/net/ipv4/conf/all/rp_filter
  echo 1 > /proc/sys/net/ipv4/conf/default/rp_filter
  # Discard ICMP redirects (prevent MITM attacks)
  echo 0 > /proc/sys/net/ipv4/conf/all/accept_redirects
  echo 0 > /proc/sys/net/ipv4/conf/default/accept_redirects
  # Accept redirects from our "default" gateways
  echo 1 > /proc/sys/net/ipv4/conf/all/secure_redirects
  # Ignore source-routed packets
  echo 0 > /proc/sys/net/ipv4/conf/all/accept_source_route
  echo 0 > /proc/sys/net/ipv4/conf/default/accept_source_route
  # Log martian packets (those with an address not belonging to the interface)
  echo 1 > /proc/sys/net/ipv4/conf/all/log_martians
  # Ignore ICMP broadcast requests
  echo 1 > /proc/sys/net/ipv4/icmp_echo_ignore_broadcasts
  # Respond to ARP on behalf of others
  #echo 1 > /proc/sys/net/ipv4/conf/all/proxy_arp
}



function bad_packets {
  iptables -N bad_packets

  function bad_tcp_packets {
    iptables -N bad_tcp_packets
    iptables -A bad_packets -p tcp -j bad_tcp_packets
    # new packets need SYN
    iptables -A bad_tcp_packets -p tcp ! --syn -m conntrack --ctstate NEW -j DROP
    # stealth scans
    iptables -A bad_tcp_packets -p tcp --tcp-flags ALL NONE -j DROP
    iptables -A bad_tcp_packets -p tcp --tcp-flags ALL ALL -j DROP
    iptables -A bad_tcp_packets -p tcp --tcp-flags ALL FIN,URG,PSH -j DROP
    iptables -A bad_tcp_packets -p tcp --tcp-flags ALL SYN,RST,ACK,FIN,URG -j DROP
    iptables -A bad_tcp_packets -p tcp --tcp-flags SYN,RST SYN,RST -j DROP
    iptables -A bad_tcp_packets -p tcp --tcp-flags SYN,FIN SYN,FIN -j DROP
    # all good
    iptables -A bad_tcp_packets -j RETURN
  }
  bad_tcp_packets # load bad tcp checks

  # icmp should always fit in layer 2, else probably DOS attack
  iptables -A bad_packets --fragment -p ICMP -j DROP
  iptables -A bad_packets -p ALL -m conntrack --ctstate INVALID -j DROP
  # all good, so return
  iptables -A bad_packets -j RETURN
}



function firewall_input {
  local wlan=172.29.29.0/24
  local transmission_in=$(grep '"peer-port"' \
    /etc/transmission-daemon/settings.json | sed 's/[^0-9]//g')
  # DROP policy
  iptables -P INPUT DROP
  # explicit drops
  # don't allow android devices to consume all mpd pool
  iptables -A INPUT -i wlan0 -p TCP --dport 6600 \
           -m conntrack --ctstate NEW \
           -m connlimit --connlimit-above 2 -j DROP
  # allowed
  iptables -A INPUT -p ALL -j bad_packets
  iptables -A INPUT -p ALL -m conntrack \
           --ctstate ESTABLISHED,RELATED -j $ACCEPT
  iptables -A INPUT -p ALL -i lo -j $ACCEPT
  # Accept ALL traffic comming from the local zone
  iptables -A INPUT -p ALL -i wlan0 -s $wlan -j $ACCEPT
  iptables -A INPUT -p ALL -i wlan0 -s 224.0.0.0/4 -j $ACCEPT
  # Allow DHCP requests from internal network (dst 255.255.255.255)
  iptables -A INPUT -p UDP -i wlan0 --dport 67 -j $ACCEPT

  # define what we accept from outside (eth0)
  function udp_input_from_ext {
    iptables -N udp_input_from_ext
    iptables -A INPUT -p UDP -i eth0 -j udp_input_from_ext
    # accept dhcp reply (might not get related because initial broadcast)
    iptables -A udp_input_from_ext -p udp --sport 67 -j $ACCEPT
    # transmission torrent peer port (incomming connections) use UPNP
    iptables -A udp_input_from_ext -p udp --dport $transmission_in -j $ACCEPT
    # Just let DDNS provider resolve *.mydomain.x.y to my ip
    # allow DNS queries to resolve our domains
    #iptables -A udp_input_from_ext -p udp --dport 53 \
    #         -m conntrack --ctstate NEW -j $ACCEPT
    iptables -A udp_input_from_ext -j RETURN
  }
  udp_input_from_ext # load accepted udp input

  function tcp_input_from_ext {
    iptables -N tcp_input_from_ext
    iptables -A INPUT -p TCP -i eth0 -j tcp_input_from_ext
    # Open our webserver to the outside world
    iptables -A tcp_input_from_ext -p tcp --dport 80 \
             -m conntrack --ctstate NEW -j $ACCEPT
    # Enable incoming ssh connections
    iptables -A tcp_input_from_ext -p tcp \
             -m multiport --dports 27022,65534 \
             -m conntrack --ctstate NEW -j $ACCEPT
    # Accept incoming torrent traffic
    iptables -A tcp_input_from_ext -p tcp --dport $transmission_in -j $ACCEPT
    iptables -A tcp_input_from_ext -p tcp -j RETURN
  }
  tcp_input_from_ext #load accepted tcp input

  function icmp_input_from_ext {
    iptables -N icmp_input_from_ext
    iptables -A INPUT -p ICMP -i eth0 -j icmp_input_from_ext
    # allow time exeeded, destination unreachable, echo request
    iptables -A icmp_input_from_ext -p ICMP --icmp-type 11 -j $ACCEPT
    iptables -A icmp_input_from_ext -p ICMP --icmp-type 3 -j $ACCEPT
    iptables -A icmp_input_from_ext -p ICMP --icmp-type 8 \
             -m limit --limit 1/second --limit-burst 3 -j $ACCEPT
    iptables -A icmp_input_from_ext -j RETURN
  }
  icmp_input_from_ext # load icmp accepted pkts

  iptables -A INPUT -m limit --limit 4/minute --limit-burst 2 \
           -j LOG --log-prefix "input pkt dropped: "
}



function firewall_output {
  iptables -P OUTPUT DROP
  # Explicit drops
  iptables -A OUTPUT -o eth0 -d 224.0.0.0/4 -j DROP
  # allow established
  iptables -A OUTPUT -p ALL -j bad_packets
  iptables -A OUTPUT -p ALL -m conntrack \
           --ctstate ESTABLISHED,RELATED -j $ACCEPT
  # allowed
  iptables -A OUTPUT -p ALL -o lo -j $ACCEPT
  local wlan=172.29.29.0/24
  iptables -A OUTPUT -p ALL -o wlan0 -d $wlan -j $ACCEPT
  iptables -A OUTPUT -p ALL -o wlan0 -d 224.0.0.0/4 -j $ACCEPT
  # allow DHCP replies to internal network (no state so must be explicit)
  iptables -A OUTPUT -p UDP -o wlan0 --sport 67 --dport 68 -j $ACCEPT
  # allow outgoing pings
  iptables -A OUTPUT -p ICMP --icmp-type 8 -j $ACCEPT
  # allow basic internet traffic (67: dhcp, 53: dns, 123: ntp)
  iptables -A OUTPUT -p UDP -o eth0 \
           -m multiport --dports 67,53,123 \
           -m conntrack --ctstate NEW -j $ACCEPT
  # allowed outgoing TCP
  local keyserver=11371
  local gmail_relay=587
  local jbot=5222
  local basic_traffic=80,443,123
  iptables -A OUTPUT -p tcp -o eth0 \
           -m multiport --dports $basic_traffic,$gmail_relay,$keyserver,$jbot \
           -m conntrack --ctstate NEW -j $ACCEPT
  # http://65.60.52.122:8531/estaciondelsol
  iptables -A OUTPUT -p tcp -o eth0 -d 65.60.52.122 \
           --dport 8531 -m conntrack --ctstate NEW -j $ACCEPT
  # allow debian-transmission to start connections
  iptables -A OUTPUT -p ALL -o eth0 \
           -m owner --uid-owner debian-transmission \
           -m conntrack --ctstate NEW -j $ACCEPT

  iptables -A OUTPUT -m limit --limit 4/minute --limit-burst 2 \
           -j LOG --log-prefix "output pkt dropped: "
}



function firewall_forward {
  iptables -P FORWARD DROP
  iptables -A FORWARD -p ALL -j bad_packets
  iptables -A FORWARD -p ALL -m conntrack \
           --ctstate ESTABLISHED,RELATED -j $ACCEPT
  iptables -A FORWARD -p ALL -i wlan0 -o wlan0 -j $ACCEPT

  # allow everything unless explicitely dropped
  function fwd_int2ext {
    iptables -N fwd_int2ext
    iptables -A FORWARD -i wlan0 -o eth0 -j fwd_int2ext
    # here we should DROP stuff we don't want forwarded to the outside world
    iptables -A fwd_int2ext -m conntrack \
             --ctstate NEW -j $ACCEPT
  }
  fwd_int2ext # load int2ext forward filtering


  # drop everything comming in unless explicit
  function fwd_ext2int {
    iptables -N fwd_ext2int
    iptables -A FORWARD -i eth0 -o wlan0 -j fwd_ext2int
    # here we should ACCEPT anything we want to allow inbound (ADD appropiate NAT)
    iptables -A fwd_ext2int -j RETURN
  }
  fwd_ext2int # load inbound forward allowances


  iptables -A FORWARD -m limit --limit 3/minute --limit-burst 3 \
    -j LOG --log-prefix "FORWARD pckt died: "
}



function firewall_nat {
  # move incomming connections on 443 from select hosts to ssh port
  #local ssh_redirect='200.**.***.***/29'
  #iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 443 \
  #         -s $ssh_redirect -j REDIRECT --to-ports 27022
  # masquerade traffic outgoing to the wild
  iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
}



function firewall_accounting {
  iptables -N accounting

  iptables -A accounting -o eth0
  iptables -A accounting -i eth0
  iptables -A accounting -o wlan0
  iptables -A accounting -i wlan0
  # www: http/https
  iptables -A accounting -o eth0 -p tcp --dport 80
  iptables -A accounting -i eth0 -p tcp --sport 80
  iptables -A accounting -o eth0 -p tcp --dport 443
  iptables -A accounting -i eth0 -p tcp --sport 443

  iptables -A accounting -j ACCEPT
}



####################################################

if [ -z "$1" ]; then
  echo "usage: $0 <start|stop|forward>"
  exit 1
fi


case $1 in
  start)
    # common setup
    reset_all
    set_kernel_opts
    firewall_accounting
    bad_packets
    # firewall main chains
    firewall_input
    firewall_output
    firewall_forward
    # nat chains
    firewall_nat
  ;;

  forward)
    reset_all
    echo "1" > /proc/sys/net/ipv4/ip_forward
    iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
  ;;

  stop)
    reset_all
    set_kernel_opts
  ;;
esac

exit 0


# Sources:
# http://www.frozentux.net/iptables-tutorial/images/tables_traverse.jpg
# http://xkr47.outerspace.dyndns.org/netfilter/packet_flow/packet_flow9.png
# http://blog.edseek.com/~jasonb/articles/tcng_shaping.html

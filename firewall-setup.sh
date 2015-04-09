#!/usr/bin/env bash

function source_variables {
  transmission_in=$(grep '"peer-port"' \
    /etc/transmission-daemon/settings.json | sed 's/[^0-9]//g')
}

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

  tc qdisc del dev ppp0 root
  tc qdisc add dev ppp0 root fifo_fast
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


#######################################################
#################### FILTER tables ####################
#######################################################


function bad_packets {
  iptables -N bad_packets
  # new packets need SYN
  iptables -A bad_packets -p tcp ! --syn -m conntrack --ctstate NEW -j DROP
  # DROP stealth scans
  iptables -A bad_packets -p tcp --tcp-flags ALL NONE -j DROP
  iptables -A bad_packets -p tcp --tcp-flags ALL ALL -j DROP
  iptables -A bad_packets -p tcp --tcp-flags ALL FIN,URG,PSH -j DROP
  iptables -A bad_packets -p tcp --tcp-flags ALL SYN,RST,ACK,FIN,URG -j DROP
  iptables -A bad_packets -p tcp --tcp-flags SYN,RST SYN,RST -j DROP
  iptables -A bad_packets -p tcp --tcp-flags SYN,FIN SYN,FIN -j DROP
  # icmp should always fit in layer 2, else probably DOS attack
  iptables -A bad_packets --fragment -p ICMP -j DROP
  iptables -A bad_packets -p ALL -m conntrack --ctstate INVALID -j DROP
  # all good
  iptables -A bad_packets -j RETURN
}


function firewall_input {
  # INPUT from LAN
  function firewall_input::from_lan {
    iptables -N input_from_lan
    # don't allow android devices to consume all mpd connections
    iptables -A input_from_lan -p TCP --dport 6600 \
             -m conntrack --ctstate NEW \
             -m connlimit --connlimit-above 2 -j RETURN
    iptables -A input_from_lan -s 172.29.29.0/24 -j ACCEPT
    iptables -A input_from_lan -s 224.0.0.0/4 -j ACCEPT
    # allow DHCP (saddr/daddr 0.0.0.0/255.255.255.255)
    iptables -A input_from_lan -p UDP --dport 67 --sport 68 -j ACCEPT
    iptables -A input_from_lan -j LOG --log-prefix "[NF] dropped input_from_lan: "
    iptables -A input_from_lan -j DROP
  }

  # INPUT from the Internet
  function firewall_input::from_internet {
    iptables -N input_from_internet
    # let our server get an IP via DHCP
    iptables -A input_from_internet -p UDP --dport 68 --sport 67 -j ACCEPT
    # transmission torrent peer port (incomming connections) use UPNP
    [ "$transmission_in" ] && {
      iptables -A input_from_internet -p UDP --dport "$transmission_in" -j ACCEPT
      iptables -A input_from_internet -p TCP --dport "$transmission_in" -j ACCEPT
    }
    # Open our webserver to the outside world
    iptables -A input_from_internet -p TCP --dport 80 \
             -m conntrack --ctstate NEW -j ACCEPT
    # Enable incoming ssh connections
    iptables -A input_from_internet -p TCP \
             -m multiport --dports 27022 \
             -m conntrack --ctstate NEW -j ACCEPT
    # allow time exeeded, destination unreachable, echo request
    iptables -A input_from_internet -p ICMP --icmp-type 11 -j ACCEPT
    iptables -A input_from_internet -p ICMP --icmp-type 3 -j ACCEPT
    iptables -A input_from_internet -p ICMP --icmp-type 8 \
             -m limit --limit 1/second --limit-burst 3 -j ACCEPT
    iptables -A input_from_internet -j LOG --log-prefix "[NF] dropped input_from_internet: "
    iptables -A input_from_internet -j DROP
  }

  firewall_input::from_lan
  firewall_input::from_internet

  iptables -P INPUT DROP
  iptables -A INPUT -j bad_packets
  iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
  iptables -A INPUT -i lo -j ACCEPT
  iptables -A INPUT -i wlan0 -j input_from_lan
  iptables -A INPUT -i ppp0 -j input_from_internet

  iptables -A INPUT -i wlan0 -j LOG --log-prefix "[NF] WHAT!!: "
  iptables -A INPUT -i ppp0 -j LOG --log-prefix "[NF] WHAT!!: "
}


function firewall_output {
  # OUTPUT to LAN
  function firewall_output::to_lan {
    iptables -N output_to_lan
    # allow DHCP replies to internal network (no state so must be explicit)
    iptables -A output_to_lan -p UDP --sport 67 --dport 68 -j ACCEPT
    iptables -A output_to_lan -p ICMP -j ACCEPT
    iptables -A output_to_lan -j LOG --log-prefix "[NF] dropped output_to_lan: "
    iptables -A output_to_lan -j DROP
  }

  # OUTPUT to Internet
  function firewall_output::to_internet {
    iptables -N output_to_internet
    iptables -A output_to_internet -p ICMP --icmp-type 8 -j ACCEPT
    # allow querying some services (dhcp:67 dns:53 ntp:123)
    iptables -A output_to_internet -p UDP \
             -m multiport --dports 67,53,123 \
             -m conntrack --ctstate NEW -j ACCEPT
    # random stuff (web:80,443 gmail-relay:587 key-server:11371)
    iptables -A output_to_internet -p TCP \
             -m multiport --dports 80,443,123,587,11371 \
             -m conntrack --ctstate NEW -j ACCEPT
    # allow debian-transmission to start connections
    iptables -A output_to_internet -p ALL \
             -m owner --uid-owner debian-transmission \
             -m conntrack --ctstate NEW -j ACCEPT
    # http://65.60.52.122:8531/estaciondelsol
    iptables -A output_to_internet -p TCP \
             -d 65.60.52.122 --dport 8531 \
             -m conntrack --ctstate NEW -j ACCEPT
    iptables -A output_to_internet -j LOG --log-prefix "[NF] dropped output_to_internet: "
    iptables -A output_to_internet -j DROP
  }

  firewall_output::to_lan
  firewall_output::to_internet

  iptables -P OUTPUT DROP
  iptables -A OUTPUT -j bad_packets
  iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
  iptables -A OUTPUT -o lo -j ACCEPT
  iptables -A OUTPUT -o wlan0 -j output_to_lan
  iptables -A OUTPUT -o ppp0 -j output_to_internet

  iptables -A OUTPUT -o wlan0 -j LOG --log-prefix "[NF] WHAT!!: "
  iptables -A OUTPUT -o ppp0 -j LOG --log-prefix "[NF] WHAT!!: "
}


function firewall_forward {
  # FORWARD LAN => Internet
  function firewall_forward::lan_to_internet {
    iptables -N lan_to_internet
    iptables -A lan_to_internet -m conntrack --ctstate NEW -j ACCEPT
    iptables -A lan_to_internet -j LOG --log-prefix "[NF] dropped lan_to_internet: "
    iptables -A lan_to_internet -j DROP
  }

  # FORWARD Internet => LAN (remember to NAT)
  function firewall_forward::internet_to_lan {
    iptables -N internet_to_lan
    iptables -A internet_to_lan -j LOG --log-prefix "[NF] dropped internet_to_lan: "
    iptables -A internet_to_lan -j DROP
  }

  firewall_forward::lan_to_internet
  firewall_forward::internet_to_lan

  iptables -P FORWARD DROP
  iptables -A FORWARD -j bad_packets
  iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
  iptables -A FORWARD -i lo -o lo -j ACCEPT
  iptables -A FORWARD -i wlan0 -o ppp0 -j lan_to_internet
  iptables -A FORWARD -i ppp0 -o wlan0 -j internet_to_lan
  # allow traffic between hosts in the LAN
  iptables -A FORWARD -i wlan0 -o wlan0 -j ACCEPT

  iptables -A FORWARD -i wlan0 -o ppp0 -j LOG --log-prefix "[NF] WHAT!!: "
  iptables -A FORWARD -i ppp0 -o wlan0 -j LOG --log-prefix "[NF] WHAT!!: "
}


#######################################################
###################### NAT tables #####################
#######################################################


function firewall_nat {
  # masquerade traffic outgoing to the wild
  iptables -t nat -A POSTROUTING -o ppp0 -j MASQUERADE
}


#######################################################
################## MANGLE tables ######################
#######################################################


function firewall_mangle {
  # get around Path MTU discovery issues for adsl
  iptables -t mangle -A FORWARD -o ppp0 \
           -p TCP --tcp-flags SYN,RST SYN \
           -j TCPMSS --clamp-mss-to-pmtu
}


#######################################################
################ TRAFFIC CONTROL ######################
#######################################################


function traffic_control {
  tc qdisc del dev ppp0 root
  tc qdisc add dev ppp0 root fq_codel
}


#######################################################
#######################################################

if [ -z "$1" ]; then
  echo "usage: $0 <start|stop|forward>"
  exit 1
fi

case "$1" in
  start)
    reset_all
    set_kernel_opts
    traffic_control
    source_variables
    bad_packets
    firewall_input
    firewall_output
    firewall_forward
    firewall_nat
    firewall_mangle
  ;;

  forward)
    reset_all
    echo "1" > /proc/sys/net/ipv4/ip_forward
    iptables -t nat -A POSTROUTING -o ppp0 -j MASQUERADE
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
# http://shearer.org/Linux_Shaping_Template

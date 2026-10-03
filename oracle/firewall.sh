#!/bin/sh
# Scope every rule to this bridge. Never flush or change another project's rules.
set -eu
bridge=br-myflps5
iptables -N MYFL-PS5-IN 2>/dev/null || true
iptables -F MYFL-PS5-IN
# Reject fragmented packets and malformed connection state before expensive handling.
iptables -A MYFL-PS5-IN -f -j DROP
iptables -A MYFL-PS5-IN -m conntrack --ctstate INVALID -j DROP
iptables -A MYFL-PS5-IN -p udp --dport 1053 -m length --length 0:600 -m hashlimit --hashlimit-upto 20/second --hashlimit-burst 40 --hashlimit-mode srcip --hashlimit-name myfl-dns-peer -m limit --limit 300/second --limit-burst 600 -j ACCEPT
iptables -A MYFL-PS5-IN -p udp --dport 1053 -j DROP
iptables -A MYFL-PS5-IN -p tcp --dport 1053 -m conntrack --ctstate ESTABLISHED -j ACCEPT
iptables -A MYFL-PS5-IN -p tcp --dport 1053 --syn -m connlimit --connlimit-above 8 --connlimit-mask 32 -j DROP
iptables -A MYFL-PS5-IN -p tcp --dport 1053 --syn -m hashlimit --hashlimit-upto 5/second --hashlimit-burst 10 --hashlimit-mode srcip --hashlimit-name myfl-dns-tcp -m limit --limit 100/second --limit-burst 200 -j ACCEPT
iptables -A MYFL-PS5-IN -j DROP
iptables -C DOCKER-USER -o "$bridge" -i enp0s6 -j MYFL-PS5-IN 2>/dev/null || iptables -I DOCKER-USER 1 -o "$bridge" -i enp0s6 -j MYFL-PS5-IN
# Even a compromised container has no route to other workloads, metadata or internet.
iptables -C DOCKER-USER -i "$bridge" ! -o "$bridge" -m conntrack --ctstate NEW -j DROP 2>/dev/null || iptables -I DOCKER-USER 1 -i "$bridge" ! -o "$bridge" -m conntrack --ctstate NEW -j DROP
iptables -C INPUT -i "$bridge" -m conntrack --ctstate NEW -j DROP 2>/dev/null || iptables -I INPUT 1 -i "$bridge" -m conntrack --ctstate NEW -j DROP

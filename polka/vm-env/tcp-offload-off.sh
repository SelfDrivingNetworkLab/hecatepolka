#! /bin/bash
if [ "$1" == "" ]; then
	echo "Specify the interface."
	exit
fi
ip addr flush dev $1
/sbin/ethtool -K $1 rx off
/sbin/ethtool -K $1 tx off
/sbin/ethtool -K $1 sg off
/sbin/ethtool -K $1 tso off
/sbin/ethtool -K $1 ufo off
/sbin/ethtool -K $1 gso off
/sbin/ethtool -K $1 gro off
/sbin/ethtool -K $1 lro off
/sbin/ethtool -K $1 rxvlan off
/sbin/ethtool -K $1 txvlan off
/sbin/ethtool -K $1 ntuple off
/sbin/ethtool -K $1 rxhash off
ip link set $1 up promisc on mtu 8192
ip link set $1 up
echo 1 > /proc/sys/net/ipv6/conf/$1/disable_ipv6

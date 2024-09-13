#!/bin/bash

if [ "$1" == "1" -o "$1" == "2" ]; then
	echo "Edges with setup $1..."
	F1="1"
	F2="1"
	F3="1"
	if [ "$1" == "2" ]; then
		F2="2"
		F3="3"
	fi
	echo -e "conf\nipv4 pbr v1 sequence 10 flow1 v1 nexthop 30.30.${F1}.2\nipv4 pbr v1 sequence 20 flow2 v1 nexthop 30.30.${F2}.2\nipv4 pbr v1 sequence 30 flow3 v1 nexthop 30.30.${F3}.2\nexit\nexit" | nc localhost 2306 > /dev/null
	echo -e "conf\nipv4 pbr v1 sequence 10 flow1 v1 nexthop 30.30.${F1}.1\nipv4 pbr v1 sequence 20 flow2 v1 nexthop 30.30.${F2}.1\nipv4 pbr v1 sequence 30 flow3 v1 nexthop 30.30.${F3}.1\nexit\nexit" | nc localhost 2307 > /dev/null
	echo -e "sh ipv4 pbr v1\nexit" | nc localhost 2306
	echo -e "sh ipv4 pbr v1\nexit" | nc localhost 2307
else
	if [ "$1" == "-i" ]; then
		echo -e "sh ipv4 pbr v1\nexit" | nc localhost 2306
		echo -e "sh ipv4 pbr v1\nexit" | nc localhost 2307
	else
		echo "Select setup (1 or 2)"
		echo ""
		echo "Setup #1: all flows through tunnel1"
		echo "Setup #2: flow1 (tos=0x20) through tunnel1"
		echo "          flow2 (tos=0x40) through tunnel2"
		echo "          flow3 (tos=0x80) through tunnel3"
		echo ""
		echo "-i information about all flows"
	fi
fi

#!/bin/bash

if [ "$1" == "1" -o "$1" == "2" -o "$1" == "3" ]; then
	echo "Setup edges to tunnel$1..."
	echo -e "conf\nipv4 pbr v1 sequence 10 polka v1 nexthop 30.30.$1.2\nexit\nexit" | nc localhost 2306 > /dev/null
	echo -e "conf\nipv4 pbr v1 sequence 10 polka v1 nexthop 30.30.$1.1\nexit\nexit" | nc localhost 2307 > /dev/null
	echo -e "sh ipv4 pbr v1\nexit" | nc localhost 2306
	echo -e "sh ipv4 pbr v1\nexit" | nc localhost 2307
else
	echo "Choose one tunnel: 1, 2 ou 3"
fi

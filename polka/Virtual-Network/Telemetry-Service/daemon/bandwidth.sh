#!/bin/bash

CORES=$(cat networks.txt | cut -f1 -d: | grep '^core[0-9]*' | sort -u)
EDGES=$(cat networks.txt | cut -f1 -d: | grep '^edge[0-9]*' | sort -u)
HOSTS=$(cat networks.txt | cut -f1 -d: | grep '^host[0-9]*' | sort -u)
HOSTNUM=""
ACTION=""
INTERVAL="5"
FILTERNODE=""
FILTERETH=""

if [ "$1" != "" ]; then
	INTERVAL="$1"
	if [ "$2" != "" ]; then
		FILTERNODE="$2"
		if [ "$3" != "" ]; then
			FILTERETH="$3"
		fi
	fi
fi

declare -A COMPUTERS
declare -i CONT=0
for index in ${CORES} ${EDGES} ${HOSTS}; do
	CONT=${CONT}+1
	COMPUTERS[${index}]=${CONT}
done
LIST=$(cat networks.txt | grep -v ':NAT$' | cut -f1,2 -d: | sort -u)
IMAP=$(cat interface_map.txt)
CLIST=$(
	for NODECFG in ${LIST}; do
		NODE=$(echo ${NODECFG} | cut -f1 -d:)
		if [ "${FILTERNODE}" == "" -o "${FILTERNODE}" == "${NODE}" ]; then
			ETH=$(echo ${NODECFG} | cut -f2 -d:)
			if [ "${FILTERETH}" == "" -o "${FILTERETH}" == "${ETH}" ]; then
				ETHMAP=""
				for IFACEMAP in ${IMAP}; do
					ETHREAL=$(echo ${IFACEMAP} | cut -f1 -d:)
					ETHVIRT=$(echo ${IFACEMAP} | cut -f2 -d:)
					if [ "${ETH}" == "${ETHVIRT}" ]; then
						ETHMAP=${ETHREAL}
					fi
				done
				if [ "${ETHMAP}" != "" ]; then
					for index in "${!COMPUTERS[@]}"; do
						value=${COMPUTERS[${index}]}
						if [ "${index}" == "${NODE}" ]; then
							COMPUTER_NUM=${value}
						fi
					done
					echo "${NODE}:${ETH}:${ETHMAP}:220${COMPUTER_NUM}"
				fi
			fi
		fi
	done
)
echo "Start traffic monitor"
while true; do
	for CCONF in ${CLIST}; do
		NODE=$(echo ${CCONF} | cut -f1 -d:)
		ETHV=$(echo ${CCONF} | cut -f2 -d:)
		ETHR=$(echo ${CCONF} | cut -f3 -d:)
		ISEQ=$(echo ${CCONF} | cut -f4 -d:)
		ssh -p ${ISEQ} root@localhost 'cat /proc/net/dev' | egrep "^ *${ETHR}" | sed "s/^ *${ETHR}:/${NODE} ${ETHV} /"
	done
	sleep ${INTERVAL}s
done | python bandwidth.py

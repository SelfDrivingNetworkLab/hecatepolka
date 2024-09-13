#!/bin/bash

CORES=$(cat networks.txt | cut -f1 -d: | grep '^core[0-9]*' | sort -u)
EDGES=$(cat networks.txt | cut -f1 -d: | grep '^edge[0-9]*' | sort -u)
HOSTS=$(cat networks.txt | cut -f1 -d: | grep '^host[0-9]*' | sort -u)
HOSTNUM=""
ACTION=""
declare -A COMPUTERS
declare -i CONT=0
for index in ${CORES} ${EDGES} ${HOSTS}; do
	CONT=${CONT}+1
	COMPUTERS[${index}]=${CONT}
done
while [ "$1" != "" -a "${1:0:1}" == "-" ]; do
	if [ "$1" == "-a" ]; then
		shift
	fi
	if [ "$1" == "-c" ]; then
		EDGES=""
		HOSTS=""
		shift
	fi
	if [ "$1" == "-e" ]; then
		CORES=""
		HOSTS=""
		shift
	fi
	if [ "$1" == "-h" ]; then
		CORES=""
		EDGES=""
		shift
	fi
	if [ "$1" == "-l" ]; then
		declare -i num
		shift
		EDGES=""
		CORES=""
		HOSTS=""
		for r in $1; do
			if [ "${COMPUTERS[${r}]}" != "" ]; then
				HOSTNUM="${HOSTNUM} ${COMPUTERS[${r}]}"
			else
				num=$r
				HOSTNUM="${HOSTNUM} ${num}"
			fi
		done
		echo ${HOSTNUM}
		shift
	fi
	if [ "$1" == "-x" -o "$1" == "-t" ]; then
		if [ "${ACTION}" != "" ]; then
			echo "Only one action can be used \"-x\" or \"-t\"."
			exit
		fi
	fi
	if [ "$1" == "-x" ]; then
		ACTION=$1
		shift
		CMD="$1"
		shift
	fi
	if [ "$1" == "-t" ]; then
		ACTION=$1
		shift
		source="$1"
		shift
		TMP="$1"
		destiny="/rtr/"
		if [ "${TMP:0:1}" != "-" ]; then
			destiny="$1"
			shift
		fi
	fi
done
if [ "${CORES}" == "" -a "${EDGES}" == "" -a "${HOSTS}" == "" -a "${HOSTNUM}" == "" ]; then
	echo "Select just one filter -c, -e, -h or -l. To run on all, don't use any filter."
	exit
fi
LISTA="${CORES} ${EDGES} ${HOSTS} ${HOSTNUM}"
if [ "${ACTION}" == "" ]; then
	echo "Run command and copy files Tool."
	echo "remote.sh [ -c | -e | -h | -l \"LIST\" ] [ -x \"command\" ] [ -t source [ destiny ] ]"
	echo ""
	echo "Computer's list filter by destiny:"
	echo "-a             All"
	echo "-c             All router cores"
	echo "-e             All router edges"
	echo "-h             All hosts"
	echo "-l \"LIST\"   Just the computers on LIST"
	echo ""
	echo "Action:"
	echo "-x \"command\" Run remote command"
	echo "-t source [destiny] Copy local files to remote machine."
	echo "               if no destiny, use \"/rtr\" as default."
	exit
fi
for I in ${LISTA}; do
	COMPUTER_NAME=${I}
	COMPUTER_NUM=${I}
	for index in "${!COMPUTERS[@]}"; do
		value=${COMPUTERS[${index}]}
		if [ "${index}" == "${I}" ]; then
			COMPUTER_NUM=${value}
		fi
		if [ "${value}" == "${I}" ]; then
			COMPUTER_NAME=${index}
		fi
	done
	if [ "${ACTION}" == "-x" ]; then
		echo "Run remote command \"${CMD}\" at ${COMPUTER_NAME}"
		echo ssh -p 220${COMPUTER_NUM} root@localhost "${CMD}"
		ssh -p 220${COMPUTER_NUM} root@localhost "${CMD}"
	fi
	if [ "${ACTION}" == "-t" ]; then
		echo "Sending file \"${source}\" to \"${destiny}\" at ${COMPUTER_NAME}"
		scp -P 220${COMPUTER_NUM} ${source} root@localhost:${destiny}
	fi
done

#!/bin/bash

CORES=$(cat networks.txt | cut -f1 -d: | grep '^core[0-9]*' | sort -u)
EDGES=$(cat networks.txt | cut -f1 -d: | grep '^edge[0-9]*' | sort -u)
HOSTS=$(cat networks.txt | cut -f1 -d: | grep '^host[0-9]*' | sort -u)
INTERVAL="5"

function usage {
	echo "Usage: $0 <source> <destiny> [ -i <interval> ] [ -d <duration> ]"

if [ "$1" == "" -o "$2" == "" ]; then
	usage
	exit
fi
SOURCE=$1
DESTINY=$2
INTERVAL=5
DURATION=10
param=""
while [ "$3" != "" ]; do
	value="$3"
	if [ "${param}" == "-i" ]; then
		INTERVAL=${value}
		param=""
	else
		if [ "${param}" == "-d" ]; then
			DURATION=${value}
			param=""
		else
			if [ "${value}" == "-i" -o "${value}" == "-d" ]; then
				param=${value}
			else
				usage
				exit
			fi
		fi
	fi
	shift
done
SOURCESEQ=""
DESTINYSEQ=""
declare -i CONT=0
for NODE in ${CORES} ${EDGES} ${HOSTS}; do
	CONT=${CONT}+1
	if [ "${NODE}" == "${SOURCE}" ]; then
		SOURCESEQ=${CONT}
	fi
	if [ "${NODE}" == "${DESTINY}" ]; then
		DESTINYSEQ=${CONT}
	fi
done
if [ "${SOURCESEQ}" == "" -o "${DESTINYSEQ}" == "" ]; then
	echo "Source or detiny not found in topology"
	exit
fi
echo "Start flow monitor"
ssp -p ${DESTINYSEQ} root@localhost 'iperf3 -s -D -p 5000'
ssh -p ${SOURCESEQ} root@localhost "iperf3 -p 5000 -R -fk --forceflush -c ${DESTINY} --timestamps='%F %T '" | python flow.py

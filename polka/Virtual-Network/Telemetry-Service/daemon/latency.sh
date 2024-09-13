#!/bin/bash
src=$1
dst=$2
dstip=$2
tos=$3
if [ "${src}" == "" ]; then
	echo "Source?"
	exit
fi
if [ "${dst}" == "" ]; then
	echo "Destiny?"
	exit
fi
if [ "${tos}" == "" ]; then
	tos="32"
fi
if [ "${src}" == "host1" ]; then
	SEQ=8
fi
if [ "${src}" == "host2" ]; then
	SEQ=9
fi
if [ "${dst}" == "host1" ]; then
	dstip="40.40.1.2"
fi
if [ "${dst}" == "host2" ]; then
	dstip="40.40.2.2"
fi
if [ "${SEQ}" == "" ]; then
	echo "Source must be host1 or host2"
	exit
fi
ssh -p 220${SEQ} root@localhost "ping -i 5 -Q ${tos} -D ${dstip}" | sed -u -r "s/\[([0-9]*\.[0-9]*)\].*time=([0-9]*\.[0-9]*) ms$/\1 \2/g" | python latency.py ${src} ${dst}

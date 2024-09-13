# !/bin/bash

TOPOLOGY=""
TEST=""
cd /rtr
if [ "$1" != "" ]; then
	if [ "$1" == "--clean" -o "$1" == "-c" ]; then
		rm -f cfgnet.sh rtr.sh interface_map.txt lista.txt template-* router-*
		echo "Files removed."
		exit
	else
		if [ "$1" == "--host" -o "$1" == "-h" ]; then
			NEWHOST=$2
			OLDHOST=$(cat /etc/hostname)
			if [ "${NEWHOST}" != "${OLDHOST}" ]; then
				echo "${NEWHOST}" > /etc/hostname
				echo "127.0.0.1 localhost ${NEWHOST}" > /etc/hosts
				hostname ${NEWHOST}
			fi
			exit
		else
			TOPOLOGY="${1}"
			TEST="${2}"
			echo ${TOPOLOGY}:${TEST} > TOPOLOGY.txt
		fi
	fi
else
	if [ -f topology.txt ]; then
		TOPOLOGY=$(cat TOPOLOGY.txt | cut -f1 -d:)
		TEST="$(cat topology.txt | cut -f2 -d:)"
	fi
	if [ "${TOPOLOGY}" == "" ]; then
		echo "Specify the topology."
		exit
	fi
fi

ROUTER=$(hostname)
SSHREMOTE=$(cat ssh_connection.txt)
REMOTE="${SSHREMOTE}:~/polka/"

scp ${REMOTE}/list.txt .
XTEST="\/${TEST}"
if [ "${TEST}" == "" ]; then
	XTEST=""
fi

for ARQ in $(cat list.txt); do
	REMOTE_FILE=$(echo ${ARQ} | sed "s/{HOST}/-${ROUTER}/g;s/{TOPOLOGY}/${TOPOLOGY}${XTEST}\//g")
	LOCAL_FILE=$(echo ${ARQ} | sed "s/{HOST}//g;s/{TOPOLOGY}//g")
	echo "Copy '${REMOTE_FILE}' to '${LOCAL_FILE}'"
	scp ${REMOTE}${REMOTE_FILE} ${LOCAL_FILE}
done
rm -f list.txt
./cfgnet.sh

#!/bin/bash

INTERFACE_MAP="interface_map.txt"
if [ "$1" != "" ]; then
	INTERFACE_MAP=$1
fi
INTERFACES=$(ip a | grep ': <' | cut -f2 -d: | cut -f2 -d\ )
REGEX=""
while read LINE; do
	ETHLOCAL=$(echo ${LINE} | cut -f1 -d:)
	OK=False
	for I in ${INTERFACES}; do
		if [ "${I}" == "${ETHLOCAL}" ]; then
			OK=True
		fi
	done
	echo "--------------------------------------------"
	if [ "${OK}" == "True" ]; then
		echo "Setup interface ${ETHLOCAL}"
		ETHRTR=$(echo ${LINE} | cut -f2 -d:)
		MACADDR=$(ip a show dev ${ETHLOCAL} | grep 'link/ether' | cut -d\  -f6)
		echo "     ${ETHLOCAL} -> ${ETHRTR} ->  ${MACADDR}"
		REGEX="${REGEX}s/{${ETHRTR}_MAC}/${MACADDR}/g;s/{${ETHRTR}_MAP}/${ETHLOCAL}/g;"
	else
		echo "Interface ${ETHLOCAL} not found"
	fi
done < ${INTERFACE_MAP}
echo "--------------------------------------------"
for TYPE in hw sw; do
	echo "Creating router-${TYPE}.txt"
	cat template-${TYPE}.txt | sed "${REGEX}" > router-${TYPE}.txt
done
echo "### END ###"

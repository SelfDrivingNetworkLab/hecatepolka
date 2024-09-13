#!/bin/bash

CORES=$(cat networks.txt | cut -f1 -d: | grep '^core[0-9]*' | sort -u)
EDGES=$(cat networks.txt | cut -f1 -d: | grep '^edge[0-9]*' | sort -u)
HOSTS=$(cat networks.txt | cut -f1 -d: | grep '^host[0-9]*' | sort -u)
LIST=""
CMD=""
declare -A COMPUTERS=( [core1]=1 [core2]=2 [core3]=3 [core4]=4 [core5]=5 [edge1]=6 [edge2]=7 [host1]=8 [host2]=9 )
TEST=$1
while [ "${TEST}" != "" ]; do
	if [ "${TEST}" == "-c" ]; then
		LIST="${CORES}"
	fi
	if [ "${TEST}" == "-e" ]; then
		LIST="${EDGES}"
	fi
	if [ "${TEST}" == "-h" ]; then
		LIST="${HOSTS}"
	fi
	if [ "${TEST}" == "-l" ]; then
		shift
		LIST="$1"
	fi
	if [ "${TEST}" == "-a" ]; then
		LIST="${CORES} ${EDGES} ${HOSTS}"
	fi
	if [ "${TEST}" == "-p" ]; then
		CMD="pause"
	fi
	if [ "${TEST}" == "-r" ]; then
		CMD="resume"
	fi
	if [ "${TEST}" == "-t" ]; then
		CMD="savestate"
	fi
	if [ "${TEST}" == "-o" ]; then
		CMD="poweroff"
	fi
	if [ "${TEST}" == "-s" ]; then
		CMD="start"
	fi
	shift
	TEST=$1
done

if [ "${LIST}" == "" -o "${CMD}" == "" ]; then
	echo "Virtual Machine Control Script."
	echo "vmcontrol.sh [-a | -c | -e | -h | -l \"LIST\"] [-p | -r]"
	echo ""
	echo "VM Selection:"
	echo "  -a             All topology machines"
	echo "  -c             All core routers"
	echo "  -e             All edge routers"
	echo "  -h             All hosts"
	echo "  -l \"LIST\"   All VMs on LIST"
	echo "Command:"
	echo "  -s             Start"
	echo "  -p             Pause"
	echo "  -r             Resume"
	echo "  -t             Savestate"
	echo "  -o             Poweroff"
	exit
fi


for VM in ${LIST}; do
	VM_NAME=${VM}
	for r in "${!COMPUTERS[@]}"; do
		if [ "${COMPUTERS[${r}]}" == "${VM}" ]; then
			VM_NAME=${r}
		fi
	done
	echo "Controle: ${CMD} ${VM_NAME}..."
	if [ "${CMD}" == "start" ]; then
		VBoxManage startvm "${VM_NAME}" --type=headless
	else
		VBoxManage controlvm "${VM_NAME}" ${CMD}
	fi
done

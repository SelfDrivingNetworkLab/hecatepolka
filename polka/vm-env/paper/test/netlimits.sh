#!/bin/bash

declare -g -a LIMIT_TUNNEL=[0,0,0,0]
remove_limits() {
	for VM in ${1}; do
		# Removing interface groups
		for INTERFACE in 1 2 3 4 5 6 7 8; do
			vboxmanage modifyvm ${VM} --nicbandwidthgroup${INTERFACE} none
		done
		# Removing any limits
		while read LIMIT; do
			if [ "${LIMIT}" != "<none>" -a "${LIMIT}" != "" ]; then
				vboxmanage bandwidthctl ${VM} remove ${LIMIT}
			fi
		done < <(vboxmanage bandwidthctl ${VM} list | cut -f2 -d\')
	done
}

add_limits() {
	while read LIN; do
		VM=$(echo ${LIN} | cut -f1 -d:)
		INTERFACE=$(echo ${LIN} | cut -f2 -d:)
		INDEX=$(echo ${LIN} | cut -f3 -d:)
		LIMIT=${LIMIT_TUNNEL[${INDEX}]}
		if [ "${LIMIT}" != "0" ]; then
			# Add new limit
			vboxmanage bandwidthctl ${VM} add Limit${INTERFACE} --type network --limit ${LIMIT}m
			# Apply limit on interface
			vboxmanage modifyvm ${VM} --nicbandwidthgroup${INTERFACE} Limit${INTERFACE}
		fi
	done < <(cat netlimits.txt | grep -v '=')
}


update_limits() {
	while read LIN; do
		VM=$(echo ${LIN} | cut -f1 -d:)
		INTERFACE=$(echo ${LIN} | cut -f2 -d:)
		INDEX=$(echo ${LIN} | cut -f3 -d:)
		LIMIT=${LIMIT_TUNNEL[${INDEX}]}m
		[ "${LIMIT}" == "0m" ] && LIMIT=0
		# Update limits
		vboxmanage bandwidthctl ${VM} set Limit${INTERFACE} --limit ${LIMIT} 2> /dev/null
	done < <(cat netlimits.txt | grep -v '=')
}

list_limits() {
	for VM in ${1}; do
		L=0
		while read LIN; do
			LIMIT=$(echo ${LIN} | cut -f2 -d\') 
			if [ "${LIMIT}" != "<none>" -a "${LIMIT}" != "" ]; then
				if [ "${L}" == "0" ]; then
					L=1
					echo "VM: ${VM}"
				fi
				VELO=$(echo ${LIN} | cut -f5 -d: | cut -f2-3 -d\ )
				NIC=${LIMIT:5:1}
				echo -e "\tNIC${NIC}: ${VELO}"
			fi
		done < <(vboxmanage bandwidthctl ${VM} list | grep -v '^<none>' | grep -v '^$')
	done
}

LIST=$(cat netlimits.txt | grep -v '=' | cut -f1 -d: | sort -u)
while read LIM; do
	INDX=$(echo ${LIM} | cut -f1 -d=)
	VELO=$(echo ${LIM} | cut -f2 -d=)
	LIMIT_TUNNEL[${INDX}]=${VELO}
done < <(cat netlimits.txt | grep '=')
if [ "$1" == "-i" ]; then
	list_limits "${LIST}"
elif [ "$1" == "-c" ]; then
	remove_limits "${LIST}"
elif [ "$1" == "-u" ]; then
	update_limits
	list_limits "${LIST}"
elif [ "$1" == "-l" ]; then
	remove_limits "${LIST}"
	add_limits
	list_limits "${LIST}"
else
	echo "Select one option:"
	echo " -i Get information about running LIMITs"
	echo " -u Update running LIMITs (with running VMs)"
	echo " -c Clear all LIMITs for all VMs"
	echo " -l Create new rules e new LIMITs"
fi


#!/bin/bash


if [ "$1" == "" ]; then
	echo "Specify the topology to remove all nics."
	exit
fi
if [ -f "$1/networks.txt" ]; then
	VMS=$(cat $1/networks.txt | cut -f1 -d: | sort -u)
	for VM in ${VMS}; do
		echo $VM
		for NIC in 1 2 3 4 5 6 7 8; do
			echo "> $NIC"
			VBoxManage modifyvm "${VM}" --nic${NIC} null
			VBoxManage modifyvm "${VM}" --nic${NIC} none
		done
	done
else
	echo "File 'networks.txt' from '$1' topology not found."
fi

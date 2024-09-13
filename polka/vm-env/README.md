# polka


1) Environment Preparation:

Install a virtual machine with 20GB of HDD on VirtualBox with Debian 11 that will serve as a template for the others.

  Note: You don't need to worry about network interfaces at this moment; they will be configured later.

Start the template virtual machine and install any necessary packages (net-tools, tcpdump, etc...)

Update the Debian packages with "apt update" and "apt upgrade".

Create an SSH key pair with the root user using the following command:
- ssh-keygen -b 1024 -t rsa
  Note: Press \<ENTER\> for all options.
  Note: By creating the key before cloning, all machines will share the same key.

Import the public key generated in the template to the guest OS running on VirtualBox by inserting the content of the VM’s /root/.ssh/id_rsa.pub file at the end of the ~/.ssh/authorized_keys file of the guest. By doing this, the update script will be able to copy files without requiring a password.

Clone the template machine to generate the hosts before installing FreeRtr.

  Note: The cloning process can be done by cloning the entire machine or by cloning just the disk and creating new machines that will use these cloned disks.

On the template machine, install FreeRtr in the '/rtr' directory.

Copy the 'update.sh' file to the '/rtr' directory of the template machine.

Edit the 'update.sh' script by changing the IP, user, and path on the guest that contains the files from this repository.

Clone the template machine to generate the core and edge routers.

  Note: The machines used in the topology are:
  - paper: core1, core2, core3, core4, core5, edge1, edge2, host1, and host2

  Note: I haven't gone into the details of how to install Debian 11 and FreeRtr on it. For information about this step, see the respective project websites.

Once all the virtual machines are created, with the machines turned off, run the 'remove-nic.sh' script on the guest. This will remove all network card configurations from the virtual machines, preparing them for topology configuration.

Run the './config_net_vbox.sh \<topology\>' script. This will configure the network interfaces of all virtual machines, setting up the internal network configurations using the information from the 'network.txt' file inside the chosen topology directory. This file indicates the VM names, the interfaces to be activated, their MAC Addresses, and the network where they will be configured. If the network name is NAT, the interface will be configured as NAT in VirtualBox with Port-Forwarding for SSH and TELNET protocols. Otherwise, it will be configured as an Internal Network, and the specified name will be the internal network name.

Start the virtual machines that will be used in the chosen topology.

On the host machines, you need to add a route so they can communicate through the topology via the edges. This is done by configuring a static IP on the second network interface and adding a route to the other network using the edge as a gateway. Below are examples for host1; then do the same for host2, changing the IPs accordingly.

Edit the '/etc/network/interfaces' file and include the static IP configuration:
```
auto enp0s8
iface enp0s8 inet static
    address 40.40.1.2/24
```
Create the '/etc/network/if-up.d/internal_network_route' file with the content below, then change the permissions with the command "chmod 751 internal_network_route":
```
#!/bin/bash
if [ "${IFACE}" = "enp0s8" ]; then
    ip route del 40.40.2.0/24 via 40.40.1.1
    ip route add 40.40.2.0/24 via 40.40.1.1
fi
```

On each virtual machine, go to the '/rtr' directory and run the 'update.sh' script specifying the topology you want to use (paper). After specifying the topology the first time, this information will be stored and does not need to be specified again unless you wish to change the topology.

When running the 'update.sh' script, it will download the 'list.txt' file containing the list of files to be copied. (In the list, if the file name has {TOPOLOGY} before it, it is copied from within the directory of the installed topology. After copying, the 'cfgnet.sh' script is executed to generate hardware and software files from the downloaded templates.

Linux interfaces are mapped to FreeRtr interfaces by the 'interface_map.txt' file inside the topology directory. In some cases, Linux interfaces have changed names; they are currently named enp0s3, enp0s8, enp0s9, enp0s10, enp0s16, etc., but sometimes they have changed to eth0, eth1, eth2, eth3, eth4, etc. If the interfaces change names in the virtual machines, just edit the mapping file. Each line in the file contains a map with the real interface name and the FreeRtr interface name separated by ":", for example, "enp0s8:eth1".

The hardware template files are named in the format "template-\<hostname\>-hw.txt", where \<hostname\> is the name of the Linux machine, for example, "router1". In the template, we can use the values {eth1_MAP}, which will be replaced by the real interface name mapped to ethernet1 of FreeRtr, and {eth1_MAC}, which will be replaced by the MAC Address of the interface.

In addition to interface mapping, the hardware file also requires the MAC Addresses of each interface. To facilitate file maintenance, I am using templates for each router and a script that updates and replaces placeholders with real interface names and their MAC Addresses. The hardware file is generated in '/rtr/router-hw.txt' and the software file in '/rtr/router-sw.txt'.

IMPORTANT: Originally, I was working with the hardware file rtr-hw.txt, but whenever Linux is restarted, upon starting the "rtr" service, the configuration file is loaded and "proc" lines are executed, creating processes with the interface mapping by MAC. When manually starting FreeRtr to test the configuration, it cannot start another process with the same ports, thus it presents an error message and tries again to start the process. The possible solutions are (a) remove the "proc" lines from the hardware file, as FreeRtr has already left the processes running, or (b) use a hardware file with a different name. I adopted the second solution by putting the configuration in the router-hw.txt file.

During the initialization of the 'rtr.sh' script, network interfaces that are neither loopback nor in the NAT network will be configured by the 'tcp-offload-off.sh' script.

The topology in the "paper" directory, has 2 hosts connected by 2 edges and 5 cores.

The details of each topology are showed in the png files.
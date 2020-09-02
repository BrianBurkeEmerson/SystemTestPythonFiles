# This script makes a certain MAC address into a routing node for N child nodes

import os
import sys
import random

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../SSHHelper")
from InteractiveSSH import InteractiveSSH

hostname = "toc0"
parent_mac = "00-1B-1E-26-5D-6B-0E-BC"
number_of_child_nodes = 3

# Create the SSH session and open nwconsole
ssh = InteractiveSSH(hostname)
ssh.start_nwconsole()

# Enable ppath command
ssh.safe_send("su becareful")
mac_id_pairs = ssh.get_mote_id_mac_associations(use_mac_keys = True, include_ap = False)

# Get the keys which correspond to MAC addresses
macs = []
for mac in mac_id_pairs:
    macs.append(mac)

# Select N MAC addresses as random
child_macs = []
while len(child_macs) < number_of_child_nodes:
    mac = random.choice(macs)
    if mac != parent_mac:
        if mac not in child_macs:
            child_macs.append(mac)

# Clear any paths already present
ssh.safe_send("ppath clear")

# Create the paths using the ppath command
for mac in child_macs:
    print(ssh.safe_send("ppath only #" + mac + " #" + parent_mac))
    print("Created path from " + mac + " to " + parent_mac)

# Reset the gateway
ssh.safe_send("exec reset mote 1")

ssh.shell.close()
ssh.close()

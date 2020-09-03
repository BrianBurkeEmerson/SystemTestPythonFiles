# This script makes a certain MAC address into a routing node for N child nodes

import os
import sys
import random

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../SSHHelper")
from InteractiveSSH import InteractiveSSH

hostname = "toc0"
parent_mac = "00-1B-1E-26-5D-6B-0E-BC"

# Create the SSH session and open nwconsole
ssh = InteractiveSSH(hostname)
ssh.start_nwconsole()

# Enable ppath command
ssh.safe_send("su becareful")
mac_id_pairs = ssh.get_mote_id_mac_associations(use_mac_keys = True, include_ap = False)
mac_id_pairs_with_ap = ssh.get_mote_id_mac_associations(use_mac_keys = True, include_ap = True)

# Determine which MAC is the AP
ap_mac = ""
for mac in mac_id_pairs_with_ap:
    if mac not in mac_id_pairs:
        ap_mac = mac

# Clear any paths already present
ssh.safe_send("ppath clear")

# Make all motes except the DUT unable to connect to the AP
for mac in mac_id_pairs:
    if (mac != parent_mac) and (mac != ap_mac):
        print(ssh.safe_send("ppath never #" + mac + " #" + ap_mac))

# Reset the gateway
ssh.safe_send("exec reset mote 1")

# End the SSH session
ssh.shell.close()
ssh.close()

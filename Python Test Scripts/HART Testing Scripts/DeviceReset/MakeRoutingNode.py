# This script makes a certain MAC address into a routing node for all other network nodes

import os
import sys
import random

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../SSHHelper")
from InteractiveSSH import InteractiveSSH

hostname = "toc0"
parent_mac = "00-1B-1E-26-5D-6B-0E-BC"

use_mote_id = True # Allows the mote ID to be used instead of the MAC address if desired
parent_id = 5

# Create the SSH session and open nwconsole
ssh = InteractiveSSH(hostname)
ssh.start_nwconsole()

# Enable ppath command
ssh.safe_send("su becareful")
mac_id_pairs = ssh.get_mote_id_mac_associations(use_mac_keys = True, include_ap = False)
mac_id_pairs_with_ap = ssh.get_mote_id_mac_associations(use_mac_keys = True, include_ap = True)

# Use the parent mote ID to get the parent MAC address if the option is selected
if use_mote_id:
    id_mac_pairs = ssh.get_mote_id_mac_associations(use_mac_keys = False, include_ap = False)
    parent_mac = id_mac_pairs[str(parent_id)]

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
print(ssh.safe_send("exec reset mote " + mac_id_pairs_with_ap[ap_mac]))

# End the SSH session
ssh.shell.close()
ssh.close()

# py -m pip install paramiko
# py -m pip install scp
# py -m pip install win10toast

import sys
import os
import time
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../ISADeviceCount")

from ISADeviceCount import IsaDeviceCounter
from win10toast import ToastNotifier

DELAY_BETWEEN_LOOPS_SECONDS = 180
RESULTS_FILE = "ResourceUsage.txt"

# Define a list with the number of devices that will be connected after turning on each rack
# For instance, if there are 20 devices on each rack, the list would be [20, 40, 60, ...]
device_count_list = [24, 48, 72, 96, 120]

# Create the SSH and SCP connections
gateway = IsaDeviceCounter(hostname = 'toc0', port = 22, username = 'root', password = 'emerson1')

# Iterate and loop on each rack until all devices join
# Then take a reading from the TOP command write it to a file
for rack in range(len(device_count_list)):
    devices_found = 0

    # Wait for the user to press enter before starting next rack (gives them a chance to power on next devices)
    input("Press enter after turning on the next rack")

    # Write a message indicating the start of a rack test
    with open(RESULTS_FILE, "a") as results:
        results.write("\nRack " + str(rack) + " started at " + str(datetime.now()) + "\n")

    while devices_found < device_count_list[rack]:
        # Start with a delay of 3 minutes since it takes a significant amount of time for devices to join
        time.sleep(DELAY_BETWEEN_LOOPS_SECONDS)

        # Download the database from the gateway
        gateway.download_db_file("/var/tmp/Monitor_Host.db3")

        # Open the database and count the devices based on status
        devices = gateway.get_isa_devices("Monitor_Host.db3")
        devices_found = devices["Joined Configured"]
    
    # Once all devices on a rack have joined, take a reading of resource utilization with the TOP command write it to a file
    stdin, stdout, stderr = gateway.clientSsh.exec_command("top -n1 -b -i")

    # Write the lines from stdout to the results log file
    with open(RESULTS_FILE, "a") as results:
        # Timestamp the end of the test
        results.write("Rack " + str(rack) + " finished at " + str(datetime.now()) + "\n")

        # Write each line of top to the file
        for line in stdout.readlines():
            results.write(line)
    
    # TODO: Replace this with email or a different notification system
    # Display a Windows 10 notification that the rack is finished
    notification = ToastNotifier()
    notification.show_toast("Rack " + str(rack) + " finished. Ready for next rack.")
    
# Close the connections
gateway.close()

import os
import sys
import time
import threading
import tkinter as tk
import tkinter.filedialog as fd
import paramiko

import StateTimeTracker as STT

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../SSHHelper")
from InteractiveSSH import InteractiveSSH


HOSTNAME = "toc0"
USERNAME = "root"
PASSWORD = "emerson1"

# Get the directory that will be used for storing results
print("Choose a folder where results will be stored")
root = tk.Tk()
directory = fd.askdirectory()
root.destroy()

# Start an SSH session and collect network statistics with "show stat short 0" and "show stat short 1"
ssh = InteractiveSSH(hostname = HOSTNAME, port = 22, username = USERNAME, password = PASSWORD)
ssh.start_nwconsole()
stats = ssh.show_stat_short(combine_list_to_string = True)
with open(directory + "/show_stat_short_before.txt", "w") as f:
    f.write(stats)
ssh.shell.close()
ssh.close()

# Wait for the user to reset the power to the device
while input("Type \"go\" after removing power from gateway and then resupplying it: ").lower() != "go":
    continue
print("Advancing... Monitoring will begin automatically once SSH is available.")

# Start the test which will keep collecting stats in the background
testObj = STT.StateTimeTracker(hostname = HOSTNAME, username = USERNAME, password = PASSWORD)
testThread = threading.Thread(target = testObj.start, args = (directory, False, True))
testThread.start()

# Wait until SSH is available before advancing
STT.verify_ssh_connection(hostname = HOSTNAME, port = 22, username = USERNAME, password = PASSWORD)

# Start an SSH session to monitor the needNeighbor attribute of all motes
ssh = InteractiveSSH(hostname = HOSTNAME, port = 22, username = USERNAME, password = PASSWORD)
ssh.start_nwconsole()

# Check the status of all motes with the command "get motes" in nwconsole
# All motes registered to the manager need to have the following attributes
# state: Operational
# needNeighbor: false (One device will always remain true)
wait_for_neighbors = True
while wait_for_neighbors:
    devices_registered = 0
    devices_operational = 0
    devices_with_neighbors = 0
    devices_publishing = 0

    # Use the command "get motes" and separate with the string "\r\n\r\n" which will divide stats by mote
    resp = ssh.safe_send("get motes").split("\r\n\r\n")

    # For each mote, split the information by line to make it easily parseable (format of "attribute: value")
    for mote in resp:
        lines = mote.splitlines()
        added_to_operational_count = False

        # Go through each line and increment the correct variables
        for line in lines:
            # Add all registered motes to the count
            if "moteId:" in line:
                devices_registered += 1
            
            # Check if the mote is operational
            if ("state:" in line) and ("Operational" in line):
                devices_operational += 1
                added_to_operational_count = True
            
            # Check if the device has a neighbor (only add if device is operational)
            if ("needNeighbor:" in line) and ("false" in line):
                if added_to_operational_count:
                    devices_with_neighbors += 1
    
    # Check if all devices have joined and have a neighbor to break the loop otherwise wait for 10 seconds then check again
    if (devices_operational == devices_registered) and (devices_with_neighbors == (devices_operational - 1)):
        # Before breaking, check the log files to make sure all devices are publishing
        for log_file in os.listdir(directory + "/hartserver"):
            added_to_publishing_count = False

            # Keep attempting to read each file until it is successful (failures occur if another thread has it open)
            read_file = True
            while read_file:
                try:
                    f = open(directory + "/hartserver/" + log_file, "r")
                    lines = f.read().splitlines()
                    f.close()

                    # Go through each line and check if the device is publishing
                    for line in lines:
                        if ("is Responding" in line) and (not added_to_publishing_count):
                            devices_publishing += 1
                            added_to_publishing_count = True
                        elif ("is Not Responding" in line) and added_to_publishing_count:
                            devices_publishing -= 1
                            added_to_publishing_count = False
                    
                    read_file = False
                except OSError:
                    print("Error opening " + directory + "/hartserver/" + log_file +". Retrying...")
        
        # If the number of devices publishing is equal to the number of devices operational (minus the AP)
        if devices_publishing >= (devices_operational - 1):
            wait_for_neighbors = False
    else:
        time.sleep(10)
    
print("All devices have neighbors and are publishing.")
testObj.stop()
testThread.join()
ssh.shell.close()
ssh.close()
print("Waiting 30 minutes before recording network statistics again...")

INTERVAL = 5 # Minutes
time_elapsed = 0
for i in range(int(30 / INTERVAL)):
    time.sleep(INTERVAL * 60)
    time_elapsed += INTERVAL
    print(str(time_elapsed) + " minutes have passed.")

print("Recording network statistics again...")

# Start an SSH session and collect network statistics with "show stat short 0" and "show stat short 1"
ssh = InteractiveSSH(hostname = HOSTNAME, port = 22, username = USERNAME, password = PASSWORD)
ssh.start_nwconsole()
stats = ssh.show_stat_short(combine_list_to_string = True)
with open(directory + "/show_stat_short_after.txt", "w") as f:
    f.write(stats)
ssh.shell.close()
ssh.close()

print("Test finished")

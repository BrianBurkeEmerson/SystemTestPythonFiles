# This module fetches data about ISA devices connected to a gateway
# It requires the paramiko and scp modules to be installed which can be installed with the following commands
# "py -m pip install paramiko"
# "py -m pip install scp"

# The module reads statuses of all devices registered with a gateway and returns counts as a dictionary
# The format of the dictionary is as follows
# {
    # "Not Joined" : <device_count>,
    # "Late" : <device_count>,
    # "Stale" : <device_count>,
    # "Security Join Request Received" : <device_count>,
    # "Security Join Response Sent" : <device_count>,
    # "Join Received" : <device_count>,
    # "Join Response Sent" : <device_count>,
    # "Contract Join Received" : <device_count>,
    # "Contract Join Response Sent" : <device_count>,
    # "Security Confirm Received" : <device_count>,
    # "Security Confirm Response Sent" : <device_count>,
    # "Joined Configured" : <device_count>
# }

# Make sure to close the connections once finished by calling the close() function

import paramiko
import scp
import sqlite3

# Relate the statuses found in the database to what they mean
DEVICE_STATUS_IDS = {
    1 : "Not Joined",
    2 : "Late",
    3 : "Stale",
    4 : "Security Join Request Received",
    5 : "Security Join Response Sent",
    6 : "Join Received",
    7 : "Join Response Sent",
    8 : "Contract Join Received",
    9 : "Contract Join Response Sent",
    10 : "Security Confirm Received",
    11 : "Security Confirm Response Sent",
    20 : "Joined Configured"
}

class IsaDeviceCounter():
    def __init__(self, hostname = "192.168.1.10", port = 22, username = "root", password = "emerson1"):

        # Create the paramiko SSH client
        self.clientSsh = paramiko.SSHClient()
        self.clientSsh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Establish the SSH connection
        self.clientSsh.connect(hostname = hostname, port = port, username = username, password = password)

        # Create the SCP connection for downloading files and use the SSH transport from paramiko
        self.clientScp = scp.SCPClient(self.clientSsh.get_transport())


    # Downloads the remote ISA database file to the folder Python is being run from
    # location: The databse file location on the remote gateway
    def download_db_file(self, location = "/var/tmp/Monitor_Host.db3"):
        self.clientScp.get(location)
    

    # Reads the devices associated with the gateway in the database file, and sorts them into the dictionary described at the top
    # db_name: The filename of the database to be read
    def get_isa_devices(self, db_name = "Monitor_Host.db3", skip_first_three = True):
        conn = sqlite3.connect(db_name)
        c = conn.cursor()

        # Create the dictionary to track the device types
        device_dict = {
            "Not Joined" : 0,
            "Late" : 0,
            "Stale" : 0,
            "Security Join Request Received" : 0,
            "Security Join Response Sent" : 0,
            "Join Received" : 0,
            "Join Response Sent" : 0,
            "Contract Join Received" : 0,
            "Contract Join Response Sent" : 0,
            "Security Confirm Received" : 0,
            "Security Confirm Response Sent" : 0,
            "Joined Configured" : 0
        }

        # Iterate through each row in the Devices table but skip the first three since they are the gateway and associated components, not wireless devices
        row_count = -1
        for row in c.execute("SELECT * FROM Devices ORDER BY DeviceID"):
            row_count += 1

            # Check index 5 in each tuple to determine the status
            if skip_first_three and row_count < 3:
                continue
            
            device_dict[DEVICE_STATUS_IDS[row[5]]] += 1
        
        conn.close()
        return device_dict
    

    def close(self):
        self.clientScp.close()
        self.clientSsh.close()

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
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../SSHHelper")
from SSHHelper import SSHHelper

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

        # Create the paramiko SSH client by using the helper class
        self.clientSsh = SSHHelper(hostname = hostname, port = port, username = username, password = password)

        # Create the SCP connection for downloading files and use the SSH transport from paramiko
        self.clientScp = scp.SCPClient(self.clientSsh.get_transport())


    # Downloads the remote ISA database file to the folder Python is being run from
    # location: The databse file location on the remote gateway
    def download_db_file(self, location = "/var/tmp/Monitor_Host.db3", local_path = ""):
        if local_path == "":
            self.clientScp.get(location)
        else:
            self.clientScp.get(location, local_path = local_path)
    

    def get_isa_device_states(self, db_name = "Monitor_Host.db3", skip_first_three = True):
        conn = sqlite3.connect(db_name)
        c = conn.cursor()

        return_dict = {}

        # Iterate through each row in the Devices table but skip the first three since they are the gateway and associated components, not wireless devices
        row_count = -1
        for row in c.execute("SELECT * FROM Devices ORDER BY DeviceID"):
            row_count += 1

            # Skip the gateway and associated components
            if skip_first_three and row_count < 3:
                continue

            # Get the device status for each device (row[5]) and put into the return_dict
            return_dict[row[0]] = row[5]
        
        return return_dict


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
            "Join-Received" : 0,
            "Join-Response Sent" : 0,
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

            # Skip the gateway and associated components
            if skip_first_three and row_count < 3:
                continue
            
            # Check index 5 in each tuple to determine the status
            device_dict[DEVICE_STATUS_IDS[row[5]]] += 1
        
        conn.close()
        return device_dict
    

    # Goes through the ISA database and calculates the reliability of each device
    # db_name: The filename of the database to be read
    def get_device_reliability(self, db_name = "Monitor_Host.db3"):
        conn = sqlite3.connect(db_name)
        c = conn.cursor()

        return_dict = {}

        for row in c.execute("SELECT * FROM NetworkHealthDevices ORDER BY DeviceID"):
            return_dict[row[0]] = 100 - row[5]
        
        conn.close()
        
        return return_dict
    

    # Goes through the ISA database and returns the RSSI of all paths on the network
    # db_name: The filename of the database to be read
    def get_path_rssi(self, db_name = "Monitor_Host.db3"):
        conn = sqlite3.connect(db_name)
        c = conn.cursor()

        return_list = []

        for row in c.execute("SELECT * FROM NeighborHealthHistory ORDER BY LinkStatus"):
            # Skip unused links
            if row[4] == 0:
                continue
            # Create dictionaries of information added to the return_list for all active links
            else:
                new_dict = {
                    "DeviceID" : row[0],
                    "NeighborDeviceID" : row[2],
                    "SignalStrength" : row[8],
                    "MoteA" : row[0],
                    "MoteB" : row[2],
                    "ABPower" : row[8]
                }
                return_list.append(new_dict)
        
        conn.close()
        
        return return_list
    

    def get_device_id_name_pairs(self, db_name = "Monitor_Host.db3"):
        conn = sqlite3.connect(db_name)
        c = conn.cursor()

        return_dict = {}
        for row in c.execute("SELECT * FROM Devices ORDER BY DeviceID"):
            try:
                return_dict[row[0]] = bytearray.fromhex(row[4]).decode()
            except:
                return_dict[row[0]] = "NULL"
        
        conn.close()

        return return_dict
    

    def close(self):
        self.clientScp.close()
        self.clientSsh.close()

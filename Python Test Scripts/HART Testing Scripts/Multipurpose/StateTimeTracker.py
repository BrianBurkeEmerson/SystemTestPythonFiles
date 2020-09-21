import os
import sys
import base64
import time
import re
import threading
import subprocess
from datetime import datetime
import paramiko

from ParseStateTimeDeviceLogs import parse_device_logs, parse_hart_device_logs, parse_isa_device_logs

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../SSHHelper")
from InteractiveSSH import InteractiveSSH

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../ISA 100 Testing Scripts/ISADeviceCount")
from ISADeviceCount import IsaDeviceCounter
from ISADeviceCount import DEVICE_STATUS_IDS

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../RandomTools")
from ConvertCsvFilesToXlsx import convert_csv_files_to_xlsx

class StateTimeTracker():
    def __init__(self, hostname, username = "root", password = "emerson1"):
        self.TS_FMT = "%m/%d/%y %H:%M:%S"
        self.DB_LOCATION = "/var/tmp/Monitor_Host.db3"
        self.DB_NAME = "Monitor_Host.db3"
        self.monitor_log = True
        self.running_test = False

        self.hostname = hostname
        self.username = username
        self.password = password


    def isa_monitor_host_observation(self, observer, folder):
        # Capture ISA100 device information in a separate folder
        if not os.path.exists(folder + "/isa"):
            os.mkdir(folder + "/isa")
        
        # Continuously attempt to download the database file until it is successful
        while True:
            try:
                observer.download_db_file(self.DB_LOCATION, local_path = folder + "/isa/" + self.DB_NAME)
                break
            except:
                time.sleep(0.1)
                print("\033[95mLooking for ISA100 database...\033[0m")
        
        print("\033[95mFound ISA100 database\033[0m")

        # Create a line that will be written to the log (since the database does not do that obviously)
        now = datetime.now()
        line = "Test Started"
        start_line = now.strftime(str(now.timestamp()) + " $ " + self.TS_FMT + " $ " + line + "\n")

        # Get the devices registered in the database to mark a start time for each
        device_id_name_pairs = observer.get_device_id_name_pairs(folder + "/isa/" + self.DB_NAME)
        for device_id, name in device_id_name_pairs.items():
            # Check if the file exists and change the write mode accordingly
            filename = folder + "/isa/" + str(device_id) + "$" + str(name) + ".txt"
            write_mode = "w"
            if os.path.exists(filename):
                write_mode = "a"

            with open(filename, write_mode) as f:
                f.write(start_line)

        # Create dictionaries used for determining whether anything of interest changed in the database
        old_statuses = {}
        statuses = {}
        old_device_id_name_pairs = {}
        device_id_name_pairs = {}

        # Enter a loop where the database is periodically downloaded and checked
        while self.monitor_log:
            #time.sleep(1)
            observer.download_db_file(self.DB_LOCATION, local_path = folder + "/isa/" + self.DB_NAME)

            # Update the list of device IDs and device names
            old_device_id_name_pairs = device_id_name_pairs
            device_id_name_pairs = observer.get_device_id_name_pairs(folder + "/isa/" + self.DB_NAME)

            # Update the CSV if the list of devices has changed
            if device_id_name_pairs != old_device_id_name_pairs:
                with open(folder + "/isa/id_name_pairs.csv", "w") as f:
                    for device_id, name in device_id_name_pairs.items():
                        f.write(str(device_id) + "," + str(name) + "\n")
            
            # Update the old device statuses with the last readings for comparison purposes
            old_statuses = statuses
            statuses = observer.get_isa_device_states(db_name = folder + "/isa/" + self.DB_NAME)

            # Go through each new status and see if it differed from the previous one to write the state change time to a file
            for device, status in statuses.items():
                if ((device in old_statuses) and (status != old_statuses[device])) or (device not in old_statuses):
                    now = datetime.now()

                    # Create a line that will be written to the log (since the database does not do that obviously)
                    line = "Device " + str(device) + " (" + str(device_id_name_pairs[device]) + ") is now in state " + str(DEVICE_STATUS_IDS[status])
                    log_line = now.strftime(str(now.timestamp()) + " $ " + self.TS_FMT + " $ " + line + "\n")

                    # Check if the file exists and change the write mode accordingly
                    filename = folder + "/isa/" + str(device) + "$" + str(device_id_name_pairs[device]) + ".txt"
                    write_mode = "a"
                    if not os.path.exists(filename):
                        write_mode = "w"

                        # Write the test start time if a new device is found
                        log_line = start_line + log_line

                    with open(filename, write_mode) as f:
                        f.write(log_line)
                    
                    print("\033[95m" + log_line + "\033[0m", end = "")


    def nwconsole_observation(self, observer, folder):
        # Keep trying to open nwconsole until the service is ready to run after a reboot
        while True:
            try:
                observer.start_nwconsole()
                break
            except TimeoutError:
                time.sleep(1)
                print("\033[92mTrying to open nwconsole...\033[0m")
        print("\033[92mOpened nwconsole\033[0m")

        now = datetime.now()
        start_line = now.strftime(str(now.timestamp()) + " $ " + self.TS_FMT + " $ Test Started\n")

        id_mac_pairs = observer.get_mote_id_mac_associations()
        print("\033[92mCreated mote ID/MAC address associations\033[0m")

        # Create a folder to hold each log
        if not(os.path.exists(folder)):
            os.mkdir(folder)
        subfolder = "nwconsole"
        if not(os.path.exists(folder + "/" + subfolder)):
            os.mkdir(folder + "/" + subfolder)
        
        # Create blank log files for each device
        for mote_id in id_mac_pairs:
            with open(folder + "/" + subfolder + "/" + str(mote_id) + "$" + str(id_mac_pairs[mote_id]) + ".txt", "w") as f:
                f.write(start_line)
        
        observer.safe_send("trace motest on")

        # Wait for status changes to come through and write them to the correct files with timestamps
        while self.monitor_log:
            return_data = observer.poll_for_data()
            
            # If lines come through, parse them and write them to the correct files
            if return_data != "":
                lines = return_data.splitlines()
                for line in lines:
                    if "Mote #" in line:
                        # Get the mote number from the message
                        start_index = line.find("Mote #") + len("Mote #")
                        end_index = line.find(" ", start_index)
                        mote_id = line[start_index:end_index]

                        # Check if the device is new and write it a default file
                        if mote_id not in id_mac_pairs:
                            id_mac_pairs = observer.get_mote_id_mac_associations()
                            print("\033[92mUpdated mote ID/MAC address associations\033[0m")
                            with open(folder + "/" + subfolder + "/" + str(mote_id) + "$" + str(id_mac_pairs[mote_id]) + ".txt", "w") as f:
                                f.write(start_line)

                        # Get a timestamp and write it in Unix format and the custom format separated by $ symbols
                        now = datetime.now()
                        log_line = now.strftime(str(now.timestamp()) + " $ " + self.TS_FMT + " $ " + line + "\n")

                        # Write the log line
                        with open(folder + "/" + subfolder + "/" + str(mote_id) + "$" + str(id_mac_pairs[mote_id]) + ".txt", "a") as f:
                            f.write(log_line)
                            print("\033[92m" + log_line + "\033[0m", end = "")


    def hartserver_observation(self, observer, folder):
        # Create a folder to hold each log
        if not(os.path.exists(folder)):
            os.mkdir(folder)
        subfolder = "hartserver"
        if not(os.path.exists(folder + "/" + subfolder)):
            os.mkdir(folder + "/" + subfolder)
        
        # Start watching hartserver with the tail commmand
        while "No such file or directory" in observer.safe_send("tail -F /var/apache/data/hartserver.txt"):
            time.sleep(1)
            print("\033[94mTrying to open hartserver...\033[0m")
        print("\033[94mOpened hartserver\033[0m")

        # Wait for status changes to come through and write them to the correct files with timestamps
        while self.monitor_log:
            tries = 0
            return_data = ""
            while tries < 10:
                if observer.shell.recv_ready():
                    return_data += observer.shell.recv(1).decode("ascii")
                    tries = 0
                else:
                    tries += 1
                    time.sleep(0.1)
            
            # If lines come through, parse them and write them to the correct files
            if return_data != "":
                lines = return_data.splitlines()
                for line in lines:
                    if "00-" in line:
                        # Get the MAC address out of the line
                        start_index = line.find("00-")
                        end_index = line.find(" ", start_index)
                        mote_mac = line[start_index:end_index]

                        # If the MAC address is at the end of the line, no space will be present after the address
                        if end_index == -1:
                            mote_mac = line[start_index:]

                        # If the MAC address is at the end of a sentence, the period needs to be removed
                        if mote_mac.endswith("."):
                            mote_mac = mote_mac[:-1]

                        # Get a timestamp and write it in Unix format and the custom format separated by $ symbols
                        now = datetime.now()
                        log_line = now.strftime(str(now.timestamp()) + " $ " + self.TS_FMT + " $ " + line + "\n")

                        # Determine whether a new file needs to be created or if an existing one should be appended
                        write_mode = "w"
                        if os.path.exists(folder + "/" + subfolder + "/" + mote_mac + ".txt"):
                            write_mode = "a"
                        
                        # Write the log line
                        with open(folder + "/" + subfolder + "/" + mote_mac + ".txt", write_mode) as f:
                            f.write(log_line)
                            print("\033[94m" + log_line + "\033[0m", end = "")


    def stop(self):
        self.monitor_log = False


    def start(self, directory = "", track_isa = False, folder_override = False):
        self.monitor_log = True
        self.running_test = True

        # Continuously attempt to connect to the gateway until a connection is established
        # Close the connection immediately to allow the nwconsole and hartserver observers to run
        connection_verification = paramiko.SSHClient()
        connection_verification.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        while True:
            try:
                connection_verification.connect(hostname = self.hostname, port = 22, username = self.username, password = self.password)
                break
            except:
                time.sleep(1)
        connection_verification.close()

        # Create two SSH sessions so one can monitor nwconsole while the other monitors hartserver
        nwconsole_observer = InteractiveSSH(hostname = self.hostname, port = 22, username = self.username, password = self.password)
        hartserver_observer = InteractiveSSH(hostname = self.hostname, port = 22, username = self.username, password = self.password)

        # Create an additional thread for ISA100 monitoring if requested
        isa_observer = None
        if track_isa:
            isa_observer = IsaDeviceCounter(hostname = self.hostname, port = 22, username = self.username, password = self.password)

        # Create a folder to hold the data
        folder = datetime.now().strftime(self.hostname + " - %a %d %B %Y - %I-%M-%S %p")
        folder = directory + "/" + folder
        if folder_override:
            folder = directory

        # Setup each observer with their own thread to begin monitoring
        nwconsole_observation_thread = threading.Thread(target = self.nwconsole_observation, args = (nwconsole_observer, folder), name = "nwconsole Observation")
        nwconsole_observation_thread.start()
        hartserver_observation_thread = threading.Thread(target = self.hartserver_observation, args = (hartserver_observer, folder), name = "hartserver Observation")
        hartserver_observation_thread.start()

        isa_observation_thread = None
        if track_isa:
            isa_observation_thread = threading.Thread(target = self.isa_monitor_host_observation, args = (isa_observer, folder), name = "ISA100 Observation")
            isa_observation_thread.start() 

        # Wait for user to enter quit to stop logging
        #while input("Type \"quit\" to stop logging data: ").lower() != "quit":
        while self.monitor_log:
            continue

        print("Stopping logging...")

        # Join the observation threads
        print("Waiting for observation threads to finish current operation...")
        nwconsole_observation_thread.join()
        hartserver_observation_thread.join()

        if isa_observation_thread != None:
            isa_observation_thread.join()
        print("Observation threads finished. Closing SSH sessions.")

        # Cancel the monitoring operations
        try:
            nwconsole_observer.safe_send("trace motest off")
        except:
            pass

        try:
            hartserver_observer.safe_send("\x03")
        except:
            pass

        # Close the SSH sessions
        try:
            nwconsole_observer.shell.close()
            nwconsole_observer.close()
        except:
            pass

        try:
            hartserver_observer.shell.close()
            hartserver_observer.close()
        except:
            pass

        try:
            isa_observer.close()
        except:
            pass

        # Combine ISA100 files for the same device into one file (can happen if a name isn't valid but later is recognized)
        if track_isa:
            merged_files = []
            for log_file in os.listdir(folder + "/isa"):
                # Skip files that aren't .txt log files
                if log_file[-4:] != ".txt":
                    continue

                # Skip files with unidentified device names (they will be merged into other files)
                if "$NULL.txt" in log_file:
                    continue
                    
                # Skip files that have already been merged
                if log_file in merged_files:
                    continue
                
                # Get the identifier before the device name (<Device ID>$)
                identifier = log_file.split("$")[0] + "$"

                # Get a list of all files to check the current log file against
                all_files = os.listdir(folder + "/isa")

                # Get the list of all files to merge together
                files_to_merge = []
                for filename in all_files:
                    if filename.startswith(identifier) and (filename != log_file):
                        files_to_merge.append(filename)
                
                # Read the contents of all files into a string
                content = ""
                for filename in ([log_file] + files_to_merge):
                    with open(folder + "/isa/" + filename, "r") as f:
                        content += f.read()
                content.replace("\n\n", "\n")

                # Write the merged content into the original log file
                with open(folder +  "/isa/" + log_file, "w") as f:
                    f.write(content)
                
                merged_files.extend(files_to_merge)
            
            # Delete the merged files
            for filename in merged_files:
                os.remove(folder + "/isa/" + filename)

        # Parse the logs
        print("Parsing device logs...")
        parse_hart_device_logs(folder)
        if track_isa:
            parse_isa_device_logs(folder)

        # Convert the CSV files to an XLSX
        convert_csv_files_to_xlsx(folder + "/DeviceTimeInfo.xlsx", folder)

        # Delete the CSV files
        os.remove(folder + "/HART.csv")
        if track_isa:
            os.remove(folder + "/ISA100.csv")

        self.running_test = False
        print("Finished test and stored results in " + folder + "/DeviceTimeInfo.xlsx")


def verify_ssh_connection(hostname, port = 22, username = "root", password = "emerson1"):
    # Continuously attempt to connect to the gateway until a connection is established
    # Close the connection immediately to allow the nwconsole and hartserver observers to run
    connection_verification = paramiko.SSHClient()
    connection_verification.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    while True:
        try:
            connection_verification.connect(hostname = hostname, port = port, username = username, password = password)
            break
        except:
            time.sleep(1)
    connection_verification.close()


if __name__ == "__main__":
    print("Please run another script that is preconfigured to call this one.")

import base64
import paramiko
import time
import re
import threading
import os
import sys
from datetime import datetime

from ParseDeviceLogs import parse_device_logs

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../SSHHelper")
from InteractiveSSH import InteractiveSSH

ts_fmt = "%m/%d/%y %H:%M:%S"
monitor_log = True


def nwconsole_observation(observer, folder):
    global ts_fmt
    global monitor_log

    # Keep trying to open nwconsole until the service is ready to run after a reboot
    while True:
        try:
            observer.start_nwconsole()
            break
        except TimeoutError:
            time.sleep(1)
    print("Opened nwconsole")

    id_mac_pairs = observer.get_mote_id_mac_associations()
    print("Created mote ID/MAC address associations")

    # Create a folder to hold each log
    if not(os.path.exists(folder)):
        os.mkdir(folder)
    subfolder = "nwconsole"
    if not(os.path.exists(folder + "/" + subfolder)):
        os.mkdir(folder + "/" + subfolder)
    
    # Create blank log files for each device
    for mote_id in id_mac_pairs:
        with open(folder + "/" + subfolder + "/" + str(id_mac_pairs[mote_id]) + ".txt", "w") as f:
            now = datetime.now()
            log_line = now.strftime(str(now.timestamp()) + " $ " + ts_fmt + " $ Test Started\n")
            f.write(log_line)
    
    observer.safe_send("trace motest on")

    # Wait for status changes to come through and write them to the correct files with timestamps
    while monitor_log:
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

                    # Get a timestamp and write it in Unix format and the custom format separated by $ symbols
                    now = datetime.now()
                    log_line = now.strftime(str(now.timestamp()) + " $ " + ts_fmt + " $ " + line + "\n")

                    # Write the log line
                    with open(folder + "/" + subfolder + "/" + str(id_mac_pairs[mote_id]) + ".txt", "a") as f:
                        f.write(log_line)
                        print(log_line, end = "")


def hartserver_observation(observer, folder):
    global ts_fmt
    global monitor_log

    # Create a folder to hold each log
    if not(os.path.exists(folder)):
        os.mkdir(folder)
    subfolder = "hartserver"
    if not(os.path.exists(folder + "/" + subfolder)):
        os.mkdir(folder + "/" + subfolder)
    
    # Start watching hartserver with the tail commmand
    while "No such file or directory" in observer.safe_send("tail -F /var/apache/data/hartserver.txt"):
        time.sleep(1)
        print("Trying to open hartserver...")
    print("Opened hartserver")

    # Wait for status changes to come through and write them to the correct files with timestamps
    while monitor_log:
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
                    log_line = now.strftime(str(now.timestamp()) + " $ " + ts_fmt + " $ " + line + "\n")

                    # Determine whether a new file needs to be created or if an existing one should be appended
                    write_mode = "w"
                    if os.path.exists(folder + "/" + subfolder + "/" + mote_mac + ".txt"):
                        write_mode = "a"
                    
                    # Write the log line
                    with open(folder + "/" + subfolder + "/" + mote_mac + ".txt", write_mode) as f:
                        f.write(log_line)
                        print(log_line, end = "")


def main():
    global monitor_log

    hostname = "toc0"
    username = "root"
    password = "emerson1"

    # Continuously attempt to connect to the gateway until a connection is established
    # Close the connection immediately to allow the nwconsole and hartserver observers to run
    connection_verification = paramiko.SSHClient()
    connection_verification.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    while True:
        try:
            connection_verification.connect(hostname = hostname, port = 22, username = username, password = password)
            break
        except:
            time.sleep(1)
    connection_verification.close()

    # Create two SSH sessions so one can monitor nwconsole while the other monitors hartserver
    nwconsole_observer = InteractiveSSH(hostname = hostname, port = 22, username = username, password = password)
    hartserver_observer = InteractiveSSH(hostname = hostname, port = 22, username = username, password = password)

    # Create a folder to hold the data
    folder = datetime.now().strftime(hostname + " - %a %d %B %Y - %I-%M-%S %p")

    # Setup each observer with their own thread to begin monitoring
    nwconsole_observation_thread = threading.Thread(target = nwconsole_observation, args = (nwconsole_observer, folder), name = "nwconsole Observation")
    nwconsole_observation_thread.start()
    hartserver_observation_thread = threading.Thread(target = hartserver_observation, args = (hartserver_observer, folder), name = "hartserver Observation")
    hartserver_observation_thread.start()

    # Wait for user to enter quit to stop logging
    while input("Type \"quit\" to stop logging data: ").lower() != "quit":
        continue

    print("Stopping logging...")

    monitor_log = False

    # Join the observation threads
    nwconsole_observation_thread.join()
    hartserver_observation_thread.join()

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

    # Parse the logs
    print("Parsing device logs...")
    loc = parse_device_logs(folder)

    print("Finished test and stored results in " + loc)


if __name__ == "__main__":
    main()

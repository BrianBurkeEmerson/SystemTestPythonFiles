import base64
import paramiko
import time
import re
import threading
import os
from datetime import datetime

ts_fmt = "%m/%d/%y %H:%M:%S"

class InteractiveSsh(paramiko.SSHClient):
    def __init__(self, hostname = "192.168.1.10", port = 22, username = "root", password = "emerson1"):
        super().__init__()

        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password

        self.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.connect(hostname = self.hostname, port = self.port, username = self.username, password = self.password)

        self.shell = self.invoke_shell()
    

    def safe_send(self, data, send_newline = True, return_response = True):
        # Send data to the client
        tries = 0
        while tries < 10:
            if self.shell.send_ready():
                self.shell.send(data)
                if send_newline:
                    self.shell.send("\n")
                break
            else:
                tries += 1
                time.sleep(0.1)
        
        # Attempt to return data returned from the command
        tries = 0
        return_data = ""
        while tries < 10:
            if self.shell.recv_ready():
                return_data += self.shell.recv(1).decode("ascii")
                tries = 0
            else:
                tries += 1
                time.sleep(0.1)
        
        if return_response:
            return return_data
        else:
            return ""
    

    def start_nwconsole(self, username = "admin", password = "admin"):
        self.safe_send("/opt/dust-manager/bin/nwconsole")
        self.safe_send(username)
        self.safe_send(password)


def nwconsole_observation(observer, folder):
    global ts_fmt

    observer.start_nwconsole()

    id_mac_pairs = {}

    # Get a list of MAC addresses with associated mote IDs
    sm = observer.safe_send("sm -a").splitlines()
    for line in sm:
        # Only parse lines containing MAC addresses (all start with the same bytes)
        if "00-1B-1E" in line:
            columns = re.split("\s{1,}", line.strip())
            if "ap" in columns:
                id_mac_pairs[columns[2]] = columns[0]
            else:
                id_mac_pairs[columns[1]] = columns[0]

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
    while True:
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
                if "Mote #" in line:
                    start_index = line.find("Mote #") + len("Mote #")
                    end_index = line.find(" ", start_index)
                    mote_id = line[start_index:end_index]

                    now = datetime.now()
                    log_line = now.strftime(str(now.timestamp()) + " $ " + ts_fmt + " $ " + line + "\n")

                    with open(folder + "/" + subfolder + "/" + str(id_mac_pairs[mote_id]) + ".txt", "a") as f:
                        f.write(log_line)
                        print(log_line, end = "")


def hartserver_observation(observer, folder):
    global ts_fmt

    # Create a folder to hold each log
    if not(os.path.exists(folder)):
        os.mkdir(folder)
    subfolder = "hartserver"
    if not(os.path.exists(folder + "/" + subfolder)):
        os.mkdir(folder + "/" + subfolder)
    
    # Start watching hartserver with the tail commmand
    while "No such file or directory" in observer.safe_send("tail -F /var/apache/data/hartserver.txt"):
        time.sleep(1)
        print("Trying to open hartserver")

    # Wait for status changes to come through and write them to the correct files with timestamps
    while True:
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
                if "00-1B-1E" in line:
                    start_index = line.find("00-1B-1E")
                    end_index = line.find(" ", start_index)
                    mote_mac = line[start_index:end_index]

                    now = datetime.now()
                    log_line = now.strftime(str(now.timestamp()) + " $ " + ts_fmt + " $ " + line + "\n")

                    write_mode = "w"
                    if os.path.exists(folder + "/" + subfolder + "/" + mote_mac + ".txt"):
                        write_mode = "a"
                    
                    with open(folder + "/" + subfolder + "/" + mote_mac + ".txt", write_mode) as f:
                        f.write(log_line)
                        print(log_line, end = "")


def main():
    hostname = "toc0"
    nwconsole_observer = InteractiveSsh(hostname = hostname)
    hartserver_observer = InteractiveSsh(hostname = hostname)

    folder = datetime.now().strftime(hostname + " - %a %d %B %Y - %I-%M-%S %p")

    # Setup each observer with their own thread to begin monitoring
    nwconsole_observation_thread = threading.Thread(target = nwconsole_observation, args = (nwconsole_observer, folder), name = "nwconsole Observation", daemon = True)
    nwconsole_observation_thread.start()
    hartserver_observation_thread = threading.Thread(target = hartserver_observation, args = (hartserver_observer, folder), name = "hartserver Observation", daemon = True)
    hartserver_observation_thread.start()

    # Wait for user to enter quit to stop logging
    while input("Type \"quit\" to stop logging data: ").lower() != "quit":
        continue

    nwconsole_observer.safe_send("trace motest off")
    hartserver_observer.safe_send("\x03")

    # Close the SSH sessions
    nwconsole_observer.shell.close()
    nwconsole_observer.close()
    hartserver_observer.shell.close()
    hartserver_observer.close()


if __name__ == "__main__":
    main()

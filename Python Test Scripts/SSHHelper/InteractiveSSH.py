import paramiko
import re
import time

class InteractiveSSH(paramiko.SSHClient):
    def __init__(self, hostname = "192.168.1.10", port = 22, username = "root", password = "emerson1", connect = True):
        super().__init__()

        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password

        self.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.shell = None

        if connect:
            self.ssh_connect()

    def ssh_connect(self):
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
        
        if tries >= 10:
            raise TimeoutError("Could not send command")
        
        # Attempt to return data returned from the command
        return_data = self.poll_for_data()
        
        if return_response:
            return return_data
        else:
            return ""
    

    def start_nwconsole(self, username = "admin", password = "admin"):
        return_string = self.safe_send("/opt/dust-manager/bin/nwconsole")
        return_string += self.safe_send(username)
        return_string += self.safe_send(password)

        if "Could not connect to dcc" in return_string:
            raise TimeoutError("DCC has not started yet")
    

    def get_mote_id_mac_associations(self, use_mac_keys = False):
        id_mac_pairs = {} # IDs are keys and MAC addresses are entries
        mac_id_pairs = {} # MAC addresses are keys and IDs are entries

        # Get a list of MAC addresses with associated mote IDs
        retry_sm = True
        while retry_sm:
            id_mac_pairs = {}
            mac_id_pairs = {}
            sm = self.safe_send("sm -a").splitlines()
            for line in sm:
                # Only parse lines containing MAC addresses (all start with the same bytes)
                if "00-" in line:
                    columns = re.split("\s{1,}", line.strip())
                    if "ap" in columns:
                        id_mac_pairs[columns[2]] = columns[0]
                        mac_id_pairs[columns[0]] = columns[2]
                        retry_sm = False
                    else:
                        id_mac_pairs[columns[1]] = columns[0]
                        mac_id_pairs[columns[0]] = columns[1]
        
        if use_mac_keys:
            return mac_id_pairs
        else:
            return id_mac_pairs
    

    def poll_for_data(self, retry_limit = 10):
        tries = 0
        return_data = ""
        while tries < retry_limit:
            if self.shell.recv_ready():
                return_data += self.shell.recv(1).decode("ascii")
                tries = 0
            else:
                tries += 1
                time.sleep(0.1)
        
        return return_data
    

    def get_paths(self, return_mac_paths = False):
        mac_id_pairs = self.get_mote_id_mac_associations(use_mac_keys = True)

        lines = self.safe_send("get paths").splitlines()
        
        # Break each path into its own array to make processing easier
        paths_raw = [] # Stores all paths
        path_raw_data = [] # Stores block of text relating to current path

        # Go through all lines and break response into blocks by path
        for line in lines:
            if "pathId:" in line:
                if path_raw_data != []:
                    paths_raw.append(path_raw_data)
                    path_raw_data = []
            path_raw_data.append(line)
        
        if path_raw_data != []:
            paths_raw.append(path_raw_data)
            path_raw_data = []
        
        paths_mac = []
        paths_id = []

        # Process each individual path
        for path in paths_raw:
            mote_A_mac = ""
            mote_B_mac = ""
            mote_A_id = ""
            mote_B_id = ""

            used_path = True

            # Go through each line in the block
            for line in path:
                columns = re.split("\s{1,}", line.strip())

                # Set the mote A and B info and mark the path as unused if its present
                if "moteAMac:" in line:
                    mote_A_mac = columns[1]
                    mote_A_id = mac_id_pairs[mote_A_mac]
                elif "moteBMac:" in line:
                    mote_B_mac = columns[1]
                    mote_B_id = mac_id_pairs[mote_B_mac]
                elif "pathDirection:" in line:
                    if "unused" in line:
                        used_path = False
            
            # If the path is used, add it to the list
            if used_path and (mote_A_mac != ""):
                paths_mac.append([mote_A_mac, mote_B_mac])
                paths_id.append([mote_A_id, mote_B_id])
            
        # Return the correct set of paths based on whether IDs or MACs were requested
        if return_mac_paths:
            return paths_mac
        else:
            return paths_id

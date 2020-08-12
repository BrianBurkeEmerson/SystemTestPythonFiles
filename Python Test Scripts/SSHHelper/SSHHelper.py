import paramiko
import concurrent.futures
import re
import time

RETRY_COUNT = 10
DELAY_BETWEEN_RETRIES = 0.5
PASS_SIZE = 3 # The number of commands that can be executed at once (in a single pass)

class SSHHelper(paramiko.SSHClient):
    def __init__(self, hostname = "192.168.1.10", port = 22, username = "root", password = "emerson1"):
        super().__init__()

        # Create the paramiko SSH client and apply a key policy
        self.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Establish the SSH connection
        self.connect(hostname = hostname, port = port, username = username, password = password)

        # Create an empty dictionary of processes being tracked
        self.processes = {}


    # Removes any characters from a string that are not numbers
    # input_string: The string from which characters are removed
    def remove_non_numbers(self, input_string = ""):
        return_string = ""

        for c in input_string:
            if c in "0123456789":
                return_string += c
        
        return return_string


    # Sends a command via the SSH channel and returns the response as a list containing each line as an individual entry
    # cmd: The command to be sent via SSH
    def send_command(self, cmd = ""):
        # Send the command and capture the output
        stdout = []
        for _ in range(RETRY_COUNT):
            try:
                _stdin, stdout, _stderr = self.exec_command(cmd)
                break
            except:
                time.sleep(DELAY_BETWEEN_RETRIES)
        
        # Put each line of the output into a list
        stdout_list = []
        for line in stdout:
            stdout_list.append(line)
        
        return stdout_list
    

    # Calls the TOP command and parses the output to determine which processes are using the most memory
    # num_of_processes: How many processes to return
    def get_top_memory_usage_processes(self, num_of_processes = 1, use_alt = False):
        return_list = []
        i = 0

        # Send a TOP command, and filter out only the lines containing "root" (lines with processes)
        # Sort by % memory usage
        if use_alt:
            for line in self.send_command("ps aux --sort -rss | grep root"):
                if i < num_of_processes:
                    columns = re.split("\s{1,}", line.strip())
                    # Get the process name by combining all columns at index 10 and after
                    process_name = ""
                    for j in range(10, len(columns)):
                        process_name += str(columns[j])
                    
                    # Add the process name and the percent memory usage (index 3)
                    return_list.append((process_name, columns[3]))
                    i += 1
        else:
            for line in self.send_command("top -n 1 -o %MEM -b | grep root"):
                if i < num_of_processes:
                    # Get the 11th column (starting from 0) to get the process name after splitting with regex
                    # Get the 9th column to get the memory usage percentage
                    return_list.append((re.split("\s{1,}", line.strip())[11], re.split("\s{1,}", line.strip())[9]))
                    i += 1
        
        # If the number of recorded processes has not reached what was requested, pad out the list with empty strings
        while i < num_of_processes:
            return_list.append("")
            i += 1
        
        return return_list


    # Returns the memory usage in kB of a process given its process ID
    # pid: The ID of the process of interest
    def get_memory_usage_by_pid(self, pid = 0):
        mem = self.send_command("sudo pmap " + str(pid) + " | tail -n 1 | awk '/[0-9]K/{print $2}'")[0]
        return int(self.remove_non_numbers(mem))


    # Looks up the process ID of a process by name and then uses that PID to return the process's memory usage in kB
    # process_name: A string of the process name (such as "hartserver" or "backbone")
    def get_memory_usage_by_name(self, process_name = ""):
        try:
            pid = self.remove_non_numbers(self.send_command("pgrep " + process_name)[0])
            return self.get_memory_usage_by_pid(pid)
        except:
            return 0
    

    # Uses multiple threads to get the memory usage of multiple processes passed in as a tuple or list
    # processes: A tuple or list of strings for the processes of interest
    def get_memory_usage_by_multi_name(self, processes = ("",)):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.get_memory_usage_by_name, process) for process in processes]
        
        return [f.result() for f in futures]

    
    # Registers a process and creates an entry for it in the class's processes dictionary
    # This entry keeps track of any PIDs for the process as well as memory usage
    # This eliminates the need to determine the PID of every process on each request (which is required by get_memory_usage_by_name() and get_memory_usage_by_multi_name())
    # process_name: The name of the process to be registered/tracked
    def register_process(self, process_name = ""):
        self.processes[process_name] = {
            "pid_list" : [],
            "memory_usages" : [],
            "total_memory" : 0
        }

        for line in self.send_command("pgrep " + process_name):
            self.processes[process_name]["pid_list"].append(self.remove_non_numbers(line))
            self.processes[process_name]["memory_usages"].append(0)
    

    # Registers multiple processes passed in as a tuple or list by calling register_process() for each process
    # processes: A tuple of list of strings for the processes to register
    def register_processes(self, processes = ("",)):
        for process in processes:
            self.register_process(process)
    

    # Checks the memory usage of each registered process and returns the result as a list
    # The list will be returned in the order that processes are registered, so using a constant tuple or list is recommended when registering
    # This makes this method of checking memory usage drop-in compatible with the other methods
    def check_processes(self):
        if self.processes != []:
            dict_access = []

            # Construct the command that will be sent via SSH to get the process memory usages
            sh_cmd = "sudo pmap "
            for process in self.processes:
                pid_index = 0

                for pid in self.processes[process]["pid_list"]:
                    sh_cmd += (str(pid) + " ")
                    dict_access.append([process, pid_index])
                    pid_index += 1
            
            # Filter all information other than total memory used by each process
            sh_cmd += "| grep total | awk '/[0-9]K/{print$2}'"

            # Send the command and capture the response
            usages = self.send_command(sh_cmd)

            # Process the response and store the memory usage of each PID in an organized dictionary
            for usage in range(len(usages)):
                #self.processes["process_name"]["pid_list/memory_usages/total_memory"]["optional index if using pid_list/memory_usages"]
                self.processes[dict_access[usage][0]]["memory_usages"][dict_access[usage][1]] = int(self.remove_non_numbers(usages[usage]))
            
            # Return the memory usages as a simple list to be drop-in compatible with the other methods of checking memory usage
            return_list = []

            # Calculate the total memory for each process (some processes have 2+ PIDs)
            for process in self.processes:
                self.processes[process]["total_memory"] = 0

                for usage in self.processes[process]["memory_usages"]:
                    self.processes[process]["total_memory"] += usage

                return_list.append(self.processes[process]["total_memory"])
            
            return return_list

        else:
            return []
    

    def dump_process_pmap_info(self):
        if self.processes != []:
            # Construct the command that will be sent via SSH to get the pmap dump
            sh_cmd = "sudo pmap"

            for process in self.processes:
                for pid in self.processes[process]["pid_list"]:
                    sh_cmd += (" " + str(pid))

            # Get the logs from the gateway
            logs_list = self.send_command(sh_cmd)
            logs = ""
            for line in logs_list:
                logs += line

            # Create a dictionary with empty string values to store each process's information
            return_dict = {}
            for process in self.processes:
                return_dict[process] = ""

            # Split the log by process and return a dictionary of the strings for each process's information
            for process in self.processes:
                for pid in self.processes[process]["pid_list"]:
                    start_index = logs.find(str(pid) + ":")
                    pre_end_index = logs.find("total", start_index)
                    end_index = logs.find("\n", pre_end_index)
                    return_dict[process] += (logs[start_index:end_index] + "\n")
            
            return return_dict
        
        else:
            return {}


    def exec_maps_cmds(self, process, cmds):
        return_dict = {process : ""}

        for cmd in cmds:
            for line in self.send_command(cmd):
                return_dict[process] += line
            #return_dict[process].extend(self.send_command(cmd))
        
        return return_dict

    def dump_process_maps_info(self, smaps = False):
        return_dict = {}

        smaps_char = ""
        if smaps:
            smaps_char = "s"

        # Construct a list of commands to send for each process when getting the memory dumps
        cmds = {}
        procs = []
        for process in self.processes:
            cmds[process] = []
            procs.append(process)

            for pid in self.processes[process]["pid_list"]:
                cmds[process].append("cat /proc/" + str(pid) + "/" + smaps_char + "maps")

        # Break the dump into multiple transmissions (sending too many SSH commands at once creates an error)
        continue_sending = True
        start_i = 0
        end_i = 0
        while continue_sending:
            # Determine how many commands to execute without overflowing past the number of processes
            end_i += PASS_SIZE
            if end_i >= len(procs):
                end_i = len(procs)
                continue_sending = False

            # Create an dictionary subset for commands to execute from the larger cmds dictionary
            with concurrent.futures.ThreadPoolExecutor() as executor:
                cmds_in_pass = {}
                for i in range(start_i, end_i):
                    cmds_in_pass[procs[i]] = cmds[procs[i]]

                futures = [executor.submit(self.exec_maps_cmds, process, cmds[process]) for process in cmds_in_pass]

            # Add the results to the returned dictionary
            for f in futures:
                return_dict.update(f.result())
            
            start_i += PASS_SIZE

        return return_dict


    def dump_process_smaps_info(self):
        return self.dump_process_maps_info(smaps = True)

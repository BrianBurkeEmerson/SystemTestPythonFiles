import paramiko
import concurrent.futures

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
        _stdin, stdout, _stderr = self.exec_command(cmd)
        
        # Put each line of the output into a list
        stdout_list = []
        for line in stdout:
            stdout_list.append(line)
        
        return stdout_list


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

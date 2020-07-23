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


    def remove_non_numbers(self, input_string = ""):
        return_string = ""

        for c in input_string:
            if c in "0123456789":
                return_string += c
        
        return return_string


    def send_command(self, cmd = ""):
        # Send the command and capture the output
        _stdin, stdout, _stderr = self.exec_command(cmd)
        
        # Put each line of the output into a list
        stdout_list = []
        for line in stdout:
            stdout_list.append(line)
        
        return stdout_list


    def get_memory_usage_by_pid(self, pid = 0):
        mem = self.send_command("sudo pmap " + str(pid) + " | tail -n 1 | awk '/[0-9]K/{print $2}'")[0]
        return self.remove_non_numbers(mem)


    def get_memory_usage_by_name(self, process_name = ""):
        try:
            pid = self.remove_non_numbers(self.send_command("pgrep " + process_name)[0])
            return self.get_memory_usage_by_pid(pid)
        except:
            return "0"
    

    def get_memory_usage_by_multi_name(self, processes = ("",)):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.get_memory_usage_by_name, process) for process in processes]
        
        return [f.result() for f in futures]

    
    def register_process(self, process_name = ""):
        self.processes[process_name] = {
            "pid_list" : [],
            "memory_usages" : [],
            "total_memory" : 0
        }

        for line in self.send_command("pgrep " + process_name):
            self.processes[process_name]["pid_list"].append(self.remove_non_numbers(line))
            self.processes[process_name]["memory_usages"].append(0)
    

    def register_processes(self, processes = ("",)):
        for process in processes:
            self.register_process(process)
    

    def check_processes(self):
        dict_access = []

        sh_cmd = "sudo pmap "
        for process in self.processes:
            pid_index = 0

            for pid in self.processes[process]["pid_list"]:
                sh_cmd += (str(pid) + " ")
                dict_access.append([process, pid_index])
                pid_index += 1
        
        sh_cmd += "| grep total | awk '/[0-9]K/{print$2}'"

        usages = self.send_command(sh_cmd)

        for usage in range(len(usages)):
            #self.processes["process_name"]["pid_list/memory_usages/total_memory"]["optional index if using pid_list/memory_usages"]
            self.processes[dict_access[usage][0]]["memory_usages"][dict_access[usage][1]] = int(self.remove_non_numbers(usages[usage]))
        
        return_list = []

        for process in self.processes:
            self.processes[process]["total_memory"] = 0

            for usage in self.processes[process]["memory_usages"]:
                self.processes[process]["total_memory"] += usage

            return_list.append(self.processes[process]["total_memory"])
        
        return return_list
        
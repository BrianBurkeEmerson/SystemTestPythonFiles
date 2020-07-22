import paramiko

class SSHHelper(paramiko.SSHClient):
    def __init__(self, hostname = "192.168.1.10", port = 22, username = "root", password = "emerson1"):
        super().__init__()

        # Create the paramiko SSH client and apply a key policy
        self.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Establish the SSH connection
        self.connect(hostname = hostname, port = port, username = username, password = password)


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

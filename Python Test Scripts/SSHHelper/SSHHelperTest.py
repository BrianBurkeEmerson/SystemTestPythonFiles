from SSHHelper import SSHHelper
import threading


def get_memory_usage(client, process):
    print(process + ": " + client.get_memory_usage_by_name(process))


ssh = SSHHelper("systestdual")

processes = ["dcc", "hartserver", "java", "stunnel", "xmlrpcd", "fimmgrd", "syslog-ng"]

# Get memory usage of multiple processes one at a time
#for process in processes:
    #print(process + ": " + ssh.get_memory_usage_by_name(process))

# Create separate threads to simultaneously request the memory usage of each process
#for process in processes:
    #threading.Thread(target = get_memory_usage, args = (ssh, process)).start()

# Use the built-in function to get the memory usage of each function simultaneously
print(ssh.get_memory_usage_by_multi_name(processes))

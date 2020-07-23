from SSHHelper import SSHHelper
import threading


def get_memory_usage(client, process):
    print(process + ": " + str(client.get_memory_usage_by_name(process)))


ssh = SSHHelper("systestdual")

processes = ["hartserver", "backbone", "dcc", "java", "stunnel", "xmlrpcd", "fimmgrd", "syslog-ng"]

# Get memory usage of multiple processes one at a time
#for process in processes:
    #print(process + ": " + str(ssh.get_memory_usage_by_name(process)))

# Create separate threads to simultaneously request the memory usage of each process
#for process in processes:
    #threading.Thread(target = get_memory_usage, args = (ssh, process)).start()

# Use the built-in function to get the memory usage of each function simultaneously
#print(ssh.get_memory_usage_by_multi_name(processes))

# Register processes and use the built-in function to check the memory usage of those all at once
ssh.register_processes(processes)
print(ssh.check_processes())


ssh.close()

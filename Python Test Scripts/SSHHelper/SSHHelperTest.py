from SSHHelper import SSHHelper
import threading


def get_memory_usage(client, process):
    print(process + ": " + client.get_memory_usage_by_name(process))


ssh = SSHHelper("systestdual")

processes = ["dcc", "hartserver", "java", "stunnel", "xmlrpcd", "fimmgrd", "syslog-ng"]

for process in processes:
    #print(process + ": " + ssh.get_memory_usage_by_name(process))
    threading.Thread(target = get_memory_usage, args = (ssh, process)).start()

import sys
import os
import threading
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../ISA 100 Testing Scripts/ISADeviceCount")
from ISADeviceCount import IsaDeviceCounter


def read_data(gateway, processes, filename):
    data = datetime.now().strftime("%x %X")
    for memory in gateway.clientSsh.check_processes():
        data += ("," + str(memory))
    
    data += "\n"

    # Write the data to the CSV file
    with open(filename, "a") as result_file:
        result_file.write(data)
    
    print(data)

    # Start a new thread for the next scheduled data recording
    recordingThread = threading.Timer(30, read_data, args = (gateway, processes, filename))
    recordingThread.daemon = True
    recordingThread.name = "DataRecording"
    recordingThread.start()


hostname = "toc0"
username = "root"
password = "emerson1"

gateway = IsaDeviceCounter(hostname = hostname, username = username, password = password)

filename = "memory_usage.csv"
processes = ["dcc", "hartserver", "java", "stunnel", "xmlrpcd", "fimmgrd",\
    "syslog-ng", "SystemManager", "isa_gw", "MonitorHost", "mbserver", "apdriver", "scgi_svc", "led_reset_monitor"]

# Write the header row for the recorded data
with open(filename, "w") as result_file:
    header = "Date and Time"
    for process in processes:
        header += ("," + process + " (kB)")

    result_file.write(header + "\n")

gateway.clientSsh.register_processes(processes)

recordingThread = threading.Thread(target = read_data, name = "DataRecording", args = (gateway, processes, filename), daemon = True)
recordingThread.start()

quit_input = ""
while quit_input != "quit":
    quit_input = input("Type \"quit\" to stop data logging: ").lower()

gateway.close()

# This test periodically checks the status of the gateway and its HART/ISA devices
# A CSV file is created where each periodic check adds a new line in the following format
# Date/Time, Number of Connected ISA Devices, Total Memory, Free Memory, Available Memory

# Execution can be set to run for a certain amount of time or it can be set to be manually stopped by typing "quit"

# pip install paramiko
# pip install scp
# pip install selenium
# pip install matplotlib

import sys
import os
import time
import threading
import tkinter as tk
import tkinter.filedialog as fd
from datetime import datetime
from getpass import getpass
from configparser import ConfigParser

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../ISA 100 Testing Scripts/ISADeviceCount")
from ISADeviceCount import IsaDeviceCounter

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../Gateway Web Scraping Tools/GwDeviceCount")
from GwDeviceCount import GwDeviceCounter
import GwDeviceCount as gdc

from MemoryUsagePlotting import plot_csv_memory_file



CONFIG_FILE_NAME = "Options_MemoryUsageOverTime.ini"

manipulating_data = False # Tracks whether the secondary thread is downloading/processing/recording data to prevent corruption

# Track the folder where all files are stored
folder = ""

# Initialize variables for counting the number of devices
isa_devices = 0
hart_devices = 0
cpu_usage = 0
memory_usages = []



def verify_int_input_option(allowed_options = (1, 2), prompt = "Choose: ", error = "ERROR: Invalid input"):
    while True:
        option = input(prompt)
        option_int = None

        # Check if input is a valid integer
        try:
            option_int = int(option)
        except:
            print("ERROR: Unable to parse input")
            continue

        # Check if the user's input is one of the allowed options
        if option_int in allowed_options:
            return option_int
        else:
            print(error)
            continue


def verify_int_input_range(upper_bound = 1, lower_bound = 0, use_upper_bound = True, use_lower_bound = True, prompt = ""):
    while True:
        value = input(prompt)
        value_int = None

        # Check if input is a valid integer
        try:
            value_int = int(value)
        except:
            print("ERROR: Enter a valid integer")
            continue
        
        # Check if the input is inside the upper and lower bounds
        if use_upper_bound:
            if value_int <= upper_bound:
                return value_int
            else:
                print("ERROR: Enter a number less than or equal to " + str(upper_bound))
                continue
        
        if use_lower_bound:
            if value_int >= lower_bound:
                return value_int
            else:
                print("ERROR: Enter a number greater than or equal to " + str(lower_bound))
                continue
        
        if not(use_upper_bound) and not(use_lower_bound):
            return value_int


def remove_non_numbers(input_string = ""):
    return_string = ""

    for c in input_string:
        if c in "0123456789":
            return_string += c
    
    return return_string


def save_top_10_memory_usage_processes(ssh_helper):
    global folder

    # Get the top 10 processes using the most memory
    processes = ssh_helper.get_top_memory_usage_processes(10, False)
    file_location = folder + "/" + "most_memory_usage_processes.log"

    # Create the string written to the log
    log_string = ""
    for process in range(len(processes)):
        log_string += (str(process + 1) + ": " + str(processes[process][0]) + " - " + str(processes[process][1]) + "%\n")
        
    log_string += "\n\n\n\n"

    # Write the string to the log
    write_mode = "a"
    if not(os.path.exists(file_location)):
        write_mode = "w"
    
    with open(file_location, write_mode) as f:
        f.write(log_string)


def save_process_logs(ssh_helper):
    global folder
    write_mode = "a"

    # pmap
    logs = ssh_helper.dump_process_pmap_info()
    for process in logs:
        sub_folder = folder + "/" + process

        if not(os.path.isdir(sub_folder)):
            os.mkdir(sub_folder)

        # Determine whether a new file needs to be written or to continue appending to an old one
        log_location = sub_folder + "/" + process + "_pmap.log"
        if not(os.path.exists(log_location)):
            write_mode = "w"
        else:
            write_mode = "a"
        
        with open(log_location, write_mode) as f:
            f.write(logs[process] + "\n\n\n\n\n")
    
    # maps
    logs = ssh_helper.dump_process_maps_info()
    for process in logs:
        sub_folder = folder + "/" + process

        if not(os.path.isdir(sub_folder)):
            os.mkdir(sub_folder)

        # Determine whether a new file needs to be written or to continue appending to an old one
        log_location = sub_folder + "/" + process + "_maps.log"
        if not(os.path.exists(log_location)):
            write_mode = "w"
        else:
            write_mode = "a"
        
        with open(log_location, write_mode) as f:
            f.write(logs[process] + "\n\n\n\n\n")
    
    # smaps
    logs = ssh_helper.dump_process_smaps_info()
    for process in logs:
        sub_folder = folder + "/" + process

        if not(os.path.isdir(sub_folder)):
            os.mkdir(sub_folder)

        # Determine whether a new file needs to be written or to continue appending to an old one
        log_location = sub_folder + "/" + process + "_smaps.log"
        if not(os.path.exists(log_location)):
            write_mode = "w"
        else:
            write_mode = "a"
        
        with open(log_location, write_mode) as f:
            f.write(logs[process] + "\n\n\n\n\n")
    
    # Dump top logs
    logs = ssh_helper.send_command("top -n1 -b")
    log_location = folder + "/top.log"
    if not(os.path.exists(log_location)):
        write_mode = "w"
    else:
        write_mode = "a"
    with open(log_location, write_mode) as f:
        for line in logs:
            f.write(line)
        f.write("\n\n\n\n\n")
    
    # Dump process logs
    logs = ssh_helper.send_command("ps -o pid,user,%mem,command ax | sort -b -k3 -r")
    log_location = folder + "/ps.log"
    if not(os.path.exists(log_location)):
        write_mode = "w"
    else:
        write_mode = "a"
    with open(log_location, write_mode) as f:
        for line in logs:
            f.write(line)
        f.write("\n\n\n\n\n")


def get_cpu_usage(ssh_helper):
    global cpu_usage

    # Send a TOP command that returns only the first line to extract CPU usage information
    stdout = ssh_helper.send_command("top -n1 -b | grep average:")

    # Parse the return data to get the first CPU usage (average usage over 1 minute (next 2 are 5 minutes and 15 minutes))
    marker_string = "load average: "
    start_index = stdout[0].find(marker_string) + len(marker_string)
    end_index = stdout[0].find(",", start_index)
    cpu_usage = float(stdout[0][start_index:end_index]) * 100.0


def get_process_memory_usage(ssh_helper):
    global memory_usages

    memory_usages = ssh_helper.check_processes()


def count_live_hart_devices(scraper):
    global hart_devices

    # If the browser has been open for 30 minutes, open a new instance
    if scraper.check_browser_lifetime(30):
        # First close the old browser
        # Use a try-except to ignore the error when initially no browser is present
        try:
            scraper.close()
        except:
            pass
        
        # Open a new browser
        scraper.open()
    
    # If a new browser isn't being opened, the tab needs to be switched to force a refresh on the device counts
    else:
        scraper.change_device_tab(gdc.ALL_DEVICES_SPAN, False)

    hart_devices = scraper.get_live_devices_count()["HART"]


def record_data(filename, gateway, scraper, measurement_interval, track_hart, track_isa):
    global manipulating_data
    global isa_devices
    global hart_devices
    global memory_usages
    global cpu_usage

    manipulating_data = True # Indicate the thread is running and working on data

    # If HART devices are being tracked, start the web scraper on a separate thread
    scraperThread = None
    if track_hart:
        scraperThread = threading.Thread(target = count_live_hart_devices, args = (scraper,), name = "HartWebScraper")
        scraperThread.start()
    
    # Check the CPU usage
    cpuUsageThread = threading.Thread(target = get_cpu_usage, args = (gateway.clientSsh,), name = "CpuUsageCheck")
    cpuUsageThread.start()

    # If any processes are being tracked, start a new thread to get the data here
    memory_usages = []
    memoryUsageThread = threading.Thread(target = get_process_memory_usage, args = (gateway.clientSsh,), name = "ProcessMemoryUsageCheck")
    memoryUsageThread.start()

    # Dump the process pmap logs
    pmapDumpThread = threading.Thread(target = save_process_logs, args = (gateway.clientSsh,), name = "PmapLogDump")
    pmapDumpThread.start()

    # Get the processes using the most memory
    mostMemoryProcessesThread = threading.Thread(target = save_top_10_memory_usage_processes, args = (gateway.clientSsh,), name = "MostMemoryProcesses")
    mostMemoryProcessesThread.start()

    # If ISA devices are being tracked, download the database and count ISA devices
    if track_isa:
        # Download the database from the gateway
        gateway.download_db_file("/var/tmp/Monitor_Host.db3")

        # Open the database and count the devices based on status
        isa_devices_all = gateway.get_isa_devices("Monitor_Host.db3")
        isa_devices = isa_devices_all["Joined Configured"]

    # If HART devices are being tracked, wait until the web scraping thread has finished
    if scraperThread != None:
        scraperThread.join()
    
    # Wait for any other threads to finish before continuing
    memoryUsageThread.join()
    cpuUsageThread.join()

    # Get the current memory utilization and record only the first three lines
    _stdin, stdout, _stderr = gateway.clientSsh.exec_command("cat /proc/meminfo")
    line_count = 0
    memory_data = ""

    for line in stdout.readlines():
        # Only record the first three lines displayed which give relevant memory usage
        if line_count < 3:
            memory_data += ("," + remove_non_numbers(line))
        else:
            break
        line_count += 1
    
    # Create the line written to the CSV file by adding on the date/time and number of ISA devices
    csv_line = datetime.now().strftime("%x %X") + "," + str(hart_devices) + "," + str(isa_devices) + "," + str(hart_devices + isa_devices) + memory_data + "," + str(cpu_usage)
    for usage in memory_usages:
        csv_line += ("," + str(usage))
    csv_line += "\n"

    # Write the data to the CSV file
    with open(filename, "a") as result_file:
        result_file.write(csv_line)
    
    # Wait for the log dumping threads to finish
    pmapDumpThread.join()
    mostMemoryProcessesThread.join()
    
    print("Wrote \"" + csv_line[0:-1] + "\" at " + datetime.now().strftime("%x %X"))
    
    # Indicate that the thread is finished working on data
    manipulating_data = False

    # Start a new thread for the next scheduled data recording
    recordingThread = threading.Timer(measurement_interval, record_data, args = (filename, gateway, scraper, measurement_interval, track_hart, track_isa))
    recordingThread.daemon = True
    recordingThread.name = "DataRecording"
    recordingThread.start()


def main():
    global folder
    
    folder = filename.split(".csv")[0]
    filename = folder + "/" + filename

    if not(os.path.exists(folder)):
        os.mkdir(folder)
    
    # Establish the SSH/SCP connections
    gateway = IsaDeviceCounter(hostname = hostname, username = username, password = password)

    # Create the GwDeviceCounter object and connect to the gateway
    scraper = None
    if track_hart:
        scraper = GwDeviceCounter(hostname = hostname, user = web_username, password = web_password, supports_isa = True, factory_enabled = True, open_devices = False)
    
    # Register the processes to track with the gateway
    gateway.clientSsh.register_processes(processes_to_track)
    
    # Write the header row for the recorded data
    with open(filename, "w") as result_file:
        header_line = "Date and Time,HART Devices,ISA Devices,All Devices,Total Mem (kB),Free Mem (kB),Avail Mem (kB),CPU Usage (%)"

        for process in gateway.clientSsh.processes:
            header_line += ("," + process)
        
        header_line += "\n"

        result_file.write(header_line)

    # Create a new thread for polling the database, getting memory usage stats, and writing results
    # Since the thread is a daemon, it will be automatically stopped once the user exits in the main thread
    recordingThread = threading.Thread(target = record_data, name = "DataRecording", args = (filename, gateway, scraper, measurement_interval, track_hart, track_isa), daemon = True)
    recordingThread.start()
    
    # Wait until manipulating_data is False to safely quit
    if manipulating_data:
        print("Waiting for data recording operation to finish")
    while manipulating_data:
        continue

    if scraper is not None:
        scraper.close()
    
    # Create a plot of the data after determine which devices to plot
    device_type_list = []
    # if track_hart:
    #     device_type_list.append(1)
    # if track_isa:
    #     device_type_list.append(2)
    # if track_hart and track_isa:
    #     device_type_list.append(3)

    print("Generating plots...")

    plot_csv_memory_file(filename, range(4, 7), device_type_list, range(1, 7), \
        axis_1_label = "Memory (kB)", axis_2_label = "Number of Devices", x_label = "Time", show_plot = False)

    print("Plots generated")

    # Close the SSH/SCP connection
    gateway.close()

    print("Program Finished")


if __name__ == "__main__":
    main()

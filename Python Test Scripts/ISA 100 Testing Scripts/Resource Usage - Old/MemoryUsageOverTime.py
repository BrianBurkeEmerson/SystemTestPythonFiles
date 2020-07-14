# This test periodically checks the status of the gateway and its ISA devices
# A CSV file is created where each periodic check adds a new line in the following format
# Date/Time, Number of Connected ISA Devices, Total Memory, Free Memory, Available Memory

# Execution can be set to run for a certain amount of time or it can be set to be manually stopped by typing "quit"

# py -m pip install paramiko
# py -m pip install scp

import sys
import os
import time
import threading
import tkinter as tk
import tkinter.filedialog as fd
from datetime import datetime
from getpass import getpass
from configparser import ConfigParser

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../ISADeviceCount")
from ISADeviceCount import IsaDeviceCounter

CONFIG_FILE_NAME = "Options_MemoryUsageOverTime.ini"

manipulating_data = False # Tracks whether the secondary thread is downloading/processing/recording data to prevent corruption

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


def record_data(filename, gateway = None, measurement_interval = 10):
    manipulating_data = True # Indicate the thread is running and working on data

    # Download the database from the gateway
    gateway.download_db_file("/var/tmp/Monitor_Host.db3")

    # Open the database and count the devices based on status
    devices = gateway.get_isa_devices("Monitor_Host.db3")
    devices_found = devices["Joined Configured"]

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
    csv_line = datetime.now().strftime("%x %X") + "," + str(devices_found) + memory_data + "\n"

    # Write the data to the CSV file
    with open(filename, "a") as result_file:
        result_file.write(csv_line)
    
    # Indicate that the thread is finished working on data
    manipulating_data = False

    # Start a new thread for the next scheduled data recording
    recordingThread = threading.Timer(measurement_interval, record_data, args = (filename, gateway, measurement_interval))
    recordingThread.daemon = True
    recordingThread.name = "DataRecording"
    recordingThread.start()


def main():
    # Create a dictionary for the various options
    options = {}

    # Create a parser that can handle INI files
    config = ConfigParser()

    # If no config file exists, create a new default one
    if not(os.path.isfile(CONFIG_FILE_NAME)):
        config["General"] = {
            "UseSettingsFromConfigFile" : "no" # Whether the settings stored in the config file should be used
        }
        config["Gateway"] = {
            "Hostname" : "192.168.1.10",
            "Username" : "root",
            "Password" : "emerson1"
        }
        config["DataRecording"] = {
            "UseTimeLimit" : "no", # If set to no, user manually stops test
            "TimeLimit" : "600", # Time limit for test in seconds
            "MeasurementInterval" : "60" # How long between measurements
        }
        config["Files"] = {
            "UseAutomaticFilename" : "no" # If set to yes, the filename is automatically generated based on when the test started
        }

        # Write the config file
        with open(CONFIG_FILE_NAME, "w") as config_file:
            config.write(config_file)
    
    # Read the options from the config file
    config.read(CONFIG_FILE_NAME)
    for section in config.sections():
        for item in config.items(section):
            options[item[0]] = item[1]
    
    # Create the variables used for configuring the test
    hostname = ""
    username = ""
    password = ""
    use_time_limit = False
    time_limit = 0
    measurement_interval = 0
    filename = ""
    
    if options["UseSettingsFromConfigFile".lower()] == "yes":
        hostname = options["Hostname".lower()]
        username = options["Username".lower()]
        password = options["Password".lower()]
        use_time_limit = options["UseTimeLimit".lower()] == "yes"
        time_limit = int(options["TimeLimit".lower()])
        measurement_interval = int(options["MeasurementInterval".lower()])
    else:
        # Ask for the gateway hostname, username, and password
        hostname = input("Enter the gateway hostname: ")
        username = input("Enter the username: ")
        password = getpass("Enter the password (no echo): ")

        # Ask whether the user wants to use a time limit, a set number of measurements, or manually stop the test
        print("1. Set test time limit")
        print("2. Stop test manually")
        use_time_limit = verify_int_input_option((1, 2), "Select 1 or 2: ") == 1

        # Ask the user for the time limit if they want to use it
        if use_time_limit:
            time_limit = verify_int_input_range(lower_bound = 60, use_upper_bound = False, prompt = "Enter how long (in seconds) the test should run for: ")
        
        # Ask the user for the time between measurements
        measurement_interval = verify_int_input_range(lower_bound = 10, use_upper_bound = False, prompt = "Enter how long (in seconds) between measurements: ")

    # Ask the user where results should be saved
    if (options["UseSettingsFromConfigFile".lower()] == "no") or (options["UseAutomaticFilename".lower()] == "no"):
        print("Choose a filename and location in the pop-up window")
        root = tk.Tk()
        filename = fd.asksaveasfilename(confirmoverwrite = True, defaultextension = ".csv", title = "Enter a Name for the Data File", filetypes = (("CSV Files", ".csv"), ("All Files","*")))
        root.destroy()
    else:
        filename = datetime.now().strftime("%a %d %B %Y - %I-%M-%S %p Memory Usage.csv")

    # Write the header row for the recorded data
    with open(filename, "w") as result_file:
        result_file.write("Date and Time,Number of Active ISA Devices,Total Memory (kB),Free Memory (kB),Available Memory (kB)\n")
    
    # Establish the SSH/SCP connections
    gateway = IsaDeviceCounter(hostname = hostname, username = username, password = password)

    # Create a new thread for polling the database, getting memory usage stats, and writing results
    # Since the thread is a daemon, it will be automatically stopped once the user exits in the main thread
    recordingThread = threading.Thread(target = record_data, name = "DataRecording", args = (filename, gateway, measurement_interval), daemon = True)
    recordingThread.start()

    print("Test Started")

    # After starting the other thread, use the main thread to determine when the program quits
    if use_time_limit:
        time.sleep(time_limit)
    else:
        quit_input = ""
        while quit_input != "quit":
            quit_input = input("Type \"quit\" to stop data logging: ").lower()
    
    # Wait until manipulating_data is False to safely quit
    while manipulating_data:
        continue

    # Close the SSH/SCP connection
    gateway.close()


if __name__ == "__main__":
    main()

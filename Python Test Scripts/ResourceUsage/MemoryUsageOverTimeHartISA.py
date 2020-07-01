# This test periodically checks the status of the gateway and its HART/ISA devices
# A CSV file is created where each periodic check adds a new line in the following format
# Date/Time, Number of Connected ISA Devices, Total Memory, Free Memory, Available Memory

# Execution can be set to run for a certain amount of time or it can be set to be manually stopped by typing "quit"

# py -m pip install paramiko
# py -m pip install scp
# py -m pip install selenium

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

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../Gateway Web Scraping Tools/gw_device_count")
from gw_device_count import GwDeviceCounter



CONFIG_FILE_NAME = "Options_MemoryUsageOverTime.ini"

manipulating_data = False # Tracks whether the secondary thread is downloading/processing/recording data to prevent corruption

# Initialize variables for counting the number of devices
isa_devices = 0
hart_devices = 0



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


def count_live_hart_devices(scraper):
    global hart_devices

    scraper.open()
    hart_devices = scraper.get_live_devices_count()["HART"]
    scraper.close()


def record_data(filename, gateway, scraper, measurement_interval, track_hart, track_isa):
    global manipulating_data
    global isa_devices
    global hart_devices

    manipulating_data = True # Indicate the thread is running and working on data

    # If HART devices are being tracked, start the web scraper on a separate thread
    scraperThread = None
    if track_hart:
        scraperThread = threading.Thread(target = count_live_hart_devices, args = (scraper,), name = "HartWebScraper")
        scraperThread.start()
    
    # If ISA devices are being tracked, download the database and count ISA devices
    if track_isa:
        # Download the database from the gateway
        gateway.download_db_file("/var/tmp/Monitor_Host.db3")

        # Open the database and count the devices based on status
        isa_devices_raw = gateway.get_isa_devices("Monitor_Host.db3")
        isa_devices = isa_devices_raw["Joined Configured"]

    # If HART devices are being tracked, wait until the web scraping thread has finished
    if scraperThread != None:
        scraperThread.join()

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
    csv_line = datetime.now().strftime("%x %X") + "," + str(hart_devices) + "," + str(isa_devices) + "," + str(hart_devices + isa_devices) + memory_data + "\n"

    # Write the data to the CSV file
    with open(filename, "a") as result_file:
        result_file.write(csv_line)
    
    # Indicate that the thread is finished working on data
    manipulating_data = False

    # Start a new thread for the next scheduled data recording
    recordingThread = threading.Timer(measurement_interval, record_data, args = (filename, gateway, scraper, measurement_interval, track_hart, track_isa))
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
        config["WebBrowser"] = {
            "WebUsername" : "admin",
            "WebPassword" : "default"
        }
        config["DataRecording"] = {
            "UseTimeLimit" : "no", # If set to no, user manually stops test
            "TimeLimit" : "600", # Time limit for test in seconds
            "MeasurementInterval" : "60", # How long between measurements
            "TrackHART" : "yes", # If set to yes, the program records the number of connected HART devices (adds extra time)
            "TrackISA" : "yes" # If set to yes, the program records the number of connected ISA devices
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
    web_username = ""
    web_password = ""
    track_hart = True
    track_isa = True

    # Check whether to used the saved settings
    if options["UseSettingsFromConfigFile".lower()] == "yes":
        hostname = options["Hostname".lower()]
        username = options["Username".lower()]
        password = options["Password".lower()]
        use_time_limit = options["UseTimeLimit".lower()] == "yes"
        time_limit = int(options["TimeLimit".lower()])
        measurement_interval = int(options["MeasurementInterval".lower()])
        web_username = options["WebUsername".lower()]
        web_password = options["WebPassword".lower()]
        track_hart = options["TrackHART".lower()] != "no"
        track_isa = options["TrackISA".lower()] != "no"
    else:
        # Ask if the user wants to track HART, ISA, or both
        print("1. Track HART devices only")
        print("2. Track ISA devices only")
        print("3. Track HART and ISA devices")
        tracking = verify_int_input_option((1, 2, 3), "Select 1, 2, or 3: ")

        # Convert tracking option to set booleans (note that they are both already set to True)
        if tracking == 1:
            track_isa = False
        elif tracking == 2:
            track_hart = False
        
        # Ask for the gateway SSH hostname, username, and password
        hostname = input("Enter the gateway hostname: ")
        if track_isa:
            username = input("Enter the SSH username: ")
            password = getpass("Enter the SSH password (no echo): ")
        
        # Ask for the gateway webpage username and password
        if track_hart:
            web_username = input("Enter the webpage username: ")
            web_password = getpass("Enter the webpage password (no echo): ")

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
        result_file.write("Date and Time,Number of Active HART Devices,Number of Active ISA Devices,Total Active Devices,Total Memory (kB),Free Memory (kB),Available Memory (kB)\n")
    
    # Establish the SSH/SCP connections
    gateway = IsaDeviceCounter(hostname = hostname, username = username, password = password)

    # Create the GwDeviceCounter object and connect to the gateway
    scraper = GwDeviceCounter(hostname = hostname, user = web_username, password = web_password, supports_isa = True, factory_enabled = True, open_devices = False)

    # Create a new thread for polling the database, getting memory usage stats, and writing results
    # Since the thread is a daemon, it will be automatically stopped once the user exits in the main thread
    recordingThread = threading.Thread(target = record_data, name = "DataRecording", args = (filename, gateway, scraper, measurement_interval, track_hart, track_isa), daemon = True)
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
    if manipulating_data:
        print("Waiting for data recording operation to finish")
    while manipulating_data:
        continue

    # Close the SSH/SCP connection
    gateway.close()


if __name__ == "__main__":
    main()

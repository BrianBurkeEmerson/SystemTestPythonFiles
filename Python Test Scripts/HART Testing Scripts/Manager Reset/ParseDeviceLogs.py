import os
from datetime import datetime

def parse_device_logs(folder):
    devices = {}

    # Go through each log starting with those in the nwconsole folder
    for log_file in os.listdir(folder + "/nwconsole"):
        device_mac = log_file.split(".")[0] # Get the filename before the .txt
        devices[device_mac] = {}

        with open(folder + "/nwconsole/" + log_file, "r") as f:
            lines = f.read().splitlines()

            for line in lines:
                end_index = line.find("$") - 1
                unix_timestamp = float(line[:end_index])
                dict_entry = "Null"

                # Determine what the data is based off the message and store the raw datetime object in the dictionary
                if "Test Started" in line:
                    dict_entry = "Start Time"
                elif "changed state to Negot1" in line:
                    dict_entry = "Negot1 Time"
                elif "changed state to Negot2" in line:
                    dict_entry = "Negot2 Time"
                elif "changed state to Conn" in line:
                    dict_entry = "Conn Time"
                elif "changed state to Oper" in line:
                    dict_entry = "Oper Time"
                
                # Write the dictionary entry
                devices[device_mac][dict_entry] = datetime.fromtimestamp(unix_timestamp)
            
            # Calculate the time differences
            for wait in ("Negot1", "Negot2", "Conn", "Oper"):
                try:
                    delta = devices[device_mac][wait + " Time"] - devices[device_mac]["Start Time"]
                    hours = divmod(delta.seconds, 3600)
                    minutes, hours = hours[1], hours[0]
                    minutes = divmod(minutes, 60)
                    seconds, minutes = minutes[1], minutes[0]

                    devices[device_mac][wait + " Wait"] = [hours, minutes, seconds]
                except:
                    devices[device_mac][wait + " Wait"] = [-1, -1, -1]
            
            # TODO: Manage hartserver files to get publishing time and write results to file

parse_device_logs("C:/Users/E1337077/Emerson/Wireless Test - Documents/InProgressProjects/ContinuingEngineering/EternaIntoLegacy/2160/ManagerReset/toc0 - Tue 01 September 2020 - 01-33-31 PM")

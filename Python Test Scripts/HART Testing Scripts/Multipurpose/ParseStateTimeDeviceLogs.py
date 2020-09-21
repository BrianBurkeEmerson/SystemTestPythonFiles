import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../ISA 100 Testing Scripts/ISADeviceCount")
from ISADeviceCount import DEVICE_STATUS_IDS

def parse_device_logs(folder):
    return parse_hart_device_logs(folder), parse_isa_device_logs(folder)


def parse_hart_device_logs(folder):
    devices = {}

    # Go through each log in the nwconsole and hartserver folders
    mac_id_pairs = {}
    for subfolder in ("nwconsole", "hartserver"):
        for log_file in os.listdir(folder + "/" + subfolder):
            device_mac = log_file.split(".")[0] # Get the filename before the .txt

            # Check if the mote ID is in the filename as well
            try:
                device_mac = device_mac.split("$")[1]
                device_id = log_file.split("$")[0]
                mac_id_pairs[device_mac] = device_id
            except:
                pass

            if device_mac not in devices:
                devices[device_mac] = {}

            with open(folder + "/" + subfolder + "/" + log_file, "r") as f:
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
                    elif "is Responding" in line:
                        dict_entry = "Publish Time"
                    elif "neighbor flag cleared" in line:
                        dict_entry = "Neighbor Time"
                    
                    # Write the dictionary entry
                    devices[device_mac][dict_entry] = datetime.fromtimestamp(unix_timestamp)
            
    # Calculate the time differences
    for wait in ("Negot1", "Negot2", "Conn", "Oper", "Publish", "Neighbor"):
        for device_mac in devices:
            # Convert the time difference in seconds to hours, minutes, and seconds
            try:
                delta = devices[device_mac][wait + " Time"] - devices[device_mac]["Start Time"]
                hours = divmod(delta.seconds, 3600)
                minutes, hours = hours[1], hours[0]
                minutes = divmod(minutes, 60)
                seconds, minutes = minutes[1], minutes[0]

                devices[device_mac][wait + " Wait"] = [hours, minutes, seconds]
            except:
                devices[device_mac][wait + " Wait"] = [0, 0, 0]
    
    # Write the results to a file
    with open(folder + "/HART.csv", "w") as f:
        f.write("Times in HH:MM:SS Format\n") # Write an infomation line
        f.write("MAC Address,Mote ID,Time to Negot1,Time to Negot2,Time to Conn,Time to Oper,Time to Publish\n") # Write the row headers

        # Iterate through each device
        for device_mac in devices:
            f.write(device_mac)

            if device_mac in mac_id_pairs:
                f.write("," + str(mac_id_pairs[device_mac]))
            else:
                f.write(",NaN")

            # Write the wait times to the CSV file with the proper padding to get HH:MM:SS format
            for wait in ("Negot1", "Negot2", "Conn", "Oper", "Publish"):
                f.write(",")
                hours = str(devices[device_mac][wait + " Wait"][0]).zfill(2)
                minutes = str(devices[device_mac][wait + " Wait"][1]).zfill(2)
                seconds = str(devices[device_mac][wait + " Wait"][2]).zfill(2)
                f.write(hours + ":" + minutes + ":" + seconds)
            
            # Add a newline for the next device
            f.write("\n")
    
    return (folder + "/HART.csv")


def parse_isa_device_logs(folder):
    devices = {}

    # Go through each log in the isa folder
    id_name_pairs = {}
    for log_file in os.listdir(folder + "/isa"):
        if log_file[-4:] != ".txt":
            continue

        device_id = log_file.split("$")[0] # Get the device ID from the filename
        device_name = log_file.split("$")[1].split(".")[0] # Get the device name from the filename

        # Add the name/ID pair to the dictionary and create a blank timing information dictionary for the device
        id_name_pairs[device_id] = device_name
        devices[device_id] = {}

        with open(folder + "/isa/" + log_file, "r") as f:
            lines = f.read().splitlines()

            # Go through each line in the log files and record the time that events happened at
            for line in lines:
                # Use the UNIX timestamp since it's easier to parse
                end_index = line.find("$") - 1
                unix_timestamp = float(line[:end_index])

                # By default, write the latest time into a "Null" entry which won't be used if it doesn't correspond to one of the possible states
                dict_entry = "Null"

                # Check if the line indicates the start of the test
                if "Test Started" in line:
                    dict_entry = "Start Time"

                # Check if the line contains any of the valid states and set the dictionary entry
                for _state_num, state_name in DEVICE_STATUS_IDS.items():
                    if state_name in line:
                        dict_entry = state_name + " Time"

                # Write the dictionary entry
                devices[device_id][dict_entry] = datetime.fromtimestamp(unix_timestamp)
    
    # Calculate the time differences
    for _state_num, state_name in DEVICE_STATUS_IDS.items():
        for device_id in devices:
            # Convert the time difference in seconds to hours, minutes, and seconds
            try:
                delta = devices[device_id][state_name + " Time"] - devices[device_id]["Start Time"]
                hours = divmod(delta.seconds, 3600)
                minutes, hours = hours[1], hours[0]
                minutes = divmod(minutes, 60)
                seconds, minutes = minutes[1], minutes[0]

                devices[device_id][state_name + " Wait"] = [hours, minutes, seconds]
            except:
                devices[device_id][state_name + " Wait"] = [0, 0, 0]

    # Write the results to a file
    with open(folder + "/ISA100.csv", "w") as f:
        f.write("Times in HH:MM:SS Format\n") # Write an infomation line

        # Write the row headers in order
        f.write("Device ID,Device Name")
        state_nums = sorted(DEVICE_STATUS_IDS)
        for i in state_nums:
            f.write("," + str(DEVICE_STATUS_IDS[i]))
        f.write("\n")

        # Iterate through each device
        for device_id in devices:
            f.write(device_id)

            if device_id in id_name_pairs:
                f.write("," + str(id_name_pairs[device_id]))
            else:
                f.write(",---")

            # Write the wait times to the CSV file with the proper padding to get HH:MM:SS format
            for i in state_nums:
                wait = DEVICE_STATUS_IDS[i]
                f.write(",")
                hours = str(devices[device_id][wait + " Wait"][0]).zfill(2)
                minutes = str(devices[device_id][wait + " Wait"][1]).zfill(2)
                seconds = str(devices[device_id][wait + " Wait"][2]).zfill(2)
                f.write(hours + ":" + minutes + ":" + seconds)
            
            # Add a newline for the next device
            f.write("\n")

    return (folder + "/ISA100.csv")


if __name__ == "__main__":
    print(__file__.replace("\\","/"))

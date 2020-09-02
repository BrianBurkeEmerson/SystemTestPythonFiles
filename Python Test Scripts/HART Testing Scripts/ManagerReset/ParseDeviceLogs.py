import os
from datetime import datetime

def parse_device_logs(folder):
    devices = {}

    # Go through each log in the nwconsole and hartserver folders
    for subfolder in ("nwconsole", "hartserver"):
        for log_file in os.listdir(folder + "/" + subfolder):
            device_mac = log_file.split(".")[0] # Get the filename before the .txt

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
                    
                    # Write the dictionary entry
                    devices[device_mac][dict_entry] = datetime.fromtimestamp(unix_timestamp)
            
    # Calculate the time differences
    for wait in ("Negot1", "Negot2", "Conn", "Oper", "Publish"):
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
    with open(folder + "/DeviceTimeInfo.csv", "w") as f:
        f.write("Times in HH:MM:SS Format\n") # Write an infomation line
        f.write("MAC Address,Time to Negot1,Time to Negot2,Time to Conn,Time to Oper,Time to Publish\n") # Write the row headers

        # Iterate through each device
        for device_mac in devices:
            f.write(device_mac)

            # Write the wait times to the CSV file with the proper padding to get HH:MM:SS format
            for wait in ("Negot1", "Negot2", "Conn", "Oper", "Publish"):
                f.write(",")
                hours = str(devices[device_mac][wait + " Wait"][0]).zfill(2)
                minutes = str(devices[device_mac][wait + " Wait"][1]).zfill(2)
                seconds = str(devices[device_mac][wait + " Wait"][2]).zfill(2)
                f.write(hours + ":" + minutes + ":" + seconds)
            
            # Add a newline for the next device
            f.write("\n")
    
    return (folder + "/DeviceTimeInfo.csv")

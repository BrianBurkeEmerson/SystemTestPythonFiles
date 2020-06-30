# py -m pip install paramiko
# py -m pip install scp

import sys
import os
import time
from datetime import datetime
import smtplib, ssl
from email.message import EmailMessage
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../ISADeviceCount")

from ISADeviceCount import IsaDeviceCounter

DELAY_BETWEEN_LOOPS_SECONDS = 60
RESULTS_FILE = "ResourceUsage.txt"

##############################################################
# Create the email information
gmail_user = "mrUTeCFGjm@gmail.com"
gmail_password = "uLf7xcSYYur2wc4"

msg = EmailMessage()
msg["Subject"] = "Automation: Rack Finished"
msg["From"] = gmail_user
msg["To"] = input("Enter the email to send status messages to: ")

context = ssl.create_default_context()
##############################################################

# Define a list with the number of devices that will be connected after turning on each rack
# For instance, if there are 20 devices on each rack, the list would be [20, 40, 60, ...]
device_count_list = [24, 48]#, 72, 96, 120]

# Write some blank lines to make separating tests easier
with open(RESULTS_FILE, "a") as results:
    results.write("\n\n\n\n\n")

# Create the SSH and SCP connections
gateway = IsaDeviceCounter(hostname = "systestdual", port = 22, username = "root", password = "emerson1")

# Iterate and loop on each rack until all devices join
# Then take a reading from the TOP command write it to a file
for rack in range(len(device_count_list)):
    devices_found = 0

    # Wait for the user to press enter before starting next rack (gives them a chance to power on next devices)
    input("Press enter after turning on the next rack")
    print("Starting rack " + str(rack))

    # Write a message indicating the start of a rack test
    with open(RESULTS_FILE, "a") as results:
        results.write("\nRack " + str(rack) + " started at " + str(datetime.now()) + "\n")

    while devices_found < device_count_list[rack]:
        # Start with a delay since it takes a significant amount of time for devices to join
        time.sleep(DELAY_BETWEEN_LOOPS_SECONDS)

        # Download the database from the gateway
        gateway.download_db_file("/var/tmp/Monitor_Host.db3")

        # Open the database and count the devices based on status
        devices = gateway.get_isa_devices("Monitor_Host.db3")
        devices_found = devices["Joined Configured"]
    
    # Once all devices on a rack have joined, take a reading of resource utilization with the TOP command write it to a file
    stdin, stdout, stderr = gateway.clientSsh.exec_command("top -n1 -b -i")

    # Write the lines from stdout to the results log file
    with open(RESULTS_FILE, "a") as results:
        # Timestamp the end of the test
        results.write("Rack " + str(rack) + " finished at " + str(datetime.now()) + "\n")

        # Write each line of top to the file
        for line in stdout.readlines():
            results.write(line)
    
    # Send an email notification that the rack is finished
    if msg["To"] != "":
        with smtplib.SMTP("smtp.gmail.com", port = 587) as smtp:
            msg.set_content("Rack " + str(rack) + " finished at " + str(datetime.now()) + ".\n\nPlease start next rack.")
            smtp.starttls(context = context)
            smtp.login(gmail_user, gmail_password)
            smtp.send_message(msg)
    
# Close the connections
gateway.close()

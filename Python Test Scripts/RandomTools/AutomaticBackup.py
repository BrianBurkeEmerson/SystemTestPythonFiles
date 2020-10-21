import os
import sys
import time
import json
import requests
import threading
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../Gateway Web Scraping Tools/GwDeviceCount")
import GwDeviceCount as gdc


CONFIG_FILE = "config.json"


def automatic_backup(hostname, backup_folder, backup_interval, supports_isa, password):
    # Create a folder for the gateway's backups
    if not os.path.exists(backup_folder):
        os.mkdir(backup_folder)

    # Open a browser to the settings page
    browser = gdc.GwDeviceCounter(hostname, supports_isa = supports_isa)
    browser.open_settings_page()

    # Open the backup page within the settings
    time.sleep(1)
    browser.open_backup_menu()

    # Create a backup and wait for it to finish
    time.sleep(1)
    browser.start_save_backup(password)
    browser.wait_for_backup_to_finish()

    # Create a filename based on the hostname and current time before downloading the file
    now = datetime.now()
    new_filename = now.strftime("%m-%d-%Y at %H-%M-%S")
    new_filename = hostname + " - " + new_filename + ".zip"
    browser.download_backup(backup_folder + "\\" + new_filename)

    # Close the browser
    browser.close()

    # Schedule the next backup
    time.sleep(backup_interval)
    threading.Thread(target = automatic_backup, args = (hostname, backup_folder, backup_interval, supports_isa, password), daemon = True).start()


config = {}

# Create a config if one does not exist
if not os.path.exists(CONFIG_FILE):
    config["Gateways"] = []
    config["BackupIntervalInSeconds"] = 60 * 60 # Default to one backup every hour
    config["SupportsISA100"] = False
    config["BackupPassword"] = "default1"
    with open(CONFIG_FILE, "w") as f:
        f.write(json.dumps(config, indent = 4))

# Read the config from the file
with open(CONFIG_FILE, "r") as f:
    config = json.loads(f.read())

# Start threads for each gateway
for gateway in config["Gateways"]:
    threading.Thread(target = automatic_backup, args = (gateway, gateway, config["BackupIntervalInSeconds"], config["SupportsISA100"], config["BackupPassword"]), daemon = True).start()

# When the user types "quit" then the program will exit
while input("Type \"quit\" to stop program: ").lower() != "quit":
    continue

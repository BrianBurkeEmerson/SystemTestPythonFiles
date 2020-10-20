import os
import sys
import time
import json
import threading
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../Gateway Web Scraping Tools/GwDeviceCount")
import GwDeviceCount as gdc


CONFIG_FILE = "config.json"


def automatic_backup(hostname, backup_folder, backup_interval, supports_isa, password):
    save_location = os.getcwd() + "\\" + backup_folder

    # Create a folder for the gateway's backups
    if not os.path.exists(backup_folder):
        os.mkdir(backup_folder)

    # Open a browser to the settings page
    browser = gdc.GwDeviceCounter(hostname, supports_isa = supports_isa, change_download_settings = True, default_download_location = save_location)
    browser.open_settings_page()

    # Open the backup page within the settings
    time.sleep(1)
    browser.open_backup_menu()

    # Create a backup, wait for it to finish, and download it
    time.sleep(1)
    browser.start_save_backup(password)
    browser.wait_for_backup_to_finish()
    browser.download_backup()

    # Wait until the download finishes
    downloaded_file = save_location + "\\system_backup.zip"
    while (not os.path.exists(downloaded_file)) or (os.path.exists(downloaded_file + ".part")):
        continue

    # Rename the file based on the hostname and current time
    now = datetime.now()
    new_filename = now.strftime("%H-%M-%S on %m-%d-%Y")
    new_filename = hostname + " - " + new_filename + ".zip"
    os.rename(downloaded_file, save_location + "\\" + new_filename)

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

while input("Type \"quit\" to stop program: ").lower() != "quit":
    continue

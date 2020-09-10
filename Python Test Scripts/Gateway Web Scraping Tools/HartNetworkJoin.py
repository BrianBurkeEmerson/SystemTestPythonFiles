from GwDeviceCount.GwDeviceCount import GwDeviceCounter
import GwDeviceCount.GwDeviceCount as gdc
import time
import threading
from datetime import datetime

# The number of devices joining and responding that is acceptable for passing the test
EXPECTED_NUM_DEVICES = 220

# The file where results are stored
RESULTS_FILE = "HartNetworkJoinResults.txt"

# Called periodically on a new thread to see if the devices are all joined and responding
def check_device_statuses(gateway):
    # Open a browser to the devices page
    gateway.open()

    # Change to live tab
    gateway.change_device_tab(gdc.LIVE_DEVICES_SPAN)

    # Get the Name and PV fields
    data = gateway.convert_table_into_dicts(device_type = "HART", fields = (gdc.TABLE_NAME_FIELD, gdc.TABLE_PV_FIELD))

    # Create variables to track the types of live devices
    devices = {
        "connected" : 0,
        "operational" : 0,
        "responding" : 0
    }

    for device in data:
        # If the device is live but contains --- UNKNOWN ---, then it is only connected
        if device[gdc.TABLE_NAME_FIELD].find("--- UNKNOWN ---") > -1:
            devices["connected"] += 1

        # Otherwise the device is connected and operational or responding
        else:
            # If the PV field is blank, then the device is only operational
            if device[gdc.TABLE_PV_FIELD] == "":
                devices["operational"] += 1

            # Otherwise the device is sending data and is responding
            else:
                devices["responding"] += 1

    msg = str(datetime.now()) + "\nConnected: " + str(devices["connected"] + "\nOperational: " + str(devices["operational"]) + "\nResponding: " + str(devices["responding"]) + "\n")
    print(msg)

    # Write the message to the results file
    with open(RESULTS_FILE, "a") as results:
        results.write(msg)

    # Close the browser
    gateway.close()

    # Finally, create a new thread to schedule the next check if not all devices have joined
    if devices["responding"] < EXPECTED_NUM_DEVICES:
        threading.Timer(600, check_device_statuses, args = (gateway,)).start()
    else:
        print("All devices joined. Exiting...")


def main():
    # Create the GwDeviceCounter object and connect to the gateway
    gateway = GwDeviceCounter( \
        hostname = "1410s-charlie", supports_isa = True, open_devices = False)

    # Start the checking thread
    check_device_statuses(gateway)


if __name__ == "__main__":
    main()

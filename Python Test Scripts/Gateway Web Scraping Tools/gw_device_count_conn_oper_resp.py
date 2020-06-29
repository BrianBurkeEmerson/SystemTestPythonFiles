# This example shows how to get information about live devices from the webpage table
# Then the data is processed to determine which devices are connected, operational, and responding

from gw_device_count.gw_device_count import GwDeviceCounter
import gw_device_count.gw_device_count as gdc
import time

# Create the GwDeviceCounter object and connect to the gateway
gateway = GwDeviceCounter( \
    hostname = "1410s-charlie", user = "admin", password = "default", supports_isa = True, factory_enabled = True)

# Change to live tab
gateway.change_device_tab(gdc.LIVE_DEVICES_SPAN)

# Get the Name and PV fields
data = gateway.convert_table_into_dicts(fields = (gdc.TABLE_NAME_FIELD, gdc.TABLE_PV_FIELD))

# Create variables to track the types of live devices
connected_state = 0
operational_state = 0
responding_state = 0

for device in data:
    # If the device is live but contains --- UNKNOWN ---, then it is only connected
    if device[gdc.TABLE_NAME_FIELD].find("--- UNKNOWN ---") > -1:
        connected_state += 1

    # Otherwise the device is connected and operational or responding
    else:
        # If the PV field is blank, then the device is only operational
        if device[gdc.TABLE_PV_FIELD] == "":
            operational_state += 1

        # Otherwise the device is sending data and is responding
        else:
            responding_state += 1

print("Connected: " + str(connected_state))
print("Operational: " + str(operational_state))
print("Responding: " + str(responding_state))

# Close the browser
gateway.close()

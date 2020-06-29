from gw_device_count.gw_device_count import GwDeviceCounter
import gw_device_count.gw_device_count as gdc
import time

# Create the GwDeviceCounter object and connect to the gateway
gateway = GwDeviceCounter( \
    hostname = "1410s-charlie", user = "admin", password = "default", supports_isa = True, factory_enabled = True)

# Change to live tab
gateway.change_device_tab(gdc.LIVE_DEVICES_SPAN)

# Get the Name and PV fields
print(gateway.convert_table_into_dicts(fields = (gdc.TABLE_NAME_FIELD, gdc.TABLE_PV_FIELD)))

# Close the browser
gateway.close()

from gw_device_count.gw_device_count import GwDeviceCounter
import time

# Create the GwDeviceCounter object and connect to the gateway
gateway = GwDeviceCounter( \
    hostname = "1410s-charlie", user = "admin", password = "default", supports_isa = True, factory_enabled = True)

# Get every type of count and print them to the console
#print(gateway.get_every_type_devices_count())
time.sleep(1)
a = gateway.count_hart_device_types()

print(a)

# Close the browser
gateway.close()

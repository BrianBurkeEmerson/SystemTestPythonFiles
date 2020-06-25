from gw_device_count.gw_device_count import GwDeviceCounter

# Create the GwDeviceCounter object and connect to the gateway
gateway = GwDeviceCounter( \
    hostname = "192.168.1.10", user = "admin", password = "default", supports_isa = False, factory_enabled = True)

# Get every type of count and print them to the console
print(gateway.get_every_type_devices_count())

# Close the browser
gateway.close()
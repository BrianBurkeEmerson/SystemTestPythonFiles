from GwDeviceCount.GwDeviceCount import GwDeviceCounter

# Create the GwDeviceCounter object and connect to the gateway
gateway = GwDeviceCounter( \
    hostname = "rosemount1", user = "admin", password = "default", \
    supports_isa = False, factory_enabled = True, old_login_fields = True)

# Get every type of count and print them to the console
print(gateway.get_every_type_devices_count())

# Close the browser
gateway.close()

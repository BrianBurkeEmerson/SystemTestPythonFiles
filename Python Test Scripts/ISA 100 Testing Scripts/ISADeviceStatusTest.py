# This is an example of how to use ISADeviceCount.py's IsaDeviceCounter class to download
# an ISA database file from a gateway and read the device statuses

from ISADeviceCount.ISADeviceCount import IsaDeviceCounter

# Create the SSH and SCP connections
gateway = IsaDeviceCounter(hostname = 'systestdual', port = 22, username = 'root', password = 'emerson1')

# Download the database from the gateway
gateway.download_db_file("/var/tmp/Monitor_Host.db3")

# Open the database, count the device types, and print each count to the console
devices = gateway.get_isa_devices("Monitor_Host.db3")
for entry in devices:
    print(str(entry) + ": " + str(devices[entry]))

# Close the connections
gateway.close()

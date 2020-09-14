from ISADeviceCount import IsaDeviceCounter
from datetime import datetime
from pprint import pprint

# Create the SSH and SCP connections
gateway = IsaDeviceCounter(hostname = "toc0", port = 22, username = "root", password = "emerson1")

time_1 = datetime.now()

# Download the database from the gateway
gateway.download_db_file("/var/tmp/Monitor_Host.db3")

time_2 = datetime.now()

delta = time_2 - time_1
print(delta)

pprint(gateway.get_device_id_name_pairs("Python/Monitor_Host.db3"))

# Close the connections
gateway.close()

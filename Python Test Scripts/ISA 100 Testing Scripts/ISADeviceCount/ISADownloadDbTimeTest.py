from ISADeviceCount import IsaDeviceCounter
from datetime import datetime

# Create the SSH and SCP connections
gateway = IsaDeviceCounter(hostname = "toc0", port = 22, username = "root", password = "emerson1")

time_1 = datetime.now()

# Download the database from the gateway
gateway.download_db_file("/var/tmp/Monitor_Host.db3")

time_2 = datetime.now()

delta = time_2 - time_1
print(delta)

# Close the connections
gateway.close()

import socket
import sys
import struct
import time
from datetime import datetime
from datetime import timedelta
from pymodbus.client.sync import ModbusTcpClient


def cdba_float_decode(data: list):
    if len(data) > 2:
        raise ValueError("Too many data points")

    hex_string = ""
    for i in [1, 0]:
        part = hex(data[i])[2:].zfill(4)
        hex_string += part

    return struct.unpack("!f", bytes.fromhex(hex_string))[0]


ip = "1410s-charlie"
port = 33333
modbus_port = 502

# Connect via Modbus
client = ModbusTcpClient("1410s-charlie", port = modbus_port)
client.connect()

# Create a list of time deltas between sending the command and the output updating
deltas = []

led_state = 0
client.write_coil(0, led_state)

input("Press enter to start test")

test_start = datetime.now()
old_time, new_time = test_start, test_start

while datetime.now() - test_start < timedelta(minutes = 30):
    old_time = new_time

    # Toggle the LED state between 1 and 0
    led_state = (led_state + 1) % 2

    # Change the LED state
    client.write_coil(0, led_state)

    # Let the user wait until the LED turns on
    input("Press enter when the LED toggles to " + str(led_state))

    # Calculate the time delta
    new_time = datetime.now()
    deltas.append(new_time - old_time)

# resp = client.read_holding_registers(10, 2)
# conv = cdba_float_decode(resp.registers)

# Shut off the LED and close the Modbus connection
client.write_coil(0, 0)
client.close()

# Print each wait time
for delta in deltas:
    print(delta)

# Calculate the average wait time
avg_time = sum(deltas, timedelta(0)) / len(deltas)
print("Average: ", end = "")
print(avg_time)

import time
import sys
import os
from datetime import timedelta
from datetime import datetime
import serial
import threading
from E3647APowerSupply import E3647A


POWER_SUPPLY_PORT = "/dev/ttyS0"
GATEWAY_PORT = "/dev/ttyUSB0"


# Globals
continue_operation = True
state = "Start"
logging_start = datetime.now()
directory = "power_cycle_test"
# POWER_ON_LENGTHS_SECONDS = [0.5, 1, 3, 5, 10, 30, 60, 2 * 60, 5 * 60]
# POWER_ON_LENGTHS_SECONDS = [0.25, 0.75, 2, 4, 7, 20, 45, 3 * 60, 4 * 60, 7 * 60]
POWER_ON_LENGTHS_SECONDS = [0.1, 1.5, 15, 40, 50, 1.5 * 60]
length_i = -1

def power_cycle(port):
    global continue_operation
    global state
    global logging_start
    global directory
    global POWER_ON_LENGTHS_SECONDS
    global length_i

    with E3647A(port) as s:
        while continue_operation:
            if state == "Start":
                length_i += 1
                if length_i >= len(POWER_ON_LENGTHS_SECONDS):
                    continue_operation = False
                    continue

                POWER_ON_LENGTH_SECONDS = POWER_ON_LENGTHS_SECONDS[length_i]

                # Repeat for 10 cycles
                for _ in range(10):
                    s.set_voltage(24, True)
                    s.enable_output()
                    time.sleep(POWER_ON_LENGTH_SECONDS)
                    s.disable_output()

                    time.sleep(1)
                
                s.enable_output()
                logging_start = datetime.now()
                state = "Logging"
            
            elif state == "Shutdown":
                s.disable_output()
                time.sleep(10)
                state = "Start"


def log_serial_output(port):
    global continue_operation
    global state
    global logging_start
    global directory
    global POWER_ON_LENGTHS_SECONDS
    global length_i

    while continue_operation:
        if state == "Logging":
            current_file = directory + "/" + str(POWER_ON_LENGTHS_SECONDS[length_i]) + " Seconds.txt"
            with open(current_file, "w") as f:
                f.write("")

            with serial.Serial(port, 115200, timeout = 1) as s:
                while state == "Logging":
                    resp = ""
                    while True:
                        temp = s.read(1000).decode()
                        resp += temp
                        if temp == "":
                            break

                    if resp != "":
                        with open(current_file, "a") as f:
                            f.write(resp)
                    
                    if "login:" in resp:
                        time.sleep(30)
                        state = "Shutdown"
                        print("Successful boot. Logs written to " + current_file + ".")

                    if (datetime.now() - logging_start) > timedelta(minutes = 15):
                        state = "Shutdown"
                        print("Failed boot. Logs written to " + current_file + ".")
                        with open(directory + "/failed_boots.txt", "a") as f:
                            f.write(current_file + "\n")


with E3647A(POWER_SUPPLY_PORT) as s:
    s.set_voltage(0)
    s.set_current(0)
    s.disable_output()

directory = input("Enter a folder name for log files: ")
if not os.path.exists(directory):
    os.mkdir(directory)

with open(directory + "/failed_boots.txt", "w") as f:
    f.write("")

power_supply_thread = threading.Thread(target = power_cycle, args = (POWER_SUPPLY_PORT,), name = "Power Supply Cycling")
serial_logging_thread = threading.Thread(target = log_serial_output, args = (GATEWAY_PORT,), name = "Serial Logging")

time.sleep(10)

power_supply_thread.start()
serial_logging_thread.start()

power_supply_thread.join()
serial_logging_thread.join()

with E3647A(POWER_SUPPLY_PORT) as s:
    s.disable_output()

print("Finished Test")

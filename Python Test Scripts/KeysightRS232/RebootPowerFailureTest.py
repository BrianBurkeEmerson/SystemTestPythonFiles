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


def write_to_numbered_file(folder, extension = ".txt"):
    if not os.path.exists(folder):
        os.mkdir(folder)
    
    files = os.listdir(folder)

    next_num = -1
    while True:
        next_num += 1

        if (str(next_num).zfill(6) + extension) not in files:
            break
    
    filename = folder + "/" + str(next_num).zfill(6) + extension

    with open(filename, "w") as f:
        f.write("")
    
    return filename


def power_cycle(port):
    global continue_operation
    global state
    global logging_start
    global directory

    with E3647A(port) as s:
        while continue_operation:
            if state == "Start":
                s.set_voltage(24, True)
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

    while continue_operation:
        if state == "Logging":
            current_file = write_to_numbered_file(directory)

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

while input("Enter \"quit\" to stop program: ").lower() != "quit":
    continue

continue_operation = False
state = "Shutdown"

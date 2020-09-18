import os
import sys
import time
import threading
import tkinter as tk
import tkinter.filedialog as fd

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../Multipurpose")
from StateTimeTracker import StateTimeTracker

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../SSHHelper")
from InteractiveSSH import InteractiveSSH

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../ISA 100 Testing Scripts/ISADeviceCount")
from ISADeviceCount import IsaDeviceCounter


HOSTNAME = "1410s-charlie"

use_isa = True

def write_to_numbered_file(folder, subfolder, data, extension = ".txt"):
    if not os.path.exists(folder + "/" + subfolder):
        os.mkdir(folder + "/" + subfolder)
    
    files = os.listdir(folder + "/" + subfolder)

    next_num = -1
    while True:
        next_num += 1

        if (str(next_num).zfill(4) + extension) not in files:
            break
    
    with open(folder + "/" + subfolder + "/" + str(next_num).zfill(4) + extension, "w") as f:
        f.write(data)


def main():
    global HOSTNAME
    global use_isa

    directory = os.getcwd().replace("\\", "/")
    print("\033[93mResults will be stored in " + directory + " unless changed\033[0m")

    if use_isa:
        print("\033[93mISA100 testing turned on\033[0m")
    else:
        print("\033[93mISA100 testing turned off\033[0m")
    
    while True:
        try:
            asyncSsh = InteractiveSSH(HOSTNAME)
            asyncSsh.shell.close()
            asyncSsh.close()
            break
        except:
            print("SSH connection to " + str(HOSTNAME) + " not available. Retrying...")
            time.sleep(1)

    testObj = StateTimeTracker(HOSTNAME)
    testThread = None

    # Enter a loop for executing commands
    cmd = "help"
    while cmd != "quit":
        if (cmd == "short") or (cmd == "life") or (cmd == "cur") or (cmd == "isa"):
            try:
                asyncSsh.safe_send("\n")
            except OSError:
                asyncSsh = InteractiveSSH(HOSTNAME)
                asyncSsh.start_nwconsole()

        if cmd == "help":
            print("help: Show this information")
            print("short: Record \"show stat 0\" and \"show stat 1\"")
            print("life: Record \"show stat life\"")
            print("cur: Record \"show stat cur\"")
            print("isa: Record ISA100 path RSSI statistics")
            print("folder: Select folder where results are stored")
            print("toggle: Toggles testing for ISA100 on/off")
            print("start: Start test if one is not running")
            print("stop: Stop running test if one is active")
            print("quit: Exit this application")
        
        elif cmd == "short":
            data = asyncSsh.show_stat_short(combine_list_to_string = True)
            write_to_numbered_file(directory, "show_stat_short", data)

        elif cmd == "life":
            data = asyncSsh.show_stat_life(combine_list_to_string = True)
            write_to_numbered_file(directory, "show_stat_life", data)

        elif cmd == "cur":
            data = asyncSsh.show_stat_cur(combine_list_to_string = True)
            write_to_numbered_file(directory, "show_stat_cur", data)
        
        elif cmd == "isa":
            dbDownloader = IsaDeviceCounter(HOSTNAME)
            dbDownloader.download_db_file()
            dbDownloader.close()
            rssis = dbDownloader.get_path_rssi()
            id_name = dbDownloader.get_device_id_name_pairs()

            # Compile the RSSIs into a string to be written into a CSV file
            csv_content = "DeviceA,DeviceB,NameA,NameB,RSSI\n"
            for path in rssis:
                moteA = str(path["MoteA"])
                moteB = str(path["MoteB"])
                nameA = str(id_name[int(moteA)])
                nameB = str(id_name[int(moteB)])
                csv_content += (moteA + "," + moteB + "," + nameA + "," + nameB + "," + str(path["ABPower"]) + "\n")
            
            # Write the data into a file
            write_to_numbered_file(directory, "isa_rssis", csv_content, ".csv")

        elif cmd == "folder":
            root = tk.Tk()
            directory = fd.askdirectory()
            root.destroy()
            print("\033[93mTest results will be stored in " + directory + "\033[0m")
        
        elif cmd == "toggle":
            use_isa = not use_isa
            if use_isa:
                print("\033[93mISA100 testing turned on\033[0m")
            else:
                print("\033[93mISA100 testing turned off\033[0m")
        
        elif cmd == "start":
            if testObj.running_test:
                print("\033[91mERROR: Test already running. Stop current test before starting new one.\033[0m")
            else:
                print("Starting logging...")
                testThread = threading.Thread(target = testObj.start, args = (directory, True), name = "Active Test")
                testThread.start()
        
        elif cmd == "stop":
            if testObj.running_test:
                testObj.monitor_log = False
                testThread.join()
                testThread = None
            else:
                print("\033[91mERROR: No test currently running\033[0m")
        
        cmd = input("> ").lower()
    
    # After quit is entered, stop any running tests and quit
    testObj.monitor_log = False
    if testThread != None:
        testThread.join()
    
    asyncSsh.shell.close()
    asyncSsh.close()


if __name__ == "__main__":
    main()

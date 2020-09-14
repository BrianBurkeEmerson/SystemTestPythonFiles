import os
import sys
import threading
import tkinter as tk
import tkinter.filedialog as fd

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../Multipurpose")
from StateTimeTracker import StateTimeTracker

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../SSHHelper")
from InteractiveSSH import InteractiveSSH


HOSTNAME = "toc0"


def write_to_numbered_file(folder, subfolder, data):
    if not os.path.exists(folder + "/" + subfolder):
        os.mkdir(folder + "/" + subfolder)
    
    files = os.listdir(folder + "/" + subfolder)

    next_num = -1
    while True:
        next_num += 1

        if (str(next_num).zfill(4) + ".txt") not in files:
            break
    
    with open(folder + "/" + subfolder + "/" + str(next_num).zfill(4) + ".txt", "w") as f:
        f.write(data)


def main():
    global HOSTNAME

    directory = os.getcwd().replace("\\", "/")
    print("Results will be stored in " + directory + " unless changed")
    
    asyncSsh = InteractiveSSH(HOSTNAME)
    asyncSsh.shell.close()
    asyncSsh.close()

    testObj = StateTimeTracker(HOSTNAME)
    testThread = None

    # Enter a loop for executing commands
    cmd = "help"
    while cmd != "quit":
        if (cmd == "short") or (cmd == "life") or (cmd == "cur"):
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
            print("folder: Select folder where results are stored")
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

        elif cmd == "folder":
            root = tk.Tk()
            directory = fd.askdirectory()
            root.destroy()
        
        elif cmd == "start":
            if testObj.running_test:
                print("ERROR: Test already running. Stop current test before starting new one.")
            else:
                print("Starting logging...")
                testThread = threading.Thread(target = testObj.start, args = (directory,), name = "Active Test")
                testThread.start()
        
        elif cmd == "stop":
            if testObj.running_test:
                testObj.monitor_log = False
                testThread.join()
                testThread = None
            else:
                print("ERROR: No test currently running")
        
        cmd = input("> ").lower()
    
    # After quit is entered, stop any running tests and quit
    testObj.monitor_log = False
    if testThread != None:
        testThread.join()


if __name__ == "__main__":
    main()

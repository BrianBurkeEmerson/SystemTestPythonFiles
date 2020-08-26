import sys
import os
import time
import threading
import tkinter as tk
import tkinter.simpledialog as sd
import tkinter.filedialog as fd
import tkinter.scrolledtext as st
from tkinter import ttk
from datetime import datetime
from configparser import ConfigParser
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")
from MemoryUsageOverTimeHartISA import (run_test, terminate_test)

ENTRY_WIDGET_WIDTH = 50
DEFAULT_COLOR = "#F0F0F0"
CONFIG_FILE_NAME_JSON = "Options_MemoryTracker.json"


class FileSelector(tk.LabelFrame):
    def __init__(self, master = None, frame_text = "", file_selector_text = "", file_types = ("ZIP",), save_file = True):
        super().__init__(master, text = frame_text)
        self.file_selector_text = file_selector_text
        self.file_types = file_types
        self.save_file = save_file

        self.entry = tk.Entry(self, width = ENTRY_WIDGET_WIDTH)
        self.entry.grid(row = 0, column = 0)

        self.browse = tk.Button(self, text = "Browse", command = self.select_file)
        self.browse.grid(row = 0, column = 1)
    

    def select_file(self):
        types = []
        for ft in self.file_types:
            types.append((ft.upper() + " Files", "*." + ft.lower()))
        
        types.append(("All Files", "*"))

        filename = ""

        if self.save_file:
            filename = fd.asksaveasfilename(confirmoverwrite = True, defaultextension = ("." + self.file_types[0].lower()), title = self.file_selector_text, filetypes = tuple(types))
        else:
            filename = fd.askopenfilename(title = "Select system backup ZIP file", filetypes = tuple(types))
        
        self.entry.delete(0, tk.END)
        self.entry.insert(0, filename)


    def select_folder(self):
        folder_name = fd.askdirectory()

        self.entry.delete(0, tk.END)
        self.entry.insert(0, folder_name)
    

    def flash_red(self):
        self.browse["bg"] = "red"

        # Start a new thread to turn the color of the button back
        recordingThread = threading.Timer(0.5, self.turn_default)
        recordingThread.start()


    def turn_default(self):
        self.browse["bg"] = DEFAULT_COLOR


class LabeledEntry(tk.LabelFrame):
    def __init__(self, master = None, frame_text = ""):
        super().__init__(master, text = frame_text)

        self.entry = tk.Entry(self, width = ENTRY_WIDGET_WIDTH)
        self.entry.grid(row = 0, column = 0)


class EntryWithRemoveButton(tk.Frame):
    def __init__(self, master = None, parent = None, label_text = ""):
        super().__init__(master)

        self.parent = parent

        self.button = tk.Button(self, text = "Delete", command = self.unregister)
        self.button.grid(row = 0, column = 0)

        self.label_text = label_text
        self.label = tk.Label(self, text = label_text)
        self.label.grid(row = 0, column = 1)
    

    def unregister(self):
        del self.parent.children_processes[self.label_text]
        self.parent.layout_children()
        self.destroy()


class ProcessEntryWindow(tk.LabelFrame):
    def __init__(self, master):
        super().__init__(master, text = "Processes to Monitor")

        # The children_processes attribute contains EntryWithRemoveButton"s for each process to track
        self.children_processes = {}
        self.children_order = []

        self.add_button = tk.Button(self, text = "Add Process by Name", command = self.add_process_by_name)
        self.add_button.grid(row = 0, column = 0)

        self.add_pid_button = tk.Button(self, text = "Add Process by PID", command = self.add_process_by_pid)
        self.add_pid_button.grid(row = 1, column = 0)

        self.spacing_label = tk.Label(self, text = "          ")
        self.spacing_label.grid(row = 0, column = 1, rowspan = 2)
    

    def add_process_by_name(self):
        process_name = sd.askstring("Process Name", "Enter the name of the process to track")
        if process_name != None:
            self._add_process_code(process_name)

    
    def add_process_by_pid(self):
        pid = sd.askinteger("Process ID", "Enter the PID of the process to track")
        if pid not in (None, ""):
            process_name = sd.askstring("Identifier", "Enter an identifier for the PID")
            if process_name in (None, ""):
                process_name = str(pid)
            
            # Add process to list
            self._add_process_code(str(pid) + "," + process_name)


    def _add_process_code(self, process_name):
        if process_name not in self.children_processes:
            self.children_processes[process_name] = EntryWithRemoveButton(self, self, label_text = process_name)
            self.children_order.append(process_name)
            self.layout_children()


    def layout_children(self):
        # Determine whether any children need to be removed from the children_order list
        for i in range(len(self.children_order) - 1, -1, -1):
            if self.children_order[i] not in self.children_processes:
                self.children_order.pop(i)

        # Reapply layouts for all children now that the list is cleaned up
        for i in range(len(self.children_order)):
            self.children_processes[self.children_order[i]].grid(row = i, column = 2, sticky = tk.W)


class MemoryTrackerGui(tk.Frame):
    def __init__(self, master = None):
        super().__init__(master)
        self.master = master

        self.hostname_entry = LabeledEntry(master, frame_text = "Gateway Hostname or IP")
        self.hostname_entry.grid(row = 0, column = 0)


        self.ssh_username_entry = LabeledEntry(master, frame_text = "SSH Username")
        self.ssh_username_entry.grid(row = 0, column = 1)

        self.ssh_password_entry = LabeledEntry(master, frame_text = "SSH Password")
        self.ssh_password_entry.grid(row = 1, column = 1)


        self.web_username_entry = LabeledEntry(master, frame_text = "Web Interface Username")
        self.web_username_entry.grid(row = 2, column = 1)

        self.web_password_entry = LabeledEntry(master, frame_text = "Web Interface Password")
        self.web_password_entry.grid(row = 3, column = 1)


        self.use_time_limit_check = ttk.Checkbutton(master, text = "Use time limit for test")
        self.use_time_limit_check.grid(row = 1, column = 0)

        self.time_limit_entry = LabeledEntry(master, frame_text = "Test time limit/duration")
        self.time_limit_entry.grid(row = 2, column = 0)

        self.measurement_period_entry = LabeledEntry(master, frame_text = "Time between Measurements")
        self.measurement_period_entry.grid(row = 3, column = 0)


        self.track_hart_check = ttk.Checkbutton(master, text = "Track HART device count")
        self.track_hart_check.grid(row = 0, column = 2)

        self.track_isa_check = ttk.Checkbutton(master, text = "Track ISA100 device count")
        self.track_isa_check.grid(row = 0, column = 3)

        self.legacy_gateway_check = ttk.Checkbutton(master, text = "Legacy Gateway")
        self.legacy_gateway_check.grid(row = 1, column = 2)

        self.supports_isa_check = ttk.Checkbutton(master, text = "Gateway Supports ISA")
        self.supports_isa_check.grid(row = 1, column = 3)


        self.save_file_selector = FileSelector(master,\
            frame_text = "Data File Name", file_selector_text = "Enter a Name for the Data File", file_types = ("CSV",))
        self.save_file_selector.grid(row = 2, column = 2, columnspan = 2)


        self.start_button = tk.Button(master, text = "     Start     ", command = self.start_test)
        self.start_button.grid(row = 3, column = 2, columnspan = 2)


        self.process_entry_frame = ProcessEntryWindow(master)
        self.process_entry_frame.grid(row = 4, column = 0, columnspan = 3)


        self.status_box = st.ScrolledText(master, width = ENTRY_WIDGET_WIDTH, height = 10, state = "disabled")
        self.status_box.grid(row = 0, column = 4, rowspan = 5, sticky = tk.N + tk.S)

        # Read the JSON config file settings into the GUI elements
        self.read_config_file()

        # Generate an output filename as a default based on the time and date
        self.save_file_selector.entry.delete(0, tk.END)
        filename = datetime.now().strftime(self.hostname_entry.entry.get() + " - %a %d %B %Y - %I-%M-%S %p Memory Usage.csv")
        self.save_file_selector.entry.insert(0, filename)


    def write_to_status_box(self, msg):
        num_lines = int(self.status_box.index("end - 1 line").split(".")[0])
        self.status_box["state"] = "normal"
        if num_lines >= 100:
            self.status_box.delete(1.0, 2.0)
        if self.status_box.index("end-1c") != "1.0":
            self.status_box.insert("end", "\n")
        self.status_box.insert("end", msg)
        self.status_box["state"] = "disabled"
        self.status_box.see(tk.END)


    def read_config_file(self):
        # Create a dictionary for the various options
        config = {}

        # If no config file exists, create a new default one
        if not(os.path.isfile(CONFIG_FILE_NAME_JSON)):
            config["General"] = {
                "UseSettingsFromConfigFile" : True # Whether the settings stored in the config file should be used
            }
            config["Gateway"] = {
                "Hostname" : "192.168.1.10",
                "SshUsername" : "root",
                "SshPassword" : "emerson1",
                "Legacy" : False,
                "SupportsIsa" : True
            }
            config["WebBrowser"] = {
                "WebUsername" : "admin",
                "WebPassword" : "default"
            }
            config["DataRecording"] = {
                "UseTimeLimit" : False, # If set to False, user manually stops test
                "TimeLimit" : 600, # Time limit for test in seconds
                "MeasurementInterval" : 60, # How long between measurements
                "TrackHART" : True, # If set to True, the program records the number of connected HART devices (adds extra time)
                "TrackISA" : True, # If set to True, the program records the number of connected ISA devices
                "ProcessesToTrack" : [] # The list of processes whose memory usage should be tracked (separated by a comma with no spaces)
            }
            config["Files"] = {
                "UseAutomaticFilename" : True # If set to True, the filename is automatically generated based on when the test started
            }

            # Write the config file to JSON
            with open(CONFIG_FILE_NAME_JSON, "w") as f:
                f.write(json.dumps(config, indent = 4))
        
        # Read the options from the config file
        with open(CONFIG_FILE_NAME_JSON, "r") as f:
            config = json.loads(f.read())

        # Fill in the GUI elements according to the JSON file
        self.hostname_entry.entry.delete(0, tk.END)
        self.hostname_entry.entry.insert(0, config["Gateway"]["Hostname"])

        self.ssh_username_entry.entry.delete(0, tk.END)
        self.ssh_username_entry.entry.insert(0, config["Gateway"]["SshUsername"])

        self.ssh_password_entry.entry.delete(0, tk.END)
        self.ssh_password_entry.entry.insert(0, config["Gateway"]["SshPassword"])

        self.web_username_entry.entry.delete(0, tk.END)
        self.web_username_entry.entry.insert(0, config["WebBrowser"]["WebUsername"])

        self.web_password_entry.entry.delete(0, tk.END)
        self.web_password_entry.entry.insert(0, config["WebBrowser"]["WebPassword"])

        self.time_limit_entry.entry.delete(0, tk.END)
        self.time_limit_entry.entry.insert(0, config["DataRecording"]["TimeLimit"])

        self.measurement_period_entry.entry.delete(0, tk.END)
        self.measurement_period_entry.entry.insert(0, config["DataRecording"]["MeasurementInterval"])

        if config["DataRecording"]["UseTimeLimit"]:
            self.use_time_limit_check.state(["selected", "!alternate"])
        else:
            self.use_time_limit_check.state(["!selected", "!alternate"])
        
        if config["DataRecording"]["TrackHART"]:
            self.track_hart_check.state(["selected", "!alternate"])
        else:
            self.track_hart_check.state(["!selected", "!alternate"])
        
        if config["DataRecording"]["TrackISA"]:
            self.track_isa_check.state(["selected", "!alternate"])
        else:
            self.track_isa_check.state(["!selected", "!alternate"])
        
        if config["Gateway"]["Legacy"]:
            self.legacy_gateway_check.state(["selected", "!alternate"])
        else:
            self.legacy_gateway_check.state(["!selected", "!alternate"])
        
        if config["Gateway"]["SupportsIsa"]:
            self.supports_isa_check.state(["selected", "!alternate"])
        else:
            self.supports_isa_check.state(["!selected", "!alternate"])

        for process in config["DataRecording"]["ProcessesToTrack"]:
            self.process_entry_frame._add_process_code(process)
    

    def save_config_file(self):
        config = {}

        config["General"] = {
            "UseSettingsFromConfigFile" : True # Whether the settings stored in the config file should be used
        }
        config["Gateway"] = {
            "Hostname" : self.hostname_entry.entry.get(),
            "SshUsername" : self.ssh_username_entry.entry.get(),
            "SshPassword" : self.ssh_password_entry.entry.get(),
            "Legacy" : self.legacy_gateway_check.instate(["selected"]),
            "SupportsIsa" : self.supports_isa_check.instate(["selected"])
        }
        config["WebBrowser"] = {
            "WebUsername" : self.web_username_entry.entry.get(),
            "WebPassword" : self.web_password_entry.entry.get()
        }
        config["DataRecording"] = {
            "UseTimeLimit" : self.use_time_limit_check.instate(["selected"]), # If set to False, user manually stops test
            "TimeLimit" : int(self.time_limit_entry.entry.get()), # Time limit for test in seconds
            "MeasurementInterval" : int(self.measurement_period_entry.entry.get()), # How long between measurements
            "TrackHART" : self.track_hart_check.instate(["selected"]), # If set to True, the program records the number of connected HART devices (adds extra time)
            "TrackISA" : self.track_isa_check.instate(["selected"]), # If set to True, the program records the number of connected ISA devices
            "ProcessesToTrack" : self.processes_tracked # The list of processes whose memory usage should be tracked (separated by a comma with no spaces)
        }
        config["Files"] = {
            "UseAutomaticFilename" : True # If set to True, the filename is automatically generated based on when the test started
        }

        # Write the config file to JSON
        with open(CONFIG_FILE_NAME_JSON, "w") as f:
            f.write(json.dumps(config, indent = 4))

    
    # Changes internal variables for how the test is run (taken from GUI elements)
    def set_test_options(self):
        self.hostname = self.hostname_entry.entry.get()
        self.ssh_username = self.ssh_username_entry.entry.get()
        self.ssh_password = self.ssh_password_entry.entry.get()
        self.use_time_limit = self.use_time_limit_check.instate(["selected"])
        self.time_limit = int(self.time_limit_entry.entry.get())
        self.measurement_period = int(self.measurement_period_entry.entry.get())
        self.web_username = self.web_username_entry.entry.get()
        self.web_password = self.web_password_entry.entry.get()
        self.track_hart = self.track_hart_check.instate(["selected"])
        self.track_isa = self.track_isa_check.instate(["selected"])
        self.filename = self.save_file_selector.entry.get()
        self.legacy_gateway = self.legacy_gateway_check.instate(["selected"])
        self.supports_isa = self.supports_isa_check.instate(["selected"])

        self.processes_tracked = []
        for process in self.process_entry_frame.children_processes:
            self.processes_tracked.append(process)

    
    def start_test(self):
        self.set_test_options()
        self.save_config_file()
        run_test(self)

        if self.use_time_limit:
            self.start_button["text"] = " Running Test "
            self.start_button["command"] = None

            timeLimitThread = threading.Timer(self.time_limit, self.stop_test)
            timeLimitThread.start()
        else:
            self.start_button["text"] = "     Stop     "
            self.start_button["command"] = self.stop_test
    

    def stop_test(self):
        terminate_test(self)

        self.start_button["text"] = "     Start     "
        self.start_button["command"] = self.start_test


root = None

def quit_program():
    global root
    root.quit()
    root.destroy()


def main():
    global root
    root = tk.Tk()
    _app = MemoryTrackerGui(root)
    root.wm_title("Memory Tracker")
    root.protocol("WM_DELETE_WINDOW", quit_program)
    root.mainloop()


if __name__ == "__main__":
    main()

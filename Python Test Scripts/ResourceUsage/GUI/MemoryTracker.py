import sys
import os
import time
import threading
import tkinter as tk
import tkinter.simpledialog as sd
import tkinter.filedialog as fd
from datetime import datetime
from configparser import ConfigParser

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

ENTRY_WIDGET_WIDTH = 50
DEFAULT_COLOR = "#F0F0F0"


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
        #self.parent.children[label_text] = self

        self.button = tk.Button(self, text = "Delete", command = self.unregister)
        self.button.grid(row = 0, column = 0)

        self.label_text = label_text
        self.label = tk.Label(self, text = label_text)
        self.label.grid(row = 0, column = 1)
    

    def unregister(self):
        del self.parent.children[self.label_text]
        self.parent.layout_children()
        self.destroy()


class ProcessEntryWindow(tk.LabelFrame):
    def __init__(self, master):
        super().__init__(master, text = "Processes to Monitor")

        # The children attribute contains EntryWithRemoveButton's for each process to track
        self.children = {}
        self.children_order = []

        self.add_button = tk.Button(self, text = "Add Process", command = self.add_process)
        self.add_button.grid(row = 0, column = 0)

        self.spacing_label = tk.Label(self, text = "          ")
        self.spacing_label.grid(row = 0, column = 1)
    

    def add_process(self):
        process_name = sd.askstring("Process Name", "Enter the name of the process to track")

        if process_name not in self.children:
            self.children[process_name] = EntryWithRemoveButton(self, self, label_text = process_name)
            self.children_order.append(process_name)
            self.layout_children()


    def layout_children(self):
        # Determine whether any children need to be removed from the children_order list
        for i in range(len(self.children_order) - 1, -1, -1):
            if self.children_order[i] not in self.children:
                self.children_order.pop(i)

        # Reapply layouts for all children now that the list is cleaned up
        for i in range(len(self.children_order)):
            self.children[self.children_order[i]].grid(row = i, column = 2, sticky = tk.W)


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


        self.use_time_limit_check = tk.Checkbutton(master, text = "Use time limit for test")
        self.use_time_limit_check.grid(row = 1, column = 0)

        self.time_limit_entry = LabeledEntry(master, frame_text = "Test time limit/duration")
        self.time_limit_entry.grid(row = 2, column = 0)

        self.measurement_period_entry = LabeledEntry(master, frame_text = "Time between Measurements")
        self.measurement_period_entry.grid(row = 3, column = 0)


        self.track_hart_check = tk.Checkbutton(master, text = "Track HART device count")
        self.track_hart_check.grid(row = 0, column = 2)

        self.track_isa_check = tk.Checkbutton(master, text = "Track ISA100 device count")
        self.track_isa_check.grid(row = 1, column = 2)


        self.save_file_selector = FileSelector(master,\
            frame_text = "Data File Name", file_selector_text = "Enter a Name for the Data File", file_types = ("CSV",))
        self.save_file_selector.grid(row = 2, column = 2)


        self.process_entry_frame = ProcessEntryWindow(master)
        self.process_entry_frame.grid(row = 4, column = 0, columnspan = 3)


def main():
    root = tk.Tk()
    _app = MemoryTrackerGui(root)
    root.wm_title("Memory Tracker")
    root.mainloop()


if __name__ == "__main__":
    main()

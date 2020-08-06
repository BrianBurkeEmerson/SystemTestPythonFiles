import locale
import tkinter as tk
from tkinter import filedialog as fd

from MemoryUsagePlotting import plot_csv_memory_file

root = tk.Tk()
filename = fd.askopenfilename(title = "Select CSV file to plot", filetypes = (("CSV Files","*.csv"), ("All Files","*.*")))
root.destroy()

try:
    locale.setlocale(locale.LC_ALL, "")
    plot_csv_memory_file(filename, range(4, 7), [1, 2, 3], range(1, 7), \
        axis_1_label = "Memory (kB)", axis_2_label = "Number of Devices", x_label = "Time", show_plot = True)
except:
    locale.setlocale(locale.LC_ALL, "C")
    plot_csv_memory_file(filename, range(4, 7), [1, 2, 3], range(1, 7), \
        axis_1_label = "Memory (kB)", axis_2_label = "Number of Devices", x_label = "Time", show_plot = True)

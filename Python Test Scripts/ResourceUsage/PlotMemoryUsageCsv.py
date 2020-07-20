import locale
import tkinter as tk
from tkinter import filedialog as fd

from MemoryUsagePlotting import plot_csv_memory_file

locale.setlocale(locale.LC_ALL, "")

root = tk.Tk()
filename = fd.askopenfilename(title = "Select CSV file to plot", filetypes = (("CSV Files","*.csv"), ("All Files","*.*")))
root.destroy()

plot_csv_memory_file(filename, range(4, 7), [1, 2, 3], range(1, 7), \
    axis_1_label = "Memory (kB)", axis_2_label = "Number of Devices", x_label = "Time", show_plot = True)

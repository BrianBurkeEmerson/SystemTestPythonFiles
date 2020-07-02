# This library accepts a CSV file as input and plots it automatically using matplotlib
# It supports two plots, and each axis can have the data to plot specified as a tuple

# py -m pip install matplotlib

import os
import csv
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.dates import date2num

# Data extracted from CSV file where each column is a separate list inside the list
data = []

# filename: The location of the CSV file to be plotted
# col_axis_1: The indices of the columns to be plotted on the left y-axis specified as a tuple [Ex. (1, 2, 4)]
# col_axis_2: The indices of the columns to be plotted on the right y-axis specified as a tuple [Ex. (0, 3, 5)]
# int_col: The indices of columns that contain integer data specified as a tuple
# first_row_labels: Boolean indicating whether the first row of data are column labels
# axis_1_label: Label for left side axis
# axis_2_label: Label for right side axis
# x_label: Label for x-axis
def plot_csv_memory_file(filename, col_y_axis_1 = (), col_y_axis_2 = (), \
    int_col = (), first_row_labels = True, axis_1_label = "", axis_2_label = "", x_label = "", show_plot = False):

    with open(filename, "r") as csvFile:
        csvReader = csv.reader(csvFile, delimiter = ",")
        first_row = True

        # Create lists inside the list for each columns
        for row in csvReader:
            if first_row:
                for col in range(len(row)):
                    data.append([])

            # Go through each row and populate the lists with the contents of each column
            for col in range(len(row)):
                if (col in int_col) and not(first_row):
                    data[col].append(int(row[col]))
                else:
                    data[col].append(row[col])
            
            first_row = False
        
    first_data_row = 0
    if first_row_labels:
        first_data_row = 1

    # Convert the timestamps into a format that matplotlib understands
    timestamps = []
    for entry in range(first_data_row, len(data[0])):
        timestamps.append(datetime.strptime(data[0][entry], "%x %X"))

    # Plot the data on two separate plots
    fig = plt.figure()
    ax1 = fig.add_subplot(211)
    ax1.set_xlabel(x_label)
    ax1.set_ylabel(axis_1_label)
    ax1.grid("on")

    # Plot the data for the first y-axis
    for col in col_y_axis_1:
        label = str(col)
        if first_row_labels:
            label = data[col][0]
        ax1.plot(timestamps, data[col][first_data_row:len(data[col])], "-o", label = label)
    
    # Create the second plot
    ax2 = fig.add_subplot(212)
    ax2.set_xlabel(x_label)
    ax2.set_ylabel(axis_2_label)
    ax2.grid("on")

    # Plot the data for the first y-axis
    for col in col_y_axis_2:
        label = str(col)
        if first_row_labels:
            label = data[col][0]
        ax2.plot(timestamps, data[col][first_data_row:len(data[col])], "-o", label = label)

    # Create legends for both plots
    for ax in (ax1, ax2):
        ax.legend(loc = "center left", bbox_to_anchor = (1.1, 0.5))

    # Display the plot
    fig.tight_layout()
    plt.gcf().autofmt_xdate()
    if show_plot:
        plt.show()
    
    # Save the plot
    png_filename = os.path.splitext(filename)[0] + ".png"
    fig.savefig(png_filename)
    
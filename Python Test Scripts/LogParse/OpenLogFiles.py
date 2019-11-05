# -*- coding: utf-8 -*-
"""
Spyder Editor

@author: daniker
@author: brianburke
"""

#%%    
import subprocess
import paramiko as pm
import time
import os
import datetime
import gzip
import xlwt
from xlwt import Workbook
 
def subprocess_cmd(command):                                                                       #uses subprocess module to send command to cmd and prints output
    process = subprocess.Popen(command,stdout=subprocess.PIPE, shell=True)
    proc_stdout = process.communicate()[0].strip()
    print(proc_stdout)
 
def session_cmd(command):                                                                            #uses paramiko to send command to server
    client = pm.Transport((hostname, port))                                                   
    client.connect(username=username, password=password)

    session = client.open_channel(kind='session')
    session.exec_command(command)   
    if command == "close":
        session.close()


nbytes = 4096
hostname = 'ubuntu18vm-1'
port = 22
username = 'ftpemerson' 
password = 'emerson'
location = '/home/ftpemerson/ftp/log_files/IntegratedTestGW/AN_000000/'

#USER INPUT
#date = str(input("What date would you like to look at? (YYYY_MM_DD) "));
date = "2019_05_30"
#SaveLoc = str(input("Copy and Paste file location you would like to save in: "));
SaveLoc = r"C:\Users\E1256881\Desktop\ISA100Testing\chris files"


#command1 changes to directory location of logs and command2 zips them together
fileName = str(date + ".isa.gz")
fileLoc = "".join([SaveLoc,"\\", fileName])   
command1 = 'cd ' + location
command2 = "".join(["cat *isa_gw.log.1_",date,"*>",fileName])                                             #program "cat" linux command to zip all files that match date and filetype  
command = "".join([command1, "\n", command2])                       
session_cmd(command)                                                                                  #commands are sent to server via paramiko using username and password contained in method                  
print(command)

#Moves file to local computer                                                                       
command = "".join(['pscp ftpemerson@10.224.42.22:',location,fileName,' "',fileLoc,'"']);                #pscp command is run with password "emerson" using subprocess method
subprocess_cmd("echo " + password +"|" + command)                                                       #this command downloads files from server and places them into specified file location                                      
time.sleep(5)
print(command)


 #removes created zip file after transfer
remove = "".join(['rm /home/ftpemerson/ftp/log_files/IntegratedTestGW/AN_000000/',fileName,"\n"])        
session_cmd(remove)
session_cmd("close")


#Opens file and writes to text file
with gzip.open(fileLoc) as open_file:
    file_content_MH = open_file.readlines()

        
text_file = open(str(SaveLoc + "\\" + date + ".txt"), "w")
for line in file_content_MH:
    line = line.decode("utf-8");
    split_line_MH = line.split(" ")
    for i in split_line_MH:
        text_file.write(i)
text_file.close()



    
    

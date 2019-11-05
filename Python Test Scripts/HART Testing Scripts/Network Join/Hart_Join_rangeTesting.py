# -*- coding: utf-8 -*-
"""
Created on Thu Mar 21 08:54:57 2019

@author: Brian Burke [FCT]
"""
#%%
import paramiko, time, re
from datetime import datetime
import threading
import queue
import matplotlib.pyplot as plt
import numpy as np

'''
HART network join time script can be used for both a network join test and a single join test.



                                    HART NETWORK JOIN 

This python file was developed to gather statistics regarding join time for a HART network.


In order for the script to process correctly the script should be run DIRECTLY after a reset so the 
script can log into the gateway and detect mote 1 (System manager) and then time the following devices 
based on this.

Internal timer will be reset when mote 1 joins.

The script will then create a log file with the same data that it prints to the python console.




                                   HART SINGLE UNIT JOIN
                                   
The script will run the exact same as the network join except GLOBAL VARIABLE: 'DEVICE COUNT' (line 282) 
must be set to 1. 

Start script at the same time as the device is powered on. The script will hang for a short amount of time after
data is captured, but the times will still be accurate.

'''

class devStatus():                          #Class devStatus desiged to store all data for each device. Every time the system detects a new Mote a new class instance is created

    def __init__(self, mote):             #class is named by mote and also owns a data type mote where mote number is stored
        self.mote = mote

    def addMac(self, mac):                 # MAC address linked to mote number
        self.mac = mac

    def addNegot1(self, negot1):          # Time of first negotiation
        self.negot1 = negot1

    def addNegot2(self, negot2):          #Time of second negotiation
        self.negot2 = negot2

    def addConn(self,conn):                 #Time of connection
        self.conn = conn

    def addOper(self,oper,DoneList):       #Adds operating time and adds itself to Global DoneList
        self.oper = oper
        DoneList.append(self.mote)

    def addPublish(self,publish):
        self.publish = publish

    def ShowData(self):                     #Class function to print all data to console...used mainly for development
        try:
            print("Mote: " + self.mote)
        except AttributeError:
            pass
        try:
            print("MAC: " + self.mac)
        except AttributeError:
            pass
        try:
            print("negot1: " + str(self.negot1))
        except AttributeError:
            pass
        try:
            print("negot2: " + str(self.negot2))
        except AttributeError:
            pass
        try:
            print("conn: " + str(self.conn))
        except AttributeError:
            pass
        try:
            print("oper: " + str(self.oper))
        except AttributeError:
            pass
        try:
            print("publish: " + str(self.publish))
        except AttributeError:
            pass

    def WriteToFile(self,outFile):                           #Writes all available data to text file...uses try except statements to avoid errors if null values are present
        try:
            print("Mote: " + self.mote,file=open(outFile, "a"))
        except AttributeError:
            pass
        try:
            print("MAC: " + self.mac,file=open(outFile, "a"))
        except AttributeError:
            pass
        try:
            print("negot1: " + str(self.negot1),file=open(outFile, "a"))
        except AttributeError:
            pass
        try:
            print("negot2: " + str(self.negot2),file=open(outFile, "a"))
        except AttributeError:
            pass
        try:
            print("conn: " + str(self.conn),file=open(outFile, "a"))
        except AttributeError:
            pass
        try:
            print("oper: " + str(self.oper),file=open(outFile, "a"))
        except AttributeError:
            pass
        try:
            print("Publish : " + str(self.publish), file=open(outFile, "a"))
        except AttributeError:
            pass




###### Login to nwconsole###### 
def nwconsoleLogin(chan, done):
    time.sleep(1)
    sendCommand('nwconsole', chan, done)
    sendCommand('admin', chan, done)
    sendCommand('admin', chan, done)
    return

###### Login to gateway SSH###### 
def gwLogin(gateway,username,password, ssh):
    try:
        ssh.connect(gateway, username=username, password=password)
        time.sleep(1)
        print('Successfully connected to %s' % gateway + '...')
    except paramiko.ssh_exception.NoValidConnectionsError:
        time.sleep(5)
        gwLogin(gateway, username, password,ssh)
    except TimeoutError:
        time.sleep(5)
        gwLogin(gateway, username, password,ssh)
        
###### Send command through SSH terminal ######
def sendCommand(cmd, chan, done):
    chan.send(cmd)
    chan.send("\n")
    time.sleep(1)
    return done

###### Finds the Mote number given a viable line of 'trace motest' data #####
def MoteFinder(line):
    MoteLoc = line.find('#')
    Mote = line[MoteLoc+1]
    if line[MoteLoc + 2] != ' ':
        Mote = Mote + line[MoteLoc + 2]
        if line[MoteLoc + 3] != ' ':
            Mote = Mote + line[MoteLoc + 3]
    if Mote not in MoteList:
        MoteList.append(Mote)
        Mote = devStatus(Mote)
        DevList.append(Mote)

def MoteFinder2(line):
    MoteLoc = line.find('#')
    Mote = line[MoteLoc + 1]
    if line[MoteLoc + 2] != ' ':
        Mote = Mote + line[MoteLoc + 2]
        if line[MoteLoc + 3] != ' ':
            Mote = Mote + line[MoteLoc + 3]
    if Mote in MoteList:
        return Mote

def getStats(chan, ssh, done,outFile):
    print(done)
    sendCommand('show stat life ', chan, done)
    results(chan,done,outFile)
    return done


def wait30():
    endTime = time.time() + 60 * 30
    while time.time() < endTime:
        print(round((endTime - time.time()) / 60, 2))
    return

###### Get results from command ######
def results(channel,ssh, done, outFile):
    resp = channel.recv(9999)
    resp = resp.decode('ascii').split('\r\n')

    parsed = parse(resp, done, outFile)
    return parsed

###### Parse results and determine what to do next ######
def parse(resp, done, outFile):
    done = list(done)
    global startTime                                                  #starTime declared as a global so that it can be updated when Mote#1 Joins
    for line in resp:
        currTime = datetime.now()
        print(datetime.strftime(datetime.now(), '%b-%d-%Y %H:%M:%S') + " " + str(line), file=open(outFile, "a"))
        print(datetime.strftime(datetime.now(), '%b-%d-%Y %H:%M:%S') + " " + str(line))
        if "Negot1" in line:
            MoteFinder(line)
            for i in DevList:                                             #loops through list of devices and checks if the mote number has been detected before
                Mote = MoteFinder2(line)                                  #Finds Mote Number in Line
                if i.mote == Mote:                                         #If the Mote number that was found is the same as the selected device program notes time of transaction
                    i.addNegot1(datetime.now() - startTime)                  #Finds the mote in the line and adds the time of the respective data to the device
        elif "Negot2" in line:
            MoteFinder(line)
            for i in DevList:
                Mote = MoteFinder2(line)
                if i.mote == Mote:
                    i.addNegot2(datetime.now() - startTime)
        elif "Conn" in line:
            MoteFinder(line)
            for i in DevList:
                Mote = MoteFinder2(line)
                if i.mote == Mote:
                    i.addConn(datetime.now() - startTime)
        elif "Oper" in line:
            MoteFinder(line)
            for i in DevList:
                Mote = MoteFinder2(line)
                if i.mote == Mote:
                    i.addOper(datetime.now() - startTime, DoneList)
                    if i.mote == '1':
                        startTime = datetime.now()
            return done
        elif "Responding" in line:
            done[1] = 'running'
            return done
    return done

def Macfinder(chan,done):
    sendCommand('sm -a', chan, done)
    resp = chan.recv(9999)
    resp = resp.decode('ascii').split('\r\n')
    for line in resp:
        for i in DevList:
            try:
                if i.mote == line[30]:
                    i.addMac(line[0:23])
            except IndexError:
                pass


def HartServer_Thread(chan,out_queue,outfile):
    done = False
    publishDict = {}
    while done == False:
        resp = chan.recv(999)
        resp = resp.decode('ascii').split('\r\n')
        for line in resp:
            print(datetime.strftime(datetime.now(), '%b-%d-%Y %H:%M:%S') + " " + str(line), file=open(outfile, "a"))
            print(datetime.strftime(datetime.now(), '%b-%d-%Y %H:%M:%S') + " " + str(line))
            if 'Responding' in line and "NOT Responding" not in line:
                mac = line.split(' ')[5]
                print(mac)
                publishDict[mac] = datetime.now() - startTime
                if len(publishDict.keys()) == DeviceCount:
                    done = True
    out_queue.put(publishDict)

    

MoteList = []                                      #All the globals listed above 'Main()'
DevList = []
DoneList = []
global startTime
startTime = datetime.now()
DeviceCount = 1                                  #Number of devices on network... 1 for single unit join test
RangeTesting = False
def main():
    gw_name = 'brianGW'
    username = 'root'
    password = 'emerson1'
    outFile = "HART_Join_log.txt"
    datafile = "HART_Join_data.txt"
    print("",open(outFile, "w"))
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    gwLogin(gw_name, username, password, ssh)
    chan = ssh.invoke_shell()
    HartServerChan = ssh.invoke_shell()
    done = 'no', 'running'
    stopTail = '\x03'                                      #Sleep added to ensure commands send correctly through ssh
    
    startTime = datetime.now()
    time.sleep(3)

    if DeviceCount == 1:
        sendCommand('rm /var/apache/data/hartserver.txt', chan, done)
        sendCommand('cat>/var/apache/data/hartserver.txt', chan, done)
        sendCommand(stopTail, chan, done)

    nwconsoleLogin(chan, done)

    motestOn = 'trace motest on'
    sendCommand(motestOn, chan, done)
#
    exitConsole = 'exit'
    quitSSH = 'quit'
    hartserverFollow = 'tail -f /var/apache/data/hartserver.txt | grep Discovery'
    sendCommand(hartserverFollow, HartServerChan, done)

    HartServerQue = queue.Queue()
    thread = threading.Thread(target=HartServer_Thread, args=[HartServerChan, HartServerQue, outFile])

    thread.start()


    while done[0] == 'no' or thread.is_alive():
        done = list(done)
        if done[1] == 'running':
            done = results(chan,ssh,done, outFile)
        elif done[1] == 'negot1':
            negot1 = datetime.now() - startTime
            done[1] = 'running'
        elif done[1] == 'negot2':
            negot2 = datetime.now() - startTime
            done[1] = 'running'
        elif done[1] == 'conn':
            conn = datetime.now() - startTime
            done[1] = 'running'
        elif done[1] == 'oper':
            oper = datetime.now() - startTime
            done[1] = 'running'
            #sendCommand(exitConsole, chan, done)
            time.sleep(2)
            sendCommand(hartserverFollow, chan, done)
        elif done[1] == 'publishing':
            print(done)
            publish = datetime.now() - startTime
            sendCommand(stopTail, chan, done)
            nwconsoleLogin(chan,done)
            wait30()
            done = list(done)
            done[1] = 'running'
            getStats(chan, ssh, done, outFile)
            sendCommand(exitConsole, chan, done)
            sendCommand(quitSSH, chan, done)
            time.sleep(1)
            ssh.close()
            chan.close()
            done = list(done)
            done[0]='yes'
        for i in DevList:
            i.ShowData()
        if len(DoneList) == DeviceCount:
            done[0] = 'yes'
            
    print("\n")
    Macfinder(chan,done)
    PublishDict = HartServerQue.get()
    for device in DevList:
        for mac in PublishDict.keys():
            if mac == device.mac:
                device.addPublish(PublishDict[mac])
        if device.mote != '1':
            device.WriteToFile(datafile)
            device.ShowData()



if __name__ == "__main__":
    main()










        

    
    
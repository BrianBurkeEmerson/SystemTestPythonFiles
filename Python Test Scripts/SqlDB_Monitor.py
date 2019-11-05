import paramiko, time
from datetime import datetime
import os

"""
                            TOOL DESIGNED TO CAPTURE AND REPORT LIVE ISA100 DATA

WARNING: TOOL READS IN AND ASSOCIATES DEVICE ID TO MAC ADDRESSES AT BEGINNING OF SCRIPT AND IF A DEVICE JOINS THE NETWORK
DURING RUNTIME IT WILL FAIL.

BEFORE RUNNING CHANGE IP (LINE 171) TO DESIRED IP OF GATEWAY

After associating the device id to the mac address this tool will then begin constantly polling the database and writing
the data for each device into a folder titled "Output Files" located in the base C drive. 


PROGRAM INFO:
    The program will create a class for each device at the beginning of runtime and then begin collecting data and writing
    it to a text file for the end user and also printing it to the console for development purposes.

"""
Gateway_ID = "integratedtestgw"


class Device:  # Class Device desiged to store all data for each device.
    # Every time the system detects a new DeviceID a new class instance is created

    def __init__(self, deviceID):  # class is named by mote and also owns a data type mote where mote number is stored
        self.deviceID = deviceID
        self.lineCount = 1
        self.PV = []

    def addMac(self, mac):  # MAC address linked to Device ID
        self.mac = mac

    def addPV(self, PV):  # Primary Variable
        self.PV.append(PV)

    def addTime(self, gwTime):
        gwTime = gwTime.split(' ')[1]
        self.gwTime = gwTime
        self.calcUpdateRate()

    def addQuality(self, Quality):
        Quality = int(Quality)
        Quality = (Quality >> 6) & 3
        if Quality == 2:
            Quality = 'GOOD'
        elif Quality == 1:
            Quality = 'UNCERTAIN'
        else:
            Quality = 'BAD'
        Quality = str(Quality)
        self.Quality = Quality

    def showdata(self):
        if self.updateRate != '0:00:00' and self.updateRate != 'Unknown':
            print("-------DATA FOR DEVICE " + self.deviceID + "---------")
            print("PV: " + str(self.PV))
            print("Quality: " + self.Quality)
            print("Update Rate: " + self.updateRate)
            print("MAC: " + self.mac)
            print(self.mac + "," + self.updateRate, file=open('updateRates.txt', "a"))

    def writeToFile(self):
        # if self.updateRate != '0:00:00' and self.updateRate != 'Unknown':
        outFile = str(r"Output Files\\" + self.mac + ".txt")
        computerTime = datetime.now().time()
        computerTime = str(computerTime)[0:8]
        # if self.updateRate != '0:00:00':
        stringToPrint = "[{0}], {1}, {2}, {3}, {4}, {5}".format(self.lineCount, self.gwTime, computerTime, self.PV,
                                                                self.Quality, self.updateRate)
        print(stringToPrint, file=open(outFile, "a"))

    # else:
    #    pass

    def calcUpdateRate(self):
        file = r"Output Files\{0}.txt".format(self.mac)
        try:
            with open(file, 'r') as f:
                lines = f.read().splitlines()
                last_line = lines[-1]
                self.lineCount = len(lines) + 1
                CurrgwTime = self.gwTime
                LastgwTime = last_line.split(', ')[1]
                FMT = '%H:%M:%S'
                self.updateRate = str(datetime.strptime(CurrgwTime, FMT) - datetime.strptime(LastgwTime, FMT))
        except:
            self.updateRate = 'Unknown'
            pass


# Runs SQL query
def runQuery(sqlQuery, chan):
    chan.send(sqlQuery)
    chan.send('\n')
    time.sleep(.5)
    Qresp = chan.recv(999999)
    queryResponse = Qresp
    queryResponse = queryResponse.decode('utf8').split('\r\n')
    #    queryResponse = bytearray.fromhex(queryResponse).decode.split('\r\n')
    return queryResponse


def formatResponse(response):
    respList = []
    for index, line in enumerate(response):
        values = []
        lineStr = str(line)
        #        print(lineStr)
        splitLineStr = lineStr.split("|")

        if 'sqlite' not in line and 'select' not in line and len(splitLineStr) > 1:
            for value in splitLineStr:
                try:
                    #                    value = bytearray.fromhex(value).decode() #enable to get device tag name in text
                    #                    print(value)
                    values.append(value)
                except ValueError:
                    pass
            respList.append(values)
    return respList


def MAC_Assignments(chan):
    devDict = {}
    deviceResponse = runQuery("SELECT * FROM Devices;", chan)
    respList = []
    for index, line in enumerate(deviceResponse):
        values = []
        lineStr = str(line)
        #        print(lineStr)
        splitLineStr = lineStr.split("|")

        if 'sqlite' not in line and 'select' not in line and len(splitLineStr) > 1:
            for value in splitLineStr:
                try:
                    #                    value = bytearray.fromhex(value).decode() #enable to get device tag name in text
                    #                    print(value)
                    values.append(value)
                except ValueError:
                    pass
            respList.append(values)
    for i in respList:
        devDict[i[0]] = i[3].replace(':', '-')
    return devDict


def main():
    try:
        os.mkdir(r'Output Files')
    except:
        pass

    ###### Login to gateway SSH, connect to sqlite DB ######
    gw_name = Gateway_ID
    password = 'root'
    username = 'root'

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(gw_name, username=username, password=password)
    time.sleep(1)
    print('Successfully connected to %s...' % gw_name)

    chan = ssh.invoke_shell()
    time.sleep(1)
    counter = 0

    chan.send('sqlite3 /var/volatile/tmp/Monitor_Host.db3')
    chan.send('\n')
    time.sleep(1)
    devdict = MAC_Assignments(chan)
    while True:

        ###### Run querys ######
        # choose from commands in line 35-59 or write custom sql query
        deviceResponse = runQuery("SELECT * FROM devicereadings;", chan)
        # deviceResponse = runQuery(seeTables)
        ###### Format the response from SQL query ######
        devicesDF = formatResponse(deviceResponse)
        DeviceDictionary = {}
        counter += 1
        for i in devicesDF:
            if i[3] != '' and i[3] != '0.000000' and i[3] != '0':
                if i[0] not in DeviceDictionary.keys():
                    dev = Device(i[0])
                    dev.addMac(devdict[i[0]])
                    DeviceDictionary[i[0]] = dev
                dev = DeviceDictionary[i[0]]
                dev.addTime(i[1])
                dev.addPV(i[3])
                dev.addQuality(i[5])
        for dev in DeviceDictionary.values():
            dev.writeToFile()


if __name__ == "__main__":
    main()


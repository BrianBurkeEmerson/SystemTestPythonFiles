# -*- coding: utf-8 -*-
"""
Created on Thu Apr 18 11:22:34 2019

@author: daniker
"""
#%%
import datetime
import gzip


class networkStats():
    
    def __init__(self,received, outOfOrder, missed, late, expired):
        self.received = received
        self.outOfOrder = outOfOrder
        self.missed = missed
        self.late = late
        self.expired = expired
        
    def pkReceive(net):
        net.received += 1
    
    def pkOutOfOuder(net, count):
        net.outOfOrder += count
        
    def pkMissed(net):
        net.missed += 1
        
    def pkLate(net):
        net.late += 1
        
    def pkExpired(net):
        net.expired += 1 
        
        
def healthCalcs(devDict, mac, network, publishRate):
    try:
        if devDict[mac]['seqDelta'] > 1:
            devDict[mac]['outOfOrder'] += devDict[mac]['seqDelta'] -1
            network.pkOutOfOuder(devDict[mac]['seqDelta'] - 1)
        elif devDict[mac]['seqDelta'] < 0:
            devDict[mac]['seqDelta'] += 256
            if devDict[mac]['seqDelta'] > 1:
                network.pkOutOfOuder(devDict[mac]['seqDelta'])
                devDict[mac]['outOfOrder'] += devDict[mac]['seqDelta']
        if devDict[mac]['timeDelta'] > datetime.timedelta(seconds=publishRate*1.05):
            network.pkLate()
            devDict[mac]['late'] += 1
        if devDict[mac]['timeDelta'] > datetime.timedelta(seconds=publishRate*2): 
            network.pkMissed()
            devDict[mac]['missed'] +=1
        return devDict
    except KeyError:
        pass
    

def dictADD(mac,date, seq, devDict):
    devDict[mac]['publish time'].append(date)
    devDict[mac]['sequence ID'].append(seq)
    devDict[mac]['expired'] += 1
    devDict[mac]['status'] = 'expired'
    return devDict


def dictCalcs(mac,date,seq,devDict):
    devDict[mac]['timeDelta'] = devDict[mac]['publish time'][-1] - devDict[mac]['publish time'][-2]
    devDict[mac]['seqDelta'] = int(devDict[mac]['sequence ID'][-1]) - int(devDict[mac]['sequence ID'][-2])
    return devDict
    
    
def dictUpdate(mac,date,seq,devDict):
    devDict[mac]['publish time'].append(date)
    devDict[mac]['sequence ID'].append(seq)
    dictCalcs(mac,date,seq,devDict)
    return devDict
    

def dictCreate(mac,date,seq,devDict):
    devDict[mac] = {}
    devDict[mac]['publish time'] = []
    devDict[mac]['publish time'].append(date)
    devDict[mac]['sequence ID'] = []
    devDict[mac]['sequence ID'].append(seq)
    devDict[mac]['missed'] = 0
    devDict[mac]['late'] = 0
    devDict[mac]['outOfOrder'] = 0
    devDict[mac]['expired'] = 0
    devDict[mac]['status'] = 'good'
    return devDict
    

def getDate(line):
    lineSplit = line.split()
    dateStr = lineSplit[0]
    timeStr = lineSplit[1]
    dateTimeStr = dateStr + " " + timeStr
    dateTime = datetime.datetime.strptime(dateTimeStr, '%Y-%m-%d %H:%M:%S')
    return dateTime


def timeCalc(testTime):
    tTHours = str(int(testTime//3600)).zfill(2)
    tTHoursMod = testTime%3600
    tTMins = str(int(tTHoursMod//60)).zfill(2)
    tTSecs = str(int(tTHoursMod%60)).zfill(2)
    easyTestTime = str(tTHours) + ":" + str(tTMins) + ":" +  str(tTSecs)
    return easyTestTime
    

def parseLine(line, macList, devDict):
    lineSplit = line.split()
#    print(lineSplit)
    dateStr = lineSplit[0]
    timeStr = lineSplit[1]
    dateTimeStr = dateStr + " " + timeStr
    dateTime = datetime.datetime.strptime(dateTimeStr, '%Y-%m-%d %H:%M:%S')
    EUID64 = lineSplit[2][lineSplit[2].find("(")+1:lineSplit[2].find(":")]
    macAddr = EUID64[8:24]
    if "ADD" in line:
        seqId = lineSplit[7]
        dictADD(macAddr,dateTime, seqId, devDict)
        return devDict, macAddr        
    else:
        seqId = lineSplit[5]
    if macAddr not in macList:
        deviceDict = dictCreate(macAddr, dateTime, seqId, devDict)
        macList.append(macAddr)
    else:
        deviceDict = dictUpdate(macAddr, dateTime, seqId, devDict)
    return deviceDict, macAddr
    

def readLines(txtFile, network, macList, devDict, publishRate, pubLines):
#    with open(txtFile) as input_file:
    with gzip.open(txtFile, 'rt') as input_file:
        lines = input_file.readlines()#[0:20]
        for line in lines:
            line = str(line)
#            print(line)
            if "skip" in line: #See all out of order
                print(line)
#            if "ADD" in line and "GSAP_OUT" not in line: #See all expired
#                print(line)
            if "PUBLISH" in line and "\(.*" not in line and 'tail' not in line and 'GSAP_OUT' not in line and "WARN" not in line:
                pubLines.append(line)
#                print(line)
                network.pkReceive()
                LineResults = parseLine(line, macList, devDict)
                devDict = LineResults[0]
                mac = LineResults[1]
                if devDict[mac]['status'] == 'good':
                    healthCalcs(devDict, mac, network, publishRate)
                else:
                    network.pkExpired()
                    devDict[mac]['status'] = 'good'
    return devDict
    
                    
def main():
    pubLines =[]
    publishRate = 60
    testTime = 60*120
    devDict = {}
    macList = []
    network = networkStats(0,0,0,0,0)
    gzipFile = r"C:\Users\E1256881\Desktop\ISA100Testing\chris files\isa_gw_2019_05_23.gz"
    devDict = readLines(gzipFile, network, macList, devDict, publishRate, pubLines)
    startTime = getDate(pubLines[0])
    endTime = getDate(pubLines[-1])
    testTime = (endTime - startTime).total_seconds()    
    easyTestTime = timeCalc(testTime)
    
    numDevs = len(devDict)

    
    print("\n")
    print("Test Info")
    print('------------------------')
    print("file name:", gzipFile[gzipFile.rfind("\\")+1:])
    print("number of devices:", numDevs)
    print("test time:",testTime, "secs", "(" + easyTestTime + ")" )
    print("expected pkts(theor): ", round(testTime * 1/publishRate * numDevs,2))

    print("\n")
    print("Network Stats")
    print('------------------------')
    print("received pkts:", network.received)
    print("late:", network.late)
    print("missed: ", network.missed)
    print("out of order:", network.outOfOrder)
    print("expired:", network.expired)
    print("reliability:", round((network.received/(network.received + network.outOfOrder)), 4)*100, '%')

    print("--------------\nSCRIPT COMPLETE")
    
#    
        
    
if __name__ == "__main__":
    main()
#%%

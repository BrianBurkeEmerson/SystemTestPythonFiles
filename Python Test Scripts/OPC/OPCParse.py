# -*- coding: utf-8 -*-
"""
Created on Mon Apr  1 10:47:40 2019

@author: daniker
"""

import datetime

#%%
def createDict(mac, ptime):
    devDict[mac] = {}
    devDict[mac]['rx packets'] = 1
    devDict[mac]['pub time'] = []
    devDict[mac]['pub time'].append(ptime)
    devDict[mac]['missed packets'] = 0
    devDict[mac]['late packets'] = 0
    network['totalRx'] += 1
    return
    
def updateDict(mac, ptime):
    devDict[mac]['rx packets'] += 1
    network['totalRx'] += 1
    devDict[mac]['pub time'].append(ptime)
    return

def calcs(mac, pubRate):
    if devDict[mac]['pub time'][-1] - devDict[mac]['pub time'][-2] >= datetime.timedelta(seconds=pubRate*2):
        devDict[mac]['missed packets'] += 1
        network['totalRxFail'] += 1
    if devDict[mac]['pub time'][-1] - devDict[mac]['pub time'][-2] >= datetime.timedelta(seconds=pubRate +1):
        devDict[mac]['late packets'] += 1
        network['late packets'] += 1
    del(devDict[mac]['pub time'][-2])
        

devDict = {}
macList = []
pubRate = 60
testTime = 30*60
network = {}
network['totalRx'] = 0
network['totalRxFail'] = 0
network['late packets'] = 0

txtFile = "E:\opcout.log"

with open(txtFile) as input_file:
    with open(txtFile) as input_file:
        lines = input_file.readlines()#[0:5]
        for line in lines:
#            print(line)
            if "Item" in line:
#                print(line)
                lineSplit = line.split()
                print(lineSplit)
                devName = lineSplit[1]
                macEnd = devName.split('.')[1][-4:]
                devMAC = '0022:FF00:0002:'+macEnd
                devValue = lineSplit[3]
                devDate = lineSplit[9]
                devTimeStr = lineSplit[10]
                devTimeStrSplit = devTimeStr.split(':')
                devTimeStrSplit[0].zfill(2)
                devTimeStr = ':'.join(devTimeStrSplit)
#                print(devTimeStr)
                devDateTimeStr = devDate + " " + devTimeStr
                devDateTime = datetime.datetime.strptime(devDateTimeStr, '%m/%d/%Y %I:%M:%S.%f')
                print(devMAC, str(devDateTime))
                if devMAC not in macList:
                    createDict(devMAC, devDateTime)
                    macList.append(devMAC)
                else:
                    updateDict(devMAC, devDateTime)
                    calcs(devMAC, pubRate)

for mac in devDict:
    print(mac, devDict[mac])

network['expected pkts'] = 1/pubRate * testTime * len(devDict)
network['reliability'] = round(network['totalRx']/network['expected pkts']*100,2)
    
print(network)

#%%
import matplotlib.pyplot as plt
from collections import Counter

missedList = []
for mac in devDict:
    missedList.append(devDict[mac]['missed packets'])
missedList.sort()
print(missedList)
plt.figure(figsize=(24, 13))

D = Counter(missedList)
plt.bar(range(len(D)), list(D.values()), align='center')
plt.xticks(range(len(D)), list(D.keys()))
plt.title('Attempts')
plt.ylabel('Number of Devices')
plt.xlabel('Number of Attempts')
plt.show()








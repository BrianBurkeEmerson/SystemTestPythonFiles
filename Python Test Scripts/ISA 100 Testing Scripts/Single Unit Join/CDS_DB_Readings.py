#%%
import paramiko, time, re
import pandas as pd
import numpy as np
import datetime
import pprint
import collections

###### Login to gateway SSH, connect to sqlite DB ######
gw_name = '10.224.42.86'
password = 'root'
username = 'root'



ssh = paramiko.SSHClient()                                                        
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(gw_name, username=username, password=password)
time.sleep(1)
print('Successfully connected to %s' % gw_name + '...')

chan = ssh.invoke_shell()
time.sleep(1)

chan.send('sqlite3 /var/volatile/tmp/Monitor_Host.db3')
chan.send('\n')
time.sleep(1)

resp = chan.recv(12800)
resp = resp.decode('ascii').split('\r\n')

for line in resp:
    print(line)



###### List of querys/commands ######
enableHeaders = '.headers on'
seeTables = '.tables'
tableName = ''
help = '.help'
getSchema = '.schema ' + tableName
exitSQL = '.exit'
devices = 'select * from devices;'
devicesInfo = 'select * from devicesInfo;'
networkHealth = 'select * from networkHealth;'
deviceHealthHistory = 'select * from deviceHealthHistory;'
deviceHistory = 'select * from deviceHistory;'
deviceConnections = 'select * from deviceConnections;'
deviceReadings = 'select * from deviceReadings;'
deviceReadingsHistory = 'select * from DeviceReadingsHistory;'
neighborHealthHistory = 'select * from neighborHealthHistory where LinkStatus = 1;'
networkHealthDevices = 'select * from networkHealthDevices;'
networkHealthHistory = 'select * from NetworkHealthHistory;'
routeLinks = 'select * from routeLinks;'
routesInfo = 'select * from routesInfo;'
firmwares = "select * from firmwares;"
commands = 'select * from commands;'
properties = 'select * from properties;'
topologyLinks = 'select * from topologyLinks;'
topologyGraphs = 'select * from topologyGraphs;'
custom= ""


#Runs SQL query
def runQuery(sqlQuery):
    print(sqlQuery)
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

        if 'sqlite' not in line and 'select' not in line and len(splitLineStr)>1:
            for value in splitLineStr:
                try:
#                    value = bytearray.fromhex(value).decode() #enable to get device tag name in text
#                    print(value)
                    values.append(value)
                except ValueError:
                    pass
            respList.append(values)
            print(values) 
    print("RESP")
    print(respList)
    return respList
     
devDict = {}
idList = []

###### Enable Headers ######
headers = []
runQuery(sqlQuery=enableHeaders)

###### Run querys ######
print('running query...')
#choose from commands in line 35-59 or write custom sql query 
deviceResponse = runQuery("SELECT * FROM commands;")
#deviceResponse = runQuery(seeTables) 
###### Format the response from SQL query ######
devicesDF = formatResponse(deviceResponse)

updateDict = {}
for i in devicesDF:
    if i[2] == '10':
        try:
            hex_rate = i[8][44] + i[8][45]
            hex_rate = int('0x' + hex_rate, 0)
        except:
            hex_rate = "Not Found"
        updateDict.update({int(i[1]):hex_rate})

pprint.pprint(updateDict)

'''
#%%
updateDict = {}
for line in devicesDF:
    id,rate = ReadUpdateRate(line)
    updateDict.update({id,rate})
    
print(updateDict)

   

###### Exit and close connection ######
runQuery(exitSQL)
ssh.close()
print("SCRIPT COMPLETE")

'''






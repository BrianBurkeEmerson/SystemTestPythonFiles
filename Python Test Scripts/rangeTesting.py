

import paramiko, time, re
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as dates


class devStatus():

    def __init__(self, negot1, negot2, conn, oper, publish):
        self.negot1 = negot1
        self.negot2 = negot2
        self.conn = conn
        self.oper = oper
        self.publish = publish


###### Login to nwconsole######
def nwconsoleLogin(chan, done):
    sendCommand('nwconsole', chan, done)
    sendCommand('admin', chan, done)
    sendCommand('admin', chan, done)
    return

###### Login to gateway SSH######
def gwLogin(gateway, username, password, ssh):
    try:
        ssh.connect(gateway, username=username, password=password)
        print('Successfully connected to %s' % gateway + '...')
        time.sleep(2)
    except paramiko.ssh_exception.NoValidConnectionsError:
        time.sleep(3)
        gwLogin(gateway, username, password,ssh)
    except TimeoutError:
        time.sleep(3)
        gwLogin(gateway, username, password,ssh)


###### Send command through SSH terminal ######
def sendCommand(cmd, chan, done):
    chan.send(cmd)
    chan.send("\n")
    time.sleep(1)
    return done


###### Get results from command ######
def results(channel, done, outFile):
    print(done)
    resp = channel.recv(9999)
    resp = resp.decode('ascii').split('\r\n')
    parsed = parse(resp, done, outFile)
    return parsed


###### Parse results and determine what to do next ######
def parse(resp, done, outFile):
    global mote_1_Joined
    global startTime
    print(done)
    done = list(done)
    for line in resp:
        currTime = datetime.now()
        print(datetime.strftime(datetime.now(), '%b-%d-%Y %H:%M:%S') + " " + str(line))
        if "Could not connect to dcc." in line:
            done[1] = "login failed"
            break;
        with open(outFile, 'a') as f:
            f.write(datetime.strftime(datetime.now(), '%b-%d-%Y %H:%M:%S') + " " + str(line) + "\n")
        # print(datetime.strftime(datetime.now(), '%b-%d-%Y %H:%M:%S') + " " + str(line), file = open(outFile, "a"))
        if "Negot1" in line and mote_1_Joined:
            done[1] = 'negot1'
        elif "Negot2" in line and mote_1_Joined:
            done[1] = 'negot2'
        elif "Conn" in line and mote_1_Joined:
            done[1] = 'conn'
        elif "Oper" in line:
            if "Mote #1" in line:
                mote_1_Joined = True
                startTime = datetime.now()
                break;
            done[1] = 'oper'
            return done
        elif "Responding" in line and mote_1_Joined:
            done[1] = 'publishing'
            return done
    return done


def getStats(chan, ssh, done):
    print(done)
    sendCommand('show stat life', chan, done)
    results(chan,done,'rangeTestOut.txt')
    return done


def wait30():
    endTime = time.time() + 60 * 30
    while time.time() < endTime:
        print(round((endTime - time.time()) / 60, 2))
    return


#GLOBAL Variable
mote_1_Joined = False
startTime = datetime.now()
def main():
    gw_name = 'briangw'
    username = 'root'
    password = 'emerson1'
    outFile = 'rangeTestOut.txt'
    print("",open(outFile, "w"))
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    gwLogin(gw_name, username, password, ssh)
    chan = ssh.invoke_shell()
    done = 'no','running'

    nwconsoleLogin(chan, done)
    
    motestOn = 'trace motest on'
    sendCommand(motestOn, chan, done)
#    
    exitConsole = 'exit'
    quitSSH = 'quit'
    hartserverFollow = 'tail -f /var/apache/data/hartserver.txt | grep Discovery'
    stopTail = '\x03'
    
    
    while done[0] == 'no':
        print("MOTE #1 status: " + str(mote_1_Joined))
        done = list(done)
        if done[1] == 'running':
            done = results(chan,done, outFile)
        elif done[1] == 'negot1':
            negot1 = datetime.now() - startTime
            done[1] = 'running'
        elif done [1] == "login failed":
            nwconsoleLogin(chan,done)
            motestOn = 'trace motest on'
            sendCommand(motestOn, chan, done)
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
            sendCommand(exitConsole, chan, done)
            time.sleep(2)
            sendCommand(hartserverFollow, chan, done)
        elif done[1] == 'publishing':
            publish = datetime.now() - startTime
            sendCommand(stopTail, chan, done)
            nwconsoleLogin(chan,done)
            #wait30()
#            done = list(done)
#            done[1] = 'running'
            getStats(chan, ssh, done)
            sendCommand(exitConsole, chan, done)
            sendCommand(quitSSH, chan, done)
            time.sleep(3)
            ssh.close()
            chan.close()
            done = list(done)
            done[0] = 'yes'
            
    print("\n")
    device = devStatus(negot1, negot2, conn, oper, publish)
    print("negot1 = ", str(device.negot1))
    print("negot2 = ", str(device.negot2))
    print("conn = ", str(device.conn))
    print("oper = ", str(device.oper))
    print("publish = ", str(device.publish))

    print("negot1 = ", str(device.negot1), file=open(outFile, "a"))
    print("negot2 = ", str(device.negot2), file=open(outFile, "a"))
    print("conn = ", str(device.conn), file=open(outFile, "a"))
    print("oper = ", str(device.oper), file=open(outFile, "a"))
    print("publish = ", str(device.publish), file=open(outFile, "a"))


    
#    gwLogin(gw_name, username, password)
#    command1 = 'nwconsole'
#    sendCommand(command1)
if __name__ == "__main__":
    main()
    
    
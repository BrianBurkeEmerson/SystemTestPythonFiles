# -*- coding: utf-8 -*-
"""
Created on Thu Mar 21 08:54:57 2019

@author: daniker
"""
#%%
import paramiko, time, re
from datetime import datetime



class devStatus():
    
    def __init__(self,negot1, negot2, conn, oper, publish):
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
def gwLogin(gateway,username,password, ssh):
    try:
        ssh.connect(gateway, username=username, password=password)
        time.sleep(1)
        print('Successfully connected to %s' % gateway + '...')
    except paramiko.ssh_exception.NoValidConnectionsError:
        time.sleep(3)
        gwLogin(gateway, username, password)
    except TimeoutError:
        time.sleep(3)
        gwLogin(gateway, username, password)
        
###### Send command through SSH terminal ######
def sendCommand(cmd, chan, done):
    chan.send(cmd)
    chan.send("\n")
    time.sleep(1)
    return done

###### Get results from command ######
def results(channel,ssh, done, outFile):
    resp = channel.recv(9999)
    resp = resp.decode('ascii').split('\r\n')
    parsed = parse(resp, done, outFile)
    return parsed

###### Parse results and determine what to do next ######
def parse(resp, done, outFile):
    done = list(done)
    for line in resp:
        currTime = datetime.now()
        print(datetime.strftime(datetime.now(), '%b-%d-%Y %H:%M:%S') + " " + str(line), file=open(outFile, "a"))
        print(datetime.strftime(datetime.now(), '%b-%d-%Y %H:%M:%S') + " " + str(line))
        if "Negot1" in line:
            done[1] = 'negot1'
        elif "Negot2" in line:
            done[1] = 'negot2'
        elif "Conn" in line:
            done[1] = 'conn'
        elif "Oper" in line:
            done[1] = 'oper'
            return done
        elif "Responding" in line:
            done[1] = 'publishing'
            return done
    return done

def getStats(interval, chan, ssh, done, outFile):
    sendCommand('show stat short ' + str(interval), chan, done)
    results(chan, ssh, done, outFile)
    return done

def wait30():
    endTime = time.time() + 60 *30
    while time.time() < endTime:
        print(round((endTime - time.time())/60,2))
    return
    
def main():   
    gw_name = 'brianGW'
    username = 'root'
    password = 'emerson1'
    outFile = r"C:\Users\E1256881\Desktop\ISA100Testing\Dan Files\2019 - 05 ISA 100\Python Scripts\isaSingleJoin.txt"
    print("",open(outFile, "w"))
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    gwLogin(gw_name, username, password, ssh)
    chan = ssh.invoke_shell()
    done = 'no','running'
    
    startTime = datetime.now()
    nwconsoleLogin(chan, done)
    
    motestOn = 'trace motest on'
    sendCommand(motestOn, chan, done)
#    
    exitConsole = 'exit'
    quitSSH = 'quit'
    hartserverFollow = 'tail -f /var/apache/data/hartserver.txt | grep Discovery'
    stopTail = '\x03'
    
    intervals  = [0,1,2]
    
    
    while done[0] == 'no':
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
            sendCommand(exitConsole, chan, done)
            time.sleep(2)
            sendCommand(hartserverFollow, chan, done)
        elif done[1] == 'publishing':
            publish = datetime.now() - startTime
            sendCommand(stopTail, chan, done)
#            nwconsoleLogin(chan,done)
#            wait30()
#            done = list(done)
#            done[1] = 'running'
#            for i in intervals:
 #               getStats(i, chan, ssh, done, outFile)
#            sendCommand(exitConsole, chan, done)
            sendCommand(quitSSH, chan, done)
            time.sleep(1)
            ssh.close()
            chan.close()
            done = list(done)
            done[0]='yes'
            
    print("\n")
    device = devStatus(negot1, negot2, conn, oper, publish)
	
	#Print to File
    print("negot1 = ", str(device.negot1), file=open(outFile, "a"))
    print("negot2 = ", str(device.negot2), file=open(outFile, "a"))
    print("conn = ", str(device.conn), file=open(outFile, "a"))
    print("oper = ", str(device.oper), file=open(outFile, "a"))
    print("publish = ", str(device.publish), file=open(outFile, "a"))
	
	#Print to Console
    print("negot1 = ", str(device.negot1))
    print("negot2 = ", str(device.negot2))
    print("conn = ", str(device.conn))
    print("oper = ", str(device.oper))
    print("publish = ", str(device.publish))



if __name__ == "__main__":
    main()
    
    
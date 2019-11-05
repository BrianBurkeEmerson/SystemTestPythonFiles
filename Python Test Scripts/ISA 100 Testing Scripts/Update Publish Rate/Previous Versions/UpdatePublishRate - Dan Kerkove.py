import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import json
import requests

host = "IntegratedTestGW:8085"
url = "http://" + host + "/app/login.html"
print(url)
br = webdriver.Firefox()
br.get(url)

time.sleep(3)

user = br.find_element_by_xpath("//input[@type ='text'][@id ='txtUser']")
user.send_keys('admin')

pas = br.find_element_by_xpath("//input[@type ='password'][@id ='txtPassword']")
pas.send_keys('adminadmin')

btn = br.find_element_by_xpath("//input[@type='button'][@id ='btnSubmit']")
btn.click()

time.sleep(3)

cookie = br.get_cookies()
for cook in cookie:
    if cook['name'] == 'CGISESSID':
        cgiSessId = cook['value']

'POST /rpc.cgi HTTP/1.1'
requestHeaders = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,en;q=0.5",
    # "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    # "Content-Length": "123",
    "Content-Type": "text/plain",
    "Cookie": "CGISESSID=" + cgiSessId + "; loggedUser=admin; loggedUserRole=0; MCS_THEME=0; DateTimeFormat=UTC; DEVICELIST_CURRENTPAGE=1; DEVICELIST_SHOWDEVICESFILTER=0; DEVICELIST_EUI64ADDRESS=; DEVICELIST_DEVICETAG=; DEVICELIST_ORDERBY=1; DEVICELIST_ORDERDIRECTION=ASC; DEVICELIST_PAGESIZE=50",
    "Host": host,
    # "Origin": "http://10.224.42.80",
    # "Pragma": "no-cache",
    "Referer": "http://" + host + "/app/devicelist.html",
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:63.0) Gecko/20100101 Firefox/63.0"
}

print(requestHeaders)

########## get list of devices on network ##########
deviceQuery = " SELECT D.DeviceID FROM Devices D  " \
              "INNER JOIN DevicesInfo I ON D.DeviceID = I.DeviceID  LEFT OUTER JOIN (SELECT DeviceID, max(ReadingTime) AS LastRead  FROM DeviceReadings " \
              "WHERE ReadingTime > '1970-01-01 00:00:00'  GROUP BY DeviceID) R ON D.DeviceID = R.DeviceID  WHERE  DeviceStatus >= 20  ORDER BY  Address64 ASC LIMIT 200 OFFSET 0"

devicePayload = {"id": "httpReq", "method": "sqldal.execute", "params": {"query": deviceQuery}}
apiUrl = 'http://' + host + '/rpc.cgi'
req = requests.post(url=apiUrl, headers=requestHeaders, json=devicePayload, verify=False)
print(req)
jsonResp = req.json()
print('result', jsonResp)
# print(json.dumps(jsonResp,sort_keys=True, indent=4))

idList = []
i = 0
for i in range(len(jsonResp['result'])):
    # print(i, jsonResp['result'][i])
    for elem in jsonResp['result'][i]:
        if elem not in [1, 2, 3, 102, 101]:  # dont include router, backbone, or manager
            deviceId = str(elem)
            # print(i, deviceId, type(deviceId))
            idList.append(deviceId)
    i = i + 1

print(idList)
print((len(idList)))

########## write publish rate to device ##########
# time in hex (secs) 4 bits
publishRate = '0001'
deviceId = ''
postedTime = ''
devCount = 0
# object id: nivis = 4, yokogawa = 3, honeywell = 8
objId = 4
objId = str(objId)

# idList = ['45','98'] #yokogawa
#idList = ['102', '101']  # honeywell

for devId in idList:
    if devId == '20':
        objId = '8'
    if devId == '17':
        publishRate = '0001'
    dateNow = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
    publishQuery = "BEGIN TRANSACTION;    INSERT INTO Commands (DeviceID, CommandCode, CommandStatus, TimePosted, ErrorCode, ParametersDescription)    " \
                   "VALUES ( " + devId + ", 10, 0, '2019-01-11 16:05:04', 0, 'Write, TsapID:2, Obj:" + objId + ", Attribute:2, Idx1:0, Idx2:0, Values:FE8000000000000000004E7C7F000001F0B2000500" + publishRate + "000101, CdtBurst:-15');" \
                                                                                                                                                                                                                  "SELECT last_insert_rowid();  INSERT INTO CommandParameters (CommandID, ParameterCode, ParameterValue)  " \
                                                                                                                                                                                                                  "SELECT l.lastrowid, t.paramcode, t.paramvalue FROM ( SELECT 80 as paramcode, '2' as paramvalue " \
                                                                                                                                                                                                                  "UNION ALL  SELECT 81 as paramcode, '4' as paramvalue " \
                                                                                                                                                                                                                  "UNION ALL  SELECT 82 as paramcode, '" + objId + "' as paramvalue " \
                                                                                                                                                                                                                                                                   "UNION ALL  SELECT 83 as paramcode, '2' as paramvalue " \
                                                                                                                                                                                                                                                                   "UNION ALL  SELECT 84 as paramcode, '0' as paramvalue " \
                                                                                                                                                                                                                                                                   "UNION ALL  SELECT 85 as paramcode, '0' as paramvalue " \
                                                                                                                                                                                                                                                                   "UNION ALL  SELECT 86 as paramcode, 'FE8000000000000000004E7C7F000001F0B2000500" + publishRate + "000101' as paramvalue " \
                                                                                                                                                                                                                                                                                                                                                                    "UNION ALL  SELECT 87 as paramcode, '0' as paramvalue " \
                                                                                                                                                                                                                                                                                                                                                                    "UNION ALL  SELECT 1230 as paramcode, '-15' as paramvalue ) t, (SELECT last_insert_rowid() as lastrowid) l;    COMMIT; "

    publishPayload = {"id": "httpReq", "method": "sqldal.execute", "params": {"mode": "write", "query": publishQuery}}
    print(publishPayload)

    apiUrl = 'http://' + host + '/rpc.cgi'

    req = requests.post(url=apiUrl, headers=requestHeaders, json=publishPayload, verify=False)
    print(req)
    jsonResp = req.json()
    print(jsonResp)
    time.sleep(.5)
    devCount += 1
    print("Done writing to device ", devId)
    print("Progress: ", str(devCount) + "/" + str(len(idList)))

    time.sleep(5)

br.close()

'''
publishQuery = "BEGIN TRANSACTION;    INSERT INTO Commands (DeviceID, CommandCode, CommandStatus, TimePosted, ErrorCode, ParametersDescription)    " \
               "VALUES ( " + devId + ", 10, 0, '2019-01-11 16:05:04' , 0, 'Read, TsapID:2, Obj:" + objId + ", Attribute:2, Idx1:0, Idx2:0, CdtBurst:-15');" \
                                                                                                           "SELECT last_insert_rowid();  INSERT INTO CommandParameters (CommandID, ParameterCode, ParameterValue)  " \
                                                                                                           "SELECT l.lastrowid, t.paramcode, t.paramvalue FROM ( SELECT 80 as paramcode, '2' as paramvalue " \
                                                                                                           "UNION ALL  SELECT 81 as paramcode, '3' as paramvalue " \
                                                                                                           "UNION ALL  SELECT 82 as paramcode, '" + objId + "' as paramvalue " \
                                                                                                                                                            "UNION ALL  SELECT 83 as paramcode, '2' as paramvalue " \
                                                                                                                                                            "UNION ALL  SELECT 84 as paramcode, '0' as paramvalue " \
                                                                                                                                                            "UNION ALL  SELECT 85 as paramcode, '0' as paramvalue " \
                                                                                                                                                            "UNION ALL  SELECT 86 as paramcode, '0' as paramvalue " \
                                                                                                                                                            "UNION ALL  SELECT 87 as paramcode, '0' as paramvalue " \
                                                                                                                                                            "UNION ALL  SELECT 1230 as paramcode, '-15' as paramvalue ) t, (SELECT last_insert_rowid() as lastrowid) l;    COMMIT; "

'''
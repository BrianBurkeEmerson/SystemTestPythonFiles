import time
import sys
from datetime import datetime
from SSHHelper import SSHHelper

HOSTNAME = "192.168.1.10"

for i in range(sys.maxsize):
    time.sleep(15 * 60)

    try:
        ssh = SSHHelper(HOSTNAME)
        ssh.send_command("reboot -p")
        ssh.close()
    except:
        now = datetime.now()
        print("Failed on loop " + str(i))
        print(now)
        break

import time
from datetime import datetime
from SSHHelper import SSHHelper

HOSTNAME = "192.168.1.10"

while True:
    time.sleep(15 * 60)

    try:
        ssh = SSHHelper(HOSTNAME)
        ssh.send_command("reboot -p")
        ssh.close()
    except:
        now = datetime.now()
        print(now)
        break

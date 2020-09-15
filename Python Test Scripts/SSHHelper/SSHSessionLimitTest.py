import threading
from SSHHelper import SSHHelper

sessions = []
for i in range(100):
    try:
        sessions.append(SSHHelper("1410s-charlie"))
        print(sessions[-1].send_command("pwd"))
        print("Opened session #" + str(i))
    except:
        pass

for i, session in enumerate(sessions):
    try:
        print(session.send_command("pwd"))
        print("Sent command for #" + str(i) + " successfully")
    except:
        print("Failed to send command for #" + str(i))
    session.close()

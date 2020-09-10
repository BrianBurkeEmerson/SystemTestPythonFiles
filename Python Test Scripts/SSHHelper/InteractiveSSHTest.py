from InteractiveSSH import InteractiveSSH
import re

mote = "5"

ssh = InteractiveSSH("toc0")
ssh.start_nwconsole()

lines = ssh.safe_send("show stat short 0").splitlines()
lines.extend([mote + " -- --"])
lines.extend(ssh.safe_send("show stat cur").splitlines())

ssh.shell.close()
ssh.close()

for line in lines:
    columns = re.split(r"\s{1,}", line.strip())
    if (len(columns) > 1) and (len(columns) < 12):
        if (columns[0] == mote) or (columns[1] == mote):
            print(line)

from InteractiveSSH import InteractiveSSH

ssh = InteractiveSSH("192.168.1.10")
ssh.start_nwconsole()

id_mac_pairs_without_ap = ssh.get_mote_id_mac_associations(include_ap = False)

for mote in id_mac_pairs_without_ap:
    print(ssh.safe_send("delete mote " + str(mote)))

ssh.shell.close()
ssh.close()

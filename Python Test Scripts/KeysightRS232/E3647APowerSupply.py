# pip install pyserial
import serial

class E3647A():
    def __init__(self, port = "/dev/ttyS0", baud = 9600, timeout = 1):
        self.port = port
        self.baud = baud
        self.timeout = timeout

        self.s = serial.Serial(self.port, self.baud, timeout = self.timeout)
    

    def open(self):
        self.s.open()


    def close(self):
        self.s.open()

    
    def send_cmd(self, cmd = ""):
        READ_AT_ONCE = 1000

        self.s.write(bytes(cmd + "\n"))

        return_string = ""
        while True:
            resp = self.s.read(READ_AT_ONCE).decode()
            if resp == "":
                break
            else:
                return_string += resp
        
        return return_string
    

    def enable_remote_control(self):
        self.send_cmd("SYST:REM")
    

    def set_voltage(self, voltage, max_current = False):
        cmd = "APPL " + str(voltage)

        if max_current:
            cmd += ",MAX"
        
        self.send_cmd(cmd)


    def set_current(self, current):
        cmd = "SOUR:CURR " + str(current)
        self.send_cmd(cmd)
    

    def enable_output(self):
        self.send_cmd("OUTP:STAT ON")
    

    def disable_output(self):
        self.send_cmd("OUTP:STAT OFF")

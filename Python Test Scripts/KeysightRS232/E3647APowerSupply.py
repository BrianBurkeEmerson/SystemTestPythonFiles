# pip install pyserial
import serial

class E3647A():
    def __init__(self, port = "/dev/ttyS0", baud = 9600, timeout = 1):
        self.port = port
        self.baud = baud
        self.timeout = timeout

        self.s = serial.Serial(self.port, self.baud, timeout = self.timeout)
    

    def __enter__(self):
        self.open()
        self.enable_remote_control()
        return self
    

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.disable_output()
        self.set_voltage(0)
        self.set_current(0)
        self.close()
    

    def open(self):
        try:
            self.s.open()
        except Exception:
            print("Serial port already opened. Further commands will attempt to use it.")


    def close(self):
        self.s.close()

    
    def send_cmd(self, cmd = ""):
        READ_AT_ONCE = 1000

        self.s.write(bytes(cmd + "\n", "utf-8"))

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

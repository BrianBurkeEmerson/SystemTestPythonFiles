import time
import sys
from datetime import datetime

from E3647APowerSupply import E3647A

s = E3647A("/dev/ttyS0")
s.open()

s.enable_remote_control()

s.set_voltage(0)
s.set_current(0)
s.disable_output()

time.sleep(1)
for i in range(13):
    s.set_voltage(i * 2, True)
    s.enable_output()
    time.sleep(1)
    s.disable_output()

s.set_voltage(0)
s.set_current(0)

s.close()

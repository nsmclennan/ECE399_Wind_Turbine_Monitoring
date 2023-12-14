from network_setup import setup_wifi

from ntptime import settime
import requests
from time import gmtime


SERVER_ADDR = "http://192.168.137.158:5000"
#SERVER_ADDR = "https://192.168.137.158:5000"

try:
    wlan, ip = setup_wifi()
    
    settime()
    
    freq = 1600
    end_time = "%04d%02d%02d%02d%02d%02d" % gmtime()[0:6]
    test_data = bytearray(b'123456789abc')
    test_data2 = b'123456789abc'*1600
    requests.post(SERVER_ADDR + f"/upload/{freq}", data=test_data)
    requests.post(SERVER_ADDR + f"/upload/{freq}/{end_time}", data=test_data2)
except KeyboardInterrupt:
    print('Reset!')
    machine.reset()
finally:
    if 'wlan' in locals():
        wlan.active(False)

from network_setup import setup_wifi

from Sensors.BMI160 import BMI160_I2C

from machine import reset, Pin, I2C
from ntptime import settime
import requests
from time import gmtime, sleep


SERVER_ADDR = "http://192.168.137.158:5000"
#SERVER_ADDR = "http://192.168.1.6:5000"
#SERVER_ADDR = "https://192.168.1.6:5000"

led = Pin("LED", Pin.OUT)

def perform_sampling(freq, duration):
    if freq not in [100, 1600]:
        raise RuntimeError("Invalid frequency! Only 100 and 1600 Hz are currently supported")
    
    sample_count = duration*freq

    buf = bytearray(sample_count*12) # TODO reuse buf for all calls?
    mv = memoryview(buf)

    bmi.begin()
    bmi.configure_fifo(freq)
    
    led.on()
    bmi.enable_fifo()
    bmi.read_fifo_into(sample_count, mv)
    end_time = gmtime()
    led.off()
    bmi.soft_reset() # Soft reset should reset all sensors to suspend mode and disable fifo
    
    end_time = "%04d%02d%02d%02d%02d%02d" % end_time[0:6]
    try:
        requests.post(SERVER_ADDR + f"/upload/{freq}/{end_time}", data=mv)
        sleep(0.1)
        led.on()
        sleep(0.1)
        led.off()
    except OSError as e:
        print("Error sending data to server:", e)


i2c = I2C(1, scl=Pin(27, Pin.IN, Pin.PULL_UP), sda=Pin(26, Pin.IN, Pin.PULL_UP), freq=1000000)
print("I2C: " + str(i2c.scan()))

bmi = BMI160_I2C(i2c)

try:
    wlan, ip = setup_wifi()
    
    count = 0
    while True:
        # Update clock time every 100 iterations
        if count % 100 == 0:
            try:
                settime()
            except OSError as e:
                print("Error synchronizing time:", e)
        sleep(3)
        
        # Perform two samples (high freq: 1600 Hz for 1s, and low freq 100 Hz for 10s)
        perform_sampling(1600, 1)
        perform_sampling(100, 10)
        count += 1
    
except KeyboardInterrupt:
    print('Reset!')
    reset()
finally:
    if 'wlan' in locals():
        wlan.active(False)

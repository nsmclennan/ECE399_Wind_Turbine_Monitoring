from time import sleep_ms, ticks_ms
from machine import Pin, I2C
from Sensors.BMI160 import BMI160_I2C, BMI160_ACCEL_ODR_100HZ, BMI160_GYRO_ODR_100HZ
from collections import namedtuple


i2c = I2C(1, scl=Pin(27, Pin.IN, Pin.PULL_UP), sda=Pin(26, Pin.IN, Pin.PULL_UP), freq=1000000)
print("I2C: " + str(i2c.scan()))

bmi = BMI160_I2C(i2c)
bmi.begin()

Gyro = namedtuple("Gyro", "x y z")
Accel = namedtuple("Accel", "x y z")

@micropython.native
def get_data():
    bmi._get_raw_data()
    
    # Convert raw values to nice units
    gf = 2000*2/65536 # LSB in 2000 deg/s mode
    af = 1/16384 # 2*2/65536 # LSB/g in 2g mode
    gyro = Gyro(bmi._gyro_x*gf, bmi._gyro_y*gf, bmi._gyro_z*gf)
    accel = Accel(bmi._accel_x*af, bmi._accel_y*af, bmi._accel_z*af)
    sensor_time = bmi._gyro_sensor_time*39e-6
    
    return gyro, accel, sensor_time

@micropython.native
def print_data(plotter=False):
    start_time = ticks_ms()
    for i in range(20/0.1):
        gyro, accel, sensor_time = get_data()
        
        mag_accel = (accel.x**2 + accel.y**2 + accel.z**2)**0.5
        if plotter:
            #print("Accel: {x: %8.5f | y: %8.5f | z: %8.5f} g\tMag: %8.5f g" % (accel.x, accel.y, accel.z, mag_accel))
            print("Gyro: {x: %7.2f | y: %7.2f | z: %7.2f} deg/s\tAccel: {x: %8.5f | y: %8.5f | z: %8.5f} g\tMag: %8.5f g"
                  % (gyro.x, gyro.y, gyro.z, accel.x, accel.y, accel.z, mag_accel))
        else:
            print("\rGyro: {x: %7.2f | y: %7.2f | z: %7.2f} deg/s\tAccel: {x: %8.5f | y: %8.5f | z: %8.5f} g\tMag: %8.5f g     Time: %9.5f"
                  % (gyro.x, gyro.y, gyro.z, accel.x, accel.y, accel.z, mag_accel, sensor_time), end='')
        
        sleep_ms(max(0, (start_time + 100*(i+1) - ticks_ms())))
    print(f'\nTime: {(ticks_ms() - start_time)/1e3}')

if __name__ == "__main__":
    print_data(True)

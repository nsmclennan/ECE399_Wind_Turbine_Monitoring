from serial import Serial, SerialTimeoutException
from serial.tools import list_ports

from binascii import unhexlify
from datetime import datetime
import requests


for port in list_ports.comports():
	print(port)

with Serial("COM6", 115200, write_timeout=2) as ser:
	# Set time over serial
	try:
		ser.write(datetime.utcnow().strftime("%Y %m %d %w %H %M %S 0\r\n").encode())
		ser.readline() # Echo back?
	except SerialTimeoutException:
		pass

	count = 0
	#while count < 4:
	while True:
		config = ser.readline()
		#print(config)
		freq, end_time, duration = config.split()
		freq = int(freq)
		duration = int(duration)
		end_time = end_time.decode()
		print(freq, end_time, duration)
		
		data = ser.read(freq*duration*12*2)
		data = unhexlify(data)
		print(f"Read {len(data)} sample bytes")
		requests.post(f"http://localhost:5000/upload/{freq}/{end_time}", data=data)
		count += 1

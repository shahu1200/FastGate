import serial

ead = serial.Serial("/dev/ttyS0", 38400,)

while True:
	data = ead.readline()
	print(data)

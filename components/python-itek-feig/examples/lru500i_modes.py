#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import logging
import time
import queue
import threading

print("Importing 'itekfeig' module ...")
try:
    from itekfeig import FeigLogger
    from itekfeig import LRU500i
except ImportError:
    print("itekfeig package not installed")
    sys.exit(0)
print("... OK")

# This will return ROOT logger, with log file in HOME folder
# and log level set to DEBUG
logger = FeigLogger(loggerLevel=logging.DEBUG)
reader = LRU500i("poe")

# Connect to the reader
print("\nConnecting to reader ...")
settings = {"IP": "192.168.1.153", "PORT": 10001}
ret = reader.connect(reader.INTERFACE_ETHERNET, settings)
if ret is False:
    print("... Failed, ", reader.get_last_error())
    sys.exit(0)

else:
    print("...", ret)

# Connection is successfull
print("\nReader Device-ID ...")
print("...", reader.device_id())

# diagnotic
print("\nPerforming reader diagnostic ...")
ret = reader.diagnostic()
if ret is None:
    print("... Failed, ", reader.get_last_error())
else:
    print("... ", ret)

# Set power level
print("\nSetting antenna power ...")
ret = reader.antenna_power(reader.ANTENNA_No1, reader.POWER_LOW)
if ret is False:
    print("... Failed=", reader.get_last_error())
else:
    print("... OK")

# Set traffic light
print("\nSetting Signaler(TrafficLight) ...")
traffic = {"idle": "green", "tag": "blue", "flash": 2, "time": 1}
ret = reader.signaler(traffic, buzzer=False)
if ret is False:
    print("... Failed=", reader.get_last_error())
else:
    print("... OK")

##############################################################################
# HOST MODE
print("\nSetting reader in HOST MODE ...")
ret = reader.change_mode(reader.MODE_HOST)
if ret is None:
    print("... Failed, ", reader.get_last_error())
    reader.disconnect()
    sys.exit(0)
elif ret is False:
    print("... ALREADY SET")
else:
    print("... OK")

# Do rf reset
print("\nPerforming RF Reset ...")
ret = reader.rf_controller_reset()
if ret is None:
    print("... Failed, ", reader.get_last_error())
else:
    print("... ", ret)

time.sleep(1.0)

# perform inventory
print("\nDoing Inventory ...")
antennas = [reader.ANTENNA_No1, reader.ANTENNA_No2]
ret = reader.HostMode.inventory(antennas)
if ret is None:
    print("... Failed, ", reader.get_last_error())
else:
    print("... ", ret)

##############################################################################
# BRM MODE
flags = {
    "uid": True,
    "db": False,
    "lsb": False,
    "antno": False,
    "time": False,
    "date": False,
    "input": False,
    "mac": False,
    "antext": True,
    "antstore": False,
    "readall": False,
    "bank": 1,
    "dbaddr": 0,
    "dbn": 1,
}
print("\nSetting ReadModeData ...")
ret = reader.read_mode_data(flags)
if ret is None:
    print("... Failed, ", reader.get_last_error())
else:
    print("... ", ret)

print("\nSetting ReadModeFilter ...")
ret = reader.read_mode_filter(transpondervalidtime=2)
if ret is None:
    print("... Failed, ", reader.get_last_error())
else:
    print("... ", ret)

# Enter BRM mode
print("\nSetting reader in BRM MODE ...")
ret = reader.change_mode(reader.MODE_BRM)
if ret is None:
    print("... Failed, ", reader.get_last_error())
    reader.disconnect()
    sys.exit(0)
elif ret is False:
    print("... ALREADY SET")
else:
    print("... OK")

# Do rf reset
print("\nPerforming RF Reset ...")
ret = reader.rf_controller_reset()
if ret is None:
    print("... Failed, ", reader.get_last_error())
else:
    print("... ", ret)

time.sleep(1.0)

# BRM SCAN
ret = reader.BufferReadMode.scan_till_no_unique_tags(noUniqueTagWaitCount=50)
print(reader.get_last_error_str(), ret)


##############################################################################
# NOTIFICATION MODE
print("\nSetting reader in NOTIFICATION MODE ...")
ret = reader.change_mode(reader.MODE_NOTIFICATION)
if ret is None:
    print("... Failed, ", reader.get_last_error())
    reader.disconnect()
    sys.exit(0)
elif ret is False:
    print("... ALREADY SET")
else:
    print("... OK")

# Configure Notification channel
print("\nSetting NOTIFICATION channel ...")
ret = reader.notification_channel(
    ackData=True, dstHost=("192.168.0.70", 10002), keepAlive=(False, 5), holdTime=5
)
if ret is False:
    print("... Failed, ", reader.get_last_error())
else:
    print("... ", ret)

# Do rf reset
print("\nPerforming RF Reset ...")
ret = reader.rf_controller_reset()
if ret is None:
    print("... Failed, ", reader.get_last_error())
else:
    print("... ", ret)

dq = queue.Queue()
print("\nStarting Notification task ...")
ret = reader.NotificationMode.start(10002, dq, True)
if ret is None or ret is False:
    print("... Failed, ", reader.get_last_error())
else:
    print("... ", ret)

# wait for data
try:
    while True:
        data = dq.get()
        if data:
            print("## NOTIFICATION_DATA: ", data)

except KeyboardInterrupt:
    reader.NotificationMode.stop()
    print("exiting")

# disconnect
print("\nDisconnecting from reader ...")
reader.disconnect()
print("... Done")

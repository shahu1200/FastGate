#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import queue
import logging

print("Importing 'itekfeig' module ...")
try:
    from itekfeig import FeigLogger
    from itekfeig import LRU1002, LRU500i
except ImportError:
    print("itekfeig package not installed")
    sys.exit(0)
print("... OK")

# This will return ROOT logger, with log file in HOME folder
# and log level set to DEBUG
logger = FeigLogger(loggerLevel=logging.DEBUG)
reader = LRU500i("poe")

# Connect to the reader
print("Connecting to reader ...")
settings = {"IP": "192.168.1.153", "PORT": 10001}
ret = reader.connect(reader.INTERFACE_ETHERNET, settings)

# Enter Notification mode
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
# note: assuming THIS HOST IP is already set in the reader
# TODO: add configuration
try:
    while True:
        print(dq.get())

except KeyboardInterrupt:
    reader.NotificationMode.stop()
    print("exiting")

# disconnect
print("\nDisconnecting from reader ...")
reader.disconnect()
print("... Done")

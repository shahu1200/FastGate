#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import sys
import uuid
import logging

print("Importing 'itekfeig' module ...")
try:
    from itekfeig import FeigLogger
    from itekfeig import LRU1002
except ImportError:
    print("itekfeig package not installed")
    sys.exit(0)
print("... OK")

# This will return ROOT logger, with log file in HOME folder
# and log level set to DEBUG
# logger = FeigLogger(loggerLevel=logging.DEBUG)
reader = LRU1002()

# Connect to the reader
print("\nConnecting to reader ...")
settings = {"PORT": "/dev/ttyS3", "BAUDRATE": 38400, "PARITY": "NONE"}
ret = reader.connect(reader.INTERFACE_SERIAL, settings)
if ret is False:
    print("... Failed, ", reader.get_last_error())
    sys.exit(0)

else:
    print("...", ret)

# Connection is successfull
print("\nReader Device-ID ...")
print("...", reader.device_id())

# Enter Host mode
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
antennas = [reader.HostMode.ANTENNA_No1, reader.HostMode.ANTENNA_No2]
ret = reader.HostMode.inventory()
if ret is None:
    print("... Failed, ", reader.get_last_error())
else:
    print("... ", ret)

tag = ret[0]
access_password = "12345678"

print("\nReading EPC memory with ACCESS password ...")
ret = reader.HostMode.read_epc_memory(tag["epc"], tag["tid"], 0, 8, access_password)
if ret is None:
    print("... Failed, ", reader.get_last_error())
else:
    print("... ", ret)

print("\nWriting EPC memory with ACCESS password ...")
newEpc = uuid.uuid4().hex[0:24]
ret = reader.HostMode.write_epc_memory(tag["epc"], tag["tid"], newEpc, access_password)
if ret is None or ret is False:
    print("... Failed, ", reader.get_last_error())
else:
    print("... ", ret)

# disconnect
print("\nDisconnecting from reader ...")
reader.disconnect()
print("... Done")

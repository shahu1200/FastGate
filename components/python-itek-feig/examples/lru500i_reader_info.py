#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import logging
import time

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
# logger = FeigLogger(loggerLevel=logging.DEBUG)
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


# get complete reader information
print("\nReading complete information from reader ...")
ret = reader.get_reader_info()
if ret is None:
    print("... Failed, ", reader.get_last_error())
else:
    print("... ", ret)

# diagnotic
print("\nPerforming reader diagnostic ...")
ret = reader.diagnostic()
if ret is None:
    print("... Failed, ", reader.get_last_error())
else:
    print("... ", ret)

# software version
print("\nReader Software version ...")
ret = reader.get_software_version()
if ret is None:
    print("... Failed, ", reader.get_last_error())
else:
    print("... ", ret)

# Current NotificationChannel settings
print("\nCurrent NotificationChannel settings ...")
ret = reader.notification_channel()
if ret is None:
    print("... Failed, ", reader.get_last_error())
else:
    print("... ", ret)

# Current ReadModeData settings
print("\nCurrent ReadModeData settings ...")
ret = reader.read_mode_data()
if ret is None:
    print("... Failed, ", reader.get_last_error())
else:
    print("... ", ret)

# Current ReadModeFilter settings
print("\nCurrent ReadModeFilter settings ...")
ret = reader.read_mode_filter()
if ret is None:
    print("... Failed, ", reader.get_last_error())
else:
    print("... ", ret)

# Current Antenna Mmultiplexing settings
print("\nCurrent Antenna Multiplexing settings ...")
ret = reader.antenna_multiplexing()
if ret is None:
    print("... Failed, ", reader.get_last_error())
else:
    print("... ", ret)

# Current Signaler settings
print("\nCurrent Signaler settings ...")
ret = reader.signaler()
if ret is None:
    print("... Failed, ", reader.get_last_error())
else:
    print("... ", ret)

# disconnect
print("\nDisconnecting from reader ...")
reader.disconnect()
print("... Done")

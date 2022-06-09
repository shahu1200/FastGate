#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import logging

print('Importing "itekfeig" module ...')
try:
    from itekfeig import FeigLogger
    from itekfeig import FeigReader
except ImportError:
    print("itekfeig package not installed")
    sys.exit(0)
print("... OK")

# This will return ROOT logger, with log file in HOME folder
# and log level set to DEBUG
# logger = FeigLogger(loggerLevel=logging.DEBUG)
reader = FeigReader("LRU1002")

# Connect to the reader
print("\nConnecting to reader ...")
# settings = {"PORT": "/dev/ttyS3", "BAUDRATE": 38400, "PARITY": "NONE"}
# ret = reader.connect(reader.INTERFACE_SERIAL, settings)
settings = {"IP": "192.168.6.15", "PORT": 10001}
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

# disconnect
print("\nDisconnecting from reader ...")
reader.disconnect()
print("... Done")

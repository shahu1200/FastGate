#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import sys
from binascii import hexlify

TR_TYPE_BARCODE = 0xC2
TR_TYPE_EPC_C1G2 = 0x84

IDDT_EPC = 0x00
IDDT_EPC_TID = 0x02


def notif_parser(data):
    # print(hexlify(data))

    #status = data[0]
    tr_data1 = data[1]
    if tr_data1 & 0x80:  # entension
        tr_data2 = data[2]
        data_sets = data[3] * 256 + data[4]
        data = data[5:]  # remainin data

    else:
        tr_data2 = 0
        data_sets = data[2] * 256 + data[3]
        data = data[4:]  # remainin data

    tags = []

    for _ in range(0, data_sets):
        tag = {}

        #rec_len = data[0] * 256 + data[1]
        offset = 2
        if tr_data1 & 0x01:  # IDD set
            tr_type = data[offset + 0]

            tag["iddt"] = data[offset + 1]
            idd_len = data[offset + 2]

            idd_start = offset + 3
            idd_end = idd_start + idd_len
            idd = data[idd_start:idd_end]

            if TR_TYPE_BARCODE == tr_type:
                tag["tr_type"] = "BARCODE"
                tag["idd"] = idd.decode("ascii")

            elif TR_TYPE_EPC_C1G2 == tr_type:
                tag["tr_type"] = "EPC_C1G2"
                tag["idd"] = hexlify(idd).decode("ascii")

            else:
                print("Error TrType=", data[offset + 0])
                raise ValueError

            offset = idd_end

        if tr_data1 & 0x80:  # extenasion flag

            if tr_data2 & 0x01:  # Input data
                tag["button"] = data[offset + 0]
                offset += 2

            if tr_data2 & 0x04:  # Scanner ID
                tag["scanner_id_type"] = data[offset + 0]
                sc_len = data[offset + 1]
                sc_start = offset + 2
                sc_end = sc_start + sc_len
                tag["scanner_id"] = data[sc_start:sc_end].decode("ascii")

        # data = data[rec_len:]
        tags.append(tag)

    return tags


###############################################################################
###############################################################################
###############################################################################
print("Importing 'itekfeig' module ...")
try:
    import itekfeig as feig
except ImportError:
    print("itekfeig package not installed")
    sys.exit(0)
print("... OK")

reader = feig.HyWear()

# Connect to the reader
print("\nConnecting to reader ...")
# settings = {"PORT": "/dev/ttyAMA0", "BAUDRATE": 38400, "PARITY": "NONE"}
settings = {"PORT": "COM8", "BAUDRATE": 38400, "PARITY": "NONE"}
ret = reader.connect(reader.INTERFACE_SERIAL, settings)
if ret is False:
    print("... Failed, ", reader.get_last_error())
    sys.exit(0)

else:
    print("...", ret)

# print(reader.get_reader_info())
print(reader.diagnostic())

# Do rf reset
print("\nPerforming RF Reset ...")
ret = reader.rf_controller_reset()
if ret is None:
    print("... Failed, ", reader.get_last_error())
else:
    print("...", ret)

state = 0

while True:
    # this is blocking read
    data = reader._interface.read(timeout=None)
    # print(hexlify(data))

    if data[0] == 0x22:  # scan event
        data = notif_parser(data[1:])

        print("\n>> RECEIVED SCAN EVENT <<")
        print("Data=", data)

        # send output
        output = [
            {
                "type": "led",
                "pin": reader.LED_GREEN,
                "mode": "flash",
                "freq": 2,
                "time": 10,
            },
            {
                "type": "buzzer",
                "mode": "flash",
                "freq": 2,
                "time": 10,
            },
        ]

        print("Send output ...")
        ret = reader.set_output(output, skipRx=True)
        if ret is True:
            print("... OK")
        else:
            print("... Fail", reader.get_last_error())

        time.sleep(1.5)  # wait till output command is executed

    #########################################################################
    if state == 0:
        state = 1

        print("Adjusting scan mode for BUTTON event ...")
        ret = reader.adjust_scanmode(idd=False, button=True, scannerId=False)
        if ret is None or ret is False:
            print("... Failed, ", reader.get_last_error())
        else:
            print("... ", ret)

    elif state == 1:
        state = 0

        print("Set RF OFF ...")
        ret = reader.rf_onoff(False, maintainhost=True)
        if ret is None or ret is False:
            print("... Failed, ", reader.get_last_error())
        else:
            print("... ", ret)
        time.sleep(0.1)

        # time.sleep(6000.0)

        print("Inventory ...")
        ret = reader.HostMode.inventory()
        if ret is None:
            print("... Failed, ", reader.get_last_error())
        else:
            print("... ", ret)
        time.sleep(0.1)

        print("Set RF ON ...")
        ret = reader.rf_onoff(True)
        if ret is None or ret is False:
            print("... Failed, ", reader.get_last_error())
        else:
            print("... ", ret)
        time.sleep(1.0)

# disconnect
print("\nDisconnecting from reader ...")
reader.disconnect()
print("... Done")

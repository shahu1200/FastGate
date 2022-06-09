"""
Feig HyWear Reader
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import threading
import time
from binascii import hexlify
from copy import deepcopy

from ..common.feig_base import FeigBase
from ..common.feig_errors import FeigError
from ..common.feig_reader_ids import FEIG_READER_IDS

VALID_CONFIG_MEMORY_LIST = [
    0,  # Passwords
    1,  # Interface and Mode
    2,  # Digital Inputs/Outputs
    3,  # RF Interface
    4,  # Transponder Parameter
    5,  # Anticollision
    9,  # Antenna Read Input/Output
    10,  # Trigger
    11,  # Read Mode - Data
    12,  # Read Mode - Filter
    13,  # Scan Mode
    15,  # Antenna Multiplexing
    16,  # Persistence Reset
    20,  # RF parameter
    22,
    23,
    24,
    25,
    26,
    27,  # Selection MASK
    33,
    34,  # LAN Hostname
    40,
    41,  # LAN Settings 1,2
    47,  # Summer Winter Time
    49,  # Notification
    63,  # Customer
]

READER_INFO_MODE_LIST = [
    0x00,  # RF-Controller Firmware
    0x03,  # RF Decoder
    0x05,  # Bootloaser
    0x09,  # Wifi/Bluetooth
    0x0B,  # Barcode
    0x10,  # Hardware Information
    0x15,  # RF-Stack Information
    0x40,  # CFG-Information for read
    0x41,  # CFG-Information for write
    0x54,  # wifi general
    0x55,  # wifi ip address
    0x56,  # Wifi netmask
    0x57,  # Wifi gateway
    0x80,  # Device-ID (Information is required for Firmware upgrades)
    0x81,  # Device Info 2
]


logger = logging.getLogger()
logger.addHandler(logging.NullHandler())


class HyWear(FeigBase):
    # Reader Type, use this to match after connection
    READER_NAME = "HYWEAR"
    READER_TYPE = FEIG_READER_IDS[READER_NAME]

    INTERFACE_SERIAL = 0
    INTERFACE_ETHERNET = 1

    MODE_HOST = 0x00
    MODE_NOTIFICATION = 0xC0

    ANTENNA_OFF = 0
    ANTENNA_ON = 1

    POWER_LOW = 0
    POWER_MEDIUM = 1
    POWER_FULL = 2

    LED_GREEN = 1
    LED_RED = 2
    LED_BLUE = 3
    LED_YELLOW = 4

    def __init__(self):
        super().__init__()

        self._reader_info = {}
        self._device_id = None
        self._callback = None

        self._event = threading.Event()
        self._thread = None

    ####################################################################################
    ####    READER CONNECTION API
    ####################################################################################

    def connect(self, interface, settings) -> bool:
        """Connect to the reader using one of its interface with given settings.
        Onece the connection is established, a complete aconfiguration is read
        from the reader.

        Args:
            interface: one of the supported interface
            settings: of selected interface

        Returns:
            bool: True if connection is sccessfull

        Raises:
            ValueError for incorrect data
        """
        if interface == self.INTERFACE_SERIAL:
            from serial import PARITY_NONE, PARITY_EVEN, PARITY_ODD
            from ..interface.feig_serial import FeigSerial

            if settings["PARITY"] == "NONE":
                parity = PARITY_NONE
            elif settings["PARITY"] == "EVEN":
                parity = PARITY_EVEN
            elif settings["PARITY"] == "ODD":
                parity = PARITY_ODD
            else:
                raise ValueError("NotSupported:Parity")

            FeigBase._interface = FeigSerial()
            opened = FeigBase._interface.open(
                settings["PORT"], settings["BAUDRATE"], parity
            )
            if opened is False:
                FeigBase._last_error = FeigError.SERIAL
                err_msg = "Failed to connect to {} {}".format(
                    settings["PORT"], FeigBase._interface.error
                )
                logger.error(err_msg)
                return False

        elif interface == self.INTERFACE_ETHERNET:
            from ..interface.feig_ethernet import FeigEthernet

            FeigBase._interface = FeigEthernet()
            opened = FeigBase._interface.open(settings["IP"], settings["PORT"])
            if opened is False:
                FeigBase._last_error = FeigError.ETHERNET
                return False

        else:
            raise ValueError("NotSupported:Interface")

        if FeigBase._interface._error is not None:
            FeigBase._last_error = FeigBase._interface._error
            return False

        # Forced: Antenna OFF, if tags are present in the feild
        # connection to reader takes time or fail
        self.rf_onoff(self.ANTENNA_OFF)

        time.sleep(0.1)

        # Get reader type
        ret = self._get_reader_type()
        if not ret:
            logger.error("Failed to get reader ID")
            return False

        if ret != self.READER_TYPE:
            FeigBase._last_error = FeigError.INVALID_READER
            FeigBase._interface.close()
            FeigBase._interface = None
            err_msg = "Expected ID={}, received ID={}".format(self.READER_TYPE, ret)
            logger.error(err_msg)
            return False

        # Get ALL INFO from the reader
        self.get_reader_info()

        time.sleep(0.1)

        # Get ALL CONFIGURATION from reader memory
        ret = self.read_all_config()
        if ret is None:
            return False

        time.sleep(0.1)

        # Configure operating modes
        from ..common.feig_host import FeigHost
        self.HostMode = FeigHost(FeigBase._interface, FeigBase._last_error) # pylint: disable=C0103

        from ..common.feig_notification import FeigNotification
        self.NotificationMode = FeigNotification(FeigBase._interface, FeigBase._last_error) # pylint: disable=C0103

        return True

    def disconnect(self):
        """Disconnect from current reader"""
        if FeigBase._interface:
            FeigBase._interface.close()

    def rf_onoff(self, onoff: bool, maintainhost=False):
        """Turn ON/OFF individual antenna"""

        if onoff is True:
            rf_output = 0x01
        else:
            rf_output = 0x00

        if maintainhost is True:
            rf_output += 0x80

        cmd = [0x6A, rf_output]
        data = FeigBase._interface.transfer(1.0, cmd)
        if data is None:
            FeigBase._last_error = FeigError.COMM_TIMEOUT
            return

        FeigBase._last_error = FeigError.INVALID_RESPONSE
        if data[0] == 0x6A:
            FeigBase._last_error = self._feig_status_parser(data[1])
            if FeigBase._last_error is FeigError.OK:
                return True

        return False

    def _set_output_record_parser(self, out_rec: dict):
        out_nr = 0
        if out_rec["type"] == "led":
            out_nr = 0x20 + out_rec["pin"]
        elif out_rec["type"] == "buzzer":
            out_nr = 0x40 + 1
        elif out_rec["type"] == "vibration":
            out_nr = 0x60 + 1
        elif out_rec["type"] == "trigger":
            out_nr = 0xE0 + 1
        else:
            raise ValueError("Invalid output type")

        out_s = 0
        if out_rec["mode"] == "flash":
            out_s = 3
            if out_rec["freq"] == 1:
                out_s += 3 << 2
            elif out_rec["freq"] == 2:
                out_s += 2 << 2
            elif out_rec["freq"] == 4:
                out_s += 1 << 2
            elif out_rec["freq"] == 8:
                out_s += 0 << 2
            else:
                raise ValueError("Invalid output flash frequency")
        elif out_rec["mode"] == "on":
            out_s = 1
        elif out_rec["mode"] == "off":
            out_s = 2
        elif out_rec["mode"] == "unchange":
            out_s = 0
        else:
            raise ValueError("Invalid output mode")

        if out_rec["time"] < 1 or out_rec["time"] > 65534:
            raise ValueError("Invalid output time")
        out_time = out_rec["time"]

        return out_nr, out_s, out_time

    def set_output(self, output=None, skipRx=False):
        """Set/Configure Digital Output or Relay pins

        Args:
            out_rec: key,value as per following format
                {
                    'type': str, 'led', 'vibration', 'buzzer', 'trigger'
                    'pin': int,
                    'mode': 'on', 'off', 'flash', 'unchange'
                    'freq': int, 1,2,4,8 Hz
                    'time': int, 1 to 65534 delay corresponds to multiple of 100milli
                }
        """
        if output is None:
            cmd = [0x72, 0x01, 0x00]

        elif isinstance(output, dict):
            out_nr, out_s, out_time = self._set_output_record_parser(output)
            cmd = [
                0x72,
                0x01,
                0x01,
                out_nr,
                out_s,
                (out_time >> 8) & 0xFF,
                (out_time >> 0) & 0xFF,
            ]

        elif isinstance(output, list):
            out_n = len(output)
            cmd = [
                0x72,
                0x01,
                out_n,
            ]
            for rec in output:
                out_nr, out_s, out_time = self._set_output_record_parser(rec)
                cmd.append(out_nr)
                cmd.append(out_s)
                cmd.append((out_time >> 8) & 0xFF)
                cmd.append((out_time >> 0) & 0xFF)
        else:
            raise TypeError("Invalid output record type")

        if skipRx is True:
            FeigBase._interface.write(cmd)
            return True

        data = FeigBase._interface.transfer(1.0, cmd)
        if data is None:
            FeigBase._last_error = FeigError.COMM_TIMEOUT
            return

        FeigBase._last_error = FeigError.INVALID_RESPONSE
        if data[0] == 0x72:
            FeigBase._last_error = self._feig_status_parser(data[1])
            if FeigBase._last_error is FeigError.OK:
                return True

    def adjust_scanmode(self, idd: bool, button: bool, scanner_id: bool) -> bool:
        """Set scanmode data

        Args:
            idd: bool, True if transponder data is required
            button: bool, True if input button data is required
            scanner_id: bool, True if barcode data is required
        """
        tr_data1 = 0x00

        cmd = [0x2A, 0x00, 0x00, 0x00]
        if idd: tr_data1 += 0x01

        if button or scanner_id:  #
            tr_data1 += 0x80
            cmd.append(tr_data1)

            tr_data2 = 0
            if button: tr_data2 += 0x01
            if scanner_id: tr_data2 += 0x04

            cmd.append(tr_data2)

        else:
            cmd.append(tr_data1)

        data = FeigBase._interface.transfer(1.0, cmd)
        if data is None:
            FeigBase._last_error = FeigError.COMM_TIMEOUT
            return False

        FeigBase._last_error = FeigError.INVALID_RESPONSE
        if data[0] == 0x2A:
            FeigBase._last_error = self._feig_status_parser(data[1])
            if FeigBase._last_error is FeigError.OK:
                return True

        return False

    def configuration_parser(self, cfg_data: list):
        """
        Parse configuration data.
        .. TODO::
        """
        return True

    def _reader_info_parser(self, mode, data):
        if mode == 0x00:
            self._reader_info["RFControllerSoftwareRevision"] = hexlify(
                data[0:3]
            ).decode("ascii")
            self._reader_info["HardwareType"] = hexlify(data[3:4]).decode("ascii")
            self._reader_info["ReaderType"] = int(data[4])
            self._reader_info["TransponderTypes"] = hexlify(data[5:7]).decode("ascii")
            self._reader_info["MaxRXBufferSize"] = data[7] * 256 + data[8]
            self._reader_info["MaxTXBufferSize"] = data[9] * 256 + data[10]

        elif mode == 0x03:
            pass

        elif mode == 0x05:
            pass

        elif mode == 0x09:
            pass

        elif mode == 0x0B:
            pass

        elif mode == 0x10:
            internal_use = (
                hexlify(data[0:2]).decode("ascii")
                + "-"
                + hexlify(data[2:4]).decode("ascii")
                + "-"
                + hexlify(data[4:6]).decode("ascii")
            )
            self._reader_info["InternalUse"] = internal_use

            freq = ""
            if data[6] & 0x80:
                freq += "HF,"
            if data[6] & 0x40:
                freq += "UHF,"
            if data[6] & 0x04:
                freq += "LOCK,"
            else:
                freq += "UNLOCK,"
            if data[6] & 0x02:
                freq += "FCC,"
            if data[6] & 0x01:
                freq += "EU"
            self._reader_info["Frequency"] = freq

            prt = ""
            if data[7] & 0x01:
                prt += "SERIAL,"
            if data[7] & 0x02:
                prt += "RS485,"
            if data[7] & 0x04:
                prt += "LAN,"
            if data[7] & 0x08:
                prt += "WLAN,"
            if data[7] & 0x10:
                prt += "USB,"
            if data[7] & 0x20:
                prt += "BT,"
            if data[7] & 0x80:
                prt += "DISCOVERY"
            self._reader_info["SupportedPorts"] = prt

        elif mode == 0x15:
            self._reader_info["RFStackSoftwareRevision"] = hexlify(data[0:2]).decode(
                "ascii"
            )

        elif mode == 0x16:
            # TODO
            pass

        elif mode == 0x40:
            self._reader_info["ReadPages"] = data[0] * 256 + data[1]
            self._reader_info["ReadPermission"] = hexlify(data[2:10]).decode("ascii")

        elif mode == 0x41:
            self._reader_info["WritePages"] = data[0] * 256 + data[1]
            self._reader_info["WritePermission"] = hexlify(data[2:10]).decode("ascii")

        elif mode == 0x50:
            mac = (
                hexlify(data[1:2]).decode("ascii")
                + ":"
                + hexlify(data[2:3]).decode("ascii")
                + ":"
                + hexlify(data[3:4]).decode("ascii")
                + ":"
                + hexlify(data[4:5]).decode("ascii")
                + ":"
                + hexlify(data[5:6]).decode("ascii")
                + ":"
                + hexlify(data[6:7]).decode("ascii")
            )
            self._reader_info["MACAddress"] = mac

            if data[7] & 0x01:
                self._reader_info["AutoNegotiation"] = "Off"
            else:
                self._reader_info["AutoNegotiation"] = "On"

            if data[7] & 0x02:
                self._reader_info["DuplexMode"] = "Full Duplex"
            else:
                self._reader_info["DuplexMode"] = "Half Duplex"

            if data[7] & 0x04:
                self._reader_info["Speed"] = "100 Mbit"
            else:
                self._reader_info["Speed"] = "10 Mbit"

        elif mode == 0x51:
            if (data[0] & 0x02) == 0x02:  # IPv4 Supported
                ip = (
                    str(data[1])
                    + "."
                    + str(data[2])
                    + "."
                    + str(data[3])
                    + "."
                    + str(data[4])
                )
                self._reader_info["IPv4Address"] = ip
            else:
                self._reader_info["IPv4Address"] = "NA"

        elif mode == 0x52:
            if (data[0] & 0x02) == 0x02:  # IPv4 Supported
                nm = (
                    str(data[1])
                    + "."
                    + str(data[2])
                    + "."
                    + str(data[3])
                    + "."
                    + str(data[4])
                )
                self._reader_info["IPv4Netmask"] = nm
            else:
                self._reader_info["IPv4Netmask"] = "NA"

        elif mode == 0x53:
            if (data[0] & 0x02) == 0x02:  # IPv4 Supported
                gw = (
                    str(data[1])
                    + "."
                    + str(data[2])
                    + "."
                    + str(data[3])
                    + "."
                    + str(data[4])
                )
                self._reader_info["IPv4Gateway"] = gw
            else:
                self._reader_info["IPv4Gateway"] = "NA"

        elif mode == 0x54:
            pass

        elif mode == 0x55:
            pass

        elif mode == 0x56:
            pass

        elif mode == 0x57:
            pass

        elif mode == 0x60:
            self._reader_info["Inputs"] = data[0]
            self._reader_info["Outputs"] = data[1]
            self._reader_info["Relays"] = data[2]

        elif mode == 0x80:
            self._reader_info["DeviceID"] = hexlify(data[0:4]).decode("ascii")
            self._reader_info["CustomerID"] = hexlify(data[4:8]).decode("ascii")
            self._reader_info["FirmwareVersion"] = hexlify(data[8:10]).decode("ascii")
            self._reader_info["TransponderDriver"] = hexlify(data[10:12]).decode(
                "ascii"
            )
            self._reader_info["FirmwareFunctions"] = hexlify(data[12:14]).decode(
                "ascii"
            )

        elif mode == 0x81:
            # device info2
            pass

    def get_reader_info(self):
        """Get complete reader information
        """
        if len(self._reader_info) == 0:

            for mode in READER_INFO_MODE_LIST:
                cmd = [0x66, mode]
                data = FeigBase._interface.transfer(1.0, cmd)
                if data is None:
                    FeigBase._last_error = FeigError.COMM_TIMEOUT
                    return

                FeigBase._last_error = FeigError.INVALID_RESPONSE
                if data[0] == 0x66:
                    FeigBase._last_error = self._feig_status_parser(data[1])
                    if FeigBase._last_error is FeigError.OK:
                        self._reader_info_parser(mode, data[2:])

        return deepcopy(self._reader_info)

    @staticmethod
    def _diagnostic_parser(data):

        def test_error(x) -> str:
            if x: return "FAIL"
            return "OK"

        diag = {}
        data_set = data[0]
        offset = 1
        for _ in range(0, data_set):
            mode = data[offset]
            if mode == 0x04:
                flagA = data[offset + 1]
                flagB = data[offset + 2]

                hwerr = {}
                hwerr["TriggerLocked"] = test_error(flagA & 0x02)
                hwerr["Barcode"] = test_error(flagA & 0x04)
                hwerr["WiFi_Bluetooth"] = test_error(flagA & 0x08)
                hwerr["Battery"] = test_error(flagA & 0x20)

                hwerr["RFDecoder"] = test_error(flagB & 0x08)
                hwerr["EEPROM"] = test_error(flagB & 0x01)

                diag["HardwareError"] = hwerr

            elif mode == 0x10:
                voltage = data[offset + 1] * 256 + data[offset + 2]
                diag["Battery"] = str(voltage) + "mV"

            elif mode == 0x20:
                # FIRMWARE
                diag["Firmware"] = data[offset + 1 :].rstrip(b"\x00").decode("ascii")

            offset = offset + 30 + 1

        return diag

    def diagnostic(self) -> dict:
        """Perform reader diagnostic"""
        cmd = [0x02, 0x00, 0x08, 0xFF, 0x6E, 0xFF, 0x30, 0xD3]
        data = FeigBase._interface.transfer(1.0, bytes(cmd))
        if data is None:
            FeigBase._last_error = FeigError.COMM_TIMEOUT
            return

        FeigBase._last_error = FeigError.INVALID_RESPONSE
        if data[0] == 0x6E:
            FeigBase._last_error = self._feig_status_parser(data[1])
            if FeigBase._last_error is FeigError.OK:
                return self._diagnostic_parser(data[2:])

    def device_id(self) -> str:
        """Returns reader device ID"""
        return deepcopy(self._reader_info["DeviceID"])

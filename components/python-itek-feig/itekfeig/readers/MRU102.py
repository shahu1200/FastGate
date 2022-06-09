"""
Feig MRU102 reader
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
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
    11,  # Read Mode - Data
    12,  # Read Mode - Filter
    13,  # Scan Mode
    15,  # Antenna Multiplexing
    16,  # Persistence Reset
    20,  # RF parameter
    22,
    23,  # Selection MASK
    33,
    34,  # LAN Hostname
    36,  # RF interface
    37,  # Transponder
    38,  # Anticollision
    40,
    41,  # LAN Settings 1,2, valid for ISC.MRU102-PoE
    49,  # Notification, valid for ISC.MRU102-PoE
    63,  # Customer
]

READER_INFO_MODE_LIST = [
    0x00,  # RF-Controller Firmware
    0x05,  # Bootloader version
    0x10,  # Hardware Information
    0x15,  # RF-Stack Information
    0x40,  # CFG-Information for read
    0x41,  # CFG-Information for write
    0x50,  # LAN-Information: MAC
    0x51,  # LAN-Information: IP-Address
    0x52,  # LAN-Information: Netmask
    0x53,  # LAN-Information: Gateway-Address
    0x80,  # Device-ID (Information is required for Firmware upgrades)
]

ANTENNA_POWER = {
    0x08: 50,
    0x10: 100,
    0x11: 200,
    0x12: 300,
    0x13: 400,
    0x14: 500,
}

ANTENNA_POWER_REVERSE = {v: k for k, v in ANTENNA_POWER.items()}


logger = logging.getLogger()
logger.addHandler(logging.NullHandler())


class MRU102(FeigBase):
    # Reader Type, use this to match after connection
    READER_NAME = "MRU102"
    READER_TYPE = FEIG_READER_IDS[READER_NAME]

    INTERFACE_SERIAL = 0
    INTERFACE_ETHERNET = 1

    MODE_HOST = 0x00
    MODE_SCAN = 0x01
    MODE_BRM = 0x80
    MODE_NOTIFICATION = 0xC0

    ANTENNA_OFF = 0x00
    ANTENNA_No1 = 0x01
    ANTENNA_No2 = 0x02
    ANTENNA_No3 = 0x03
    ANTENNA_Internal = 0x04

    MAX_ANTENNA = 4

    POWER_LOW = 50
    POWER_MEDIUM = 300
    POWER_FULL = 500

    RSSI_MIN = 0
    RSSI_MAX = 255

    def __init__(self):
        # print("MRU102.py class MRU102 init")
        super().__init__()
        self._reader_info = {}
        self._device_id = None

    ####################################################################################
    ####    READER CONNECTION API
    ####################################################################################

    def connect(self, interface, settings):
        """Connect to the reader using one of its interface with given settings.
        Onece the connection is established, a complete aconfiguration is read
        from the reader.

        Args:
            interface: one of the supported interface
            settings: of selected interface

        Returns:
            bool: True if connection is sccessfull
        """

        # Configure interface
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

        if FeigBase._interface.error != FeigError.OK:
            FeigBase._last_error = FeigBase._interface.error
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

        # Get ALL CONFIGURATION from reader memory
        ret = self.read_all_config()
        if ret is None:
            return False

        time.sleep(0.1)

        # Configure operating modes
        from ..common.feig_host import FeigHost

        self.HostMode = FeigHost(FeigBase._interface, FeigBase._last_error)

        from ..common.feig_buffer_read import FeigBufferRead

        self.BufferReadMode = FeigBufferRead(FeigBase._interface, FeigBase._last_error)

        if interface == self.INTERFACE_SERIAL:
            from ..common.feig_scan import FeigScan

            self.ScanMode = FeigScan(FeigBase._interface, FeigBase._last_error)
        elif interface == self.INTERFACE_ETHERNET:
            from ..common.feig_notification import FeigNotification

            self.NotificationMode = FeigNotification(
                FeigBase._interface, FeigBase._last_error
            )

        return True

    def disconnect(self):
        """Disconnect from current reader"""
        if FeigBase._interface:
            FeigBase._interface.close()

    ####################################################################################
    ####    READER CONTROL API
    ####################################################################################

    def rf_onoff(self, antno, maintainhost=False):
        """Turn ON/OFF individual antenna"""
        rf_output = 0
        if maintainhost is True:
            rf_output += 0x80
        rf_output += antno

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

    def set_output(self, out_rec: dict):
        """Set/Configure Digital Output or Relay pins

        Args:
            out_rec: key,value as per following format
                {
                    'type': str, 'digital' or 'relay',
                    'pin': int,
                    'mode': 'on' or 'off' or 'flash',
                    'freq': int, 1,2,4,8 Hz
                    'time': int, 1 to 65535 delay corresponds to multiple of 100milli
                }
        """
        if out_rec["type"] == "digital":
            out_type = 0x00
        elif out_rec["type"] == "relay":
            out_type = 0x80
        else:
            raise ValueError("Invalid Value")
        out_type = 0x80 + out_rec["pin"]

        if out_rec["mode"] == "on":
            out_state = 0x01
        elif out_rec["mode"] == "off":
            out_state = 0x02
        elif out_rec["mode"] == "flash":
            out_state = 0x03
        else:
            raise ValueError("Invalid Value")

        if out_rec["freq"] == 1:
            out_state += 0x03 * 4
        elif out_rec["freq"] == 2:
            out_state += 0x02 * 4
        elif out_rec["freq"] == 4:
            out_state += 0x01 * 4
        elif out_rec["freq"] == 8:
            out_state += 0x00 * 4
        else:
            raise ValueError("Invalid Value")

        if out_rec["time"] < 1 or out_rec["time"] > 65535:
            raise ValueError("Invalid Value")
        out_time = out_rec["time"]

        cmd = [
            0x72,
            0x01,
            0x01,
            out_type,
            out_state,
            (out_time >> 8) & 0xFF,
            (out_time >> 0) & 0xFF,
        ]
        data = FeigBase._interface.transfer(1.0, cmd)
        if data is None:
            FeigBase._last_error = FeigError.COMM_TIMEOUT
            return

        FeigBase._last_error = FeigError.INVALID_RESPONSE
        if data[0] == 0x72:
            FeigBase._last_error = self._feig_status_parser(data[1])
            if FeigBase._last_error is FeigError.OK:
                return True

    def get_input(self):
        """Get reader INPUT pin status"""
        cmd = [0x02, 0x00, 0x07, 0xFF, 0x74, 0x66, 0x60]
        data = FeigBase._interface.transfer(1.0, bytes(cmd))
        if data is None:
            FeigBase._last_error = FeigError.COMM_TIMEOUT
            return

        FeigBase._last_error = FeigError.INVALID_RESPONSE
        if data[0] == 0x74:
            FeigBase._last_error = self._feig_status_parser(data[1])
            if FeigBase._last_error is FeigError.OK:
                in1 = data[2] & 0x01
                in2 = (data[2] >> 1) & 0x01
                return in1, in2

    def change_mode(self, mode):
        """Change Reader mode

        Args:
            mode: one of the supporeted operating mode

        Returns:
            None: Call get_last_error() for more reason
            bool: If True, new mode is set in the reader
        """
        cfgData = self.read_config(1)
        if cfgData is None:
            return False

        if cfgData[13] == mode:  # Current Mode is same
            FeigBase._last_error = FeigError.MODE_SAME
            return False

        # update mode
        cfgData[13] = mode

        ret = self.write_config(1, cfgData)
        if ret is None:
            return False

        FeigBase._current_mode = mode

        return True

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
                # EEPROM
                eeprom = {}
                int_error = data[offset + 1] * 256 + data[offset + 2]

                eeprom["EE_DEV1"] = test_error(int_error & 0x0001)
                eeprom["RF_DECODER"] = test_error(int_error & 0x0008)
                eeprom["ParameterMismatch"] = test_error(int_error & 0x0010)
                eeprom["TEMP_WARN"] = test_error(int_error & 0x0020)
                eeprom["PeripheryError"] = test_error(int_error & 0x0400)

                diag["Eeprom"] = eeprom

            offset = offset + 30 + 1

        return diag

    def diagnostic(self):
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

    ####################################################################################
    ####    READER INFO API
    ####################################################################################
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

        elif mode == 0x05:
            self._reader_info["RFCBootloaderSoftwareRevision"] = hexlify(
                data[0:2]
            ).decode("ascii")

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
            if data[6] & 0x40:
                freq += "UHF,"
            if data[6] & 0x02:
                freq += "FCC,"
            if data[6] & 0x01:
                freq += "EU"
            self._reader_info["Frequency"] = freq

            prt = ""
            if data[7] & 0x01:
                prt += "SERIAL,"
            if data[7] & 0x04:
                prt += "LAN,"
            if data[7] & 0x10:
                prt += "USB,"
            if data[7] & 0x80:
                prt += "DISCOVERY"
            self._reader_info["SupportedPorts"] = prt

        elif mode == 0x15:
            self._reader_info["RFStackSoftwareRevision"] = hexlify(data[0:2]).decode(
                "ascii"
            )

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

    def device_id(self) -> str:
        """Returns reader device ID"""
        return deepcopy(self._reader_info["DeviceID"])

    ####################################################################################
    ####    READER CONFIGURATION API
    ####################################################################################

    def antenna_power(self, ant, pwr_in_milliwatts: int = -1):
        """Change Antenna Power
        """
        if not (
            ant is self.ANTENNA_No1
            or ant is self.ANTENNA_No2
            or ant is self.ANTENNA_No3
            or ant is self.ANTENNA_Internal
        ):
            raise ValueError("Antenna= {0} is NOT supported".format(ant))

        # depending upon antenna read config
        if ant is self.ANTENNA_No1:
            cfg_page = 36
        else:
            cfg_page = 20

        # Get index of respective antenna
        index = 2  # default Antenna1
        if ant is self.ANTENNA_No2:
            index = 6
        elif ant is self.ANTENNA_No3:
            index = 7
        elif ant is self.ANTENNA_Internal:
            index = 8

        cfgData = self.read_config(cfg_page)
        if cfgData is None:
            return False

        if pwr_in_milliwatts == -1:
            return ANTENNA_POWER[cfgData[index]]

        # check antenna power
        # Adjust 'pwr_in_milliwatts' to nearest supported POWER
        if pwr_in_milliwatts < 100:
            pwr = ANTENNA_POWER_REVERSE[50]
        elif 100 <= pwr_in_milliwatts < 200:
            pwr = ANTENNA_POWER_REVERSE[100]
        elif 200 <= pwr_in_milliwatts < 300:
            pwr = ANTENNA_POWER_REVERSE[200]
        elif 300 <= pwr_in_milliwatts < 400:
            pwr = ANTENNA_POWER_REVERSE[300]
        elif 400 <= pwr_in_milliwatts < 500:
            pwr = ANTENNA_POWER_REVERSE[400]
        else:  # pwr_in_milliwatts >= 500:
            pwr = ANTENNA_POWER_REVERSE[500]

        cfgData[index] = pwr

        ret = self.write_config(cfg_page, cfgData)
        if ret is None:
            return False

        return True

    def antenna_rssi(self, ant, rssi):
        """Change Antenna RSSI
        """
        if not (
            ant is self.ANTENNA_No1
            or ant is self.ANTENNA_No2
            or ant is self.ANTENNA_No3
            or ant is self.ANTENNA_Internal
        ):
            raise ValueError("Antenna= {0} is NOT supported".format(ant))

        if (rssi < self.RSSI_MIN) or (rssi > self.RSSI_MAX):
            raise ValueError("RSSI= {0} is NOT supported".format(rssi))

        cfgData = self.read_config(20)
        if cfgData is None:
            return False

        # update rssi
        if ant is self.ANTENNA_No1:
            cfgData[0] = rssi

        elif ant is self.ANTENNA_No2:
            cfgData[1] = rssi

        elif ant is self.ANTENNA_No3:
            cfgData[2] = rssi

        elif ant is self.ANTENNA_Internal:
            cfgData[3] = rssi

        ret = self.write_config(20, cfgData)
        if ret is None:
            return False

        return True

    def system_timer(self, timer_value=None):
        if timer_value is None:
            # get
            cmd = [0x86]
        else:
            # set
            if not isinstance(timer_value, tuple):
                raise ValueError("Invalid Argument")

            hour = timer_value[0]
            minutes = timer_value[1]
            milli = timer_value[2]
            if (hour > 23) or (minutes > 59) or (milli > 59999):
                raise ValueError("Invalid range")

            cmd = [0x85, hour, minutes, (milli >> 8) & 0xFF, (milli >> 0) & 0xFF]

        data = FeigBase._interface.transfer(1.0, cmd)
        if data is None:
            FeigBase._last_error = FeigError.COMM_TIMEOUT
            return

        FeigBase._last_error = FeigError.INVALID_RESPONSE
        if data[0] == 0x85:  # Set
            FeigBase._last_error = self._feig_status_parser(data[1])
            if FeigBase._last_error is FeigError.OK:
                return True

        elif data[0] == 0x86:  # Get
            FeigBase._last_error = self._feig_status_parser(data[1])
            if FeigBase._last_error is FeigError.OK:
                return data[2], data[3], (data[4] * 256 + data[5])

    def system_date_time(self, date_value=None, timer_value=None):
        if date_value is None and timer_value is None:
            # get
            cmd = [0x88]
        else:
            # set
            if not isinstance(date_value, tuple):
                raise ValueError("Invalid Argument {}".format(date_value))
            if not isinstance(timer_value, tuple):
                raise ValueError("Invalid Argument {}".format(timer_value))

            century = date_value[0]
            year = date_value[1]
            month = date_value[2]
            day = date_value[3]
            timezone = date_value[4]
            if (
                (century > 99)
                or (year > 99)
                or ((month < 1) or (month > 12))
                or ((day < 1) or (day > 31))
                or (timezone > 23)
            ):
                raise ValueError("Invalid range")

            hour = timer_value[0]
            minutes = timer_value[1]
            milli = timer_value[2]
            if (hour > 23) or (minutes > 59) or (milli > 59999):
                raise ValueError("Invalid range")

            cmd = [
                0x87,
                century,
                year,
                month,
                day,
                timezone,
                hour,
                minutes,
                (milli >> 8) & 0xFF,
                (milli >> 0) & 0xFF,
            ]

        data = FeigBase._interface.transfer(1.0, cmd)
        if data is None:
            FeigBase._last_error = FeigError.COMM_TIMEOUT
            return

        FeigBase._last_error = FeigError.INVALID_RESPONSE
        if data[0] == 0x87:  # Set
            FeigBase._last_error = self._feig_status_parser(data[1])
            if FeigBase._last_error is FeigError.OK:
                return True

        elif data[0] == 0x88:  # Get
            FeigBase._last_error = self._feig_status_parser(data[1])
            if FeigBase._last_error is FeigError.OK:
                return (
                    (data[2], data[3], data[4], data[5], data[6]),
                    (data[7], data[8], (data[9] * 256 + data[10])),
                )

    def read_mode_data(self, flags=None):
        raise NotImplementedError

    def read_mode_filter(self, transpondervalidtime=None, trid=None, inevflt=None):
        raise NotImplementedError

    def antenna_multiplexing(self, muxEnable=None, selectedAntennas=None):
        raise NotImplementedError

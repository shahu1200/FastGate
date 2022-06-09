"""
Feig LRU1002 reader
"""
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from enum import unique
import ipaddress
import logging
import time
from binascii import hexlify
from copy import deepcopy
from typing import Union

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
    0x10,  # Hardware Information
    0x15,  # RF-Stack Information
    0x16,  # IDT-Stack Information
    0x40,  # CFG-Information for read
    0x41,  # CFG-Information for write
    0x50,  # LAN-Information: MAC
    0x51,  # LAN-Information: IP-Address
    0x52,  # LAN-Information: Netmask
    0x53,  # LAN-Information: Gateway-Address
    0x60,  # I/O Capabilities
    0x80,  # Device-ID (Information is required for Firmware upgrades)
]

ANTENNA_POWER = {
    0x10: 100,
    0x11: 200,
    0x12: 300,
    0x13: 400,
    0x14: 500,
    0x15: 600,
    0x16: 700,
    0x17: 800,
    0x18: 900,
    0x19: 1000,
    0x1A: 1100,
    0x1B: 1200,
    0x1C: 1300,
    0x1D: 1400,
    0x1E: 1500,
    0x1F: 1600,
    0x20: 1700,
    0x21: 1800,
    0x22: 1900,
    0x23: 2000,
}

ANTENNA_POWER_REVERSE = {v: k for k, v in ANTENNA_POWER.items()}


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class LRU1002(FeigBase):
    # Reader Type, use this to match after connection
    READER_NAME = "LRU1002"
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
    ANTENNA_No4 = 0x04

    MAX_ANTENNA = 4

    # in milliwatts
    POWER_LOW = 100
    POWER_MEDIUM = 1000
    POWER_FULL = 2000

    RSSI_MIN = 0  # disabled
    RSSI_MAX = 255

    def __init__(self):
        super().__init__()

        self._reader_info = {}
        self._deviceId = None

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
            FeigBase._interface.open(settings["PORT"], settings["BAUDRATE"], parity)

        elif interface == self.INTERFACE_ETHERNET:
            from ..interface.feig_ethernet import FeigEthernet

            FeigBase._interface = FeigEthernet()
            FeigBase._interface.open(settings["IP"], settings["PORT"])

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

        time.sleep(0.1)

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

        def test_error(x):
            if x: return "FAIL"
            return "OK"

        diag = {}
        data_set = data[0]
        offset = 1
        for _ in range(0, data_set):
            mode = data[offset]
            if mode == 0x01:
                flag_a = data[offset + 1]
                flag_b = data[offset + 2]

                rf_status = {}
                rf_status["NOISE"] = test_error(flag_a & 0x02)
                rf_status["POWER"] = test_error(flag_a & 0x10)
                rf_status["TEMP_WARNING"] = test_error(flag_a & 0x20)
                rf_status["TEMP_ALARM"] = test_error(flag_a & 0x80)

                # ANTENNA FLAGS are SET when impedance |Z| != 50
                rf_status["Antenna1"] = test_error(flag_b & 0x01)
                rf_status["Antenna2"] = test_error(flag_b & 0x02)
                rf_status["Antenna3"] = test_error(flag_b & 0x04)
                rf_status["Antenna4"] = test_error(flag_b & 0x08)

                diag["RF_Status"] = rf_status

            elif mode == 0x04:
                # EEPROM
                eeprom = {}
                int_error = data[offset + 1] * 256 + data[offset + 2]

                eeprom["EE_DEV1"] = test_error(int_error & 0x0001)
                eeprom["RF_DECODER"] = test_error(int_error & 0x0004)
                eeprom["RTC"] = test_error(int_error & 0x0040)
                eeprom["ADC"] = test_error(int_error & 0x0080)
                eeprom["IO_EXPANDER"] = test_error(int_error & 0x0100)
                eeprom["DC_OUT"] = test_error(int_error & 0x0200)
                eeprom["USB_IMAX"] = test_error(int_error & 0x0400)

                diag["Eeprom"] = eeprom

            elif mode == 0x05:
                # MUX
                diag["Mux1"] = hex(data[offset + 1])
                diag["Mux2"] = hex(data[offset + 4])
                diag["Mux3"] = hex(data[offset + 7])
                diag["Mux4"] = hex(data[offset + 10])

            elif mode == 0x20:
                # FIRMWARE
                diag["Firmware"] = data[offset + 1 :].rstrip(b"\x00").decode("ascii")

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
            # .. TODO::
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

    ##########################################################################
    ####    READER CONFIGURATION API
    ##########################################################################

    def antenna_power(self, ant, pwr_in_milliwatts: int = -1) -> Union[bool, int]:
        """Change Antenna Power

        Args:
            ant: must be one of supported ANTENNA_No*
            pwr_in_milliwatts: int, in milliwats
            if -1 return current power

        Returns:
            bool: True, if power is set in the reader
            pwr_in_milliwatts: int

        Raises:
            ValueError

        .. note:: Given power is always adjusted to nearest valid value.
        """
        if not (
            ant is self.ANTENNA_No1
            or ant is self.ANTENNA_No2
            or ant is self.ANTENNA_No3
            or ant is self.ANTENNA_No4
        ):
            raise ValueError("Antenna= {0} is NOT supported".format(ant))

        # depending upon antenna read config
        if ant is self.ANTENNA_No1:
            cfg_page = 3
        else:
            cfg_page = 20

        # Get index of respective antenna
        index = 2  # Default to Antenna1
        if ant is self.ANTENNA_No2:
            index = 10
        elif ant is self.ANTENNA_No3:
            index = 11
        elif ant is self.ANTENNA_No4:
            index = 12

        # read current configuration
        cfgData = self.read_config(cfg_page)
        if cfgData is None:
            return False

        if pwr_in_milliwatts == -1:
            return ANTENNA_POWER[cfgData[index]]

        # check antenna power
        # Adjust 'pwr_in_milliwatts' to nearest supported POWER
        if pwr_in_milliwatts < 200:
            pwr = ANTENNA_POWER_REVERSE[100]
        elif 200 <= pwr_in_milliwatts < 300:
            pwr = ANTENNA_POWER_REVERSE[200]
        elif 300 <= pwr_in_milliwatts < 400:
            pwr = ANTENNA_POWER_REVERSE[300]
        elif 400 <= pwr_in_milliwatts < 500:
            pwr = ANTENNA_POWER_REVERSE[400]
        elif 500 <= pwr_in_milliwatts < 600:
            pwr = ANTENNA_POWER_REVERSE[500]
        elif 600 <= pwr_in_milliwatts < 700:
            pwr = ANTENNA_POWER_REVERSE[600]
        elif 700 <= pwr_in_milliwatts < 800:
            pwr = ANTENNA_POWER_REVERSE[700]
        elif 800 <= pwr_in_milliwatts < 900:
            pwr = ANTENNA_POWER_REVERSE[800]
        elif 900 <= pwr_in_milliwatts < 1000:
            pwr = ANTENNA_POWER_REVERSE[900]
        elif 1000 <= pwr_in_milliwatts < 1100:
            pwr = ANTENNA_POWER_REVERSE[1000]
        elif 1100 <= pwr_in_milliwatts < 1200:
            pwr = ANTENNA_POWER_REVERSE[1100]
        elif 1200 <= pwr_in_milliwatts < 1300:
            pwr = ANTENNA_POWER_REVERSE[1200]
        elif 1300 <= pwr_in_milliwatts < 1400:
            pwr = ANTENNA_POWER_REVERSE[1300]
        elif 1400 <= pwr_in_milliwatts < 1500:
            pwr = ANTENNA_POWER_REVERSE[1400]
        elif 1500 <= pwr_in_milliwatts < 1600:
            pwr = ANTENNA_POWER_REVERSE[1500]
        elif 1600 <= pwr_in_milliwatts < 1700:
            pwr = ANTENNA_POWER_REVERSE[1600]
        elif 1700 <= pwr_in_milliwatts < 1800:
            pwr = ANTENNA_POWER_REVERSE[1700]
        elif 1800 <= pwr_in_milliwatts < 1900:
            pwr = ANTENNA_POWER_REVERSE[1800]
        elif 1900 <= pwr_in_milliwatts < 2000:
            pwr = ANTENNA_POWER_REVERSE[1900]
        else:  # pwr_in_milliwatts >= 2000:
            pwr = ANTENNA_POWER_REVERSE[2000]

        cfgData[index] = pwr

        ret = self.write_config(cfg_page, cfgData)
        if ret is None:
            return False

        return True

    def antenna_rssi(self, ant: int, rssi: int):
        """Change Antenna RSSI

        Args:
            ant: must be one of supported ANTENNA_No*
            rssi: must be in range RSSI_MIN and RSSI_MAX
            IF rssi == 0, then itis disabled

        Returns:
            bool: True, if power is set in the reader
            rssi: current rssi value

        Raises:
            ValueError
        """
        if not (
            ant is self.ANTENNA_No1
            or ant is self.ANTENNA_No2
            or ant is self.ANTENNA_No3
            or ant is self.ANTENNA_No4
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

        elif ant is self.ANTENNA_No4:
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
            return False

        FeigBase._last_error = FeigError.INVALID_RESPONSE
        if data[0] == 0x85:  # Set
            FeigBase._last_error = self._feig_status_parser(data[1])
            if FeigBase._last_error is FeigError.OK:
                return True

        elif data[0] == 0x86:  # Get
            FeigBase._last_error = self._feig_status_parser(data[1])
            if FeigBase._last_error is FeigError.OK:
                return data[2], data[3], (data[4] * 256 + data[5])

    def system_date_time(self, date_value=None, timer_value=None) -> Union[bool, tuple]:
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
            return False

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

        return False

    def notification_channel(self, ackData=None, dstHost=None, keepAlive=None, holdTime=None)-> Union[bool, dict]:
        """Configure Notification channel of the reader

        Args:
            ackData:bool,
                True = Acknowledge Notification Data

            dstHost:tuple, (dstIP,dstPort)
                dstIP: str, Destination IPv4
                dstIP: str/int, Destination PORT from 0 - 65535

            keepAlive:tuple, (enable, time)
                enable: bool, True to enable keep alive message
                time: int, keep alive message time from 0 - 65535 secs

            holdTime:int, Defines the connection hold time from 0 - 255 sec

        Returns:
            currentConfig: dict, If no argument is passed return current config
                {
                    'ackData': None,
                    'dstHost': None,
                    'keepAlive': None
                }

            status: bool, True if configuration set successfully
        """

        # check argument
        if ackData and not isinstance(ackData, bool):
            raise TypeError("bool type expected")

        if dstHost and not isinstance(dstHost, tuple):
            raise TypeError("tuple type expected")

        if keepAlive and not isinstance(keepAlive, tuple):
            raise TypeError("tuple type expected")

        if holdTime and not isinstance(holdTime, int):
            raise TypeError("int type expected")

        cfgData = self.read_config(49)
        if cfgData is None:
            return False

        if not ackData and not dstHost and not keepAlive:
            # return dictionary
            ackData = bool(cfgData[0] & 0x80)

            dstIp = (
                (cfgData[7] << 24)
                + (cfgData[8] << 16)
                + (cfgData[9] << 8)
                + cfgData[10]
            )
            dstIp = str(ipaddress.ip_address(dstIp))
            dstPort = cfgData[11] * 256 + cfgData[12]

            keepen = bool(cfgData[4] & 0x01)
            keeptime = cfgData[5] * 256 + cfgData[6]

            holdTime = cfgData[13]

            return {
                "ackData": ackData,
                "dstHost": (dstIp, dstPort),
                "keepAlive": (keepen, keeptime),
                "holdTime": holdTime,
            }

        # set ack
        if ackData:
            if ackData is True:
                cfgData[0] = 0x80
            else:
                cfgData[0] = 0x00

        # keep alive
        if keepAlive:
            if keepAlive[0] is True:
                cfgData[4] = 0x01
            else:
                cfgData[4] = 0x00
            if keepAlive[1] > 65535:
                raise ValueError("keepAlive time exceeds range")
            cfgData[5] = (keepAlive[1] >> 8) & 255
            cfgData[6] = (keepAlive[1] >> 0) & 255

        # destintation
        if dstHost:
            try:
                ipaddr = dstHost[0]
                ipaddr = int(ipaddress.ip_address(ipaddr))
                ipaddr = ipaddress.v4_int_to_packed(ipaddr)
                iperr = False
            except ipaddress.AddressValueError:
                iperr = True
            if iperr is True:
                raise ValueError("dst IP incorrect")
            cfgData[7] = ipaddr[0]
            cfgData[8] = ipaddr[1]
            cfgData[9] = ipaddr[2]
            cfgData[10] = ipaddr[3]

            if dstHost[1] > 65535:
                raise ValueError("dst Port excceds range")
            cfgData[11] = (dstHost[1] >> 8) & 255
            cfgData[12] = (dstHost[1] >> 0) & 255

        # hold time
        if holdTime:
            if holdTime > 255:
                raise ValueError("holdTime exceeds range")
            cfgData[13] = holdTime

        # write configs
        ret = self.write_config(49, cfgData)
        if ret is None:
            return False

        return True

    def read_mode_data(self, flags=None) -> Union[bool, dict]:
        """Configure READ MODE data

        Args:
            flags: dict, All parameters are MANDATORY
            {
                'uid': bool, If True reader will send IDD(EPC or EPC+TID)
                'lsb': bool, If True byte order of frame will be LSB else MSB
                'time': bool, If True reader will send its time
                'date': bool, If True reader will send its date
                'input': bool, If True reader will send its INPUT status
                'mac': bool, If True reader will send its MAC address
                'input': bool, If True reader will send its INPUT status

                'antno': bool, If True reader will send Antenna number
                'antext': bool, If True reader will send antenna rssi, phase angle
                'antstore': bool, If True reader will collect transponder data from all antennas in one data record

                'readall': bool, If True reader will read complete BANK data
                'bank': int, One of BANK_EPC, BANK_TID, BANK_USER banks from which data is to be read.

                'db': bool, If True reader will send DATA BLOCKs
                'dbaddr': int, Address of first data blocks from 0 to 65535
                'dbn': int, Number of data blocks from 0 to 65535
            }

        Returns:
            flags: dict , If no argument is passed current settings is send as per above flags definitions
            True: If write opertaion is successfull

        """

        if flags and not isinstance(flags, dict):
            raise TypeError("dict type expected")

        cfgData = self.read_config(11)
        if cfgData is None:
            return False

        if not flags:
            # return flags
            if cfgData[3] == self.BANK_EPC:
                bank = self.BANK_EPC
            elif cfgData[3] == self.BANK_TID:
                bank = self.BANK_TID
            elif cfgData[3] == self.BANK_USER:
                bank = self.BANK_USER
            else:
                bank = -1

            dbaddr = cfgData[4] * 256 + cfgData[5]
            dbn = cfgData[8] * 256 + cfgData[9]

            return {
                "uid": bool(cfgData[0] & 0x01),
                "db": bool(cfgData[0] & 0x02),
                "lsb": bool(cfgData[0] & 0x08),
                "antno": bool(cfgData[0] & 0x10),
                "time": bool(cfgData[0] & 0x20),
                "date": bool(cfgData[0] & 0x40),
                "input": bool(cfgData[1] & 0x01),
                "mac": bool(cfgData[1] & 0x02),
                "antext": bool(cfgData[1] & 0x10),
                "antstore": bool(cfgData[2] & 0x02),
                "readall": bool(cfgData[2] & 0x08),
                "bank": bank,
                "dbaddr": dbaddr,
                "dbn": dbn,
            }

        try:
            trdata1 = 0
            if flags["uid"] is True:
                trdata1 += 0x01
            if flags["db"] is True:
                trdata1 += 0x02
            if flags["lsb"] is True:
                trdata1 += 0x08
            if flags["time"] is True:
                trdata1 += 0x20
            if flags["date"] is True:
                trdata1 += 0x40

            trdata2 = 0
            if flags["input"] is True:
                trdata2 += 0x01
            if flags["mac"] is True:
                trdata2 += 0x02
            if flags["antext"] is True:
                trdata2 += 0x10
                trdata1 += 0x80
            else:
                if flags["antno"] is True:
                    trdata1 += 0x10

            trdata3 = 0
            if flags["antstore"] is True:
                trdata3 += 0x02
            if flags["readall"] is True:
                trdata3 += 0x08

            cfgData[0] = trdata1
            cfgData[1] = trdata2
            cfgData[2] = trdata3
            cfgData[3] = flags["bank"]
            cfgData[4] = (flags["dbaddr"] >> 8) & 0xFF
            cfgData[5] = (flags["dbaddr"] >> 0) & 0xFF
            cfgData[8] = (flags["dbn"] >> 8) & 0xFF
            cfgData[9] = (flags["dbn"] >> 0) & 0xFF

        except KeyError:
            raise ValueError("Invalid arguments")

        # write configs
        ret = self.write_config(11, cfgData)
        if ret is None:
            return False

        return True

    def read_mode_filter(self, transpondervalidtime=None, trid=None, inevflt=None) -> Union[bool, dict]:
        """Configure READ MODE Filter

        Args:
            transpondervalidtime: int, This the time during which a transponder will not be reported a second time,
                                        range is from 0 - 65535 (x100msec)

            trid: dict, Sets the data source for transponder identification
            {
                'source': int, values are 0=DataBlock ; 1=SerialNumber
                'dbaddr': int, Set start address of data block, range(0 - 65535). Ignored for SerialNumber.
                'dbn': int, Set start address of data block, range(0 - 255). Ignored for SerialNumber.
            }

            inevflt: dict,
            {
                'input1': bool, If True input event on input-1 will be notified
                'input2': bool, If True input event on input-2 will be notified
                'timeout': bool, If True timeout event during active BRM or Notification Mode will be notified
                'trig': bool, If True change of the BRM or Notification Mode status will be notified
            }

        Returns:
            data: dict, current cconfiguration
            {
                'transpondervalidtime': int,
                'trid': {
                    'source': int,
                    'dbaddr': int,
                    'dbn': int,
                },
                'inevflt':{
                    'input1': bool,
                    'input2': bool,
                    'timeout': bool,
                    'trig': bool,
                }
            }

            True: If write successfull
        """

        if transpondervalidtime and not isinstance(transpondervalidtime, int):
            raise TypeError("int type expected")

        if trid and not isinstance(trid, dict):
            raise TypeError("dict type expected")

        if inevflt and not isinstance(inevflt, int):
            raise TypeError("dict type expected")

        cfgData = self.read_config(12)
        if cfgData is None:
            return False

        if not transpondervalidtime and not trid and not inevflt:
            # return current config
            return {
                "transpondervalidtime": cfgData[0] * 256 + cfgData[1],
                "trid": {
                    "source": 1 if (cfgData[2] & 0x02) else 0,
                    "dbaddr": cfgData[3] * 256 + cfgData[4],
                    "dbn": cfgData[5],
                },
                "inevflt": {
                    "input1": bool(cfgData[6] & 0x01),
                    "input2": bool(cfgData[6] & 0x02),
                    "timeout": bool(cfgData[7] & 0x02),
                    "trig": bool(cfgData[7] & 0x01),
                },
            }

        if transpondervalidtime:
            cfgData[0] = (transpondervalidtime >> 8) & 0xFF
            cfgData[1] = (transpondervalidtime >> 0) & 0xFF

        if trid:
            cfgData[2] = trid["source"]
            cfgData[3] = (trid["dbaddr"] >> 8) & 0xFF
            cfgData[4] = (trid["dbaddr"] >> 0) & 0xFF
            cfgData[5] = trid["dbn"]

        if inevflt:
            cfgData[6] = 0
            if inevflt["input1"] is True:
                cfgData[6] += 0x01
            if inevflt["input2"] is True:
                cfgData[6] += 0x02

            cfgData[7] = 0
            if inevflt["timeout"] is True:
                cfgData[7] += 0x02
            if inevflt["trig"] is True:
                cfgData[7] += 0x01

        # write configs
        ret = self.write_config(12, cfgData)
        if ret is None:
            return False

        return True

    def antenna_multiplexing(self, mux_enable=None, selected_antennas=None) -> Union[bool, dict]:
        """Configure the multiplexing of antennas in Auto Read Modes

        Args:
            mux_enable: bool, If True activates multiplexing

            selected_antennas: dict, Antennas which are used for the internal multiplexing
            {
                'ant1': bool, If True antenna-1 is selected
                'ant2': bool, If True antenna-2 is selected
            }

        Returns:
            bool: if antenna is configured
            dict: current multiplex configuration

        Raises:
            ValueError for incorrect data
        """

        if mux_enable and not isinstance(mux_enable, bool):
            raise ValueError("bool type expected")

        if selected_antennas and not isinstance(selected_antennas, dict):
            raise ValueError("dict type expected")

        cfgData = self.read_config(15)
        if cfgData is None:
            return False

        if not mux_enable and not selected_antennas:
            # return current config
            return {
                "mux_enable": bool(cfgData[0] & 0x01),
                "selected_antennas": {
                    "ant1": bool(cfgData[1] & 0x08),
                    "ant2": bool(cfgData[1] & 0x10),
                },
            }

        if mux_enable and mux_enable is True:
            cfgData[0] = 0x01

        if selected_antennas:
            cfgData[1] = 0x00
            if selected_antennas["ant1"] is True:
                cfgData[1] += 0x08
            if selected_antennas["ant2"] is True:
                cfgData[1] += 0x10

        # write configs
        ret = self.write_config(15, cfgData)
        if ret is None:
            return False

        return True

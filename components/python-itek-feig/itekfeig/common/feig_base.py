#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from binascii import hexlify, unhexlify

from ..common.feig_errors import FeigError


class FeigBase:
    """Base class for all readers
    """
    MAX_CONFIGURATION_PAGES = 64

    BANK_RESERVED = 0
    BANK_EPC = 1
    BANK_TID = 2
    BANK_USER = 3

    FILTER_EPC = 1
    FILTER_RSSI = 2
    FILTER_DATA = 3

    _interface = None
    _last_error = None

    _current_mode = None
    _mask_list = None

    def __init__(self):
        # print("feig_base.py class FeigBase init")
        self._all_reader_config = []
        self.filters = {}

    def get_last_error(self) -> FeigError:
        """Returns Last Error
        """
        return FeigBase._last_error

    def get_last_error_str(self) -> str:
        """Returns Last Error as string
        """
        return FeigBase._last_error.name

    def _feig_status_parser(self, status: int) -> FeigError:
        if status == 0x00:
            return FeigError.OK

        if status == 0x01:
            return FeigError.NO_TAG

        if status == 0x02:
            return FeigError.DATA_FALSE

        if status == 0x03:
            return FeigError.WRITE_ERROR

        if status == 0x04:
            return FeigError.ADDRESS_ERROR

        if status == 0x05:
            return FeigError.WRONG_TRANSPONDER_TYPE

        if status == 0x08:
            return FeigError.AUTHENT_ERROR

        if status == 0x10:
            return FeigError.EEPROM_FAILURE

        if status == 0x11:
            return FeigError.PARAMETER_RANGE_ERROR

        if status == 0x13:
            return FeigError.LOGIN_REQUEST

        if status == 0x14:
            return FeigError.LOGIN_ERROR

        if status == 0x15:
            return FeigError.READ_PROTECT

        if status == 0x16:
            return FeigError.WRITE_PROTECT

        if status == 0x17:
            return FeigError.FIRMWARE_ACTIVATION_REQUIRED

        if status == 0x18:
            return FeigError.WRONG_FIRMWARE

        if status == 0x80:
            return FeigError.UNKNOWN_COMMAND

        if status == 0x81:
            return FeigError.LENGTH_ERROR

        if status == 0x82:
            return FeigError.COMMAND_NOT_AVAILABLE

        if status == 0x83:
            return FeigError.RF_COMMUNICATION_ERROR

        if status == 0x84:
            return FeigError.RF_WARNING

        if status == 0x92:
            return FeigError.NO_VALID_DATA

        if status == 0x93:
            return FeigError.DATA_BUFFER_OVERFLOW

        if status == 0x94:
            return FeigError.MORE_DATA

        if status == 0x95:
            return FeigError.TAG_ERROR

        if status == 0xF1:
            return FeigError.HARDWARE_WARNING

        return FeigError.UNKNOWN

    def read_config(self, addr) -> list:
        """Read configuration from reader.

        Args:
            addr: int, configuration page/address,
            .. note:: should not excced MAX_CONFIGURATION_PAGES

        Returns:
            data:list, empty if error
        """
        config_data = []
        cmd = [0x80, addr + 0x80]
        data = FeigBase._interface.transfer(1.0, cmd)
        if data is None:
            FeigBase._last_error = FeigError.COMM_TIMEOUT
            return config_data

        FeigBase._last_error = FeigError.INVALID_RESPONSE
        if data[0] == 0x80:
            FeigBase._last_error = self._feig_status_parser(data[1])
            if FeigBase._last_error is FeigError.OK:
                config_data = list(data[2:])  # remove control & status byte

        return config_data

    def write_config(self, addr, data: list) -> bool:
        """Write configuration to reader.

        Args:
            addr: int, configuration page/address,
            .. note:: should not excced MAX_CONFIGURATION_PAGES

        Returns:
            True if configuration written in reader.
        """
        cmd = [0x81, addr + 0x80]
        cmd = cmd + data
        data = FeigBase._interface.transfer(1.0, cmd)
        if data is None:
            FeigBase._last_error = FeigError.COMM_TIMEOUT
            return False

        FeigBase._last_error = FeigError.INVALID_RESPONSE
        if data[0] == 0x81:
            FeigBase._last_error = self._feig_status_parser(data[1])
            if FeigBase._last_error is FeigError.OK:
                return True

        return False

    def reset_config(self, addr, eeprom=False, all_blocks=False) -> bool:
        """Reset reader configuration.

        Args:
            addr: int, configuration page/address,
            .. note:: should not excced MAX_CONFIGURATION_PAGES

            eeprom: bool, if true reset eeprom configuration
            all_blocks: bool, if true reset complete configuration

        Returns:
            True if configuration reset.
        """
        if addr >= self.MAX_CONFIGURATION_PAGES:
            return False

        value = addr
        if all_blocks is True:
            value = value + 0x40
        if eeprom is True:
            value = value + 0x80

        cmd = [0x83, value]
        data = FeigBase._interface.transfer(1.0, cmd)
        if data is None:
            FeigBase._last_error = FeigError.COMM_TIMEOUT
            return False

        FeigBase._last_error = FeigError.INVALID_RESPONSE
        if data[0] == 0x83:
            FeigBase._last_error = self._feig_status_parser(data[1])
            if FeigBase._last_error is FeigError.OK:
                return True

        return False

    def read_all_config(self) -> bool:
        """Read ALL Configuration from READER"""
        for i in range(0, 64):
            cmd = [0x80, 0x80 + i]
            data = FeigBase._interface.transfer(2.0, cmd)
            if data is None:
                FeigBase._last_error = FeigError.COMM_TIMEOUT
                return False

            if data[0] != 0x80:
                FeigBase._last_error = FeigError.INVALID_RESPONSE
                return False

            FeigBase._last_error = self._feig_status_parser(data[1])
            if FeigBase._last_error is FeigError.OK:
                self._all_reader_config.append([i, data[2:]])

        return True

    def get_software_version(self) -> dict:
        """Get readers software version.

        Returns:
            sw_version: dict, empty if any error

            .. code:: python
                sw_version = {
                    "RFControllerSoftwareRevision": "",
                    "HardwareType": "",
                    "ReaderFirmware": int,
                    "TransponderTypes": "",
                    "MaxRXBufferSize": int,
                    "MaxTXBufferSize": int,
                }
        """
        software_version = {}

        cmd = [0x02, 0x00, 0x07, 0xFF, 0x65, 0x6E, 0x61]
        data = FeigBase._interface.transfer(1.0, bytes(cmd))
        if data is None:
            FeigBase._last_error = FeigError.COMM_TIMEOUT
            return software_version

        FeigBase._last_error = FeigError.INVALID_RESPONSE
        if data[0] == 0x65:
            FeigBase._last_error = self._feig_status_parser(data[1])
            if FeigBase._last_error is FeigError.OK:
                sw_rev = hexlify(data[2:5]).decode("ascii")
                hw_rev = hexlify(data[5:6]).decode("ascii")
                fw_rev = int(data[6])
                tr_type = hexlify(data[7:9]).decode("ascii")
                rx_size = data[9] * 256 + data[10]
                tx_size = data[11] * 256 + data[12]

                software_version = {
                    "RFControllerSoftwareRevision": sw_rev,
                    "HardwareType": hw_rev,
                    "ReaderFirmware": fw_rev,
                    "TransponderTypes": tr_type,
                    "MaxRXBufferSize": rx_size,
                    "MaxTXBufferSize": tx_size,
                }

        return software_version

    def _get_reader_type(self):
        cmd = [0x02, 0x00, 0x08, 0xFF, 0x66, 0x00, 0x88, 0x12]
        data = FeigBase._interface.transfer(1.0, bytes(cmd))
        if data is None:
            FeigBase._last_error = FeigError.COMM_TIMEOUT
            return

        FeigBase._last_error = FeigError.INVALID_RESPONSE
        if data[0] == 0x66:
            FeigBase._last_error = self._feig_status_parser(data[1])
            if FeigBase._last_error is FeigError.OK:
                return data[6]

    ####################################################################################
    ####    READER CONTROL API
    ####################################################################################

    def rf_controller_reset(self) -> bool:
        """Perform RF controller reset

        Returns:
            True if RF controller is reset.

        .. note:: wait for atleast 1second after calling this function
        """
        cmd = [0x02, 0x00, 0x07, 0xFF, 0x63, 0x58, 0x04]
        data = FeigBase._interface.transfer(1.0, bytes(cmd))
        if data is None:
            FeigBase._last_error = FeigError.COMM_TIMEOUT
            return False

        FeigBase._last_error = FeigError.INVALID_RESPONSE
        if data[0] == 0x63:
            FeigBase._last_error = self._feig_status_parser(data[1])
            if FeigBase._last_error is FeigError.OK:
                return True

        return False

    def system_reset(self) -> bool:
        """Perform Reader reset

        Returns:
            True if reader is reseted.

        .. note:: wait for atleast 1second after calling this function
        """
        cmd = [0x02, 0x00, 0x08, 0xFF, 0x64, 0x38, 0x21]
        data = FeigBase._interface.transfer(1.0, bytes(cmd))
        if data is None:
            FeigBase._last_error = FeigError.COMM_TIMEOUT
            return

        FeigBase._last_error = FeigError.INVALID_RESPONSE
        if data[0] == 0x64:
            FeigBase._last_error = self._feig_status_parser(data[1])
            if FeigBase._last_error is FeigError.OK:
                return True

        return False

    def rf_reset(self) -> bool:
        """Returns True if RF reset done"""
        cmd = [0x02, 0x00, 0x07, 0xFF, 0x69, 0x02, 0xAB]
        data = FeigBase._interface.transfer(1.0, bytes(cmd))
        if data is None:
            FeigBase._last_error = FeigError.COMM_TIMEOUT
            return False

        FeigBase._last_error = FeigError.INVALID_RESPONSE
        if data[0] == 0x69:
            FeigBase._last_error = self._feig_status_parser(data[1])
            if FeigBase._last_error is FeigError.OK:
                return True

        return False

    def login(self, password: str) -> bool:
        """Login into the reader using given password.

        .. warning:: Should be done whenever reader is poweron or RF_Reset command is issued.

        Args:
            password: 4byte hex string

        Returns:
            True if login success.
        """
        cmd = [0xA0] + list(unhexlify(password))
        data = FeigBase._interface.transfer(1.0, bytes(cmd))
        if data is None:
            FeigBase._last_error = FeigError.COMM_TIMEOUT
            return False

        FeigBase._last_error = FeigError.INVALID_RESPONSE
        if data[0] == 0xA0:
            FeigBase._last_error = self._feig_status_parser(data[1])
            if FeigBase._last_error is FeigError.OK:
                return True

        return False

    def add_filter(self, filter_type: int, filter_data)->bool:
        """Add filtering to TAG data

            filter_type: int, one of the value from FILTER_*
            filter_data: data, as per filter_type

        .. TODO::
        """
        raise NotImplementedError

    def remove_filter(self, filter_type, remove_all=False) -> bool:
        """Remove specified TAG FILTER

        .. TODO::
        """
        raise NotImplementedError

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import enum


class FeigError(enum.IntEnum):
    """Feig Errors"""
    OK = 0

    # LIBRARY Specific
    COMM_TIMEOUT = 1  # When response is not receive in time
    INVALID_RESPONSE = 2  # Response from reader is NOT as expected
    INVALID_READER = 3  # Connected reader is NOT as expected
    EPC_LEN_MISMATCH = 4  # When read/write operation on tag, EPC must be EVEN length
    MODE_SAME = 5  # Requested reader mode and current mode is SAME
    INVALID_MODE = 6  # Some commnads require reader to be in specific mode only
    INVALID_INTERFACE = 7  # Some commnads require reader to be in specific interface only

    NO_ROUTE_TO_HOST = 8
    CONNECTION_REFUSED = 9
    UNHANDLED = 10

    SERIAL = 11
    ETHERNET = 12

    INTERFACE_ERROR = 13

    # FEIG Specific ERROR/STATUS
    NO_TAG = 50
    DATA_FALSE = 51
    WRITE_ERROR = 52
    ADDRESS_ERROR = 53
    WRONG_TRANSPONDER_TYPE = 54
    AUTHENT_ERROR = 55
    EEPROM_FAILURE = 56
    PARAMETER_RANGE_ERROR = 57
    LOGIN_REQUEST = 58
    LOGIN_ERROR = 59
    READ_PROTECT = 60
    WRITE_PROTECT = 61
    FIRMWARE_ACTIVATION_REQUIRED = 62
    WRONG_FIRMWARE = 63

    UNKNOWN_COMMAND = 0x80
    LENGTH_ERROR = 0x81
    COMMAND_NOT_AVAILABLE = 0x82
    RF_COMMUNICATION_ERROR = 0x83
    RF_WARNING = 0x84

    NO_VALID_DATA = 0x92
    DATA_BUFFER_OVERFLOW = 0x93
    MORE_DATA = 0x94
    TAG_ERROR = 0x95

    HARDWARE_WARNING = 0xF1

    UNKNOWN = 255

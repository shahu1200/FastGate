#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import enum


class RFIDErrors(enum.IntEnum):
    SUCCESS = 0
    INVALID_CONFIG = 1
    INVALID_INTERFACE = 2
    COMM_TIMEOUT = 3
    CONNECT_FAILED = 4
    READER_NOT_SUPPORTED = 5
    READER_NOT_CONNECTED = 6
    READER_HOST_MODE = 7
    READER_BRM_MODE = 8
    READER_ANTENNA = 9
    INVALID_DATA = 10
    INVALID_READER = 11

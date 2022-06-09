#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

logger = logging.getLogger(__name__)


def check_frame(data):
    # Frames
    # - '#ffff#vvvvv!' => #vvvvv!
    # - 'ffff!#vvvvv!' => #vvvvv!
    # - 'ffff#vvvvv!' => #vvvvv!
    frame = ""

    start_index = data.rfind("#")
    if start_index >= 0:
        frame = data[start_index:]

    return frame


def check_frame_type(data):
    txd_type = ""
    to_split = data.split(",")
    if to_split[0] == "#T":
        txd_type = "success"
    elif to_split[0] == "#E":
        txd_type = "error"
    elif to_split[0] == "#S02":
        txd_type = "status"
    elif to_split[0].startswith("#C"):
        txd_type = "config"

    return txd_type


def create_ack_trans(count):
    # command
    # #^^000000!
    frame = "#" + "^^" + str(count).zfill(6) + "!"
    return frame.encode()


def create_ack_heart(count, status, ser_id):
    # command
    # #R02,000000,0,0!
    frame = "#R02," + f"{count:06d}," + f"{status}," + f"{ser_id}" + "!"
    return frame.encode()


def get_status_id(data):
    to_string = data.decode("utf-8")
    to_split = to_string.split(",")
    count = to_split[7][0:4]
    return count


def create_frame_config(config):
    c01 = "C01" + config["C01DongleResetTime"]
    c02 = "$C02" + config["C02UhfReaderBudRate"]
    c03 = "$C03" + config["C03TimeZone"]
    c04 = "$C04" + config["C04WbEnable"]
    c05 = config["C05MaxStackLevel"]
    c06 = "$C06" + config["C06LowerBoardEnable"]
    c07 = "$C07" + config["C07TagExitTimeCount"]
    range_levels = []
    for level in range(1, 8):
        range_levels.append(config["HeightRangeLevel" + str(level)])

    c05_full = "$C05" + c05 + "," + ",".join(range_levels[: int(c05) + 1])
    # command
    # #C01 XX $ C02 XX $ C03 X HHMM $ C04 X $ C05 XX $ C06 X $ C07 XX!
    frame = "#" + c01 + c02 + c03 + c04 + c05_full + c06 + c07 + "!"
    return frame.encode()


def get_hw_status(count):
    # command
    # '#S02000000!'
    frame = "#S02{}!".format(str(count).zfill(6))
    return frame.encode()

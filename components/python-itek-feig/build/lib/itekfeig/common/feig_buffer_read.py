#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
import time

from ..common.feig_base import FeigBase
from ..common.feig_data_parser import brm_and_notif_parser
from ..common.feig_errors import FeigError


class FeigBufferRead(FeigBase):
    def __init__(self, interface, lastError):
        """This class implements Buffer Read mode functionality of Feig reader.

        Args:
            interface: This the interface on which communication will happen.
            lastError: This parameter is shared for reporting error
        """
        super().__init__()

        FeigBase._interface = interface
        FeigBase._last_error = lastError

    def init(self):
        """This function initializes internal buffer of the reader.
        """
        cmd = [0x02, 0x00, 0x07, 0xFF, 0x33, 0xDD, 0x56]
        data = FeigBase._interface.transfer(1.0, bytes(cmd))
        if data is None:
            FeigBase._last_error = FeigError.COMM_TIMEOUT
            return

        FeigBase._last_error = FeigError.INVALID_RESPONSE
        if data[0] == 0x33:
            FeigBase._last_error = self._feig_status_parser(data[1])
            if FeigBase._last_error is FeigError.OK:
                return True

    def clear(self):
        """This function clears internal buffer of the reader.
        """
        cmd = [0x02, 0x00, 0x07, 0xFF, 0x32, 0x54, 0x47]
        data = FeigBase._interface.transfer(1.0, bytes(cmd))
        if data is None:
            FeigBase._last_error = FeigError.COMM_TIMEOUT
            return

        FeigBase._last_error = FeigError.INVALID_RESPONSE
        if data[0] == 0x32:
            FeigBase._last_error = self._feig_status_parser(data[1])
            if FeigBase._last_error is FeigError.OK:
                return True

    def info(self):
        """This function gives info of internal buffer of the reader.
        """
        cmd = [0x02, 0x00, 0x07, 0xFF, 0x31, 0xCF, 0x75]
        data = FeigBase._interface.transfer(1.0, bytes(cmd))
        if data is None:
            FeigBase._last_error = FeigError.COMM_TIMEOUT
            return

        FeigBase._last_error = FeigError.INVALID_RESPONSE
        if data[0] == 0x31:
            FeigBase._last_error = self._feig_status_parser(data[1])
            if (
                FeigBase._last_error is FeigError.OK
                or FeigBase._last_error is FeigError.RF_WARNING
                or FeigBase._last_error is FeigError.DATA_BUFFER_OVERFLOW
            ):
                info = {
                    "TableSize": data[2] * 256 + data[3],
                    "TableStart": data[4] * 256 + data[5],
                    "TableLength": data[6] * 256 + data[7],
                }

                return info

    def read(self):
        """This function read internal buffer of the reader.
        """
        cmd = [0x02, 0x00, 0x09, 0xFF, 0x22, 0x00, 0xFF, 0x79, 0x69]  # MAX 255 data set
        data = FeigBase._interface.transfer(1.0, bytes(cmd))

        if data is None:
            FeigBase._last_error = FeigError.COMM_TIMEOUT
            return

        if data[0] != 0x22:
            FeigBase._last_error = FeigError.INVALID_RESPONSE
            return

        FeigBase._last_error = self._feig_status_parser(data[1])
        if (
            FeigBase._last_error is FeigError.OK
            or FeigBase._last_error is FeigError.DATA_BUFFER_OVERFLOW
            or FeigBase._last_error is FeigError.RF_WARNING
        ):
            return brm_and_notif_parser(data[2:])

        elif (
            FeigBase._last_error is FeigError.NO_TAG
            or FeigBase._last_error is FeigError.NO_VALID_DATA
        ):
            return []

    def _update_antennas(self, current_antennalist, new_antennalist):
        for i in range(0, len(current_antennalist)):
            for j in range(0, len(new_antennalist)):
                if current_antennalist[i]["antno"] == new_antennalist[j]["antno"]:
                    current_antennalist[i]["phase_angle"] = new_antennalist[j]["phase_angle"]
                    current_antennalist[i]["rssi"] = new_antennalist[j]["rssi"]
                    # remove same antenna
                    new_antennalist.pop(j)
                    break

        # add new antenna
        for ant in new_antennalist:
            current_antennalist.append(ant)

        return current_antennalist

    def _unique_tags(self, taglist):
        unique_tags = {}  # based on TID only

        for tag in taglist:
            tid = tag["tid"]
            try:
                unique_tags[tid]["seen_count"] += 1
                unique_tags[tid]["last_seen"] = tag["time"]
                current_antennalist = unique_tags[tid]["antennas"]

                new_antennalist = tag["antennas"]

                unique_tags[tid]["antennas"] = self._update_antennas(
                    current_antennalist, new_antennalist
                )

            except KeyError:
                # add new tag
                timestamp = tag.pop("time")  # individual tag time is not required
                unique_tags[tid] = tag
                unique_tags[tid]["first_seen"] = timestamp
                unique_tags[tid]["last_seen"] = timestamp
                unique_tags[tid]["seen_count"] = 1

        return unique_tags

    def inventory(self, timeout: int, unique=False):
        timeout_event = threading.Event()
        timeout_event.clear()

        if timeout < 100:  # min 0.1sec
            timeout = 100

        readTimer = threading.Timer(timeout / 1000, timeout_event.set)
        readTimer.start()

        ret = self.init()
        if ret is None:
            return

        ret = self.clear()
        if ret is None:
            return

        tagList = []

        while not timeout_event.isSet():
            time.sleep(0.02)  # wait for 20msec

            tags = self.read()
            if tags is None:
                readTimer.cancel()
                break

            if len(tags) > 0:
                tagList.extend(tags)
                self.clear()

        self.clear()
        if len(tagList) > 0 and unique is True:
            return self._unique_tags(tagList)  # return dict()

        return tagList  # return list

    def scan_till_no_unique_tags(self, noUniqueTagWaitCount=10):
        ret = self.init()
        if ret is None:
            return

        uniqueTags = {}
        uniqueTagsCount = 0
        noNewTagsCount = 0

        self.clear()
        while True:
            tags = self.read()
            if tags is None:
                break

            if len(tags) > 0:
                self.clear()
                uniqueTags.update(self._unique_tags(tags))

                if len(uniqueTags) > uniqueTagsCount:
                    uniqueTagsCount = len(uniqueTags)
                    noNewTagsCount = 0

                elif len(uniqueTags) == uniqueTagsCount:  # same unique tag count
                    noNewTagsCount += 1

            else:
                noNewTagsCount += 1  # no tag in buffer

            if noNewTagsCount >= noUniqueTagWaitCount:
                break

        return uniqueTags

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    RTC module.
"""
#9834226776
#Gopal

import imp
import logging
import smbus
import time
import subprocess
from datetime import date, datetime

from .utils import convert_to_localtime

logger = logging.getLogger(__name__)

# 	DS1307
RTC_ADDRESS = 0x68


def int2bcd(intval):
    bcdval = -1
    if intval >= 0 and intval <= 99:
        bcdval = intval // 10
        bcdval = bcdval << 4
        bcdval += intval % 10

    return bcdval

class Error(Exception):
    """Base class for other exceptions"""
    pass

class I2CBusNotFoundError(Error):
    """Raised when I2C bus is not found."""
    pass

class RTCNotFoundError(Error):
    """Raised when RTC is not found."""
    pass

class itekRTC:

    MILLENNIUM = 2020
    
    def __init__(self):
        # print("itek_rtc.py class itekRTC init")
        self._i2cbus = None
        self._is_present = False

    def is_present(self) -> bool:
        return self._is_present

    def connect(self, bus=1) -> bool:
        """Connect to the RTC.

        If connection is False, then check
        - I2C is enable in the raspi-config
        - Correct bus number is passed

        Args:
            bus:int, I2C bus number on which RTC is connected.

        Returns:
            bool: if rtc connected

        Raises:
            I2CBusNotFoundError: when I2C bus is not found
            RTCNotFoundError: when RTC module is not found

        """
        status = False
        try:
            self._i2cbus = smbus.SMBus(bus)

        except FileNotFoundError:
            raise I2CBusNotFoundError("Bus={}".format(bus))

        else:
            # Do dummy read, so that it will detect if
            # RTC module is connected/working or not
            data = self._rtc_read(startaddr=0, count=1)
            if len(data) != 1:
                self._i2cbus.close()
                self._i2cbus = None
                raise RTCNotFoundError("ADDRESS={}".format(RTC_ADDRESS))

            status = True
            self._is_present = status

        return status

    def close(self):
        """Close RTC connection
        """
        if self.is_present():
            self._i2cbus.close()
            self._is_present = False
            self._i2cbus = None

    def _rtc_read(self, startaddr: int = 0, count: int = 0) -> list:
        """Read RTC memory

        Args:
            startaddr: int, Address from where to read memory
            count: int, Number of bytes to read

        Returns:
            data:list, Non-empty if read is successfull else empty list
        """
        data = []
        try:
            data = self._i2cbus.read_i2c_block_data(RTC_ADDRESS, startaddr, count)
        except Exception:
            logger.exception("RTC Read Error")

        return data

    def _rtc_write(self, startaddr: int = 0, data: list = None) -> bool:
        """Write RTC memory

        Args:
            startaddr: int, Address from where to read memory
            data: list, Data to write in the memory

        Returns:
            status:bool, True If write successfull
        """
        status = False
        try:
            self._i2cbus.write_i2c_block_data(RTC_ADDRESS, startaddr, data)
            status = True
        except Exception:
            logger.exception("RTC Write Error")

        return status

    def rtc_getdate(self) -> tuple:
        """Get RTC Date

        Returns:
            (date, month, year): tuple, RTC's date, month, year

            If error occured then
            (date, month, year) = (-1, -1, -1)
        """
        date = -1
        month = -1
        year = -1

        if self.is_present():
            data = self._rtc_read(4, 3)  # read current date from rtc
            if len(data) > 0:
                # BCD into integer
                date = data[0] & 0x3F
                date = (date >> 4) * 10 + (date & 0xF)

                month = data[1] & 0x1F
                month = (month >> 4) * 10 + (month & 0xF)

                year = data[2] & 0xFF
                year = (year >> 4) * 10 + (year & 0xF)
                year = year + self.MILLENNIUM

        return (date, month, year)

    def rtc_setdate(self, date: int, month: int, year: int) -> bool:
        """Set RTC Date

        Args:
            date:int, Range is from 01 to 31
            month:int, Range is from 01 to 12
            year:int, Range is from MILLENNIUM+00 to MILLENNIUM+99

            Here, MILLENNIUM = 2000, you can set this value.

        Returns:
            True: If rtc is updated else False

        Raises:
            ValueError: if parameters are outside range
        """
        if date < 1 or date > 31:
            raise ValueError("date outside range")
        if month < 1 or month > 12:
            raise ValueError("month outside range")
        if int2bcd(year - self.MILLENNIUM) == -1:
            raise ValueError("year outside range")

        update = [int2bcd(date), int2bcd(month), int2bcd(year - self.MILLENNIUM)]

        status = False
        if self.is_present():
            status = self._rtc_write(4, update)  # write current date from rtc

        return status


    def rtc_setDateFromServer(self) -> bool:
        """
        sets rtc date with raspberry pi system date

        Returns:
            bool: return true if rtc update is success else returls false
        """
        date = datetime.now()

        year = int(date.strftime("%Y"))
        month = int(date.strftime("%m"))
        date = int(date.strftime("%d"))

        update = [int2bcd(date), int2bcd(month), int2bcd(year - self.MILLENNIUM)]
        # print(update)
        # print(self.is_present())
        status = False
        if self.is_present():
            status = self._rtc_write(4, update)  # write current date from rtc

        return status
    
                
        
    def rtc_settime(self, hour: int, minutes: int, seconds: int = 0) -> bool:
        """Set RTC Time

        Args:
            hour:int, Range is from 00 to 23
            minutes:int, Range is from 00 to 59
            seconds:int, Range is from 00 to 59

        Returns:
            True: If rtc is updated else False

        Raises:
            ValueError: if parameters are outside range
        """
        if hour < 0 or hour > 23:
            raise ValueError("hour outside range")
        if minutes < 0 or minutes > 59:
            raise ValueError("minutes outside range")
        if seconds < 0 or seconds > 59:
            raise ValueError("seconds outside range")

        update = [int2bcd(seconds), int2bcd(minutes), int2bcd(hour)]

        status = False
        if self.is_present():
            status = self._rtc_write(0, update)  # write current time from rtc

        return status

    def rtc_setTimeFromServer(self) -> bool:
        """sets rtc time with raspberry pi system time

        Returns:
            bool: returns true if rtc update is success else returns false
        """
        time = datetime.now()

        hour = int(time.strftime("%H"))
        min = int(time.strftime("%M"))
        sec = int(time.strftime("%S"))

        update = [int2bcd(sec), int2bcd(min), int2bcd(hour)]
        # print(update)
        # print(self.is_present())
        status = False
        if self.is_present():
            status = self._rtc_write(0, update)  # write current date from rtc

        return status

    def rtc_gettime(self) -> tuple:
        """Get RTC Time

        Returns:
            (hour, minutes, seconds): tuple, RTC's time
            (-1, -1, -1): tuple, If error occured
        """
        hour = -1
        minutes = -1
        seconds = -1

        if self.is_present():
            data = self._rtc_read(0, 4)  # read current time from rtc
            if len(data) > 0:
                # BCD into integer
                seconds = data[0] & 0x7F
                seconds = (seconds >> 4) * 10 + (seconds & 0xF)

                minutes = data[1] & 0x7F
                minutes = (minutes >> 4) * 10 + (minutes & 0xF)

                # hour24 = data[2] & 0x40
                # am_pm = data[2] & 0x20

                hour = data[2] & 0x3F
                hour = (hour >> 4) * 10 + (hour & 0xF)

                # days = data[3] & 0x07

        return (hour, minutes, seconds)

    def rtc_set_datetime(self, date_time: str = "") -> bool:
        """Set RTC date time

        Args:
            date_time: str, in format 'YYYY-MM-DD HH:MM:SS'

        Returns:
            bool, True if date time updated in RTC
        """
        status = False
        if date_time != "":
            date_time = date_time.split()
            current_date = date_time[0].split("-")
            current_time = date_time[1].split(":")

            if self.is_present():
                status = self.rtc_setdate(
                    int(current_date[2]),
                    int(current_date[1]),
                    int(current_date[0]),
                )
                if status is True:
                    status = self.rtc_settime(
                        int(current_time[0]),
                        int(current_time[1]),
                        int(current_time[2]),
                    )

        return status

    def rtc_get_datetime(self) -> str:
        """Get RTC datetime in 'YYYY-MM-DD HH:MM:SS' format
        If returns '' then error occured.

        """
        datetimestamp = ""

        if self.is_present():
            date, month, year = self.rtc_getdate()
            hour, minutes, seconds = self.rtc_gettime()

            if (
                (date != -1 and month != -1 and year != -1) and
                (hour != -1 and minutes != -1 and seconds != -1)
            ):
                datetimestamp = (
                    str(year).zfill(4)
                    + "-"
                    + str(month).zfill(2)
                    + "-"
                    + str(date).zfill(2)
                    + " "
                    + str(hour).zfill(2)
                    + ":"
                    + str(minutes).zfill(2)
                    + ":"
                    + str(seconds).zfill(2)
                )
            else:
                logger.warning(
                    "rtc invalid date=%d-%d-%d or time=%d:%d:%d",
                    date, month, year, hour, minutes, seconds
                )

        return datetimestamp

    def rtc_datetimestamp(self) -> str:
        """Get RTC datetime stamp in 'DDMMYYYYHHMMSS' format

        If returns '' then error occured.
        """
        datetimestamp = ""

        if self.is_present():
            date, month, year = self.rtc_getdate()
            hour, minutes, seconds = self.rtc_gettime()

            if (
                (date != -1 and month != -1 and year != -1) and
                (hour != -1 and minutes != -1 and seconds != -1)
            ):
                datetimestamp = (
                    str(year).zfill(4)
                    + str(month).zfill(2)
                    + str(date).zfill(2)
                    + str(hour).zfill(2)
                    + str(minutes).zfill(2)
                    + str(seconds).zfill(2)
                )
            else:
                logger.warning(
                    "rtc invalid date=%d-%d-%d or time=%d:%d:%d",
                    date, month, year, hour, minutes, seconds
                )

        return datetimestamp

    def update_system_datetime(self, date_time: str = "", rtc=False, localtime=False) -> bool:
        """Update System datetime.

        Args:
            datetime: str, Format is "YYYY-MM-DD HH:MM:SS"
            rtc:bool, If true update this time in RTC.
            localtime:bool, If true converts datetime to local else sets as is.

        NOTE:-
        For this to work systems NTP must be disabled.
            sudo systemctl stop systemd-timesyncd
            sudo systemctl disable systemd-timesyncd
            sudo timedatectl set-ntp false

        Returns:
            True if updated successfully
        """
        if date_time == "":
            return False

        if localtime is True:
            date_time = convert_to_localtime(date_time)

        subprocess.call(["sudo", "date", "-s", date_time])

        if rtc is True:
            self.rtc_set_datetime(date_time)

        return True

    def compare_datetime(self, datetime1: str, datetime2: str) -> int:
        """Compare two date time.

        Args:
            datetime1,datetime2:str, date and time in string format be "05/01/2021 20:35:50"

        Returns:
           -1 = Any error
            0 = If datetime1 = datetime2
            1 = If datetime1 > datetime2
            2 = If datetime1 < datetime2
        """
        dtformat = "%d/%m/%Y %H:%M:%S"
        try:
            dt1 = time.strptime(datetime1, dtformat)
            dt2 = time.strptime(datetime2, dtformat)
            if dt1 == dt2:
                return 0
            if dt1 > dt2:
                return 1
            if dt1 < dt2:
                return 2

        except ValueError:
            return -1


if __name__ == '__main__':
	rtc = itekRTC()
	print(rtc.connect())
	print(rtc.rtc_get_datetime())
	rtc.close()

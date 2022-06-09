#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import threading

from serial import Serial, SerialException, SerialTimeoutException
from . import serial_utils

logger = logging.getLogger(__name__)


class SerialConnection:
    def __init__(self, settings):
        """Create serial connection"""
        # print("serial_connection.py class SerialConnection init")
        logger.debug("init Serial Connection")
        self._port = settings["port"]
        self._baudrate = settings["baudrate"]

        self._write_lock = threading.Lock()
        self._serial = Serial(port=self._port, baudrate=self._baudrate)

    def read(self):
        """Read from serial interface"""
        ser_data = None
        try:
            ser_data = self._serial.read_until(b"!")

        except SerialException:
            logger.critical("while reading serial data")

        return ser_data

    def send(self, data):
        """Write data to serial interface"""
        logger.info("serial raw data sending: %s", data)
        self._write_lock.acquire()
        try:
            if self._serial.writable():
                ret = self._serial.write(data)
                if not ret:
                    logger.critical("data can't be send to serial port")
            else:
                logger.warning("data can't be send, port is busy")

        except SerialTimeoutException:
            logger.exception("serial write timeout")

        finally:
            self._write_lock.release()

    def _serial_rx_thread(self, data_queue):
        logger.info("serial rx thread started")
        while True:
            raw_data = self.read()
            if raw_data is not None:
                try:
                    raw_data = raw_data.decode("utf-8")
                except UnicodeError:
                    logger.warning("data decode failed: {}".format(raw_data))

                else:
                    ## check data
                    frame = serial_utils.check_frame(raw_data)
                    if frame != "":
                        data_queue.put(("serial", frame))
                    else:
                        logger.warning("unwanted data received %s", raw_data)

        logger.info("serial rx thread finished")

    def start_receive(self, data_queue):
        """Start serial reception"""
        self._serial.reset_input_buffer()

        threading.Thread(
            target=self._serial_rx_thread,
            args=(data_queue,),
            daemon=True,
        ).start()

    def close(self):
        """Close serial connection"""
        logger.debug("closing serial connection")
        self._serial.close()

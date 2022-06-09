"""
Feig Serial Interface
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import serial
import threading
from typing import Union

from copy import deepcopy
from binascii import hexlify

from ..common.feig_errors import FeigError
from ..common.feig_protocol import STX, encode, decode

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class FeigSerial:

    ID = "Serial"

    def __init__(self):
        self._serial = None

        self.error = None

        self._close = False

        self._rxdone_event = threading.Event()
        self._rxdone_event.clear()

        self._rxstart_event = threading.Event()
        self._rxstart_event.clear()

        self._rxtimeout_event = threading.Event()
        self._rxtimeout_event.clear()

        self._rxdata = None

        self._rxthread = None

    def _receive_thread(self):

        logger.info("receive thread started")

        packet_len = 0
        packet = b""

        state = 0

        start = False

        while True:

            if start is False:
                # wait forever till start event is generated
                self._rxstart_event.wait()
                self._rxstart_event.clear()
                if self._close is True:
                    break  # exit thread
                start = True
                state = 0
                packet = b""

            # Read Data
            byte = self._serial.read(size=1)
            if byte != b"":
                if state == 0:
                    if byte == STX:
                        packet = packet + byte
                        state = 1

                elif state == 1:
                    packet = packet + byte
                    packet_len = int(byte.hex(), base=16)
                    state = 2

                elif state == 2:
                    packet = packet + byte

                    packet_len = packet_len * 256 + int(byte.hex(), base=16)
                    packet_len = packet_len - 3  # we already received 3bytes

                    # read remainig bytes or timeout
                    # WARNING: Do not reduce the offset = 100,
                    #          this will cause TIMEOUT
                    self._serial.timeout = self._inter_byte_time * (packet_len + 100)
                    data = self._serial.read(size=packet_len)
                    self._serial.timeout = 0

                    if data and len(data) == packet_len:
                        packet = packet + data
                        self._rxdata = deepcopy(packet)
                    else:
                        self._rxdata = None
                    self._rxdone_event.set()
                    start = False

            # Timeout
            if self._rxtimeout_event.isSet():
                self._rxdata = None
                self._rxdone_event.set()
                start = False

        logger.info("receive thread closed")

    def open(self, port, baudrate, parity):
        """
        This function opens the SERIAL port with given parameters.

        Parameters:

        Returns:
            True: if successfully OPEN else FALSE, with error set
        """
        if self._serial is None:
            try:
                self._serial = serial.Serial(
                    port=port,
                    baudrate=baudrate,
                    bytesize=serial.EIGHTBITS,
                    parity=parity,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=0,  # Read timeout
                )
                self.error = FeigError.OK
            except ValueError:
                logger.exception("Serial exception")
                self.error = FeigError.INTERFACE_ERROR
                return False

            except serial.serialutil.SerialException:
                logger.exception("Serial exception")
                self.error = FeigError.INTERFACE_ERROR
                return False

            bit_time = 1 / baudrate
            byte_time = 10 * bit_time  # 1-Start + 8-Data + 1-Stop BITS
            self._inter_byte_time = round(byte_time, 6)

            self._serial.reset_input_buffer()

            # start recevie thread
            self._rxthread = threading.Thread(
                target=self._receive_thread, name="Serial RX thread"
            )
            self._rxthread.start()

        return True

    def close(self):
        """Close interface"""
        if self._serial:
            self._close = True
            self._rxstart_event.set()
            self._rxthread.join()
            self._serial.close()
            self._serial = None

    def _timer_callback(self):
        self._rxtimeout_event.set()

    def read(self, timeout):
        # self._serial.reset_input_buffer()

        # clear events
        self._rxdone_event.clear()
        self._rxtimeout_event.clear()

        self._rxstart_event.set()

        # start timer
        rxtimer = None
        if timeout is not None:
            rxtimer = threading.Timer(timeout, self._timer_callback)
            rxtimer.start()

        self._rxdone_event.wait()  # wait till timeout or data

        # self._rxdone_event.clear()
        # self._startEvent.clear()

        if self._rxdata:  # data is received
            logger.debug("RX= %s", hexlify(self._rxdata))

            if rxtimer:
                rxtimer.cancel()
                self._rxtimeout_event.clear()

            # validate, decode raw frame received
            return decode(self._rxdata)

        # response timeout
        logger.debug("RX= TIMEOUT")

    def write(self, txdata):
        if isinstance(txdata, list):
            # encode data with feig protocol
            txdata = encode(txdata)

        elif isinstance(txdata, bytes):
            pass

        else:
            raise ValueError("Invalid txdata")

        logger.debug("TX= %s", hexlify(txdata))

        # self._serial.reset_output_buffer()
        self._serial.write(txdata)
        # self._serial.flushOutput() # note: this line works in windows, but breaks in pi3

    def transfer(self, timeout: int, txdata: Union[list, bytes]) -> Union[None, bytes]:
        """Send and receive through the interface.

        Args:
            timeout: int,
            txdata: data to be send

        Returns:
            None, if error else bytes()

        Raises:
            ValueError for incorrect txdata
        """
        self.write(txdata)
        return self.read(timeout)

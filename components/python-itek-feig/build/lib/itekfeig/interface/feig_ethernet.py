"""
Feig Ethernet Interface
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import socket
from binascii import hexlify
from typing import Union

from ..common.feig_errors import FeigError
from ..common.feig_protocol import decode, encode

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

MAX_RETRY = 3


class FeigEthernet:

    ID = "Ethernet"

    def __init__(self):
        self._tcpsock = None
        self.error = None
        self._ipaddr = None
        self._tcpport = None
        self._retry = 0

    def _connect(self):
        status = False
        if self._tcpsock is not None:
            try:
                self._tcpsock.connect((self._ipaddr, self._tcpport))
                self.error = FeigError.OK
                status = True
                self._retry = 0

            except socket.timeout:
                logger.debug("connect timeout")
                self._tcpsock.close()
                self._tcpsock = None
                self.error = FeigError.COMM_TIMEOUT

            except socket.error:
                logger.exception("connect error")
                self.error = FeigError.INTERFACE_ERROR
                self._tcpsock.close()
                self._tcpsock = None
                # if error.errno == errno.EHOSTUNREACH:
                #     self.error = FeigError.NO_ROUTE_TO_HOST
                # elif error.errno == errno.ECONNREFUSED:
                #     self.error = FeigError.CONNECTION_REFUSED
                # else:
                #     self.error = FeigError.UNHANDLED

        return status

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
        if isinstance(txdata, list):
            # encode data with feig protocol
            txdata = encode(txdata)

        elif isinstance(txdata, bytes):
            pass

        else:
            raise ValueError("Invalid txdata")

        # If interface error do not transfer, this error might happen
        # - remote socket closed
        if self.error and self.error is FeigError.INTERFACE_ERROR:
            return

        # time.sleep(0.020) # DO_NOT_MODIFY

        # Send Data
        try:
            logger.debug("TX= %s", hexlify(txdata))
            self._tcpsock.settimeout(timeout)
            self._tcpsock.sendall(txdata)
            self.error = FeigError.OK

        except socket.timeout:
            logger.debug("TX= TIMEOUT")
            self.error = FeigError.COMM_TIMEOUT
            self._retry += 1
            if self._retry == MAX_RETRY:
                self.error = FeigError.INTERFACE_ERROR
                logger.error("TX= MAX_RETRY")
            return

        except socket.error:
            logger.exception("TX= ERROR")
            self.error = FeigError.INTERFACE_ERROR
            return

        # Receive Data
        try:
            self._tcpsock.settimeout(timeout)
            rxdata = self._tcpsock.recv(4096)
            self.error = FeigError.OK
            self._retry = 0
            logger.debug("RX= %s", hexlify(rxdata))
            if rxdata:
                return decode(rxdata)

        except socket.timeout:
            logger.debug("RX= TIMEOUT")
            self.error = FeigError.COMM_TIMEOUT
            self._retry += 1
            if self._retry == MAX_RETRY:
                self.error = FeigError.INTERFACE_ERROR
                logger.error("RX= MAX_RETRY")
            return

        except socket.error:
            logger.exception("RX= ERROR")
            self.error = FeigError.INTERFACE_ERROR

    def open(self, ipaddr: str, tcpport: int, timeout=5.0) -> bool:
        """Open interface with given settings.

        Returns:
            True, if interface is/already opened
        """
        if self._tcpsock is None:
            self._ipaddr = ipaddr
            self._tcpport = tcpport

            # configure tcp port
            self._tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._tcpsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            self._tcpsock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            self._tcpsock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 1)
            self._tcpsock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 5)
            self._tcpsock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 2)

            self._tcpsock.settimeout(timeout)

            return self._connect()

    def close(self):
        """Close interface"""
        if self._tcpsock:
            self._tcpsock.shutdown(socket.SHUT_RDWR)
            self._tcpsock.close()
            self._retry = 0
            self._tcpsock = None

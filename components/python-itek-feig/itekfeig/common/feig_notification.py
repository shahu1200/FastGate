#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import socket
import threading
from binascii import unhexlify

from ..common.feig_base import FeigBase
from ..common.feig_errors import FeigError
from ..common.feig_protocol import decode
from ..common.feig_data_parser import brm_and_notif_parser

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# TODO: implement using asyncio


class FeigNotification(FeigBase):
    def __init__(self, interface, lastError):
        """This class implements NOTIFICATION mode functionality of Feig reader.

        Args:
            interface: This the interface on which communication will happen.
            lastError: This parameter is shared for reporting error
        """

        super().__init__()
        FeigBase._interface = interface
        FeigBase._last_error = lastError

        self._maxListner = 1
        self._currentListner = 0

        self._thread = None
        self._event = threading.Event()

    def _socket_comm_thread(self, conn, address, dataQ, ack):
        FeigBase._last_error = FeigError.COMM_TIMEOUT

        try:
            packet = conn.recv(4096)
            if ack is True:
                conn.sendall(unhexlify("020007FF325447"))  # clear buffer
            data = decode(packet)
            if data:
                FeigBase._last_error = FeigError.INVALID_RESPONSE
                if data[0] == 0x22:
                    FeigBase._last_error = self._feig_status_parser(data[1])
                    if (
                        FeigBase._last_error is FeigError.MORE_DATA
                        or FeigBase._last_error is FeigError.OK
                    ):
                        tags = brm_and_notif_parser(data[2:])
                        if tags and len(tags) > 0:
                            if not dataQ.full():
                                dataQ.put((address, tags))

        except (socket.timeout, socket.error):
            logger.exception("NotificationListener")

        finally:
            conn.shutdown(socket.SHUT_RDWR)
            conn.close()

    def _notification_thread(self, port, dataQ, ack):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", port))  # bind on all
        sock.listen()

        while not self._event.set():

            conn, address = sock.accept()
            # spwan a new thread which does communication
            threading.Thread(
                target=self._socket_comm_thread,
                args=(conn, address, dataQ, ack),
                daemon=True,
            ).start()

        # close all connection
        self._event.clear()
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()

    def start(self, port: int, dataQ, ack: bool, listners: int = 1):
        """Start Notification thread.

        Args:
            port: int, PORT on which to listen for incoming data
            dataQ: queue, Queue in which data will be pushed
            ack: bool, True if data received is to be ACKed
            listners: int, Maximum number of listners for diffrent reader
        Returns:
            False If interface is not 'Ethernet'
            True If thread is started or already started
        """
        # check if interface is Ethernet
        if FeigBase._interface.ID != "Ethernet":
            FeigBase._last_error = FeigError.INVALID_INTERFACE
            return False

        self._maxListner = listners

        if self._thread is None:
            self._thread = threading.Thread(
                target=self._notification_thread, args=(port, dataQ, ack), daemon=True
            )
            self._event.clear()
            self._thread.start()

        return True

    def stop(self):
        """Stop Notification thread.
        """
        if self._thread:
            self._event.set()
            self._thread.join()
            self._thread = None

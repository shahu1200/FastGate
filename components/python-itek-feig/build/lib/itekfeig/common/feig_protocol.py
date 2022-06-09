#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FEIG Extended Protocol format

Host -> Reader
-------------------------------------------------------------
|  1  |  2  |  3  |  4  |    5    | 6...N-2 |  N-1  |   N   |
-------------------------------------------------------------
| STX | MSB | LSB | COM | CONTROL |   DATA  |  LSB  |  MSB  |
| x02 | LEN | LEN | ADR |  BYTE   |         | CRC16 | CRC16 |
-------------------------------------------------------------

Reader -> Host
----------------------------------------------------------------------
|  1  |  2  |  3  |  4  |    5    |    6   | 7...N-2 |  N-1  |   N   |
----------------------------------------------------------------------
| STX | MSB | LSB | COM | CONTROL | STATUS |  DATA   |  LSB  |  MSB  |
| x02 | LEN | LEN | ADR |  BYTE   |        |         | CRC16 | CRC16 |
----------------------------------------------------------------------

CRC16 - Cyclic redundancy check of the protocol bytes from 1 to n-2,
CCITT-CRC16 Polynomial: x16 + x12 + x5 + 1 (0x8408)
Start Value: 0xFFFF
Direction: Backward

"""

STX = b"\x02"


def crc16(data: bytes, length):
    """Calculate CRC for the packet
    """
    CRC_PRESET = 0xFFFF
    CRC_POLYNOM = 0x8408
    crc = CRC_PRESET
    for i in range(0, length):
        crc = crc ^ data[i]
        for _ in range(0, 8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ CRC_POLYNOM
            else:
                crc = crc >> 1

    return crc & 0xFFFF


def encode(payload: list):
    """Encode payload as per FEIG protocol.
    This function creates final packet by adding HEADER, FOOTER.

    Returns:
        packet:bytes Final packet to send as per FEIG
    """
    packet_len = 1 + 2 + 1 + len(payload) + 2
    len_lsb = packet_len & 0x00FF
    len_msb = (packet_len >> 8) & 0x00FF

    packet = [
        0x02,
        len_msb,
        len_lsb,
        0xFF,
    ]
    packet = packet + payload

    packet_crc = crc16(packet, len(packet))
    packet.append(packet_crc & 0x00FF)  # LSB
    packet.append((packet_crc >> 8) & 0x00FF)  # MSB

    return bytes(packet)


def decode(packet: bytes):
    """This function will decode the packet as per FEIG protocol. It will also
    verify the CRC of the packet. If OK, it will remove headers, footers from the
    packet and retun the remaining data
    """
    MIN_LENGTH = 7

    data = None
    plen = len(packet)

    if plen >= MIN_LENGTH:
        # when indexing bytes, return value if of type int
        STX_INT = int(STX.hex(), base=16)
        if packet[0] == STX_INT:

            calculated_crc = crc16(packet, plen - 2)
            received_crc = (packet[plen - 1] * 256) + packet[plen - 2]

            if received_crc == calculated_crc:
                # comadr = packet[3]
                data = packet[4:-2]

    return data

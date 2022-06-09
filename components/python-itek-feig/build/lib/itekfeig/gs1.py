"""
Tool used to parse SGTIN-96 hex string from RFID tags.
SGTIN Format (bits):
Header    Filter  Partition   Company Prefix  Item Reference  Serial
8         3       3           20-40           24-4            38
Documentation here:
http://www.gs1.org/sites/default/files/docs/tds/TDS_1_9_Standard.pdf

"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math

# Table defining partition sizes for SGTIN-96
SGTIN_96_PARTITION_MAP = {
    0: (40, 12, 4, 1),
    1: (37, 11, 7, 2),
    2: (34, 10, 10, 3),
    3: (30, 9, 14, 4),
    4: (27, 8, 17, 5),
    5: (24, 7, 20, 6),
    6: (20, 6, 24, 7),
}


class Error(Exception):
    """base error class"""


class SGTINDecodeError(Error):
    """Raised when failed to decode SGTIN"""


def sgtin96_decoder(sgtin96: str) -> tuple:
    """Given a SGTIN-96 hex string, parse each segment.

    Returns:
        tuple: (company_prefix, item_reference, serial) in string

    Raises:
        ValueError
    """

    if not sgtin96.startswith("30"):
        # not a sgtin, not handled
        raise SGTINDecodeError("Invalid SGTIN Header")

    binary = "{0:020b}".format(int(sgtin96, 16)).zfill(96)

    # header = int(binary[:8], 2)
    #tag_filter = int(binary[8:11], 2)

    partition = binary[11:14]
    partition_value = int(partition, 2)

    try:
        m, l, n, k = SGTIN_96_PARTITION_MAP[partition_value]
    except KeyError:
        raise SGTINDecodeError("Invalid Partition")

    company_start = 8 + 3 + 3
    company_end = company_start + m
    company_data = int(binary[company_start:company_end], 2)
    if company_data > pow(10, l):
        # can't be too large
        raise SGTINDecodeError("Invalid Company")

    company_prefix = str(company_data).zfill(l)

    item_start = company_end
    item_end = item_start + n
    item_data = binary[item_start:item_end]
    item_number = int(item_data, 2)
    item_reference = str(item_number).zfill(k)

    serial = str(int(binary[-38:], 2))

    return (company_prefix, item_reference, serial)


def gtin_check_digit(gtin: str) -> int:
    """Given a GTIN (8-14) or SSCC, calculate its appropriate check digit"""

    reverse_gtin = gtin[::-1]
    total = 0
    count = 0
    for char in reverse_gtin:
        digit = int(char)
        if count % 2 == 0:
            digit = digit * 3
        total = total + digit
        count = count + 1

    nearest_multiple_of_ten = int(math.ceil(total / 10.0) * 10)

    return nearest_multiple_of_ten - total


def gtin_check(ean: str) -> bool:
    """Verify EAN/GTIN-8,13 by checking its CHECK digit"""
    ean_len = len(ean)
    if ean_len in (8, 13):
        check_digit = int(ean[-1])
        if gtin_check_digit(ean[:-1]) == check_digit:
            return True

    return False


def tid_parser(tid: str) -> dict:
    """Parse given TID (hex-str)

    Ref: https://www.gs1.org/standards/epcrfid-epcis-id-keys/epc-rfid-tds/1-13

    .. TODO:: parse xtid
    """
    data = {}
    tid_bytes = bytes.fromhex(tid)

    # ISO/IEC 15963 allocation class identifier of E2
    if len(tid_bytes) == 12 and tid_bytes[0] == 0xE2:
        extend_bit = bool(tid_bytes[1] & 0x80)
        security_bit = bool(tid_bytes[1] & 0x40)
        file_bit = bool(tid_bytes[1] & 0x20)

        mdid = tid_bytes[1] & 0x1F
        mdid = (mdid << 4) + ((tid_bytes[2] & 0xF0) >> 4)

        tmn = tid_bytes[2] & 0x0F
        tmn = tmn * 256 + tid_bytes[3]

        sr_no = bytes.hex(tid_bytes[6:])

        data["extend_indicator"] = extend_bit
        data["security_indicator"] = security_bit
        data["file_indicator"] = file_bit
        data["mask_designer_id"] = mdid
        data["tag_model_number"] = tmn
        data["tag_serial_number"] = sr_no

        if extend_bit is True:
            xtid = bytes.hex(tid_bytes[4:6])
            data["xtid"] = xtid
            # TODO: parse xtid

    return data


def sgtin96_to_ean(sgtin96: str) -> tuple:
    """Returns EAN and SerialNumber from SGTIN96"""
    (company_prefix, item_reference, serialno) = sgtin96_decoder(sgtin96)
    ean = company_prefix + item_reference[1:6]
    ean = ean + str(gtin_check_digit(ean))
    srno = serialno.zfill(12)

    return (ean, srno)

"""
Decoding Feig BRM and Notification packets.
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from binascii import hexlify


def _brm_and_notif_record_parser(tr1, tr2, record):
    record = record[2:]  # remove first 2 bytes are record length

    tag = {}
    if tr1 & 0x01:  # epc,tid
        #trtype = record[0]
        #iddib = record[1]
        iddlen = record[2]
        uid = record[3 : 3 + iddlen]
        record = record[3 + iddlen :]

        # add epc, tid
        pc = uid[0:2]
        uid = uid[2:]
        epc_len = (pc[0] >> 3) * 2
        tid_len = iddlen - epc_len - 2

        tag["epc"] = hexlify(uid[0:epc_len]).decode()
        tag["tid"] = hexlify(uid[epc_len : epc_len + tid_len]).decode()

    if tr1 & 0x02:  # Data block present
        db_len = record[0] * 256 + record[1]
        db_size = record[2]
        data = record[3 : 3 + (db_len * db_size)]
        record = record[3 + (db_len * db_size) :]
        tag["data"] = hexlify(data).decode()

    if tr1 & 0x20:  # Time
        dtime = record[0:4]
        record = record[4:]
        tag["rtime"] = int(hexlify(dtime).decode(), base=16)

    if tr1 & 0x40:  # Date
        ddate = record[0:5]
        record = record[5:]
        tag["rdate"] = hexlify(ddate).decode()

    if tr1 & 0x10:  # antenna
        tag["antno"] = record[0]

        if (tr1 & 0x80) and (tr2 & 0x08):
            # Tag Statistics
            tag["tag_cnt"] = str(record[1] * 256 + record[2])
            tag["rssi_max"] = str(record[3])
            tag["rssi_avg"] = str(record[4])
            record = record[8:]

        else:
            # Antenna No only
            record = str(record[1:])

    if tr1 & 0x80:  # Extended Data

        if tr2 & 0x01:  # INPUT
            tag["input"] = hexlify(record[0:2]).decode()
            record = record[2:]

        if tr2 & 0x02:  # MAC
            mac = record[0:6]
            record = record[6:]
            tag["mac"] = hexlify(mac).decode()

        if tr2 & 0x10:  # Antenna Entension
            antennas = []
            ant_cnt = record[0]
            offset = 1
            antennas = []
            for _ in range(0, ant_cnt):
                angle = record[offset + 2] * 256 + record[offset + 3]
                antennas.append(
                    {
                        "antno": record[offset + 0],
                        "rssi": record[offset + 1],
                        "phase_angle": (angle * 360) // 4096,
                    }
                )

                offset += 6

            tag["antennas"] = antennas

    return tag


def brm_and_notif_parser(data):
    tr_data1 = data[0]
    tr_data2 = None

    offset = 1
    if tr_data1 & 0x80:
        tr_data2 = data[1]
        offset = 2

    data_sets = data[offset + 0] * 256 + data[offset + 1]

    tags = []
    if data_sets > 0:
        timestamp = time.time()

        data = data[offset + 2 :]  # remove data_sets
        for _ in range(0, data_sets):
            record_len = data[0] * 256 + data[1]  # get record lenght
            record = data[:record_len]

            tag = _brm_and_notif_record_parser(tr_data1, tr_data2, record)

            data = data[record_len:]  # remove current record

            tag["time"] = timestamp
            tags.append(tag)

    return tags

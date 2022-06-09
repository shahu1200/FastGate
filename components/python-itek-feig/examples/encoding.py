#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import time
import sys
import requests
import os

# get EPC List for encoding
# This API will generate SGTIN and send to caller with access password
def get_epcforencode(url, data):
    TOKEN = "7-HmeNpvrK3xmNZRIVFDxOrSZcYexJEV-eu7M4KbZEBnt8Gp013CUXRmsxokD6wz_ycXUUSjVML9gIrBJ_II6Xt1R1ZAAuOz5mbk18W78sNBDBbTWkifYDMI9navriXK2T-BnnbIptRx96fgF99LoEwCx9imCFKkJjpKGB3j7AjCBjE7iRd7m2Xm4U8ZId-kD67-oZwL8BuJdw0v0_cSctuRCR9kZWH8XyTtlDphH9FAbkotQD7931VEN7oA2Vr7Jx0Sj5viuxJSgWEOHQez7u3bGIVv7_ul9E-NTat1a-8"
    headers = {"Content-Type": "application/json", "Authorization": "Bearer " + TOKEN}

    x = requests.post(url + "getepcforencode", headers=headers, json=data)
    if x.status_code == 200:
        return x.json()

    else:
        print("Request error= ", x.status_code)


def make_scan_transaction(taglist):
    data = {
        # "deviceid": "b8-27-eb-26-82-d2",
        "deviceid": "b8-27-eb-3e-83-db",
        "ean": "8907594310619",
        "qty": len(taglist),
        "items": [],
    }

    for tag in taglist.values():
        # print(tag)

        antennalist = tag["antennas"]
        nearAntNo = antennalist[0]["antno"]
        nearRssi = int(antennalist[0]["rssi"])

        for i in range(1, len(antennalist)):
            if int(antennalist[i]["rssi"]) < nearRssi:
                nearAntNo = antennalist[i]["antno"]
                nearRssi = int(antennalist[i]["rssi"])

        rssilist = []
        for i in range(0, len(antennalist)):
            rssilist.append(
                {
                    "antno": antennalist[i]["antno"],
                    "rssi": antennalist[i]["rssi"],
                    "phase": antennalist[i]["phase_angle"],
                }
            )

        tagInfo = {
            "skuid": "",
            "rfid": tag["epc"].lower(),
            "epc": tag["epc"].lower(),
            "tid": tag["tid"].lower(),
            "readcount": 1,
            "flag": "Ant No:1, RSSI:46, Phase:115",
            "rssi": rssilist,
            "hardtag": True,
            "nearestAntNo": int(nearAntNo),
        }

        data["items"].append(tagInfo)
    return data


def create_unique_tags(taglist):
    unique_tags = {}

    for tag in taglist:
        epc = tag["epc"]
        tid = tag["tid"]

        try:
            rssilist = unique_tags[tid]["rssi"]
            for i in range(0, len(rssilist)):
                if rssilist[i]["antno"] != tag["antno"]:
                    rssilist.append(
                        {
                            "antno": tag["antno"],
                            "rssi": tag["rssi"],
                            "phase": tag["angle"],
                        }
                    )

                else:
                    rssilist[i]["phase"] = tag["angle"]
                    rssilist[i]["rssi"] = tag["rssi"]

            unique_tags[tid]["rssi"] = rssilist

        except KeyError:
            unique_tags[tid] = {}
            unique_tags[tid]["tid"] = tid
            unique_tags[tid]["epc"] = epc
            unique_tags[tid]["rssi"] = []
            unique_tags[tid]["rssi"].append(
                {"antno": tag["antno"], "rssi": tag["rssi"], "phase": tag["angle"]}
            )

    return unique_tags


def scan_count():
    # perform inventory
    # print('\nDoing Inventory ...')
    tags = reader.BufferReadMode.inventory(4000, unique=True)
    if tags is None:
        print("... Failed, ", reader.get_last_error())
        return

    # print(tags)

    if isinstance(tags, list):
        # unique = False
        print("Error: Unique Flag = False")
        return

    # uniqueList = create_unique_tags(tags)
    # print('Unique= ', len(uniqueList))

    return tags


def write_tag_epc(tid, oldepc, newepc, password):
    current_password = password[0]

    #    print('TAG=', tid, oldepc, newepc)

    for pwd in password:
        ret = reader.HostMode.write_epc_memory(oldepc, tid, newepc, pwd)
        #        print(ret)
        if ret is True:
            if current_password != pwd:
                # update password
                ret = reader.HostMode.write_access_password(
                    newepc, tid, current_password, pwd
                )
                # print('password=', ret,tid, oldepc, current_password, pwd)
                if ret is True:  # return correct password
                    return pwd

                else:  # return none
                    # print(reader.get_last_error(), oldepc, tid, nearestAntNo)
                    return

            else:  # return correct password
                return pwd

    return  # return none


def lock_tag(epc, tid, password):
    lock_val = reader.HostMode.ACCESS_LOCK + reader.HostMode.EPC_LOCK
    ret = reader.HostMode.lock(epc, tid, lock_val, password)
    print("LOCK=", ret)

    return ret


def write_ok_data(tagdata, newepc):
    return {
        "tid": tagdata["tid"],
        "epc": newepc,
        "previousepc": tagdata["epc"],
        "antennas": tagdata["antennas"],
    }


def write_sgtins(taglist, sgtinlist, password):

    retry = 0
    writeOkList = []
    failedlist = []

    DEFAULT_PASSWORD = "00000000"

    # password = ['AAAAAAAA', '88888888', '12345678', '00000000']
    # password.append('AAAAAAAA')

    password.append(DEFAULT_PASSWORD)  # append default password

    CURRENT_PASSWORD = password[0]
    # print(password)

    # seprate tags on basis of nearest antennas
    ant1Sgtin = []
    ant2Sgtin = []
    ant3Sgtin = []
    for sgtin in sgtinlist:
        if sgtin["nearestAntNo"] == 1:
            ant1Sgtin.append(sgtin)
        elif sgtin["nearestAntNo"] == 2:
            ant2Sgtin.append(sgtin)
        elif sgtin["nearestAntNo"] == 3:
            ant3Sgtin.append(sgtin)

    # deafult power
    ret = reader.antenna_power(reader.ANTENNA_No1, reader.POWER_1500mW)
    ret = reader.antenna_power(reader.ANTENNA_No2, reader.POWER_1500mW)
    ret = reader.antenna_power(reader.ANTENNA_No3, reader.POWER_1500mW)

    while retry < 3:

        if len(ant1Sgtin) > 0:
            # turn on antenna1
            ret = reader.rf_onoff(reader.ANTENNA_No1, maintainhost=True)
            time.sleep(0.010)
            for sgtin in ant1Sgtin:
                tid = sgtin["tid"]
                oldepc = taglist[tid]["epc"]
                newepc = sgtin["epc"]
                ret = write_tag_epc(tid, oldepc, newepc, password)
                if ret is None:
                    failedlist.append(sgtin)
                elif ret == DEFAULT_PASSWORD:
                    ret = lock_tag(newepc, tid, CURRENT_PASSWORD)
                    if ret is True:
                        writeOkList.append(write_ok_data(taglist[tid], newepc))
                else:
                    writeOkList.append(write_ok_data(taglist[tid], newepc))

            ant1Sgtin = failedlist.copy()
            failedlist.clear()

        if len(ant2Sgtin) > 0:
            # turn on antenna2
            ret = reader.rf_onoff(reader.ANTENNA_No2, maintainhost=True)
            time.sleep(0.010)
            for sgtin in ant2Sgtin:
                tid = sgtin["tid"]
                oldepc = taglist[tid]["epc"]
                newepc = sgtin["epc"]
                ret = write_tag_epc(tid, oldepc, newepc, password)
                if ret is None:
                    failedlist.append(sgtin)
                elif ret == DEFAULT_PASSWORD:
                    ret = lock_tag(newepc, tid, CURRENT_PASSWORD)
                    if ret is True:
                        writeOkList.append(write_ok_data(taglist[tid], newepc))
                else:
                    writeOkList.append(write_ok_data(taglist[tid], newepc))

            ant2Sgtin = failedlist.copy()
            failedlist.clear()

        if len(ant3Sgtin) > 0:
            # turn on antenna3
            ret = reader.rf_onoff(reader.ANTENNA_No3, maintainhost=True)
            time.sleep(0.010)
            for sgtin in ant3Sgtin:
                tid = sgtin["tid"]
                oldepc = taglist[tid]["epc"]
                newepc = sgtin["epc"]
                ret = write_tag_epc(tid, oldepc, newepc, password)
                if ret is None:
                    failedlist.append(sgtin)
                elif ret == DEFAULT_PASSWORD:
                    ret = lock_tag(newepc, tid, CURRENT_PASSWORD)
                    if ret is True:
                        writeOkList.append(write_ok_data(taglist[tid], newepc))
                else:
                    writeOkList.append(write_ok_data(taglist[tid], newepc))

            ant3Sgtin = failedlist.copy()
            failedlist.clear()

        # no tag remainings
        if len(ant1Sgtin) == 0 and len(ant2Sgtin) == 0 and len(ant3Sgtin) == 0:
            break

        # retry
        retry += 1
        print("RETRY=", retry)
        ret = reader.antenna_power(reader.ANTENNA_No1, reader.POWER_1700mW)
        ret = reader.antenna_power(reader.ANTENNA_No2, reader.POWER_1700mW)
        ret = reader.antenna_power(reader.ANTENNA_No3, reader.POWER_1700mW)

    failedTags = []
    if retry >= 3:
        for sgtin in ant1Sgtin:
            failedTags.append({"tid": sgtin["tid"], "epc": sgtin["epc"]})
        for sgtin in ant2Sgtin:
            failedTags.append({"tid": sgtin["tid"], "epc": sgtin["epc"]})
        for sgtin in ant3Sgtin:
            failedTags.append({"tid": sgtin["tid"], "epc": sgtin["epc"]})

    return writeOkList, failedTags


def change_brm():
    # print('>> Change to BRM ...')
    ret = reader.change_mode(reader.MODE_BRM)
    if ret is None:
        print("... Failed, ", reader.get_last_error())
        reader.disconnect()
        sys.exit(0)
    #    elif ret is False:
    #        print('... ALREADY SET')
    #    else:
    #        print('... OK')

    # rf reset
    #    reader.rf_controller_reset()

    #    time.sleep(10.0)

    # antenna enable
    reader.rf_onoff(reader.ANTENNA_No1)


def change_host():

    # force off antenna
    ret = reader.rf_onoff(reader.ANTENNA_OFF, maintainhost=True)
    print("HOST MODE = ", ret)


#    #print('>> Change to HOST ...')
#    ret = reader.change_mode(reader.MODE_HOST)
#    if ret is None:
#        print('... Failed, ', reader.get_last_error())
#        reader.disconnect()
#        sys.exit(0)
#    elif ret is False:
#        print('... ALREADY SET')
#    else:
#        print('... OK')

# Do rf reset
# reader.rf_reset()
#    reader.rf_controller_reset()

#    time.sleep(0.010)


def send_to_server(taglist):
    # create json asper api
    tagTransaction = make_scan_transaction(taglist)
    # print('TXN=',tagTransaction)

    return get_epcforencode("http://192.168.0.32:9032/StoresAPI/api/", tagTransaction)


def print_stats(cycle_data, cycle_count):
    def avg(data: list):
        return sum(data) / len(data)

    print(
        "\n*************** Statistics for {0} cycles ***************".format(
            cycle_count
        )
    )
    brm = cycle_data["brm"]
    print(">> Change to BRM timings...")
    print(
        "   MIN=",
        round(min(brm), 3),
        "AVG=",
        round(avg(brm), 3),
        "MAX=",
        round(max(brm), 3),
    )

    scan = cycle_data["scan"]
    print(">> Scan count timings...")
    print(
        "   MIN=",
        round(min(scan), 3),
        "AVG=",
        round(avg(scan), 3),
        "MAX=",
        round(max(scan), 3),
    )

    server = cycle_data["server"]
    print(">> Send data to server timings...")
    print(
        "   MIN=",
        round(min(server), 3),
        "AVG=",
        round(avg(server), 3),
        "MAX=",
        round(max(server), 3),
    )

    host = cycle_data["host"]
    print(">> Change to HOST timings...")
    print(
        "   MIN=",
        round(min(host), 3),
        "AVG=",
        round(avg(host), 3),
        "MAX=",
        round(max(host), 3),
    )

    encode = cycle_data["encode"]
    print(">> Encoding timings...")
    print(
        "   MIN=",
        round(min(encode), 3),
        "AVG=",
        round(avg(encode), 3),
        "MAX=",
        round(max(encode), 3),
    )

    read = cycle_data["read"]
    print(">> Total tag read...")
    print(
        "   MIN=",
        round(min(read), 3),
        "AVG=",
        round(avg(read), 3),
        "MAX=",
        round(max(read), 3),
    )

    write = cycle_data["write"]
    print(">> Total tag write...")
    print(
        "   MIN=",
        round(min(write), 3),
        "AVG=",
        round(avg(write), 3),
        "MAX=",
        round(max(write), 3),
    )


###############################################################################
###############################################################################
###############################################################################

print("Importing 'itekfeig' module ...")
try:
    from itekfeig import FeigLogger
    from itekfeig import LRU1002
except ImportError:
    print("itekfeig package not installed")
    sys.exit(0)
print("... OK")

# This will return ROOT logger, with log file in HOME folder
# and log level set to DEBUG
logger = FeigLogger(loggerLevel=logging.DEBUG)
reader = LRU1002()

# Connect to the reader
print("\nConnecting to reader ...")
if os.name == "nt":  # windows
    settings = {"PORT": "COM3", "BAUDRATE": 38400, "PARITY": "NONE"}

else:  # posix/linux/rpi
    settings = {"PORT": "/dev/ttyS3", "BAUDRATE": 38400, "PARITY": "NONE"}

ret = reader.connect(reader.INTERFACE_SERIAL, settings)
if ret is False:
    print("... Failed, ", reader.get_last_error())
    sys.exit(0)

else:
    print("...", ret)

# Connection is successfull
print("\nReader Device-ID ...")
print("...", reader.device_id())

process_timeing = {
    "brm": [],
    "host": [],
    "scan": [],
    "server": [],
    "encode": [],
    "read": [],
    "write": [],
    "failed": [],
}

# do encoding in multiple times
MAX_CYCLE = 1
for i in range(0, MAX_CYCLE):
    print("\n>>>> CYCLE=", i + 1)

    # Enter Brm mode
    start = time.time()
    change_brm()
    end = time.time() - start
    process_timeing["brm"].append(end)

    # do scanning
    start = time.time()
    taglist = scan_count()
    end = time.time() - start
    process_timeing["scan"].append(end)
    # print('SCAN=', taglist)

    failed_tags = ["e2801170200013d1d6bf09e9"]
    keys = taglist.keys()
    for ft in failed_tags:
        if ft in keys:
            taglist.pop(ft)

    # send to server
    start = time.time()
    resp = send_to_server(taglist)
    # print('server rsp=', resp)
    end = time.time() - start
    process_timeing["server"].append(end)

    if (resp is not None) and (resp["Success"] == "true"):
        # extract info
        password = []
        pwd = resp["Data"]["ap"]["currentaccesspwd"]
        password.append(pwd)

        oldpassword = resp["Data"]["ap"]["oldaccesspwds"]
        for i in range(0, len(oldpassword)):
            pwd = oldpassword[i]["accesspwd"]
            password.append(pwd)

        sgtins = resp["Data"]["sgtins"]
        # print('SGTINS=', sgtins)

        # Enter Host mode
        start = time.time()
        change_host()
        end = time.time() - start
        process_timeing["host"].append(end)

        process_timeing["read"].append(len(sgtins))

        print(">> Writing SGTINS=", len(sgtins))
        start = time.time()
        writeok, failedTags = write_sgtins(taglist, sgtins, password)
        end = time.time() - start
        process_timeing["encode"].append(end)

        print("   Wrote= ", len(writeok))
        process_timeing["write"].append(len(writeok))

        if len(failedTags) > 0:
            print("\nFailed tags...", len(failedTags))
            print(failedTags)

        """
        if len(writeok) != len(sgtins):
            failedList = process_timeing['failed']
            for tag1 in failedTags:
                if tag2 in failedList:
                    failedList.append(tag)
            process_timeing['failed'] = failedList
        """

    else:
        process_timeing["host"].append(0.0)
        process_timeing["encode"].append(0.0)
        print("Error:", resp)

### print statistics
print_stats(process_timeing, MAX_CYCLE)

if len(process_timeing["failed"]) > 0:
    print("\n!!! Failed Tag List", len(process_timeing["failed"]))
    print(process_timeing["failed"])

# disconnect
print("\nDisconnecting from reader ...")
reader.disconnect()
print("... Done")

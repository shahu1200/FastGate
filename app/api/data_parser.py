#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
import json
import logging
from .errors import APIParsingError

logger = logging.getLogger(__name__)

def current_datetime():
    now = datetime.now()
    return now.strftime("%d-%b-%Y %H:%M:%S")

def current_datetime1():
    now = datetime.now()
    return now.strftime("%Y-%m-%dT%H:%M:%S")

def generate_flag(flag_data):
    s_tring = ''
    for num in flag_data:
        if s_tring != '':
            s_tring += ", "
        s_tring += "Ant No:{}, RSSI:{}, Phase:{}".format(num['antno'], num['rssi'], num['phase_angle'])
    return s_tring

def common_items(data):
    items = []
    if data:
        if len(data) > 0:
            items = [
                {
                    "skuid": data[key]['ean'],
                    "rfid": data[key]['epc'],
                    "tid": data[key]['tid'],
                    "epc": data[key]['epc'],
                    "readcount": data[key]['seen_count'],
                    "flag": generate_flag(data[key]['antennas']),
                    "rssi": data[key]['antennas'],
                    "hardtag": data[key]['hard_tag'],
                    "nearestAntNo": data[key]['nearestAnt'],
                }
                for key in data
            ]

    return items

def scancount(settings, txd, data):
    """
    Add Fields and Create JSON for scan count
    """
    logger.debug("scancount data : "+str(data))
    try:
        items = [
                    {
                    "skuid": item['ean'],
                    "tid": item['tid'],
                    "rfid": item['epc'],
                    "epc": item['epc'],
                    "flag": generate_flag(item['antennas']),
                    "readcount": item['seen_count'],
                    "hardtag":False,
                    "nearestAntNo": 1,
                    "rssi": [
                            {
                            "antno":antenna['antno'],
                            "rssi":antenna['rssi'],
                            "phase":antenna['phase_angle']
                            }
                            for antenna in item['antennas']
                        ]
                    }
                    for item in data.values()
                ]
        req_data = {
                "deviceid": settings["app"]["macId"],
                "txdate": current_datetime1(),
                "hunumber": txd,
                "storecode":settings["app"]["storeCode"],
                "streetTags":[],
                "storevendorid":None,
                "salesordernumber":None,
                "destinationtype":None,
                "codeandname":None,
                "items": items
                }
        return json.dumps(req_data)
    except KeyError as e:
        logger.warning("scan count data parsing key error %s", e)
        raise APIParsingError("scan count data parsing key error")

def hurejection(settings, txd, data):
    """
    HU rejection, in any process if hu is rejected then need to call api
    Add Fields and Create JSON for HU Rejection
    """
    try:
        req_data = {
                "deviceid": settings["macId"],
                "txdate": current_datetime(),
                "hunumber": txd['huNumber'],
                "hureason": txd['huReason'],
                "trip_num": txd['tripNo'],
                "delvno": None,
                "flag": txd['flag'],
                "items": common_items(data)
                }
        return json.dumps(req_data)
    except KeyError as e:
        logger.warning("hu rejection data parsing key error %s", e)
        raise APIParsingError("hu rejection data parsing key error")

def sendcompletetrip(settings, txd):
    """
    to upload & mark trip completed or cancel call api.
    """
    try:
        req_data = {
                "deviceid": settings["macId"],
                "txdate": current_datetime(),
                "tripno": txd['tripNo'],
                "status": txd["status"],
                "IsInward": txd['isInward']
                }
        return json.dumps(req_data)
    except KeyError as e:
        logger.warning("send complete trip data parsing key error %s", e)
        raise APIParsingError("send complete trip data parsing key error")

def get_store_list(settings):
    """get store list
    """
    try:
        req_data = {
                "deviceid": settings["macId"],
                "macid": settings["macId"]
                }
        return json.dumps(req_data)
    except KeyError as e:
        logger.warning("get store list parsing key error %s", e)
        raise APIParsingError("get store list parsing key error")

def get_vendor_list(settings):
    """get vendor list
    """
    try:
        req_data = {
                "deviceid": settings["macId"],
                "macid": settings["macId"]
                }
        return json.dumps(req_data)
    except KeyError as e:
        logger.warning("get vendor list parsing key error %s", e)
        raise APIParsingError("get vendor list parsing key error")

def bulkencoding(settings, data):
    """
    To upload encoding logs and decoding
    """
    logger.info(data)
    taglist = data.get("tagList", None)
    try:
        items = [
            {
            "tid": item['tid'],
            "epc": item['epc'],
            "previousepc": item['previousepc'],
            "rssi": [
                    {
                    "antno":antenna['antno'],
                    "rssi":antenna['rssi'],
                    "phase":antenna['phase_angle']
                    }
                    for antenna in item['antennas']
                ]
            }
            for item in taglist.values()
        ]
        req_data = {
            "deviceid": settings["macId"],
            "txdate": current_datetime(),
            "skuid": data['skuid'],
            "type": data['type'],
            "items": items
        }
        return json.dumps(req_data)
    except KeyError as e:
        logger.warning("bulkencoding data parsing error %s", e)
        raise APIParsingError("bulkencoding data parsing error")

def bulkdecodingpwd(settings):
    try:
        req_data = {
                "deviceid": settings["macId"],
                "txdate": current_datetime()
                }
        return json.dumps(req_data)
    except KeyError as e:
        logger.warning("bulkdecodingpwd data parsing key error %s", e)
        raise APIParsingError("bulkdecodingpwd data parsing key error")

def gethuoutward(settings, txd):
    """
    To hu 'HUverificationn' call api to get hu level sku detail to verify
    """
    try:
        req_data = {
                "deviceid": settings["macId"],
                "huNumber": txd['huNumber']
                }
        return json.dumps(req_data)
    except KeyError as e:
        logger.warning("gethuoutward data parsing key error %s", e)
        raise APIParsingError("gethuoutward data parsing key error")

def tagcirculation(settings, txd, data):
    """
    Outward
        To Tag circulation log upload call api
    """
    try:
        req_data = {
            "deviceid": settings["app"]["macId"],
            "txdate": current_datetime(),
            "hunumber": txd["huNumber"],
            "destinationtype": txd["destinationtype"],
            "codeandname":txd["codeandname"],
            "streetTags":[],
            "storevendorid":txd["storevendorid"],
            "salesordernumber":txd["salesordernumber"],
            "storecode":settings["app"]["storeCode"],
            "items": common_items(data)
            }
        return json.dumps(req_data)
    except KeyError as e:
        logger.warning("tagcirculation data parsing key error %s", e)
        raise APIParsingError("tagcirculation data parsing key error")

def hu_quantity(settings, txd, data):
    """
    After verification completed upload logs to server
    """
    try:
        req_data = {
                "deviceid": settings["macId"],
                "txdate": current_datetime(),
                "trip_num": txd['tripNo'],
                "IsInward": txd['isInward'],
                "hu_details": generate_hu_details(txd, data)
                }
        return json.dumps(req_data)
    except KeyError as e:
        logger.warning("hu quantity data parsing key error %s", e)
        raise APIParsingError("hu quantity data parsing key error")

def generate_hu_details(txd, data):
    try:
        hu_details = [
                {
                    "hu_number": txd['huNumber'],
                    "receivedQty": data["recQty"],
                    "reprocessReason": data["reprocessReason"],
                    "items": generate_hu_items(data),
                    "streetTags": []
                    }
                for key in data
                ]
        return hu_details
    except KeyError as e:
        logger.warning("generate hu details data parsing key error %s", e)
        raise APIParsingError("generate hu details data parsing key error")

def generate_hu_items(data):
    try:
        hu_items = [
                {
                    "skuid": None,
                    "previousepc": None,
                    "epc": data[key]['epc'],
                    "tid": data[key]['tid'],
                    "hardtag": True,
                    "rssi": data[key]['antennas']
                    }
                for key in data
                ]
        return hu_items
    except KeyError as e:
        logger.warning("generate hu items data parsing key error %s", e)
        raise APIParsingError("generate hu items data parsing key error")

def getepcencode(settings, data):
    try:
        req_data = {
            "deviceid": settings["macId"],
            "ean": data['ean'],
            "qty": data['qty'],
            "items": common_items(data["data"]),
        }
        return json.dumps(req_data)

    except KeyError as e:
        logger.warning("getepcencode data parsing key error %s", e)
        raise APIParsingError("getepcencode data parsing key error")

def completetripdata(settings, txd, data):
    """
    to upload HU inward completed call api
    """
    try:
        DataList = [
            {
            "$id": data[key]["id"],
            "trip_num": txd["tripNo"],
            "delv_num": txd["delvNo"],
            "hu_number": txd['huNumber'],
            "skuid": data[key]['skuId'],
            "packQty": txd["packQty"],
            "hustatus": "P"
            }
            for key in data
            ]
        req_data = {
            "$id": "1",
            "Success": "true",
            "Error": False,
            "Data" : DataList
            }
        return json.dumps(req_data)
    except KeyError as e:
        logger.warning("complete trip data parsing key error %s", e)
        raise APIParsingError("complete trip data parsing key error")

def get_token(settings):
    try:
        req_data = {
                "grant_type": "password",
                "username": settings["username"],
                "password": settings["password"]
                }
        return req_data
    except KeyError as e:
        logger.warning("get token data parsing key error %s", e)
        raise APIParsingError("get token data parsing key error")

def trip_hu_data(settings, txd):
    """
    Add Fields and Create JSON for get Trip HU Data
    Get Trip Hu data from server using this parameter,
    type - H for HU Number or T for Trip Number
    """
    try:
        req_data = {
                "tripNo": txd['tripNo'],
                "storeCode": settings["app"]["storeCode"],
                "type": txd['type'],  # H for HU Number or T for Trip Number
                "deviceid": settings["app"]["macId"],
                "isinward": txd['isinward']  # True or False
                }
        return json.dumps(req_data)
    except KeyError as e:
        logger.warning("trip hu data parsing key error %s", e)
        raise APIParsingError("trip hu data parsing key error")

def complete_trip_data(settings, txd, data):
    """
    Add Fields and Create JSON for Send Complete Trip Data
    """
    try:
        req_data = {
                "deviceid": settings["macId"],
                "txdate": current_datetime(),
                "trip_num": txd['tripNo'],
                "IsInward": txd['isInward'],
                "hu_details": generate_hu_details(data),
                }
        return json.dumps(req_data)
    except KeyError as e:
        logger.warning("complete trip data parsing key error %s", e)
        raise APIParsingError("complete trip data parsing key error")

def complete_trip(settings, txd):
    try:
        req_data = {
                "tripno": txd['tripNo'],
                "status": txd['status'],
                "deviceid": settings["macId"],
                "txdate": current_datetime(),
                "IsInward": txd['isInward']
                }
        return json.dumps(req_data)
    except KeyError as e:
        logger.warning("complete trip parsing key error %s", e)
        raise APIParsingError("complete trip parsing key error")

def hu_details(settings, txd):
    try:
        req_data = {
                "huNumber": txd['huNumber'],
                "deviceid": settings["macId"]
                }
        return json.dumps(req_data)
    except KeyError as e:
        logger.warning("hu details parsing key error %s", e)
        raise APIParsingError("hu details parsing key error")

def access_password(settings):
    try:
        req_data = {
                "deviceid": settings["macId"]
                }
        return json.dumps(req_data)
    except KeyError as e:
        logger.warning("access password parsing key error %s", e)
        raise APIParsingError("access password parsing key error")

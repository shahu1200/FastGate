#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
File     : data_parser.py
Author   : Abhijit Darwan
Email    : abhijit.darwan@infoteksoftware.com
Created  : Tuseday 18 May 2021
Modified : FILE_MODIFIED
"""

import requests
import logging
import json

from logging import ERROR, handlers

from . import data_parser
from . import data_unparser
from api.errors import *

from api.settings import POST

#####################################################################
# Setup logger
PATH_FILE_LOG = "logs/"
formatter = logging.Formatter(
    "%(asctime)s::%(levelname)s::%(filename)s::%(lineno)d %(message)s"
)
logger = logging.getLogger("api")
logger.setLevel(logging.DEBUG)

# time logger
handler = handlers.TimedRotatingFileHandler(
    PATH_FILE_LOG + "api/api.log",
    when="midnight",
    backupCount=10,
    interval=1,
)
handler.setFormatter(formatter)
logger.addHandler(handler)
# handler.doRollover()


class API:

    def __init__(self, settings):
        logger.debug("API debug mode!")
        # print("data_api.py class API init")
        try:
            self._settings = settings
            self._app_settings = settings["app"]
            username = settings["api"].get("username", None)
            password = settings["api"].get("password", None)
            if username is None or password is None:
                username = "apiuser"
                password = "apiuser"
            POST["username"] = username
            POST["password"] = password
            self._api_settings = POST
            self.__url = settings["api"]["url"]
            self.__token = "Bearer "+ self._settings["api"]["token"]
        except KeyError:
            logger.fatal("settings are not provided")
            raise APIError("settings are not provided")

    def header(self, token=None):
        """
        Common Header for API's except get_security_token
        """
        if token != None:
            self.__token = token
        return {
            "Content-Type": "application/json",
            "Authorization": self.__token
            }

    def scan_count(self, txd, data):
        """
        scan count rfid tags
        """
        url = self.__url + self._api_settings["scancount"]
        header = self.header(self.__token)
        try:
            req_msg = data_parser.scancount(self._settings, txd, data)
        except APIError:
            raise APIError("API parsing error")
    
        try:
            api_ret = _api_request(url, header, req_msg,"scancount", self._settings["api"]["timeout"])
        except APITimeoutError as e:
            raise APIError(str(e))
        except APIError as e:
            raise APIError(str(e))

        try:
            ret_unpars = data_unparser.scancount(api_ret)
        except APIError:
            raise APIError("unparsing error")
        return ret_unpars

    def get_trip_hu_data(self, txd):
        """
        Inward
        to get trip detail call api or to get hu data same api need to call
        """
        url = self.__url + self._api_settings["gettriphudata"]
        header = self.header(self.__token)

        try:
            req_msg = data_parser.trip_hu_data(self._settings, txd)
        except APIParsingError:
            raise APIParsingError("get trip hu data parsing error")
        try:
            api_ret = _api_request(url, header, req_msg, "gettriphudata", self._settings["api"]["timeout"])
        except APIError:
            raise APIError("get trip hu data API bad request")
        try:
            if api_ret["Success"] == "true":
                ret_unpars = data_unparser.gethutripdata(api_ret)
            else:
                ret_unpars = api_ret
        except APIError:
            raise APIError("unparsing error")
        return ret_unpars

    def hu_rejection(self, txd, data):
        """
        Inward
        to upload & mark trip completed or cancel call api.
        """
        url = self.__url + self._api_settings["hurejection"]
        header = self.header(self.__token)
        try:
            req_msg = data_parser.hurejection(self._app_settings, txd, data)
        except APIParsingError:
            raise APIParsingError("hurejection API data parsing error")

        try:
            api_ret = _api_request(url, header, req_msg,"hurejection", self._settings["api"]["timeout"])
        except APIError as e:
            raise APIError(str(e))
        try:
            ret_unpars = data_unparser.hurejection(api_ret)
        except APIError:
            raise APIError("unparsing error")

        return ret_unpars

    def send_complet_trip(self, txd):
        """
        Inward
        to upload & mark trip completed or cancel call api.
        """
        url = self.__url + self._api_settings["sendcompletetrip"]
        header = self.header(self.__token)
        try:
            req_msg = data_parser.sendcompletetrip(self._app_settings, txd)
        except APIParsingError:
            raise APIParsingError("send complete trip API data parsing error")

        try:
            api_ret = _api_request(url, header, req_msg,"sendcompletetrip", self._settings["api"]["timeout"])
        except APIError:
            raise APIError("send complete trip API request error")

        try:
            ret_unpars = data_unparser.sendcompletetrip(api_ret)
        except APIError:
            raise APIError("unparsing error")
        return api_ret

    def get_store_list(self):
        url = self.__url + self._api_settings["getstorelist"]
        header = self.header(self.__token)
        try:
            req_msg = data_parser.get_store_list(self._app_settings)
        except APIParsingError:
            raise APIParsingError("getstorelist API data parsing error")

        try:
            api_ret = _api_request(url, header, req_msg,"getstorelist", self._settings["api"]["timeout"])
        except APIError as e:
            raise APIError(e)

        try:
            ret_unpars = data_unparser.getstorelist(api_ret)
        except APIError:
            raise APIError("unparsing error")
        return api_ret

    def get_vendor_list(self):
        url = self.__url + self._api_settings["getvendorlist"]
        header = self.header(self.__token)
        try:
            req_msg = data_parser.get_vendor_list(self._app_settings)
        except APIParsingError:
            raise APIParsingError("getvendorlist API data parsing error")

        try:
            api_ret = _api_request(url, header, req_msg,"getvendorlist", self._settings["api"]["timeout"])
        except APIError as e:
            raise APIError(e)

        try:
            ret_unpars = data_unparser.getvendorlist(api_ret)
        except APIError:
            raise APIError("unparsing error")
        return api_ret

    def get_hu_outward(self, txd):
        """
        Outward
        txd : huNumber
        To hu 'HUverificationn' call api to get hu level sku detail to verify
        """
        url = self.__url + self._api_settings["gethuoutward"]
        header = self.header(self.__token)
        try:
            req_msg = data_parser.gethuoutward(self._app_settings, txd)
        except APIParsingError:
            raise APIParsingError("get hu outward data parsing error")
        try:
            api_ret = _api_request(url, header, req_msg,"gethuoutward", self._settings["api"]["timeout"])
        except APIError as e:
            raise APIError(str(e))

        try:
            ret_unpars = data_unparser.gethuoutward(api_ret)
        except APIError:
            raise APIError("unparsing error")
        return api_ret

    def tag_circulation(self, txd, data):
        """
        Outward
        To Tag circulation log upload call api
        """
        url = self.__url + self._api_settings["tagcirculation"]
        header = self.header(self.__token)
        try:
            req_msg = data_parser.tagcirculation(self._settings, txd, data)
        except APIParsingError:
            raise APIParsingError("tag circulation data parsing error")

        try:
            api_ret = _api_request(url, header, req_msg,"tagcirculation", self._settings["api"]["timeout"])
        except APIError as e:
            raise APIError(str(e))

        try:
            ret_unpars = data_unparser.tagcirculation(api_ret)
        except APIError:
            raise APIError("unparsing error")
        return api_ret

    def send_hu_qty(self, txd, data):
        """
        Outward
        After verification completed upload logs to server
        sendHUQty
        """
        url = self.__url + self._api_settings["sendhuqty"]
        header = self.header(self.__token)
        try:
            req_msg = data_parser.hu_quantity(self._app_settings, txd, data)
        except APIParsingError:
            raise APIParsingError("send hu qty data parsing error")
        try:
            api_ret = _api_request(url, header, req_msg,"sendhuqty", self._settings["api"]["timeout"])
        except APIError:
            raise APIError("send hu qty API bad request")

    def bulk_encoding(self, data):
        """
        To upload encoding logs
        API will send list of all epc to server of a encode products.
        """
        url = self.__url + self._api_settings["bulkencoding"]
        header = self.header(self.__token)
        
        try:
            req_msg = data_parser.bulkencoding(self._app_settings, data)
        except APIParsingError:
            raise APIParsingError("bulk encoding data parsing error")

        try:
            api_ret = _api_request(url, header, req_msg,"bulkencoding", self._settings["api"]["timeout"])
        except APIError:
            raise APIError("bulk encoding un-parsing error")

        try:
            ret_unpars = data_unparser.bulkencoding(api_ret)
        except APIError:
            raise APIError("unparsing error")
        return api_ret

    def get_epc_bulk_encoding(self, txd, data):
        """
        To get sgtin list for encode rfid tag and password to write data into rfid tag.
        """
        url = self.__url + self._api_settings["getepcbulkencoding"]
        header = self.header(self.__token)
        try:
            req_msg = data_parser.getepcbulkencoding(self._app_settings, txd, data)
        except APIParsingError:
            raise APIParsingError("get epc bulk encoding data parsing error")

        try:
            api_ret = _api_request(url, header, req_msg, "getepcbulkencoding", self._settings["api"]["timeout"])
        except APIError:
            raise APIError("get epc bulk encoding API bad request")

        try:
            ret_unpars = data_unparser.getepcbulkencoding(api_ret)
        except APIError:
            raise APIError("unparsing error")
        return api_ret

    def bulk_decoding_pwd(self):
        """
        To write data in RFID tag get access password
        """
        url = self.__url + self._api_settings["bulkdecodingpwd"]
        header = self.header(self.__token)

        try:
            req_msg = data_parser.bulkdecodingpwd(self._app_settings)
        except APIParsingError:
            raise APIParsingError("bulk encoding pwd data parsing error")

        try:
            api_ret = _api_request(url, header, req_msg, "bulkdecodingpwd", self._settings["api"]["timeout"])
        except APIError:
            raise APIError("bulk encoding pwd API bad request")

        try:
            ret_unpars = data_unparser.bulkdecodingpwd(api_ret)
        except APIError:
            raise APIError("unparsing error")
        return api_ret

    def get_epc_for_encoding(self, data):
        """
        To get sgtin list for encode rfid tag and password to write data into rfid tag.
        """
        url = self.__url + self._api_settings["getepcforencode"]
        header = self.header(self.__token)
        try:
            req_msg = data_parser.getepcencode(self._app_settings, data)
        except APIParsingError:
            raise APIParsingError("get epc encode API data parsing error")

        try:
            api_ret = _api_request(url, header, req_msg, "getepcforencode", self._settings["api"]["timeout"])
        except APIError:
            raise APIError("get epc encode API request error")

        try:
            ret_unpars = data_unparser.getepcencode(api_ret)
        except APIError:
            raise APIError("unparsing error")

        return api_ret

    def send_complet_trip_data(self, txd, data):
        """
        Inward
        to upload HU inward completed call api
        """
        url = self.__url + self._api_settings["completetripdata"]
        header = self.header(self.__token)

        try:
            ret_unpars = data_unparser.getepcencode(api_ret)
        except APIError:
            raise APIError("unparsing error")
        return api_ret

    def get_token(self):
        """
        Get access token
        """
        url = self.__url + self._api_settings["token"]
        header = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Bearer " + self.__token
        }
        try:
            req_msg = data_parser.get_token(self._api_settings)
        except APIParsingError:
            raise APIParsingError("get token API data parsing error")
        try:
            
            api_ret = _api_request(url, header, req_msg, "get token", self._settings["api"]["timeout"])
        except Exception as e:
            raise APIError(e)
        try:
            out = data_unparser.get_token(api_ret)
        except APIParsingError:
            raise APIParsingError("get token API un parsing error")

        if out["error"] == "false":
            self.__token = out["Authorization"]

        return out


def _api_request(url, header, req_msg, apiname, timeout=10.0):
    logger.info("request url name: %s body: %s", url, req_msg)
    try:
        ret = requests.post(url,
                            headers=header,
                            data=req_msg,
                            timeout=timeout)

        if ret.status_code == 200:
            logger.debug('api response : ' + str(ret.json()))
            return ret.json()
        else:
            message = json.loads(ret.text)
            if "Message" in message.keys():
                message = message["Message"]
            logger.debug("http error : "+ str(ret.status_code) + " " + str(ret.text))
            raise APIError(str(message))

    except APIError as e:
        raise APIError(str(e))
    except ConnectionError as e:
        raise APIError("Http connection error : " + str(e))
    except TimeoutError:
        logger.error("%s API Not working", apiname)
        raise APIError("Http Timeout error")


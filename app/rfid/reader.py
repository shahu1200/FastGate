#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import queue
import copy
import threading
from tkinter import E

import serial
import logging
from logging import handlers

import itekfeig as feig
from itekfeig import FeigError
from itekfeig import gs1

from .errors import RFIDErrors
from ..settings import PATH_FILE_LOG ,CONFIG_TOML_FILE
# from ..gpio import GpioProcess
from ..utils import read_local_config

# from ..gpio.HandleGpio import HandleGPIO
from ..gpio import GpioProcess
# from ..main import gpio1
from app import main
# gpio = main.gpio1
#####################################################################
# Setup logger


PATH_FILE_LOG += "logs/"


formatter = logging.Formatter(
    "%(asctime)s::%(levelname)s::%(filename)s::%(lineno)d %(message)s"
)
logger = logging.getLogger("rfid")
#logger.setLevel(logging.DEBUG)

# time logger
handler = handlers.TimedRotatingFileHandler(
    PATH_FILE_LOG + "rfid/rfid.log",
    when="midnight",
    backupCount=10,
    interval=1,
)
handler.setFormatter(formatter)
logger.addHandler(handler)
# handler.doRollover()

"""
# stream logger
console = logging.StreamHandler()
console.setFormatter(formatter)
logger.addHandler(console)
"""


class RFIDReader:
    # publish topic
    PUBLISH_SETUP = 1
    PUBLISH_SCANCOUNT = 2
    PUBLISH_ENCODING = 3
    PUBLISH_DECODING = 4
    PUBLISH_DIAGNOSTIC = 5
    PUBLISH_FASTGATE = 6
    PUBLISH_MRU_SETUP = 7

    STATUS_OK = 0
    STATUS_RUNNING = 1
    STATUS_ERROR = 2
    

    def __init__(self, loglevel="DEBUG"):
        # print("reader.py class RFIDReader init")
        logger.setLevel(loglevel)

        self._queue = queue.Queue()

        self._config = None
        self._interface = None

        self.on_setup = None
        self.on_scancount = None
        self.on_encoding = None
        self.on_decoding = None
        self.on_diagnostic = None
        self.on_fastgate = None
        self.on_info = None

        self.reader_id = None
        self.reader_info = None

        self._reader = None

        self.DEFAULT_PASSWORD = "00000000"

        self._exitEvent = threading.Event()

        self._ant_power = {}
        self._ant_rssi = {}
        self._rssi_filter = False

        self._encode_list = {}
        self.MAX_ENCODE_RETRY = 0
        self._serial_set = True     
        # configfile = read_local_config(CONFIG_TOML_FILE)
        # self.gpio = GpioProcess(configfile["gpio"])
        # self.rfidId = None
        # self.rfidName =None


    def publish(self, topic, message=None):
        self._queue.put((topic, message))

    def run(self):
        logger.debug("RFID service started...")
        
       
        while not self._exitEvent.is_set():
            topic, message = self._queue.get()
            logger.debug("RFID published message = {} on topic {}".format(message, topic))
            print("reader.py run topic >",topic)
            # Exceute respective cmds
            if topic == RFIDReader.PUBLISH_SETUP:
                if message["interface"] == "serial":
                    self._serial_set = True                    
                    self.setup_fastgate(message)
                else:
                    self._serial_set = False                    
                    self.setup(message)
                print("setup done!")

            elif topic == RFIDReader.PUBLISH_SCANCOUNT:
                self.scan_count(message)
            
            elif topic == RFIDReader.PUBLISH_FASTGATE:
                print("Fastgate scan started!")
                print(message)
                if self._serial_set:
                    self.fastgate_scan(message)
                else:
                    logger.fatal("Device can not except serial mode! in scan mode!")

            elif topic == RFIDReader.PUBLISH_ENCODING:
                self.encode_decode(message, decode=False)

            elif topic == RFIDReader.PUBLISH_DECODING:
                self.encode_decode(message, decode=True)

            elif topic == RFIDReader.PUBLISH_DIAGNOSTIC:
                self.diagnostic(message)

    def setup(self, config):
        message = {
            "cmd": "setup",
            "status": "error",
            "reason": "",
        }
        print("setup call!")
        # Create reader
        try:
            reader = feig.FeigReader(config["reader"])
        except feig.ReaderNotSupportedError:
            logger.error("Reader={} is not supported".format(config['reader']))
            message["reason"] = RFIDErrors.READER_NOT_SUPPORTED.name
            self.on_setup(self, message)
            return


        # Get interface configuration
        interface_settings = {}
        interface = config["interface"]
        if interface == "serial":
            logger.info("configured serial interface!...")
            interface = {
                "interface" : reader.INTERFACE_SERIAL,
                "settings": {
                    "PORT": config["port"],
                    "BAUDRATE": config["baudrate"],
                    "PARITY": config["parity"],
                }
            }

        elif interface == "ethernet":
            interface = {
                "interface" : reader.INTERFACE_ETHERNET,
                "settings": {
                    "IP": config["reader_ip"],
                    "PORT": config["reader_port"],
                }
            }

        else:
            logger.error("Reader Interface={} NOT supported".format(interface))
            message["reason"] = RFIDErrors.INVALID_INTERFACE.name
            self.on_setup(self, message)
            return

        # Start reader connection
        try:            
            print(interface["interface"], interface["settings"])
            ret = reader.connect(
                interface["interface"], interface["settings"]
            )
            logger.info("reader connect to interface!..")
        except Exception as err:
            logger.error("Connection to reader failed {}".format(err))
            message["reason"] = RFIDErrors.CONNECT_FAILED.name
            self.on_setup(self, message)
            return
        else:
            # Check why failed
            if ret is False:
                message["reason"] = reader.get_last_error_str()
                self.on_setup(self, message)
                return

        ######################################
        ## READER CONNECTED
        ######################################
        reader_id = config.get("reader_id", "")
        if reader_id != "":
            # match reader ID
            if reader_id.lower() != reader.device_id():
                logger.error("expected reader id={} got id={}".format(reader_id.lower(), reader.deviceID()))
                message["reason"] = RFIDErrors.INVALID_READER.name
                self.on_setup(self, message)
                return

        self.reader_id = reader.device_id()
        self.reader_info = reader.get_reader_info()

        self.MAX_ENCODE_RETRY = config["max_encode_retry"]
        if self.MAX_ENCODE_RETRY <= 0:
            self.MAX_ENCODE_RETRY = 1

        logger.info("antenna config in rfid setup!")
        # Apply antenna configuration
        for ant in config["antennas"]:
            ant_no = ant[0]
            # create default power
            ant_pwr = ant[1]
            self._ant_power[ant_no] = ant_pwr

            # create rssi filter
            ant_rssi = ant[2]
            if ant_rssi > 0:
                self._rssi_filter = True
                self._ant_rssi[ant_no] = ant_rssi

            self._encode_list[ant_no] = []
           # print("antenna config :"+str(ant))

        self._interface = interface
        self._config = config
        self._reader = reader

        message["status"] = "success"
        self.on_setup(self, message)
        print("call setup done!")
        reader.disconnect()
        logger.info("rfid setup done!")

    def setup_fastgate(self, config):
            # print("setup_fastgate config >",config)
            message = {
            "cmd": "setup",
            "status": "error",
            "reason": "",
        }
            global rfidId             
            global rfidName 

            try:
                reader = feig.FeigReader(config["reader"])                
            except feig.ReaderNotSupportedError:
                logger.error("Reader={} is not supported".format(config['reader']))
                message["reason"] = RFIDErrors.READER_NOT_SUPPORTED.name
                self.on_setup(self, message)
                return 

            self._reader = reader
            interface = config["interface"]
            self._interface = interface
            self._config = config
            
            interface = {
                "interface" : reader.INTERFACE_SERIAL,
                "settings": {
                    "PORT": config["port"],
                    "BAUDRATE": config["baudrate"],
                    "PARITY": config["parity"],
                }
            }

            # Start reader connection
            try:            
                # print(interface["interface"], interface["settings"])
                ret = reader.connect(
                    interface["interface"], interface["settings"]
                )
                logger.info("reader connect to interface!..")                
            except Exception as err:
                logger.error("Connection to reader failed {}".format(err))
                # print("Connection to reader failed {}".format(err))
                message["reason"] = RFIDErrors.CONNECT_FAILED.name
                self.on_setup(self, message)
                return
            else:
                # Check why failed
                if ret is False:
                    message["reason"] = reader.get_last_error_str()
                    # print("Connection to reader failed {}".format(message["reason"]))
                    self.on_setup(self, message)                   
                    return
           
            self.reader_id = reader.device_id()
            
            rfidId = self.reader_id
            rfidName = reader.READER_NAME           

            self.MAX_ENCODE_RETRY = config["max_encode_retry"]
            if self.MAX_ENCODE_RETRY <= 0:
                self.MAX_ENCODE_RETRY = 1

            # here set antenna power as per config file ant power
            for ant in config["antennas"]:
                ant_no = ant[0]
                # create default power
                ant_pwr = ant[1]
                self._ant_power[ant_no] = ant_pwr

                # create rssi filter
                ant_rssi = ant[2]
                if ant_rssi > 0:
                    self._rssi_filter = True
                    self._ant_rssi[ant_no] = ant_rssi

                self._encode_list[ant_no] = []
           
            self.default_antenna_power()
            
            self.serial_read = serial.Serial(config["port"], config["baudrate"],)
            message["status"] = "success"
            self.on_setup(self, message)
            print("call setup done!")
            reader.disconnect()
            logger.info("rfid setup done!")
    
    def default_antenna_power(self):
        # print(self._ant_power)
        for antno, antpwr in self._ant_power.items():
            try:
                self._reader.antenna_power(antno, antpwr)
                self._reader.rf_onoff(antno)
                # print(f"antenna power set {antpwr} for antenna no. {antno}")
            except ValueError as err:
                # print("antenna power set error >",str(err))
                logger.error("error={} while setting antenna={} power={}".format(
                    err,antno, antpwr
                ))
            else:
                if self._reader.get_last_error() != FeigError.OK:
                    logger.warning("failed={} to set antenna={} power={}".format(
                        self._reader.get_last_error_str(), antno, antpwr
                    ))


    def set_antenna_power(self,antNo, antPwr):
        """set feig antenna power to antPwr value for perticular antNo 
        example- antNo =1 , antPwr = 200 set antenna 1 power to 200 miliwatt
        before calling this function feig reader must be selected ex. LRU,MRU102 etc 

        Args:
            antNo (str): 1,2,3 etc
            antPwr (int):in miliwatts such as 100,200,300,400 etc
        """
        try:
            self._reader.antenna_power(antNo, antPwr)
        except ValueError as err:
            logger.error("error={} while setting antenna={} power={}".format(
                err,antNo, antPwr
            ))
        else:
            if self._reader.get_last_error() != FeigError.OK:
                logger.warning("failed={} to set antenna={} power={}".format(
                    self._reader.get_last_error_str(), antNo, antPwr
                ))

    def _lock_tag(self, epc, tid, password):
        lock_val = self._reader.HostMode.ACCESS_LOCK + self._reader.HostMode.EPC_LOCK
        ret = self._reader.HostMode.lock(epc, tid, lock_val, password)
        if ret is True and self._reader.get_last_error() == FeigError.OK:
            return True  # lock OK

        # lock failed
        logger.warning(
            "WRITE error={} while Locking={}".format(
                self._reader.get_last_error_str(), tid
            )
        )

        return False

    def _write_epc(self, epc, tid, password=None):
        ret = self._reader.HostMode.write_epc_memory("", tid, epc, password)
        if ret is True and self._reader.get_last_error() == FeigError.OK:
            return True  # write OK

        # Write failed
        logger.warning(
            "WRITE error={} while writing EPC={} to TID={}".format(
                self._reader.get_last_error_str(), epc, tid
            )
        )

        return False

    def _write_access_pwd(self, epc, tid, currpwd, newpwd):
        ret = self._reader.HostMode.write_access_password(epc, tid, currpwd, newpwd)
        if ret is True and self._reader.get_last_error() == FeigError.OK:
            return True  # write OK

        # Write failed
        logger.warning(
            "WRITE error={} while writing to TID={}".format(
                self._reader.get_last_error_str(), tid
            )
        )

        return False

    def _encoding_beta(self, tid, newepc, password):
        # TODO:
        # 1. Check default Access Password is set or not in RFID tag
        # 2. Set Access Password if already not in RFID tag
        # 3. Assign access password to EPC memory & set access password lock
        # 4. Encode RFID tags EPC write
        return False

    def _encoding_gamma1(self, tid, newepc, password):
        CURRENT_PASSWORD = password[0]

        # Write SGTIN with CURRENT_PASSWORD
        ret = self._write_epc(newepc, tid, CURRENT_PASSWORD)
        if ret is True:
            return True  # Write OK

        # Write SGTIN with DEFAULT_PASSWORD
        ret = self._write_epc(newepc, tid, self.DEFAULT_PASSWORD)
        if ret is True:
            # If written by DEFAULT password, then we have to
            # Update the access password and LOCK the EPC, ACCESS memory

            # update access password to CURRENT
            ret = self._write_access_pwd(
                newepc, tid, CURRENT_PASSWORD, self.DEFAULT_PASSWORD
            )
            if ret is False:
                return ret  # failed to update access password

            # LOCK memory
            ret = self._lock_tag(newepc, tid, CURRENT_PASSWORD)
            return ret

        # Try with remaining Passwords
        for idx in range(1, len(password)):
            if password[idx] != self.DEFAULT_PASSWORD:  # Skip Default password
                ret = self._write_epc(newepc, tid, password[idx])
                if ret is True:
                    # update access password to CURRENT
                    return self._write_access_pwd(
                        newepc, tid, password[idx], CURRENT_PASSWORD
                    )

        return False

    def _encoding_gamma(self, tid, newepc, password):
        ok_password = ""
        status = False

        CURRENT_PASSWORD = password[0]

        # Try to write epc using password
        for idx in range(0, len(password)):
            status = self._write_epc(newepc, tid, password[idx])
            if status is True:
                ok_password = password[idx]
                break

        # Check which password matched
        if ok_password == CURRENT_PASSWORD:
            # Write successfull, nothing to do
            pass

        elif ok_password == self.DEFAULT_PASSWORD:
            # Write successfull, update access password to CURRENT
            status = self._write_access_pwd(
                newepc, tid, CURRENT_PASSWORD, self.DEFAULT_PASSWORD
            )
            if status is True:
                # and LOCK memory
                status = self._lock_tag(newepc, tid, CURRENT_PASSWORD)

        elif ok_password in password:
            # Write successfull, update access password to CURRENT
            status = self._write_access_pwd(newepc, tid, ok_password, CURRENT_PASSWORD)

        else:
            # Write failed, try without password
            # TODO:
            self._write_epc(newepc, tid)
            logger.warning(
                "WRITE status={} with no password".format(
                    self._reader.get_last_error_str()
                )
            )

        return status

    def _write_multiple_sgtin(self, taglist, password, decode):
        failedtags = []
        oktags = []

        for tag in taglist:
            tid = tag[0]
            epc = tag[1]
            if decode: epc = "00"+epc[2:]
            writestatus = self._encoding_gamma1(tid, epc, password)
            if writestatus is True:
                # Write Successfull
                if decode: tag[1] = epc
                tag[3] = True
                oktags.append(tag)
            else:
                # Write Failed
                failedtags.append(tag)

        return oktags, failedtags

    def _clear_encode_list(self):
        for antno in self._encode_list.keys():
            self._encode_list[antno] = []

    def change_brm(self):
        status, mesg = False, ""

        # enter brm mode scan mode(0x80)
        ret = self._reader.change_mode(self._reader.MODE_SCAN)
        if ret != FeigError.OK and ret != FeigError.MODE_SAME:
            mesg = self._reader.get_last_error_str()
            return status, mesg

        # buffer init
        self._reader.ScanMode.init()
        if self._reader.get_last_error() != FeigError.OK:
            mesg = self._reader.get_last_error_str()
            return status, mesg

        # buffer clear
        self._reader.ScanMode.clear()
        if self._reader.get_last_error() != FeigError.OK:
            mesg = self._reader.get_last_error_str()
            return status, mesg

        # antenna enable
        self._reader.rf_onoff(self._reader.ANTENNA_No1)
        if self._reader.get_last_error() != FeigError.OK:
            mesg = self._reader.get_last_error_str()
            return status, mesg

        status, mesg = True, "ok"

        return status, mesg

    def change_host(self):
        status, mesg = False, ""
        self._reader.rf_onoff(self._reader.ANTENNA_OFF, maintainhost=True)
        if self._reader.get_last_error() != FeigError.OK:
            mesg = self._reader.get_last_error_str()
        else:
            status, mesg = True, "ok"

        return status, mesg

    def connect(self):
        """Connnect to reader"""
        status = False
        message = ""
        
        try:
            ret = self._reader.connect(
                self._interface["interface"], self._interface["settings"]
            )
        except Exception as err:
            logger.error("exception={} while connecting to reader".format(err))
            message = RFIDErrors.CONNECT_FAILED.name
        else:
            # Check why failed
            if ret is True:
                status = True
                message = ""
            else:
                message = self._reader.get_last_error_str()

        #logger.info("Connecting to reader={}".format(message))

        return status, message

    def disconnect(self):
        """Disconnect from reader"""
        status, mesg = True, "ok"

        if self._reader:
            self._reader.disconnect()

        return status, mesg

    def encode_decode(self, data, decode=False):
        cmd_output = {
            "cmd": "decode" if decode else "encode",
            "status": "error",
            "reason": "",
            "data": None,
        }
        on_callback = self.on_decoding if decode else self.on_encoding

        # Check and validate data
        try:
            taglist = data["sgtins"]
            password = data["password"]
        except KeyError:
            cmd_output["reason"] = RFIDErrors.INVALID_DATA.name
            on_callback(self, cmd_output)
            return

        if not taglist or not password:  # None of them should be empty
            cmd_output["reason"] = RFIDErrors.INVALID_DATA.name
            on_callback(self, cmd_output)
            return

        # seperate out tags wrt antenna number
        self._clear_encode_list()
        for tag in taglist:
            # Format: Tag(tupple) = (tid, epc, antno)
            # Convert this to LIST and append <write_status>, so it becomes
            # Tag = [tid, epc, antno, write_status]
            antno = tag[2]
            if antno in self._encode_list.keys():
                tag = list(tag)
                tag.append(False)  # write flag
                self._encode_list[antno].append(tag)

            else:
                logger.debug("ENCODE antenna={} NOT supported".format(tag))

        # connect to reader
        status, mesg = self.connect()
        if status is False:
            cmd_output["reason"] = mesg
            on_callback(self, cmd_output)
            return

        # enter in HOST mode
        status, mesg = self.change_host()
        if status is False:
            cmd_output["reason"] = mesg
            on_callback(self, cmd_output)
            return

        # change antenna power
        ant_pwr = 1500
        for antno in self._encode_list.keys():
            self._reader.antenna_power(antno, ant_pwr)

        sgtinOK = []
        retryCount = 0
        total_tags = len(taglist)

        cmd_output["status"] = "running"
        cmd_output["data"] = {"count": 0, "tagList": None}

        while retryCount < self.MAX_ENCODE_RETRY:
            retryCount = retryCount + 1
            logger.info("encoding started with retry={}".format(retryCount))
            for antno, sgtins in self._encode_list.items():
                self._reader.rf_onoff(antno, maintainhost=True)
                time.sleep(0.010)
                oktags, sgtins = self._write_multiple_sgtin(sgtins, password, decode)
                sgtinOK.extend(oktags)
                self._encode_list[antno] = sgtins  # updated
                # send encodeing count
                cmd_output["data"]["count"] = len(sgtinOK)
                on_callback(self, cmd_output)

            if total_tags == len(sgtinOK):
                break

            ant_pwr += 100 # increase power by 100mW
            # change antenna power
            for antno in self._encode_list.keys():
                self._reader.antenna_power(antno, ant_pwr)

        # check if all tags are written.
        # If not then retry those tag on all antenna
        failed_tags = []
        for sgtins in self._encode_list.values():
            if len(sgtins) > 0:
                failed_tags += list(sgtins)

        for anto in self._encode_list.keys():
            self._reader.rf_onoff(antno, maintainhost=True)
            time.sleep(0.010)
            oktags, failed_tags = self._write_multiple_sgtin(failed_tags, password, decode)
            sgtinOK.extend(oktags)
            # send encodeing count
            cmd_output["data"]["count"] = len(sgtinOK)
            on_callback(self, cmd_output)

        # SEND FINAL RESPONSE
        cmd_output["status"] = "success"
        cmd_output["data"]["count"] = len(sgtinOK)
        if len(sgtinOK) != total_tags:
            # copy failed tags
            sgtinOK += failed_tags

        cmd_output["data"]["tagList"] = sgtinOK
        self.on_encoding(self, cmd_output)

        # Turn OFF antenna.
        self._reader.rf_onoff(self._reader.ANTENNA_OFF)

    def check_hard_tag(self, epc, srno):
        if epc == self._config["oem_epc"]:
            return False

        if srno == "":  # Non encoded, default as HARD tag
            return True

        # Serial Number is of 12digits ex: 110000000001
        # For SoftTag, 1st and 2nd digit are '1'
        if srno[0] == "1" and srno[1] == "1":
            return False  # this is SOFT tag

        # rest decalare as HARD tag

        return

    @staticmethod
    def nearest_antenna_no(antennas)-> int:
        # minimum rssi is best
        nearest_antenna = min(antennas, key=lambda ant: ant['rssi'])
        return int(nearest_antenna["antno"])

    def apply_rssi_filter(self, taglist):
        # apply rssi
        for tag in taglist.values():
            for idx, ant in enumerate(tag["antennas"]):
                antno = ant["antno"]
                if antno in self._ant_rssi:
                    if self._ant_rssi[antno] <= ant["rssi"]:
                        tag["antennas"].pop(idx)

        # remove empty antenna
        tags = {}
        for tid,tag in taglist.items():
            if tag["antennas"] != []:
                tags[tid] = tag

        return tags

    def update_tags_list(self, currentlist, newlist):
        new_tag_count = 0
        new_tags = {}

        for tid, tag in newlist.items():
            try:
                # Update respective parameters
                currentlist[tid]["last_seen"] = tag["last_seen"]
                currentlist[tid]["seen_count"] += tag["seen_count"]

                currentlist[tid]["antennas"] = self._reader.BufferReadMode._update_antennas(
                    currentlist[tid]["antennas"], tag["antennas"]
                )

            except KeyError:
                # New Tag, add it
                new_tag_count += 1
                new_tags[tid] = tag  # add only new tag

                # update current tag list
                currentlist[tid] = tag

                # get EAN,SerialNumber
                try:
                    ean, srno = gs1.sgtin96_to_ean(currentlist[tid]["epc"])
                except gs1.SGTINDecodeError:
                    # Make it NON-ENCODED
                    ean, srno = "NON-ENCODED", ""

                currentlist[tid]["nearestAnt"] = self.nearest_antenna_no(currentlist[tid]["antennas"])
                currentlist[tid]["ean"] = ean
                currentlist[tid]["serialNo"] = srno

                # Get Tagtype
                currentlist[tid]["hard_tag"] = self.check_hard_tag(
                    currentlist[tid]["epc"], srno
                )

        return new_tag_count, new_tags

    def update_ean_list(self, taglist, eanlist):
        for tid in taglist:
            ean = taglist[tid]["ean"]
            try:
                eanlist[ean] += 1
            except KeyError:
                eanlist[ean] = 1

    def scan_count(self, data):
        message = {
            "cmd": "scancount",
            "status": "error",
            "reason": "",
            "eanList": None,
            "tagList": None,
        }

        # connect to reader
        status, mesg = self.connect()
        if status is False:
            message["reason"] = mesg
            self.on_fastgate(self, message)
            return

        # Set RF Power
        self.default_antenna_power()

        # Enter BRM Mode
        status, mesg = self.change_brm()
        if status is False:
            logger.error("error={} while seting BRM".format(mesg))
            message["reason"] = mesg
            self.on_fastgate(self, message)
            return

        uniqueEanList = {}
        uniqueTags = {}

        noTagTime = time.time()
        noTagTimeLimit = 1.0

        comm_timeout = 0

        while True:

            # read buffer
            tags = self._reader.BufferReadMode.read()
            if tags is None:
                if self._reader.get_last_error() == FeigError.INVALID_RESPONSE:
                    # try next
                    continue

                else:
                    # error occured
                    err_mesg = self._reader.get_last_error_str()
                    logger.debug("error buffer read={}".format(err_mesg))
                    message["reason"] = err_mesg
                    self.on_scancount(self, message)
                    return

            if len(tags) > 0:
                # clear buffer
                self._reader.BufferReadMode.clear()
                if self._reader.get_last_error() != FeigError.OK:
                    err_msg = self._reader.get_last_error_str()
                    logger.debug("buffer clear Failed. {}".format(err_msg))

                # make unique lists
                tags = self._reader.BufferReadMode._unique_tags(tags)
                logger.debug("tags = {}".format(tags))

                if self._rssi_filter:
                    tags = self.apply_rssi_filter(tags)
                    logger.debug("filtered tags = {}".format(tags))

                # update current tag list and return NEW tags if found
                new_tag_count, new_tags = self.update_tags_list(uniqueTags, tags)
                if new_tag_count > 0:
                    logger.info("NEW tags found={}".format(new_tag_count))
                    self.update_ean_list(new_tags, uniqueEanList)

                    # tag in field, reset
                    noTagTime = time.time()

                    # SEND ITERMEDIATE RESPONSE
                    message["status"] = "running"
                    message["eanList"] = uniqueEanList.copy()

                    self.on_fastgate(self, message)

            if noTagTime and (time.time() - noTagTime) >= noTagTimeLimit:
                logger.info("SCANCOUNT noNewTagCounter expired.")
                break

        # SEND FINAL RESPONSE
        message["status"] = "success"
        message["eanList"] = uniqueEanList.copy()
        message["tagList"] = uniqueTags.copy()
        self.on_fastgate(self, message)

        logger.debug("Scanned tags={}".format(uniqueTags))

        self.change_host()

        # disconnect from reader
        status, mesg = self.disconnect()

    def diagnostic(self,data):
        cmd_response = {
            "cmd": "diagnostic",
            "status": "error",
            "reason": "",
            "data": None,
        }
                 
        # connect to reader
        status, mesg = self.connect()
        if status is False:
            cmd_response["reason"] = mesg
            print(cmd_response)
            self.on_diagnostic(self, cmd_response)
            return

        ret = self._reader.diagnostic()
        if self._reader.get_last_error() != FeigError.OK:
            cmd_response["reason"] = self._reader.get_last_error_str()
            print(cmd_response)
            self.on_diagnostic(self, cmd_response)
            return

        cmd_response["status"] = "success"
        cmd_response["data"] = ret
        print(cmd_response)
        self.on_diagnostic(self, cmd_response)

        # disconnect from reader
        status, mesg = self.disconnect()

    def fastgate_rfid_info(self):

        ret = {}
        # print("rfidName >",rfidName)
        # print("rfidId",rfidId)
        try:
            ret = {'rfidname': rfidName,'rfidID': rfidId}
        except Exception as e:
            print("rfid not connected >",str(e))

        return ret        

    
    def fastgate_scan(self, data):
        message = {
            "cmd": "fastgate",
            "status": "error",
            "reason": "",
            "eanList": None,
            "tagList": None,
        }
        print("starting scanning ..rfid!")
        self.serial_read.flushInput()
        EPC_OFFSET = 4
        EPC_LEN = 12 # in bytes
        EPC_ASCII_LEN = EPC_LEN*2
        EPC_START = EPC_OFFSET
        EPC_END = EPC_START + EPC_ASCII_LEN
        
        TID_LEN = 12 # in bytes
        TID_ASCII_LEN = TID_LEN*2
        TID_START = EPC_END
        TID_END = TID_START + TID_ASCII_LEN

        ANT_LEN = 12 # in bytes
        ANT_ASCII_LEN = TID_LEN*2
        ANT_START = TID_END + 1
        ANT_END = ANT_START + ANT_ASCII_LEN

        print("Starting reception....")

        main.gpio1.booting_blink_stop()  
              
        main.gpio1.buzzer_startup_blink()
        main.gpio1.prog_run_blink()       

        #print("list of epcs :" +str(epc_list))

        while True:
            d = self.serial_read.readline()
            # print('\nRAW= ', d, len(d))
            # print((d[0:len(d)-1]).decode("ascii").encode("utf16"))

            if len(d) == 57:
                # extract EPC, TID
                EPC = d[EPC_START : EPC_END].decode('ascii')
                TID = d[TID_START : TID_END].decode('ascii')
                ANT = (d[ANT_START : ANT_END].decode('ascii')).replace("\r\n","")
                # print("EPC > ",EPC)
                # print("TID > ",TID)
                # print("Ant no. > ",ANT)
                # print(EPC, TID, ANT)
                message["taglist"] = {"EPC":EPC, "TID":TID,"ANT":ANT}
                message["status"] = "running"
                self.on_fastgate(self, message)

    
   
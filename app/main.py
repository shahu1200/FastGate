#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import date, datetime
import logging
import logging.handlers as handlers
from traceback import print_tb
from urllib import request
import requests
import queue
import threading
import time
from functools import partial
from flask import Flask
import faulthandler
import os

from .itek_rtc import itekRTC, I2CBusNotFoundError, RTCNotFoundError
from .utils import get_mac, get_datetime_stamp, is_internet, read_local_config,get_ipv4
from .system_status import get_system_status
from .version import APP_VERSION, APP_BUILD
from .gpio import GpioProcess
from .rfid import RFIDReader
from .settings import CONFIG_TOML_FILE, PATH_FILE_LOG
#from .api import API
from .data_conversion import pars, unpars
from .mqtt.proto_mqtt import MQTTProto as MQTT
from .validation import Validator
from .web.weber import webpage

from .gpio.HandleGpio import HandleGPIO


faulthandler.enable()
#####################################################################
# Setup logger
PATH_FILE_LOG1 = PATH_FILE_LOG + "logs/"
TR_ACC = 1
TR_BLK = 2
TR_NDB = 3
RFID_DISCONNECT = 1

TR_ACC1 = "Authorized"
TR_BLK1 = "Blocked"
TR_NDB1 = "Unauthorized"



formatter = logging.Formatter(
    "%(asctime)s::%(levelname)s::%(filename)s::%(lineno)d %(message)s"
)
logger = logging.getLogger("app")
logger.setLevel(logging.DEBUG)

# time logger
handler = handlers.TimedRotatingFileHandler(
    PATH_FILE_LOG1 + "app/app.log",
    when="midnight",
    backupCount=10,
    interval=1,
)
handler.setFormatter(formatter)
logger.addHandler(handler)
#handler.doRollover()

# tags logger
PATH_FILE_LOG1 = PATH_FILE_LOG +  "logs/"
formatter = logging.Formatter(
    "%(asctime)s :: %(message)s"
)
tag_logger = logging.getLogger("tags")
tag_logger.setLevel(logging.DEBUG)

handler = handlers.TimedRotatingFileHandler(
    PATH_FILE_LOG1 + "tags/tags.log",
    when="midnight",
    backupCount=30,
    interval=1,
)
handler.setFormatter(formatter)
tag_logger.addHandler(handler)

# try:                        
#     shPointer = os.popen('sh '+PATH_FILE_LOG+'make_package.sh')
#     print(shPointer)
#     from .version import APP_VERSION, APP_BUILD
# except Exception as e:
#     print("shpointer exception >",str(e))


global rfid_not_connected
# Get local configuration
localConfig = read_local_config(CONFIG_TOML_FILE)
gpio1 = GpioProcess(localConfig["gpio"])

# gpio1.booting_blink_start()
gpio1.booting_blink_start()
locahost = localConfig["static_ipv4"]

# ipv4 = get_ipv4(interface="br0")
print("device ipv4 > ",locahost)
# print(ipv4)

API_URL = 'http://' + locahost + ':8080/api/'

# print(API_URL)

# get raspberry pi mac id for comparison
macId = get_mac(interface="eth0")
print("device mac id > ",macId)

# if mac id in sd card(config.toml) project is not equal to currernt raspberry pi mac id then system will not boot
if localConfig is None or macId != localConfig["deviceid"]:
    logger.fatal("ERROR while reading config file or mac id doesnt matches")
    logger.fatal("Exiting application.")
    print("Reading config file Failed")    
    gpio1.prog_run_blink_stop()
    gpio1.booting_blink_stop() 
    # blink buzzer for 3 seconds to know mac id mismatched
    
    gpio1.buzzer_blink()
    time.sleep(3)
    gpio1.buzzer_blink_stop() 
    
    # print("buzzer stop")  
    exit(0)
else:
    print("Reading config file ... OK")
    logger.info("Local config read ... OK")

time.sleep(5)

WebApp = Flask(__name__)
appWrap=webpage(WebApp)
apps=appWrap.app   
apps.secret_key = 'iTEK_AVI_secret_key'
apps.env = 'development'

@apps.route('/', defaults={'route': 'login'})
@apps.route('/<route>',methods=["POST","GET"])
def routes_checks(route):
    return appWrap.allwebpath(route)

@apps.route('/api/<route>',methods=["POST","GET"])
def api_routes(route):
    # print("API route > ",route)
    return appWrap.handle_api(route)
# this function is called first, which will set rfid reader as per fastgate rquirment 
 
def on_setup(app, reader, message):
    # print("on_setup message >",message)
    if message["status"] == "success":
        # start fastgate scanning
        rfid_not_connected = 0
        reader.publish(reader.PUBLISH_FASTGATE, message="")
    elif message["status"] == "error":
        print("RFID reader connection error >",message["reason"])
        rfid_not_connected = RFID_DISCONNECT
        # set one flag here, check that flag in main
        # if that flag is set on error led and stop reading tags

    logger.debug("rfid setup message : " + str(message))
    # if app:
    #     app.insert_que(data=message)        

def on_fastgate(app, reader, message):
    if message:
        logger.debug("insert que data : "+str(message))
    if app: 
        app.insert_que(data=message)

def process_rfid(reader, mesg):
    cmd = mesg.get("cmd")
    if cmd == "fastgate":
        logger.debug("process rfid " + str(cmd))
        reader.publish(reader.PUBLISH_SETUP, localConfig["rfid"])

def msg_listener(app):
    """call on_setup and on_fastgate functions in this same file
    
    object app is passed to this function which is Application(localConfig) in this same file
    """
    
    
    reader = RFIDReader(localConfig["loglevel"])
    # on_setup function is called which is defined above
    reader.on_setup = partial(on_setup, app)
    # on_fastgate function is called which is defined above
    reader.on_fastgate = partial(on_fastgate, app)
   
    threading.Thread(
        target=reader.run,
        name="reader",
        daemon=True,
    ).start()

    logger.debug("started message listner!....")
    
    while True:
        """ mesg = {
                "topic": "",
                "cmd": "",
                ...
            }
        """      
    #    function listen_message in this same is called in which message is taken out from queue 
        mesg = app.listen_message()
        topic = mesg.get("topic")
        print("message listner msg > ",mesg)
       
        #logger.debug("messege listner msg : " + str(mesg))

        ## RFID Functions
        if topic == "rfid":
            process_rfid(reader, mesg)

        if topic == "mqtt":
            process_mqtt(mesg)

def process_mqtt(mesg):
    """all device configuration using mqtt subscribe msg
    {topic, type, data{action, data}}
    """
    # print("process mqtt > "+str(mesg))
    if 'action' in mesg['data']:
        action = mesg['data']['action']
       
        url = API_URL + str(action)
        # here action is userConfig, which is a function in weber.py -> def userConfig(self)
        # so url will call api which is http://192.168.1.203:8080/api/userConfig
        logger.info("call url : "+str(url))
        # print("main proccess_mqtt for > ",mesg['data']['data'])
        resp = requests.post(url, json=mesg['data']['data'], timeout=3.0)
        # from here it will jump to weber.py to -> def userConfig(self)
        logger.info("response : {}".format(str(resp)))

class Application:

    def __init__(self, settings):
        # print("main.py class Application init")
        self.__settings = settings
        self._app_settings = settings["app"]
        self._gpio_settings = settings["gpio"]
        self._api_settings = settings["api"]
        self._mqtt_settings = settings["mqtt"]
        self._db_settings = settings["database"]
        self._controller_settings = settings["controller"]
        self._rfid_settings = settings["rfid"]
        self._standalone_system = int(settings["standalone_system"])
        self._boom_on_time = self._gpio_settings["boom_on_time"]
        self._all_boom_on_time = self._gpio_settings["boom_config"]["booms"]        
       
        self.max_trans_count = self._db_settings["max_trans_count"]

        self.service_activation_flag = self._app_settings["service_activation_flag"]
        
        self.gpio = GpioProcess(self._gpio_settings)

        self.rtc = itekRTC()
       
        self.tag_form = settings["tag_form"]
        self.antennas = self._rfid_settings["antennas_name"]

        self.last_invalidtag_scan = None 

        if "deviceid" in settings:
            self._device_id = settings["deviceid"]
        else:
            self._device_id = get_mac()

        # check_internet is false then api/mqtt not execute 
        self.check_internet = False
        self.check_internet = is_internet()
        self.mqtt = None

        #standalone_system is 0 means system is in online mode
        # in online mode, system is configured online using mqtt
        if self._standalone_system is 0:  
            if self.check_internet:
                self.hertbeat_data = pars.device_setup(settings)
                subtopic = []
                for sub in self._mqtt_settings["channel"]["sub"]:
                    subtopic.append((sub.replace("<DeviceId>",self._device_id), 1))
                # from proto_mqtt.py class MQTTProto is impoerted as MQTT above in this file
                # this MQTT now object as self.mqtt so after this self.mqtt.something means it is refering to proto_mqtt.py file things 
                self.mqtt = MQTT(self._mqtt_settings)
                self.mqtt.connection(sub_topic=subtopic)
                #self.mqtt.subscribe(self._mqtt_settings["channel"]["HB_pub"])
                self.mqtt.start_loop()
                self.mqtt.heartbeat(self.hertbeat_data)
                self.mqtt.dump_que = self.dump_que                
        # else system is in offline mode where everything is done localy without server
        # create que named _queue 
        self._queue = queue.Queue()
        self.scanning_data_que = []
        self.fastgate_data = []

        self.total_transaction = 0
        self.pending_transaction = 0
        self._pre_hb_time = time.time()
            
        # heartbeat thread is started
        hb_thread = threading.Thread(target=self._periodic_thread,daemon=True)
        hb_thread.start()

        self.dataq = queue.Queue()

        self._controller_config = threading.Event()
        self._controller_config.clear()

        self._is_rtc_updated = threading.Event()

        self.right_mark = u'\u2714'
        self.wrong_mark = u'\u2718'
        self.skull_mark = u'\u2620'
        self.block_mark = u'\u1f6a7'
        self.smily_mark = u'\u1f600'
        self.antennas_status = []
        self.last_trigger_red = time.time()

# listen message is to get message out of the queue and proccess it
    def listen_message(self, block=True, timeout=None):
        """ listen message queue
        mesg = {
            "topic": "",
            "cmd": "",
            "type":"",
        }
        """
        try:
            
            return self._queue.get(block=block, timeout=timeout)
        except queue.Empty:
            return {}
    
    # put data in queue here it for rfid tag data 
    def insert_que(self, data, todays_tasks=None):
        """ data que append from rfid scan function
        """
        #print(data)
        if data and len(data) > 0:
            self.fastgate_data.append(data)
            logger.debug("insert data : " + str(data))
            if data["taglist"]!= None and len(data["taglist"]) > 0:
                self.scanning_data_que.append(data["taglist"])

    # put data in queue
    def dump_que(self, mesg):
        """mesg = {
            "topic": "rfid",
            "cmd": "fastgate",
            "type":"None",
            "data": ""
        }"""
        self._queue.put(mesg)        
        logger.debug("send start scanning : "+str(mesg))

# put message in queue with given mesg dictionary 
    def start_scanning(self):
        self.scanning_data_que = []
        mesg = {
            "topic": "rfid",
            "cmd": "fastgate",
            "type":"None",
            "data": ""
        }
        self._queue.put(mesg)
        logger.debug("send start scanning : "+str(mesg))

# when length of scanning_data_que is greater than zero then tag is scanned 
# get that data out of queue and give for validation
    def read_tags(self):
        if len(self.scanning_data_que) > 0:
                # when data available on queue
            return self.scanning_data_que.pop(0)
        return None

    # def _append_internet_server_error(self, count):
    #     magic = 0

    #     if self.api.is_server() is False:
    #         magic = 900000

    #     if self.check_internet is True:
    #         if self.api.is_internet() is False:
    #             magic = 800000

    #     return count + magic

# send heartbeat to server after perticular time
# heartbeat contains device data
    def heartbeat(self):
        # check internet:
        self.check_internet = is_internet()
        if self.check_internet is True and self._standalone_system is 0:
            if self.mqtt == None:
                self.hertbeat_data = pars.device_setup(self.__settings)
                subtopic = []
                for sub in self._mqtt_settings["channel"]["sub"]:
                    subtopic.append((sub.replace("<DeviceId>",self._device_id), 1))
                self.mqtt = MQTT(self._mqtt_settings)
                self.mqtt.connection(sub_topic=subtopic)
                #self.mqtt.subscribe(self._mqtt_settings["channel"]["HB_pub"])
                self.mqtt.start_loop()
                self.mqtt.dump_que = self.dump_que
            self.hertbeat_data1 = pars.heartbeat_data(self._device_id)
            self.mqtt.heartbeat(self.hertbeat_data1)

# called at the begining in same file above, for heartbeat data sending
    def _periodic_thread(self):
        logger.info("periodic thread started!") 
        while True:
            try:       
                heartbeat_time = time.time()
                if self._app_settings["heartbeat_time"] != 0:
                    if heartbeat_time - self._pre_hb_time >= self._app_settings["heartbeat_time"]:
                        self.heartbeat()
                        self._pre_hb_time = time.time()
            except Exception as e:
                logger.error("error in periodic thread!, {}".format(e))    

# not called anywhere
    def _config_thread(self):
        logger.info("config thread started")

        # wait sometime before config
        wait_time = self.controllerConfig.get("get_config_wait_time")
        if wait_time is not None:
            time.sleep(float(wait_time))

        logger.info("wait time finished")

        # controller
        use_local_config = self.controllerConfig["use_local_config"]

        hw_config_state = 0
        max_config_retry = 0
        config_retry_time = 0

        work_done = False

        while not self.appHB.is_set() and work_done is False:
            if use_local_config == CONFIG_FROM_FILE:
                if hw_config_state == 0:
                    # apply local config
                    self.dataq.put(
                        ("config", CONFIG_FROM_FILE, self.controllerConfig["config"])
                    )
                    logger.info("applying local config")
                    time.sleep(1.0)
                    work_done = True

            elif use_local_config == CONFIG_FROM_SERVER:
                if hw_config_state == 0:  # get config from server
                    config_retry_time += 1
                    if config_retry_time >= self.controllerConfig["config_retry_time"]:
                        config_retry_time = 0
                        max_config_retry += 1
                        if (
                            max_config_retry
                            >= self.controllerConfig["max_config_retry"]
                        ):
                            # maximum retry done
                            logger.info("getting config from server failed, reached MAX_RETRY=%d", max_config_retry)
                            print("Get config from server Failed, reached MAX_RETRY=", max_config_retry)
                            work_done = True

                        else:
                            # get from server
                            status, data = self.api.get_config(
                                {"mac": self.mac_address}
                            )
                            if status is True:
                                self.dataq.put(("config", CONFIG_FROM_SERVER, data))
                                logger.info("applying server config")
                                print("Get config from server Ok. Applying server config")
                                hw_config_state = 2

                elif hw_config_state == 2:
                    # check config is applied
                    if self._controller_config.is_set():
                        # send response to server
                        status, data = self.api.send_config_update(
                            {"mac": self.mac_address, "time": get_datetime_stamp()}
                        )

                        if status is True:
                            # config process completed
                            self._controller_config.clear()
                            logger.info("controller config update completed")
                            print("Sending config response to server...Ok")
                            work_done = True

                        else:
                            print("Sending config response to server...Failed, ", data)

                    else:
                        # wait till 10seconds for response from controller
                        config_retry_time += 1
                        if config_retry_time >= 10:
                            # reset complete cycle
                            hw_config_state = 0
                            config_retry_time = 0

        logger.info("config thread finished")

    def _get_data_from_queue(self):
        try:
            data = self.dataq.get(block=True, timeout=0.01)
        except queue.Empty:
            data = None

        return data

    def antenna_close_status(self, antenna_on_no):
        if antenna_on_no in self.antennas_status:
            self.antennas_status.remove(antenna_on_no)

    def run(self):
        # Connect to RTC
        # store device id in log file
        logger.debug("Device ID : "+str(self._device_id))

        print("system date time is > ",datetime.now())
        
        try:
            # connect to rtc on seperate relay board
            self.rtc.connect()
        except I2CBusNotFoundError:
            logger.warning("I2C bus not found")
            print("!!! I2C bus not found. Check if I2C enabled.")
        except RTCNotFoundError:
            logger.warning("RTC module not found")
            print("!!! RTC module not found.")
        else:
            # load datetime from rtc to system
            rtc_dt = self.rtc.rtc_get_datetime()

            print("current rtc date time is ",rtc_dt)
            
            if rtc_dt != '':
                self.check_internet = is_internet()
                # print("internet is ",self.check_internet)
                
                if self.check_internet:
                    self.rtc.rtc_setDateFromServer()
                    self.rtc.rtc_setTimeFromServer()
                    logger.info("RTC get datetime= %s", rtc_dt)
                    print("RTC updated datetime =", rtc_dt)
                # self.rtc.update_syst3zem_datetime(rtc_dt)
            else:
                logger.info("RTC get datetime failed")
                print("RTC get datetime Failed.")

        # start scanning rfid tag
        last_ant_time = [0,0,0,0]
        self.start_scanning()
        print("!!! Start Scanning....")
        logger.debug(">>> Start scanning !.....")
        # object is valid_tag and class validator(validation.py) is asgined to it
        valid_tag = Validator()
        # if rfid reader is not detected on red led, dont enter while loop
        # if rfid_not_detected != RFID_DISCONNECT:
        # self.gpio.prog_run_blink()
        
        while True:
            # while 1, check if tag is present or not
            # this function checks the queue scanning_data_que
            # and if something is there it will return tag data
            
            tag_data = self.read_tags()
            #print(tag_data)
            # if tag is present go in this loop
            # check service_activation_flag here if it is not 1, dont do anything
            if self.service_activation_flag == 1:
                # self.gpio.service_active_relays_off()
                if tag_data:
                    # print(tag_data)
                    # row_frame = appWrap.vehicle_access(tag_data[self.tag_form])
                    ant_name = self.antennas[int(tag_data["ANT"])-1]
                    # local verification of tag done via api to avoid blocking of data
                    # make url with api and vehicle_access to understand which api task is to be performed               
                    url = API_URL + "vehicle_access"
                    
                    # make log in logs/app/app.log file
                    logger.info("call url : "+str(url))
                    # tag_data = {"EPC": ,"TID": , "ANT":}
                    # requests.posts return <[status_code] 200> or <[status_code] 201> 200 means tag present in reader memory database, 201 means tag is not present in reader memory database  
                    # url is URL + vehicle_access vehicle_access is a function in weber.py it is called and tag is searched in reader from that function
                    # and tag information of that tag is taken from database is saved in row_frame tag id, access date, time , block date,time 
                    row_frame = requests.post(url, data=str(tag_data[self.tag_form]))
                    # make log in logs/app/app.log file, logger.(something) will make log in logs/app/app.log
                    logger.info("resp url : "+str(row_frame.status_code))
                
                    if row_frame.status_code == 200: 
                        data_frame = row_frame.json()
                        
                        # print(data_frame)
                        # data_frame from database comes like below
                        # {'data': [3, '00361F46981138174876EE46', 'None', '30-03-2022 11:44:44', 'None',                     
                        # 'None', '01-04-2022 00:00:00', '01-04-2022 00:00:00', '10:12:00', '17:12:00', 'A                   
                        #  ', '01-09-2023 00:00:00', '30-11-2023 00:00:00', '16:02:00', '20:04:00', '7-6,', 1]}

                        # call run function in validator class(validation.py) to check tag for date,time and day access
                        status = valid_tag.run(data_frame["data"])
                        print(status)
                        # if valid tag comes go in this if
                        if status:
                            print("Access Granted!")

                            # here check for has tag came from same antenna if from same antenna dont give access
                            # ant_name = self.antennas[int(tag_data["ANT"])-1]
                            last_ant_time_now = time.time()
                            # print("time.time function ",time.time())
                            # print("datetime.now function ",datetime.now())
                            # print("last ant time now ")
                            # print(last_ant_time_now)
                            # check if same tag is detected on same antenna within access time
                            if(last_ant_time_now - last_ant_time[int(tag_data["ANT"])-1]  > self._all_boom_on_time[int(tag_data["ANT"])-1][1]):
                            # last_ant_name = ant_name
                                last_ant_time[int(tag_data["ANT"])-1] = last_ant_time_now
                                # make log in logs/tags/tags.log, tag_logger.(something) will make log in logs/tags/tags.lo
                                tag_logger.info("{} {} Access granted".format(self.right_mark, tag_data[self.tag_form]))
                                
                                # save the log of this tag in reader memory
                                
                                # url = API_URL + "save_transaction"
                                url = API_URL + "save_transaction_withLimit"
                                logger.info("call url : "+str(url))
                                # request.post will save transaction in reader memory database 
                                # row_frame = requests.post(url, json={"tagid":tag_data[self.tag_form], "ANT":ant_name, "tr_flag":TR_ACC}) #"status":TR_ACC
                                row_frame = requests.post(url, json={"tagid":tag_data[self.tag_form], "ANT":ant_name, "tr_flag":TR_ACC1, "limit":self.max_trans_count}) #"status":TR_ACC
                                logger.info("resp url : "+str(row_frame))

                                # open the corsponding boom barrier
                                self.gpio.boom_open(int(tag_data["ANT"])) #this function will open the boom for ton time and maked it off after that
                                self.gpio.green_led_on(int(tag_data["ANT"])) #this function will turn on green led for on time and turns it off after that
                                # self.antennas_status.append(int(tag_data["ANT"]))

                                # send data to server using mqtt 
                                if self.mqtt:
                                    transaction_data = pars.vehicle_access(
                                        data_pack={"tagId":tag_data[self.tag_form],
                                        "vehicleTime":get_datetime_stamp("%Y-%m-%d %H:%M:%S"),
                                        "gate":ant_name,
                                        "tFlag":TR_ACC1},
                                        deviceid = self._device_id
                                        )
                                    self.mqtt.publish(
                                        pub_topic=self._mqtt_settings["channel"]["vehicle_transaction"],
                                        pub_payload=transaction_data,
                                        qos=1
                                        )
                                logger.info("all antenna status list {} in thread : ".format(self.antennas_status))
                                                    
                        else:
                            # if it is an invalid tag, dont give access, dont make transaction in eader memory, dont send any data to server,
                            # just on error light  
                            print("Access denied")
                            now_red_trigger1 = time.time()
                            if self.last_invalidtag_scan != tag_data[self.tag_form] or (self.last_trigger_red - now_red_trigger1 ) > 3:
                                self.last_trigger_red = now_red_trigger1

                                # url = API_URL + "save_transaction"
                                url = API_URL + "save_transaction_withLimit"
                                logger.info("call url : "+str(url))
                                # request.post will save transaction in reader memory database 
                                # row_frame = requests.post(url, json={"tagid":tag_data[self.tag_form], "ANT":ant_name, "tr_flag":TR_BLK})
                                row_frame = requests.post(url, json={"tagid":tag_data[self.tag_form], "ANT":ant_name, "tr_flag":TR_BLK1, "limit":self.max_trans_count})
                                logger.info("resp url : "+str(row_frame))
                                
                                if self.mqtt:
                                    transaction_data = pars.vehicle_access(
                                        data_pack={"tagId":tag_data[self.tag_form],
                                        "vehicleTime":get_datetime_stamp("%Y-%m-%d %H:%M:%S"),
                                        "gate":ant_name,
                                        "tFlag":TR_BLK1},
                                        deviceid = self._device_id
                                        )
                                    self.mqtt.publish(
                                        pub_topic=self._mqtt_settings["channel"]["vehicle_transaction"],
                                        pub_payload=transaction_data,
                                        qos=1
                                        )

                                tag_logger.info("{} {} available in DB but access denied".format(self.wrong_mark, tag_data[self.tag_form]))
                                self.last_invalidtag_scan = tag_data[self.tag_form]
                                self.gpio.red_led_thread(int(tag_data["ANT"]))
                    
                    else:
                        print("vehicle not in database")
                        now_red_trigger = time.time()
                        #print(now_red_trigger - self.last_trigger_red)
                        if self.last_invalidtag_scan != tag_data[self.tag_form] or (self.last_trigger_red - now_red_trigger ) > 3:
                            self.last_trigger_red = now_red_trigger

                            # url = API_URL + "save_transaction"
                            url = API_URL + "save_transaction_withLimit"
                            logger.info("call url : "+str(url))
                            # request.post will save transaction in reader memory database 
                            # row_frame = requests.post(url, json={"tagid":tag_data[self.tag_form], "ANT":ant_name, "tr_flag":TR_NDB})
                            row_frame = requests.post(url, json={"tagid":tag_data[self.tag_form], "ANT":ant_name, "tr_flag":TR_NDB1, "limit":self.max_trans_count})
                            logger.info("resp url : "+str(row_frame))

                            if self.mqtt:
                                    transaction_data = pars.vehicle_access(
                                        data_pack={"tagId":tag_data[self.tag_form],
                                        "vehicleTime":get_datetime_stamp("%Y-%m-%d %H:%M:%S"),
                                        "gate":ant_name,
                                        "tFlag":TR_NDB1},
                                        deviceid = self._device_id
                                        )
                                    self.mqtt.publish(
                                        pub_topic=self._mqtt_settings["channel"]["vehicle_transaction"],
                                        pub_payload=transaction_data,
                                        qos=1
                                        )

                            tag_logger.info("{} {} tag not available in DB".format(self.skull_mark, tag_data[self.tag_form]))
                            self.last_invalidtag_scan = tag_data[self.tag_form]
                            self.gpio.red_led_thread(int(tag_data["ANT"]))
                
            else:
                self.gpio.service_active_relays_on()

        # else:
        # turn on red led  
    
    def close(self):
        logger.fatal("app Exited!")

    def config_dump(self, data):
        print("pushing data "+str(data))

def main():
    logger.info("Application VERSION= %s %s", APP_VERSION, APP_BUILD)
    print("Application VERSION=", APP_VERSION, ", Build=", APP_BUILD)
    #print(localConfig["gpio"])
    # class Application in same main.py is objected as app
    # where ever you see app.something it means that is in class Application of this file
    app = Application(localConfig)


    # Start application
    # make and start thread to listen the messages from rfid and mqtt
    # main program starts here after this one by one is processed
    # from here execution goes to msg_listener
    threading.Thread(
        target=msg_listener,
        args=(app,),
        daemon=True,
    ).start()
    
    # initialize web application requirments 
    appWrap.initialising(localConfig)
    # start web application or webpage used to change reader settings this will run in background and looks for webpage login and changes
    appWrap.run()

    try:
        # check for tag and validate it this function is in same file above
        
        app.run()
    except Exception as e:
        gpio1.prog_run_blink_stop()
        gpio1.booting_blink_stop()
        logger.exception("Error while running application " +str(e))
    finally:
        gpio1.prog_run_blink_stop()
        app.close()

if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("MAIN exited due to error")


"""
data = hashlib.sha256("E4:5F:01:62:20:16".encode('utf-8'))
data.hexdigest()
'f6623ba8c0d455291b93a589e4932cf531a65feb24110567698a603285114982'
"""


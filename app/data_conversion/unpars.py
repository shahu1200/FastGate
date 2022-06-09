import json
import logging
import re

logger = logging.getLogger(__name__)

def avil_check(data, key):
    if key in data.keys():
        return data[key]
    else:
        return None

def config_data(data_pack):
    try:
        return data_pack
    except Exception as e:
        logger.warning(str(e))

def antConfig(config_frame, data_pack):
    """
    data_pack : 
    [
        {"antNo":1,"power":0.5,"title":"IN", "gpioNo":1},
        {"antNo":2,"power":0.5,"title":"IN", "gpioNo":1}
    ]
    ANTENNA_POWER = 1
    """
    try:
        ANTENNA_POWER = 1
        for _frame in data_pack:
            ant_no = int(_frame["antNo"])-1
            config_frame["rfid"]["antennas"][ant_no][ANTENNA_POWER] = int(_frame["power"])
            config_frame["rfid"]["antennas_name"][ant_no] = _frame["title"]
            config_frame["gpio"]["out_pin"]["boom_output"][ant_no] = _frame["gpioNo"]
    except Exception as e:
        logger.warn("while configure antenna configuration!")
    return config_frame

def timeConfig(config_frame, data_pack):
    """
    "timeConfig":{"boomOutputON":6,"redLedON":3, "transactionPost":0, "deviceHBInterval":30}
    """
    try:
        config_frame["app"]["boom_on_time"] = data_pack["boomOutputON"]
        config_frame["app"]["red_led_on_time"] = data_pack["redLedON"]
        config_frame["app"]["transactionpost"] = data_pack["transactionPost"]
        config_frame["app"]["devicehbinterval"] = data_pack["deviceHBInterval"]
    except Exception as e:
        logger.warn("while configure time intervals configuration!")
    return config_frame

def serialConfig(config_frame, data_pack):
    """
    "serialConfig":{"baudrate":"38400","serialPath":"/dev/ttyAMA0"}
    """
    try:
        keys = data_pack.keys()
        config_frame["rfid"]["interface"] = "serial"
        config_frame["rfid"]["baudrate"] = data_pack["baudrate"]
        config_frame["rfid"]["port"] = data_pack["port"]
        if "parity" in keys:
            config_frame["rfid"]["parity"] = data_pack["parity"]
    except Exception as e:
        logger.warn("while configure serial configuration!")
    return config_frame

def setAntConfiguration(config_frame, data_pack):
    try:
        antno = int(data_pack["antNo"]) - 1
        config_frame["rfid"]["antennas_name"][antno] = data_pack["antname"]
        config_frame["rfid"]["ant_location"][antno] = data_pack["antlocation"]
        config_frame["rfid"]["antennas"][antno][1] = int(float(data_pack["antpower"]) * 1000)

        if data_pack["relayNum"] == "Relay-1":
           config_frame["gpio"]["out_pin"]["boom_output"][antno] =  config_frame["gpio"]["out_pin"]["board_relays"][0]
        elif data_pack["relayNum"] == "Relay-2":   
            config_frame["gpio"]["out_pin"]["boom_output"][antno] =  config_frame["gpio"]["out_pin"]["board_relays"][4]
        elif data_pack["relayNum"] == "Relay-6":     
            config_frame["gpio"]["out_pin"]["boom_output"][antno] =  config_frame["gpio"]["out_pin"]["board_relays"][1]

        if data_pack["validRelayNum"] == "Relay-3":
            config_frame["gpio"]["out_pin"]["green_led"][antno] =  config_frame["gpio"]["out_pin"]["board_relays"][5]
        elif data_pack["validRelayNum"] == "Relay-4":
            config_frame["gpio"]["out_pin"]["green_led"][antno] =  config_frame["gpio"]["out_pin"]["board_relays"][3]
            
        # config_frame["gpio"]["out_pin"]["boom_output"][antno] = int(data_pack["relayNum"])
        config_frame["gpio"]["out_pin"]["invaid_led"][antno] = int(data_pack["ledNum"])
        config_frame["gpio"]["boom_on_time"] = int(data_pack["boomOnTime"])
        # print(config_frame["rfid"])
    except Exception as e:
        logger.error(str(e))
    return config_frame
    

def setMqttConfiguration(config_frame,data_pack):
    try:
        config_frame["mqtt"]["connection"]["broker_address"] = data_pack["hostip"]
        config_frame["mqtt"]["connection"]["port"] = int(data_pack["port"])
        config_frame["mqtt"]["connection"]["user_id"] = data_pack["username"]
        config_frame["mqtt"]["connection"]["password"] = data_pack["password"]  
        # print(config_frame["mqtt"]["connection"])
    except Exception as e:
        logger.error(str(e))
    return config_frame

if __name__=="__main__":
    try:
        config_data()
    except:
        logger.warning("data un-parsing problem!")
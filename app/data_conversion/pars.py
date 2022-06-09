import json
import logging

from .system_status import status_temperature, status_ram, hotspot_name
from app.utils import get_ipv4, get_mac, get_datetime_stamp,read_local_config
from app.settings import CONFIG_TOML_FILE, PATH_FILE_LOG

logger = logging.getLogger(__name__)
localConfig = read_local_config(CONFIG_TOML_FILE)

def config_data(data_pack):
    try:
        return data_pack
    except Exception as e:
        logger.warning(str(e))

def heartbeat(data_pack):
    data_frame = status_temperature()
    ram_status = status_ram()
    data = {
        "DeviceId": "101",
        "Hotspot": hotspot_name(),
        "LocalStaticIp":"192.168.1.160",
        "Temp": data_frame["temperature"],
        "UsedRam": ram_status["used"]
    }
    return data

def heartbeat_data(device_id):
    data_frame = status_temperature()
    data = {
        "action":"hb",
        "data":{
                "deviceId": device_id,
                "hotspot": hotspot_name(),
                "localStaticIp": localConfig["static_ipv4"],
                "temp": data_frame["temperature"],
                "ramStatus": status_ram()
            }
        }
    return data

def vehicle_access(data_pack, deviceid):
    """
    data_pack : tagId, vehicleTime, gate
    settings : deviceid
    """
    data = {
        "action":"transVehicle",
        "data":{
            "deviceId": deviceid,
            "time": get_datetime_stamp("%Y-%m-%d %H:%M:%S"),
            "transVehicle":[
                {
                    "tagId":data_pack["tagId"],
                    "time":data_pack["vehicleTime"], # Vehicle in/out time
                    "gate":data_pack["gate"], # Antenna title scanned from which antenna
                    "tFlag":data_pack["tFlag"] #transaction flag 1 or 2 or 3 where 1-authorized, 2-blocked, 3-unauthorized
                    }
                    ]
                }
        }
    return data

def device_setup(settings):
    data = {
        "action":"devicedata",
        "data":{
            "deviceId": settings["deviceid"],
            "time": get_datetime_stamp("%Y-%m-%d %H:%M:%S"),
            "userName":None, # optional # user name and password for login on server for
            "passwd":None, # optional
                                   # with latest configuration of device
            "antConfig":antenna_config(settings["rfid"], settings["gpio"]),
            "timeConfig":time_config(settings),
            "serialConfig":serial_config(settings["rfid"])
            }
        }
    return data

def antenna_config(settings, gpio_settings):
    data = [
        {
            "antNo":ant[0],
            "power":ant[1], # Set antenna power
            "title":settings["antennas_name"][i], # Give Antenna name, IN/OUT boom
            "gpioNo":gpio_settings["out_pin"]["boom_output"][i], # set Output Number to antenna with respective boom
            "boomConfig":gpio_settings["boom_config"]["booms"][i]
        }
        for i, ant in enumerate(settings["antennas"])
    ]
    return data

def time_config(settings):
    # open, open_time, open_buzzer_on,open_buzzer_on_time,invalid_led_trigger,invalid_buzzer_trigger,invalid_led_on_time
    # take settings["app"]
    data = {
        "boomOutputON":settings["gpio"]["boom_on_time"], # Output ON time for boom trigger
        "redLedON":settings["gpio"]["red_led_on_time"], # Red LED ON time in seconds
        "transactionPost":settings["app"]["transactionpost"], # Transaction vehicle log send to server periodically in s
        "deviceHBInterval":settings["app"]["devicehbinterval"] # Heart Beat send to server periodically in seconds
    }
    return data

def serial_config(settings):
    # settings["rfid"] accepted
    data = {
        "baudrate":settings["baudrate"],
        "serialPath":settings["port"],
        "parity":settings["parity"]
        }
    return data

if __name__=="__main__":
    try:
        config_data()
    except:
        logger.warning("data parsing problem!")
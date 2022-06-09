#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import psutil
import subprocess

logger = logging.getLogger(__name__)


def hotspot_name():
    ssid = "iTEKAVI"
    try:
        hostapdfile = "/etc/hostapd/hostapd.conf"
        with open(hostapdfile, "r") as fs:
            data = fs.readlines()
            fs.close()
        if len(data) > 0:
            data = list(data)
            ssid = data[1].replace("ssid=","")
            ssid = ssid.replace("\n","")
    except Exception as e:
        logger.error(str(e))
    return ssid

def status_disk():
    """
    Used to get Hard drive, SD storage Usage in bytes
    total = drive.total
    used = drive.used
    free = drive.free
    """
    disk = {}
    data = psutil.disk_usage("/")
    disk = {"total": data.total, "used": data.used, "free": data.free}
    return disk


def status_ram():
    """
    Used to get RAM Usage in bytes
    total = ram.total
    used = ram.used
    free = ram.free
    """
    ram = {}
    data = psutil.virtual_memory()
    ram = {"total": data.total, "used": data.used, "free": data.free}
    return ram


def status_cpu():
    """
    Used to get CPU Usage in 0.0 %
    cpu_1 = cpu[0]
    cpu_2 = cpu[1]
    cpu_3 = cpu[2]
    cpu_4 = cpu[3]
    """
    cpu = {}
    data = psutil.cpu_percent(interval=1, percpu=True)
    cpu = {"cpu1": data[0], "cpu2": data[1], "cpu3": data[2], "cpu4": data[3]}
    return cpu


def status_temperature():
    """
    Used to get device temperature
    in celsius unless fahrenheit is set to True
    temp = temp.current
    """
    temp = {}
    temp_data = psutil.sensors_temperatures(fahrenheit=False)
    if "cpu_thermal" in temp_data:
        data = temp_data["cpu_thermal"][0]
        temp = {"temperature": data.current}
    return temp


def status_throttle():
    """
    Used to get raspberry throttled status

    Bit     Hex     value Meaning
    0       1       Under-voltage detected
    1       2       Arm frequency capped
    2       4       Currently throttled
    3       8       Soft temperature limit active
    16      10000   Under-voltage has occurred
    17      20000   Arm frequency capping has occurred
    18      40000   Throttling has occurred
    19      80000   Soft temperature limit has occurred
    """
    THROTTLED_CMD = "vcgencmd get_throttled"
    throttled = {}
    try:
        throttled_output = subprocess.check_output(THROTTLED_CMD, shell=True)
        throttled_value = int(throttled_output.decode("ascii").strip().split("=")[1], 0)

        throttled["RawValue"] = hex(throttled_value)

        if throttled_value & (1 << 0):  # Under-voltage
            throttled["UnderVoltageDetected"] = True
        else:
            throttled["UnderVoltageDetected"] = False

        if throttled_value & (1 << 1):  # Arm frequency capped
            throttled["ArmFreqCapped"] = True
        else:
            throttled["ArmFreqCapped"] = False

        if throttled_value & (1 << 2):  # Currently throttled
            throttled["CurrentlyThrottled"] = True
        else:
            throttled["CurrentlyThrottled"] = False

        if throttled_value & (1 << 3):  # Soft temperature limit active
            throttled["SoftTemperatureLimitActive"] = True
        else:
            throttled["SoftTemperatureLimitActive"] = False

        if throttled_value & (1 << 16):  # Under-voltage has occurred
            throttled["UnderVoltageOccurred"] = True
        else:
            throttled["UnderVoltageOccurred"] = False

        if throttled_value & (1 << 17):  # Arm frequency capping has occurred
            throttled["ArmFreqCappedOccurred"] = True
        else:
            throttled["ArmFreqCappedOccurred"] = False

        if throttled_value & (1 << 18):  # Throttling has occurred
            throttled["ThrottledOccurred"] = True
        else:
            throttled["ThrottledOccurred"] = False

        if throttled_value & (1 << 19):  # Soft temperature limit has occurred
            throttled["SoftTemperatureLimitOccurred"] = True
        else:
            throttled["SoftTemperatureLimitOccurred"] = False
    except subprocess.CalledProcessError:
        logger.exception("while throttle process error")

    return throttled


def get_system_status():
    status = {}
    try:
        status["disk"] = status_disk()
        status["ram"] = status_ram()
        status["tempearture"] = status_temperature()
        status["cpu"] = status_cpu()
        status["throttle"] = status_throttle()

    except Exception:
        logger.exception("while getting system status")

    return status


if __name__ == "__main__":
    try:
        print("status disk: ", status_disk())
        print("status ram: ", status_ram())
        print("status temperature: ", status_temperature())
        print("status cpu: ", status_cpu())
        print("status throttle: ", status_throttle())
    except Exception as e:
        logger.exception("while main, error: %s", e)

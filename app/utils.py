#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import requests
import subprocess
from subprocess import call

from datetime import datetime, timedelta
from datetime import timezone

from socket import AF_INET
from psutil import net_if_addrs, AF_LINK
import toml
import os


logger = logging.getLogger(__name__)

class NetworkInterfaceNotFound(Exception):
    pass

net_interfaces = net_if_addrs()
# print("net_interfaces >",net_interfaces)

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

def is_internet():
    """
    This api is used to check internet connection
    """
    #url = "http://www.google.com/" # using this causes timeout
    url = "https://www.google.com/"
    ret = None
    _internet = False
    try:
        ret = requests.get(url, timeout=15)
        if ret.status_code == 200:
            _internet = True

    except requests.ReadTimeout:
        logger.error("request read timeout")

    except requests.ConnectTimeout:
        logger.error("request connect timeout")

    except requests.ConnectionError:
        logger.error("request connect error")

    except Exception:
        logger.exception("while check internet")
    return _internet

def get_mac(interface="eth0") -> str:
    """Return the MAC address of the specified interface

    Args:
        interface: str, network interface of which to get MAC

    Returns:
        macaddr: str, mac address of the interface like 'aa:bb:cc:dd:ee:ff',
                      '' if not found
    Raises:
        NetworkInterfaceNotFound
    """
    macaddr = ""
    try:
        interface = net_interfaces[interface]
       # print(interface)
    except KeyError:
        raise NetworkInterfaceNotFound

    for ifaddr in interface:
        if ifaddr.family == AF_LINK:
            #print(ifaddr)
            macaddr = ifaddr.address
            break

    return macaddr

def get_gateway(interface="br0") -> str:

    gateway = ""
    try:
        gateway = subprocess.run(['sudo', 'route', '-n'], 
                                        universal_newlines=True, 
                                        stdout=subprocess.PIPE
                                    )
        gateway = gateway.stdout.split()
        gateway = gateway[13]
    except Exception as e:
        logger.error("exception while getting gateway >"+str(e))

    return gateway

def get_netmask(interface="br0") -> str:
    netmask = ""
    try:
        netmask = subprocess.run(['sudo', 'route', '-n'], 
                                        universal_newlines=True, 
                                        stdout=subprocess.PIPE
                                    )
        netmask = netmask.stdout.split()
        netmask = netmask[22]
    except Exception as e:
        logger.error("exception while getting netmask >"+str(e))
        # interface = net_interfaces[interface]
    # except KeyError:
        # raise NetworkInterfaceNotFound    

    return netmask

def get_ipv4(interface="eth0") -> str:
    """Return the IPv4 address of the specified interface

    Args:
        interface: str, network interface of which to get IP

    Returns:
        ipaddr: str, ip address of the interface like '192.168.0.1',
                    '' if not found

    Raises:
        NetworkInterfaceNotFound
    """
    ipaddr = ""
    try:       
        ipaddr = os.popen("hostname -I").readline()    
        
    except Exception as e:
        logger.error("exception while getting ip >"+str(e))   

    return ipaddr

def get_datetime_stamp(fmt: str = "") -> str:
    """Returns current date & time.

    Args:
        fmt: str, This defines date time format object for strftime().

    Returns:
        stamp:str,
            If format is None then output will in the form 'DDMMYYYYHHMMSS'
    """
    dt = datetime.now()
    if fmt != "":
        stamp = dt.strftime(fmt)
    else:
        stamp = dt.strftime("%d-%m-%Y %H:%M:%S")

    return stamp

def yesterday_date(beforeday=1):
    dt = datetime.today() - timedelta(days=beforeday)
    stamp = dt.strftime("%d-%m-%Y")
    return stamp

def today_date():
    dt = datetime.today()
    stamp = dt.strftime("%d-%m-%Y")
    return stamp

def convert_to_localtime(date_time: str):
    """Convert to local datetime.
    """
    temp1 = datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S")
    temp2 = temp1.replace(tzinfo=timezone.utc)
    local_time = temp2.astimezone()

    return local_time.strftime("%Y-%m-%d %H:%M:%S")

def setDate(date: str):
    try:
        today = datetime.now()
        date = [int(x) for x in date.split("-")]
        # print("date in setDate",date)
        date2 = today.replace(year=date[0],month=date[1],day=date[2])
        # return date2
        print(date2)
    except Exception as e:
        print("exception while setting date >",str(e))

def setTime(time: str):
    try:
        today = datetime.now()
        time = [int(x) for x in time.split(":")]
        # print("Time in setTime",time)
        time2= today.replace(hour=time[0],minute=time[1],second=time[2])
        print(time2)
        # return time2
    except Exception as e:
        print("exception while setting time >",str(e))
    
def setDateTime(date: str,time: str):
    # pass
    try:
        print("date time before update >",datetime.now())        
        dateTime = date + ' ' + time
        
        res = subprocess.run(["sudo", "date", "--set", dateTime])
       
        print("date time after update >",datetime.now())

    except Exception as e:
        print("while changing date time >",str(e))


def read_local_config(file):
    config = None
    try:
        config = toml.load(file)
       # print(config)
    except toml.decoder.TomlDecodeError as err:
        logger.error("Error while decoding %s, %s", file, err)
    except FileNotFoundError:
        logger.error("Error= FileNotFoundError while opening %s", file)
    except Exception:
        logger.exception("Error while opening %s", file)
    return config

def write_local_config(file, updated_data):
    try:
        with open(file, "w") as config_toml:
            toml.dump(updated_data, config_toml)
        config_toml.close()
    except toml.encoder.TomlDecodeError as err:
        logger.error("Error while decoding %s, %s", file, err)

    config_data = read_local_config(file)
    return config_data

def reboot_system():
    call("sudo reboot", shell=True)
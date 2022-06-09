#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from logging import exception, handlers
from functools import partial

from app.gpio.HandleGpio import onIOForTime

from .HandleGpio import HandleGPIO, BlinkIO, BlinkIOTime
from .errors import *
from ..settings import PATH_FILE_LOG
#####################################################################
# Setup logger
PATH_FILE_LOG += "logs/"
formatter = logging.Formatter(
    "%(asctime)s::%(levelname)s::%(filename)s::%(lineno)d %(message)s"
)
logger = logging.getLogger("gpio")
logger.setLevel(logging.DEBUG)

# print("gpio process before handler")
# try: 
# time logger
handler = handlers.TimedRotatingFileHandler(
    PATH_FILE_LOG + "gpio/gpio.log",
    when="midnight",
    backupCount=10,
    interval=1,
)
# print("gpio process after handler")
handler.setFormatter(formatter)
logger.addHandler(handler)
# print("gpio process after add handler")
# except Exception as e:
#     print("gpio handler error")
#     print(str(e))


class GpioProcess(HandleGPIO):

    def __init__(self, settings):
        """
        BlinkIO gpio base program package
        """
        # print("gpio_process.py class GpioProcess init")
        self.__gpio_settings = settings
        try:
            #self.io_run = HandleGPIO(settings)
            HandleGPIO.__init__(self, self.__gpio_settings)
        except AttributeError as e:         
            logger.error("not found : "+str(e))
            raise AttributeError("not found")
        
        self._boom_on_time = self.__gpio_settings["boom_on_time"]
        self._red_led_on_time = self.__gpio_settings["red_led_on_time"]

        self._out_pins = self.__gpio_settings["out_pin"]
        self._out = self.__gpio_settings["out_pin"]["boom_output"]        
        self._green_led = self.__gpio_settings["out_pin"]["green_led"]
        # print("self._out >",self._out)
        # print("self._green_led >",self._green_led)
        self._out_invalid_led = self.__gpio_settings["out_pin"]["invaid_led"]
        self._in = self.__gpio_settings["in_pin"]["safety_boom"]
        self._boom_config = self.__gpio_settings["boom_config"]["booms"]

        self._buzzer = self.__gpio_settings["out_pin"]["buzzer"]

        # thread for blinking
        self.__app_running = BlinkIO(pin=self._out_pins['app_running'], Ton=self.__gpio_settings["io_blink_on_time"], Toff=self.__gpio_settings["io_blink_off_time"])
        self.__scanning_mode = BlinkIO(pin=self._out_pins['scanning_mode'], Ton=self.__gpio_settings["io_blink_on_time"], Toff=self.__gpio_settings["io_blink_off_time"])
        self.__error_mode = BlinkIO(pin=self._out_pins['error_mode'], Ton=self.__gpio_settings["io_blink_on_time"], Toff=self.__gpio_settings["io_blink_off_time"])
        self.__buzzer = BlinkIO(pin=self._buzzer, Ton=self.__gpio_settings["buzzer_on_time"], Toff=self.__gpio_settings["buzzer_off_time"])

        self.__prog_running = BlinkIO(pin=self._out_pins['prog_running'],Ton=0.07,Toff=1.5)
        self.__boot_running = BlinkIO(pin=self._out_pins['prog_running'],Ton=0.02,Toff=0.07)
        # self.__prog_running = None
        # self.__boot_running = None
        
        self.__safety_boom1 = None
        self.__safety_boom2 = None

        # external callbacks
        self.__cb_emergency = None
        self.__cb_safety_in = None
        self.__cb_safety_out = None
        self.result = None

        self.on_emergency = None
        self.emergency_on_detect = False        

    def prog_run_blink(self):
        """functino to blink prog_running led(refer config.toml),
        forever after program starts, to let know that program is running
        """
        logger.debug("blink program running thread!")
        try:      
            # self.__prog_running = BlinkIO(pin=self._out_pins['prog_running'])      
            self.__prog_running.enable()
            self.__prog_running.start()
        except Exception as e:
            logger.exception("while program running thread mode")
            # print("while program running thread mode >",e)
    
    def prog_run_blink_stop(self):
        logger.debug("stopping program running blink thread")
        if self.__prog_running.is_alive():
            self.__prog_running.stop()   

    def booting_blink_start(self):
        logger.debug("blink booting light thread!")
        try:        
            # self.__boot_running = BlinkIO(pin=self._out_pins['prog_running'])    
            self.__boot_running.enable()
            self.__boot_running.start()
        except Exception as e:
            logger.exception("while program booting thread mode")
            # print("while program running thread mode >",e)

    def booting_blink_stop(self):
        logger.debug("stopping booting light blink thread")
        if self.__boot_running.is_alive():        
            self.__boot_running.stop()          

# not used in fastgate
    def app_run_blink(self):
        '''
        Blink indicator
        '''
        logger.debug("blink scanning mode thread!")
        try:
            self.__app_running = BlinkIO(pin=self._out['app_running'])
            self.__app_running.enable()
            self.__app_running.start()
        except Exception:
            logger.exception("while app_running mode")

# not used in fastgate
    def app_run_blink_stop(self):
        logger.debug("stopping app_running mode blink")
        if self.__app_running.is_alive():
            self.__app_running.stop()

# not used in fastgate
    def scanning_blink(self):
        '''
        Blink indicator
        '''
        logger.debug("blink scanning mode thread!")
        try:
            self.__scanning_mode = BlinkIO(pin=self._out['scanning_mode'])
            self.__scanning_mode.enable()
            self.__scanning_mode.start()
        except Exception:
            logger.exception("while blinking scanning mode")

# not used in fastgate
    def scanning_blink_stop(self):
        logger.debug("stopping scanning mode blink")
        if self.__scanning_mode.is_alive():
            self.__scanning_mode.stop()

# not used in fastgate
    def running_mode(self):
        '''
        Blink indicator
        '''
        logger.debug("blink running mode thread!")
        try:
            self.__running_mode = BlinkIO(pin=self._out['running_mode'])
            self.__running_mode.enable()
            self.__running_mode.start()
        except Exception:
            logger.exception("while blinking scanning mode")

# not used in fastgate
    def running_blink_stop(self):
        logger.debug("stopping running mode thread")
        if self.__running_mode.is_alive():
            self.__running_mode.stop()

# not used in fastgate
    def error_mode(self):
        '''
        Blink indicator
        '''
        logger.debug("blink error mode thread!")
        try:
            self.__error_mode = BlinkIO(pin=self._out['error_mode'])
            self.__error_mode.enable()
            self.__error_mode.start()
        except Exception:
            logger.exception("while blinking scanning mode")

# not used in fastgate
    def error_mode_stop(self):
        logger.debug("stopping error mode thread")
        if self.__error_mode.is_alive():
            self.__error_mode.stop()

    def buzzer_startup_blink(self):
        """blink buzzer at start up
        """

        logger.debug("start up buzzer blink")
        try:
            buzzer_on_startup_thread = BlinkIOTime(
                                    pin=self._buzzer,
                                    Ton=0.4,
                                    Toff=0.4,
                                    blink_time=1
            )
            buzzer_on_startup_thread.enable()
            buzzer_on_startup_thread.start()           
        except Exception as e:
            logger.warn(f"execption while start up buzzer {str(e)}")
           
# not used in fastgate
    def buzzer_blink(self):
        '''
        Blink indicator
        '''
        logger.debug("blink error mode thread!")
        try:
            self.__buzzer = BlinkIO(pin=self._buzzer)
            self.__buzzer.enable()
            self.__buzzer.start()
        except Exception:
            logger.exception("while blinking scanning mode")

# not used in fastgate
    def buzzer_blink_stop(self):
        logger.debug("stopping error mode thread")
        if self.__buzzer.is_alive():
            self.__buzzer.stop()

    def buzzer_on_thread(self, Ton):
        '''
        on buzzer
        '''
        try:
            logger.debug("on buzzer!")
            buzzer_on_thread = BlinkIOTime(
                pin=self._buzzer, 
                Ton=Ton,
                Toff=0,
                blink_time=Ton)
            buzzer_on_thread.enable()
            buzzer_on_thread.start()
        except Exception as e:
            logger.warn("while buzzer on thread {}".format(str(e)))

    def buzzer_off(self):
        '''
        off buzzer
        '''
        logger.debug("off buzzer!")
        self.pin_write(self._out['error_mode'], 0)

    def boom_open(self, boom_no):
        '''
        open boom and close in thread automatically as per time
        '''
       # try:
        boom = boom_no-1
        logger.debug("opening boom no {}".format(str(boom)))
        # in/main roller start
        if self._boom_config[boom][0]:
            if self._boom_on_time == 0:
                Ton = self._boom_config[boom][1]
            else:
                Ton = self._boom_on_time

            # print("Ton : "+str(Ton))
            # print("gpio pin to ", self._out[boom])
            boom_open_tread = onIOForTime(
                    pin=self._out[boom],
                    Ton=Ton)

            boom_open_tread.enable()
            boom_open_tread.start()
            # boom_open_thread = BlinkIOTime(
            #     pin=self._out[boom], 
            #     Ton=Ton,
            #     Toff=0.5,
            #     blink_time=Ton)
            # boom_open_thread.enable()
            # boom_open_thread.start()

            if self._boom_config[boom][2]:
                self.buzzer_on_thread(self._boom_config[boom][3])

        # except Exception as e:
        #     logger.exception("while open boom thread! "+str(e))
        
    def boom_close(self, boom_no):
        '''
        boom closing trigger
        '''
        try:
            boom = boom_no-1
            logger.debug("Closing boom no {}".format(str(boom)))
            self.pin_write(self._out[boom], 0)
        except Exception as e:
            logger.exception("while close boom! "+str(e))

    def green_led_on(self,led_num):
        # try:
            led_num=led_num-1
            logger.debug("green led on led number {}".format(str(led_num)))
            if self._boom_on_time == 0:
                Ton = self._boom_config[led_num][1]
            else:
                Ton = self._boom_on_time
            
            green_led_open_thread = onIOForTime(
                pin=self._green_led[led_num], 
                Ton=Ton,)
            green_led_open_thread.enable()
            green_led_open_thread.start()
    
    def green_led_off(self,led_num):
        
        led_num = led_num-1
        logger.debug("green led off led num {}".format(str(led_num)))
        self.pin_write(self._green_led[led_num], 0)

    def service_active_relays_on(self):
        logger.debug("making service activation relays ON")
        try:
            self.pin_write(self._out[0],1)
            self.pin_write(self._out[1],1)

            self.pin_write(self._green_led[0],1)
            self.pin_write(self._green_led[1],1)

            self.pin_write(self._out_invalid_led[0],1)
            self.pin_write(self._out_invalid_led[1],1)

        except Exception as e:
            print("while making service activation relays ON",str(e))
            logger.debug("while making service activation relays ON"+str(e))
    
    def service_active_relays_off(self):
        logger.debug("making service activation relays OFF")
        try:
            self.pin_write(self._out[0],0)
            self.pin_write(self._out[1],0)

            self.pin_write(self._green_led[0],0)
            self.pin_write(self._green_led[1],0)
        except Exception as e:
            print("while making service activation relays OFF",str(e))
            logger.debug("while making service activation relays OFF"+str(e))

    def red_led_thread(self, boom_no):
        try:
            boom = boom_no-1
            logger.debug("red led on pin {} open boom {}".format(self._out_invalid_led[boom], str(boom_no)))
            
            # in/main roller start
            if self._boom_config[boom][0]:
                if self._red_led_on_time == 0:
                    Ton = self._boom_config[boom][6]
                else:
                    Ton = self._red_led_on_time
                if self._boom_config[boom][4]:
                    red_led_on = onIOForTime(
                        pin=self._out_invalid_led[boom],
                        Ton=Ton
                    )
                    red_led_on.enable()
                    red_led_on.start()
                    # red_led_on = BlinkIOTime(
                    #     pin=self._out_invalid_led[boom],
                    #     Ton=Ton,
                    #     Toff=0.5,
                    #     blink_time=Ton
                    # )
                    # red_led_on.enable()
                    # red_led_on.start()
        except Exception as e:
            logger.exception("while read led thread! " + str(e))

    def enable_safety_boom1(self, callback, channel):
        '''
        Enable or Add callback event for safety check.
        '''
        logger.debug("enabling safety boom1")
        self.__safety_boom1 = partial(callback, channel)
        self.pin_event_rising(self._in['safety_boom1'],
                           self.__safety_boom1)

    def disable_safety_boom1(self):
        '''
        Disable safety event.
        '''
        logger.debug("disabling safety boom1 in")
        self.pin_event_remove(self._in['safety_boom2'])

    def enable_safety_boom2(self, callback, channel):
        '''
        Enable or Add callback event for safety boom2 check.
        '''
        logger.debug("enabling safety boom2")
        self.__safety_boom2 = partial(callback, channel)
        self.pin_event_rising(self._in['safety_boom2'],
                           self.__safety_boom2)

    def disable_safety_boom2(self):
        '''
        Disable safety event.
        '''
        logger.debug("disabling safety boom2")
        self.pin_event_remove(self._in['safety_boom2'])

    def start_safety_control(self):
        '''
        Wait for shutter in and out open.
        '''
        logger.debug("checking for safety control")

        self.enable_safety_boom1(callback=self.callback_safety_boom1, channel=self._in['safety_boom1'])
        self.enable_safety_boom2(callback=self.callback_safety_boom2, channel=self._in['safety_boom2'])

    def callback_safety_boom1(self, channel):
        logger.critical('safety in sensor is in action')
        if self.pin_read(channel):
            logger.warning("safety sensor : detected")
            self.boom1_open()
        else:
            logger.warning("safety sensor : activated")
            self.boom1_close()

    def callback_safety_boom2(self, channel):
        logger.critical('safety out sensor is in action')
        if self.pin_read(channel):
            logger.warning("safety sensor : detected")
            self.boom2_open()
        else:
            logger.warning("safety sensor : activated")
            self.boom2_close()

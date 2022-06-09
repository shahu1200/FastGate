#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from multiprocessing.spawn import is_forking
import time
from threading import Timer, Thread, Event
import logging

logger = logging.getLogger("gpio")

try:
    from RPi import GPIO
except ImportError as e:
    logger.fatal("GPIO : " + str(e))
    raise

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

class HandleGPIO:

    def __init__(self, settings):
        """
        GPIO initialise pins
        """
        # print("HandleGpio.py class HandleGPIO init")
        #print(settings["out_pin"])
        try:
            #print(settings["out_pin"]["boom_output"], settings["out_pin"]["invaid_led"])
            self._out = settings["out_pin"]["boom_output"]
            self._outG = settings["out_pin"]["green_led"]            
            self._out.extend(settings["out_pin"]["invaid_led"])
            self._relayPins = settings["out_pin"]["board_relays"]
            #print(self._out)
            self._in = settings["in_pin"]["safety_boom"]
            self._bounce_time = settings["io_time_bounce"]
            self._app_running = settings["out_pin"]["app_running"]
            self._scanning_mode = settings["out_pin"]["scanning_mode"]
            self._error_mode = settings["out_pin"]["error_mode"]
            self._buzzer = settings["out_pin"]["buzzer"]
            self._prog_running = settings["out_pin"]["prog_running"]
        except  Exception as e:
            logger.warning("GPIO initialisation problem : "+str(e))

        self.__active = True
        self.__ret = False

        GPIO.setup(self._app_running, GPIO.OUT)
        GPIO.output(self._app_running, GPIO.LOW)
        
        GPIO.setup(self._scanning_mode, GPIO.OUT)
        GPIO.output(self._scanning_mode, GPIO.LOW)

        GPIO.setup(self._error_mode, GPIO.OUT)
        GPIO.output(self._error_mode, GPIO.LOW)

        GPIO.setup(self._buzzer, GPIO.OUT)
        GPIO.output(self._buzzer, GPIO.LOW)
        
        GPIO.setup(self._prog_running, GPIO.OUT)       
        GPIO.output(self._prog_running, GPIO.LOW)

        # # for boom_output list in config.toml set those pin as output pins
        # for pin_no in self._out:
        #     try:
        #         GPIO.setup(pin_no, GPIO.OUT)
        #         GPIO.remove_event_detect(pin_no)
        #         GPIO.output(pin_no, GPIO.LOW)
        #     except Exception:
        #         logger.exception('set as output pin: {}'.format(pin_no))
        
        # # for green led list in config.toml set those pins as output pins
        # for pin_no in self._outG:
        #     try:
        #         GPIO.setup(pin_no, GPIO.OUT)
        #         GPIO.remove_event_detect(pin_no)
        #         GPIO.output(pin_no, GPIO.LOW)
        #     except Exception:
        #         logger.exception('set as output pin: {}'.format(pin_no))

        # set all relay pins as output pins and make them low
        for pin_no in self._relayPins:
            try:
                GPIO.setup(pin_no, GPIO.OUT)
                GPIO.remove_event_detect(pin_no)
                GPIO.output(pin_no, GPIO.LOW)
              
            except Exception:
                logger.exception('set as output pin: {}'.format(pin_no))

        
        for pin_no in self._in:
            try:
                GPIO.setup(pin_no, GPIO.IN)
                GPIO.remove_event_detect(pin_no)
            except Exception:
                logger.exception('set as input pin: {}'.format(pin_no))

        self.emergency_on_detect = False

        # gpioPins = [7,21,24,26,29,31]
        # gpioPins7 = [29,31,]
        # self.pins_on(self._relayPins,3)
        # self.pins_on(self._out,5)
        # self.pins_on(self._outG,5)
        

    def pin_write(self, pin=None, state=0):
        """
        write pin low/high
        """
       # logger.debug("write pin: {} state to {}".format(pin, state))
        try:
            GPIO.output(pin, state)
        except Exception:
            logger.exception('write pin: {} state to {}'.format(pin, state))

    def pin_read(self, pin=None):
        '''
        read IO state
        '''
        #logger.debug("read pin: {}".format(pin))
        try:
            return GPIO.input(pin)
        except Exception:
            logger.exception("read pin: {}".format(pin))

    def emergency_on(self):
        """
        Emergency pressed and all outputs off
        """
        for pin_name, pin_no in self._out.items():
            try:
                GPIO.setup(pin_no, GPIO.OUT)
                GPIO.output(pin_no, GPIO.LOW)
            except Exception:
                logger.exception('set as output pin: {}={}'
                .format(pin_name, pin_no))

    def alert_detection(self):
        """
        Alert can on from this fuction
        """
        try:
            GPIO.setup(self._out["led_red"], 1)
            GPIO.setup(self._out["led_yellow"], 2)
        except Exception:
            logger.exception("read pin: ")

    def pins_on(self, pins=[], for_time=0):
        """
        ON multiple outputs/ ON to OFF with time
        pins: ["pin1","pin2"]
        for_time : seconds, Output ON for seconds time.
        """
        on_time = 0
        for pin in pins:
            try:
                GPIO.output(pin, GPIO.HIGH)
                on_time = time.time()
            except Exception:
                logger.exception('ON Output pin: {}'.format(pin))


        while for_time:
            run_time = time.time()

            if run_time - on_time > for_time:
                self.pins_off(pins)
                break

    def pins_off(self, pins=[], for_time=0):
        """
        OFF multiple outputs / OFF to ON with time
        pins: ["pin1","pin2"]
        for_time : seconds, Output OFF for seconds time.
        """
        off_time = 0
        for pin in pins:
            try:
                GPIO.output(pin, GPIO.LOW)
                off_time = time.time()
            except Exception:
                logger.exception('OFF Output pin: {}'.format(pin))

        while for_time:
            run_time = time.time()
            if run_time - off_time > for_time:
                self.pins_on(pins)
                break

    def pins_flashing(self, pins=[], on_time=1, off_time=1, for_time=5):
        """
        Pin/LED ON OFF for some duration
        pins: list of all pins
        on_time: pin ON state for seconds
        off_time: pin OFF state for seconds
        for_time: pin ON - OFF - ON for sencods
        """
        start_time = time.time()
        while for_time:
            self.pins_on(pins, on_time)
            self.pins_off(pins, off_time)
            end_time = time.time()
            if end_time - start_time > for_time:
                self.pins_off(pins, 0)
                break

    def pins_clean(self):
        '''
        clean all pins used in this module
        '''
        logger.debug("clean io")
        try:
            GPIO.cleanup()
        except Exception:
            logger.exception("while cleaning gpio")

    def pin_event_falling(self, pin=None, cb=None):
        '''
        Add callback on IO event=FALLING
        '''
        logger.debug("add event: FALLING pin: %d", pin)
        try:
            GPIO.add_event_detect(pin,
                                  GPIO.FALLING,
                                  callback=cb,
                                  bouncetime=self._bounce_time)
        except Exception:
            logger.exception("while registering event FALLING for pin: %d", pin)

    def pin_event_rising(self, pin=None, cb=None):
        '''
        Add callback on IO event=RISING
        '''
        logger.debug("add event: RISING pin: %d", pin)
        try:
            GPIO.add_event_detect(pin,
                                  GPIO.RISING,
                                  callback=cb,
                                  bouncetime=self._bounce_time)
        except Exception:
            logger.exception("while registering event RISING for pin: %d", pin)

    def pin_wait_rising(self, pin=None, tout=0):
        '''
        wait IO until RISING or TIMEOUT
        '''
        logger.debug("wait for edge: RISING pin: %d", pin)
        try:
            def cb_io_timeout():
                self.__ret = False
                self.__active = False

            def cb_io_event(channel):
                self.__ret = True
                self.__active = False

            GPIO.add_event_detect(pin,
                                  GPIO.RISING,
                                  callback=cb_io_event,
                                  bouncetime=self._bounce_time)
            tmr = Timer(tout,  cb_io_timeout)
            tmr.start()

            while self.__active:
                pass

            tmr.cancel()
            GPIO.remove_event_detect(pin)
            self.__active = True
            return self.__ret

        except Exception:
            logger.exception("while waiting for RISING, pin: %d", pin)

    def pin_wait_falling(self, pin=None, tout=0):
        '''
        wait IO until FALLING or TIMEOUT
        '''
        logger.debug("wait for edge: FALLING pin: %d", pin)
        try:
            def cb_io_timeout():
                self.__ret = False
                self.__active = False

            def cb_io_event(channel):
                self.__ret = True
                self.__active = False

            GPIO.add_event_detect(pin,
                                  GPIO.FALLING,
                                  callback=cb_io_event,
                                  bouncetime=self._bounce_time)

            tmr = Timer(tout,  cb_io_timeout)
            tmr.start()

            while self.__active:
                if self.emergency_on_detect:
                    self.__active = False
                pass

            tmr.cancel()
            GPIO.remove_event_detect(pin)
            self.__active = True
            return self.__ret
        except Exception:
            logger.exception("while waiting for FALLING, pin: %d", pin)

    def pin_event_remove(self, pin=None):
        '''
        Remove IO event
        '''
        logger.debug("remove event pin: %d", pin)
        try:
            GPIO.remove_event_detect(pin)
        except Exception:
            logger.exception("while removing event for pin: %d", pin)

    def pin_event_both(self, pin=None, cb=None):
        '''
        Add callback on IO event=BOTH
        '''
        logger.debug("add event: BOTH pin: %d", pin)
        try:
            GPIO.add_event_detect(pin,
                                  GPIO.BOTH,
                                  callback=cb,
                                  bouncetime=self._bounce_time)
        except Exception:
            logger.exception("while registering event BOTH for pin: %d", pin)

class BlinkIO(Thread):

    def __init__(self, pin=None, Ton=0.5, Toff=0.5):
        # print("HandleGpio.py class BlinkIO init")
        Thread.__init__(self)
        logger.debug('IO Blink thread')
        self._event = Event()
        if not pin:
            raise Exception
        self._pin = pin
        self._ton = Ton
        self._toff = Toff

    def run(self):
       # logger.debug("IO Blink thread running")
        while self._event.is_set():
            if self._event.is_set():
                GPIO.output(self._pin, 1)
                time.sleep(self._ton)

            if self._event.is_set():
                GPIO.output(self._pin, 0)
                time.sleep(self._toff)

        GPIO.output(self._pin, 0)

    def enable(self):
        # logger.debug("IO Blink thread enable")
        self._event.set()

    def stop(self):
       #  logger.debug("IO Blink thread stopping")
        try:
            # GPIO.output(self._pin, 0)           
            if self._event.is_set:                
                GPIO.output(self._pin, 0)
                self._event.clear()                      
            # self.join()
        except Exception as e:
            logger.exception("while stopping blink thread")
            print("while stopping blink thread >",str(e))

# blink led/alarm for time in seconds
class BlinkIOTime(Thread):

    def __init__(self, pin=None, Ton=0.5, Toff=0.5, blink_time=4.0):
        # print("HandleGpio.py class BlinkIOTime init")
        Thread.__init__(self)
        logger.debug('IO Blink thread')
        self._event = Event()
        if not pin:
            raise Exception
        self._pin = pin
        self._ton = Ton
        self._toff = Toff
        self.blink_time = blink_time
        # print(pin, Ton, Toff, blink_time)

    def run(self):
        logger.debug("IO Blink thread running pin {}".format(self._pin))
        start_time = time.time()
        last_time = time.time()
        while self._event.is_set() and ((last_time - start_time) < self.blink_time):
            last_time = time.time()
            if self._event.is_set():
                GPIO.output(self._pin, 1)
                # print("i m in pin on loop for pin > ",self._pin)
                time.sleep(self._ton)
                logger.info("on out : {}".format(self._pin))

            if self._event.is_set():
                GPIO.output(self._pin, 0)
                time.sleep(self._toff)
                logger.info("off out : {}".format(self._pin))
        GPIO.output(self._pin, 0)
        self.stop()

    def enable(self):
        # logger.debug("IO Blink thread enable")
        self._event.set()

    def stop(self):
       #  logger.debug("IO Blink thread stopping")
        try:
            GPIO.output(self._pin, 0)
            self._event.clear()
            # self.join()
        except Exception:
            logger.exception("while stopping blink thread")

class onIOForTime(Thread):
    def __init__(self, pin=None, Ton=0.5):
        # print("HandleGpio.py class BlinkIOForTime init")
        Thread.__init__(self)
        logger.debug('IO ON thread')
        self._event = Event()
        if not pin:
            raise Exception
        self._pin = pin
        self._ton = Ton
        # print(pin,Ton)

    def run(self):
        logger.debug("IO ON thread running pin {}".format(self._pin))
        start_time = time.time()
        last_time = time.time()
        while self._event.is_set() and ((last_time - start_time) < (self._ton)/2):
            last_time = time.time()          
            GPIO.output(self._pin, 1)
            # print("i m in pin on loop for pin > ",self._pin,datetime.now())
            time.sleep((self._ton)/2)
     
        GPIO.output(self._pin, 0)
        logger.debug("IO ON thread over for pin {}".format(self._pin))
        # print("on thread over for pin > ",self._pin,datetime.now())
        self.stop()

    def enable(self):
        # logger.debug("IO Blink thread enable")
        self._event.set()

    def stop(self):
       #  logger.debug("IO Blink thread stopping")
        try:
            self._event.clear()
            # self.join()
        except Exception:
            logger.exception("while stopping ON for time thread")

            
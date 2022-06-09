#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
File     : settings.py
Author   : Abhijit Darwan
Email    : abhijit.darwan@infoteksoftware.com
Created  : Tuseday 18 May 2021
Modified : FILE_MODIFIED
"""

# all pin numbers are board pin numbers
# all output pin are defined here
# initially all pins are low (set low)
OUT_PIN = {
        # pins used for roller/conveyor
        "roller_in": 26,  # High = Start (forward dir)
        "roller_main": 7,
        "roller_out": 24,
        # pins used for shutter
        "shutter_in": 29,  # High = Close
        "shutter_out": 31,
        # pins used for tower indicator
        "led_green": 32,  # High = On
        "led_red": 19,
        "led_yellow": 23,
        # material stop for rejection push
        "mat_stopper": 33,
        # pin used for material segregation
        "mat_seg_switch": 21,  # High = Reject Object
        }

# all input pins used are defined here
# initially all pins are high (set high)

IN_PIN = {
        # object position
        "sensor_obj_det": 36,  # Low = Object Detected /position sensor
        "sensor_obj_rej": 11,
        "sensor_obj_seg": 16,
        # pins used for shutter position detection
        "shutter_in_close": 12,  # Low = fully closed
        "shutter_in_open": 35,   # Low = fully open
        "shutter_out_close": 38,
        "shutter_out_open": 40,
        # pin used for material segregation cylinder position
        "mat_seg_cyl_pos": 13,  # Low = Source Position / limit switch
        # pins used for safety detection
        "safety_in": 18,  # Low = Object Detected
        "safety_out": 22,
        # Emergency switch
        "emergency_switch": 37,  # Low = Active
        }

# set bounce time in millisecond
# keep between 30 to 50
IO_TIME_BOUNCE = 100

# add io process timeouts
# all in seconds
IO_TIMEOUT_SHUTTER_CLOSE = 15
IO_TIMEOUT_SHUTTER_OPEN = 15
IO_TIMEOUT_DETECT_OBJECT = 15
IO_TIMEOUT_DETECT_SEGREGATION = 15
IO_TIMEOUT_DETECT_REJECT = 15

IO_BLINK_ON_OFF_TIME = 4.0
IO_BLINK_ON_TIME = 0.5
IO_BLINK_OFF_TIME = 0.5
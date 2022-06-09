# error to command not found
ERROR_UNKNOWN_COMMAND = 101  # -->
# error to detect object
ERROR_TOUT_DETECT_OBJECT = "HU IN Timeout"  # -->
ERROR_TOUT_DETECT_SEGRE = "Segregation Timeout"
ERROR_TOUT_DETECT_REJECT = "Rejection Timeout"
# error to detect current object
ERROR_DETECTED_OBJECT = "Not detect"  # -->
ERROR_DETECTED_SEGRE = "segregation problem"
ERROR_DETECTED_REJECT = "Reject Problem"
# error to detect shutter position
ERROR_TOUT_SHUTTER_IN_CLOSE = "Shutter IN close position detect problem"
ERROR_TOUT_SHUTTER_IN_OPEN = "Shutter IN open position detect problem"
ERROR_TOUT_SHUTTER_OUT_CLOSE = "Shutter OUT close position detect problem"
ERROR_TOUT_SHUTTER_OUT_OPEN = "Shutter OUT open position detect problem"
# error to detect shutter current position
ERROR_SHUTTER_IN_CLOSE = "Shutter in closing problem"
ERROR_SHUTTER_IN_OPEN = "Shutter in opening problem"
ERROR_SHUTTER_OUT_CLOSE = "Shutter out closing problem"
ERROR_SHUTTER_OUT_OPEN = "Shutter out opening problem"
# error to detect segregation cylinder position sensor
ERROR_MATERIAL_SEGREGATION = "Segregation Problem"
# emergency states
EMERGENCY_SWITCH = "Emergency Activated"
EMERGENCY_SAFETY_ACTIVE = "Object detected while door closing. Safety activated."
EMERGENCY_TEMPERATURE = 704
EMERGENCY_CPU = 705
EMERGENCY_RAM = 706

# success messages
SUCCESS_MAT_IN = "Successfully In"
SUCCESS_MAT_OUT = "Process completed. Please place next HU"
SUCCESS_MAT_REJECT = "Rejected"

#
WAIT_FOR_HU = "Waiting for HU.."
WAIT_DOOR_CLOSE_MSG = 'Wait for Door Closing'
WAIT_CLOSE_SHUTTER_IN = 'Closing IN shutter! Please Wait..'
WAIT_CLOSE_SHUTTER_OUT = 'Closing OUT shutter! Please Wait..'
START_SCANNING = 'Start scanning..'
WAIT_SEGREGATION = 'Scanning done. Wait for Process Exited.'
WAIT_MAT_REJECTION = 'Wait for rejection'

class AttributeMissing(Exception):
    """ Attribute missing in setings.py
    """
    pass

class Error(Exception):
    pass

class GpioError(Error):
    pass

class GpioTimeoutError(GpioError):
    pass

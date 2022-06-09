class Error(Exception):
    """Base class for other exceptions"""
    pass

class MqttLoginError(Error):
    """Raised when mqtt not login."""
    pass

class MqttTopicError(Error):
    """Raised when mqtt topic error."""
    pass
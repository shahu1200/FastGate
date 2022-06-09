class Error(Exception):
    pass

class APIError(Error):
    pass

class APITimeoutError(APIError):
    pass

class APIDataKeyError(APIError):
    pass

class APIParsingError(APIError):
    pass

class APIRequestsError(APIError):
    pass

class APIUnParsingError(APIError):
    pass

class API404Error(APIError):
    pass
import logging

from api.errors import *
from api import settings

logger = logging.getLogger(__name__)

def get_token(api_output:str):
    token_type = "Bearer"
    try:
        #api_out_json = json.dumps(api_output)
        if "access_token" in api_output.keys():
            if "token_type" in api_output.keys():
                token_type = api_output["token_type"]

            Auth= token_type + " " + api_output["access_token"]
            if "expires_in" in api_output.keys():
                return {"Authorization":Auth, "error":"false", "expires_in":api_output["expires_in"]-100}
            else:
                return {"Authorization":Auth, "error":"false"}

        elif "error" in api_output.keys():
            # {'error': 'invalid_grant', 'error_description': 'Provided username and password is incorrect'}
            return api_output
    except KeyError as e:
        logger.warning("get token data unparsing key error %s", e)
        raise APIUnParsingError("scan count un-parsing error")

def scancount(api_output):
    #api_out_json = json.dumps(api_output)
    try:
        if "Error" in api_output.keys():
            if api_output["Error"] == "true":
                return {"Error":"true"}
            else:
                api_output["msg"] = settings.SUCCESS_MSG_PUSH
                return api_output
        else:
            return api_output
    except KeyError as e:
        logger.warning("scan count unparsing key error %s", e)
        raise APIUnParsingError("scan count un-parsing error")

def gethutripdata(api_output):

    """ create in json unparsing format
    """
    try:
        indata_format = {}
        items = []
        pars_api_output = {}
        data = api_output["Data"]
        for item in data:
            items.append(item['items'])
        for sub_items in range(0, len(items)):
            for item_list in items[sub_items]:
                if item_list["delv_num"] not in indata_format.keys():
                    indata_format[str(item_list["delv_num"])] = {}
                    Recv_QTY = PQTY = Rej_QTY = 0
                    EQTY = 1
                    if item_list["hustatus"] == settings.RECIEVED_QTY:
                        Recv_QTY = 1
                    if item_list["hustatus"] == settings.PENDING_QTY:
                        PQTY = 1
                    if item_list["hustatus"] == settings.REJECTED_QTY:
                        Rej_QTY = 1
                else:
                    EQTY = indata_format[str(item_list["delv_num"])]["EQTY"] + 1
                    if item_list["hustatus"] == settings.RECIEVED_QTY:
                        Recv_QTY = indata_format[str(item_list["delv_num"])]["Recv_QTY"] + 1
                    if item_list["hustatus"] == settings.PENDING_QTY:
                        PQTY = indata_format[str(item_list["delv_num"])]["PQTY"] + 1
                    if item_list["hustatus"] == settings.REJECTED_QTY:
                        Rej_QTY = indata_format[str(item_list["delv_num"])]["Rej_QTY"] + 1

                indata_format[str(item_list["delv_num"])]["EQTY"] = EQTY
                indata_format[str(item_list["delv_num"])]["Recv_QTY"] = Recv_QTY
                indata_format[str(item_list["delv_num"])]["PQTY"] = PQTY
                indata_format[str(item_list["delv_num"])]["Rej_QTY"] = Rej_QTY

        pars_api_output['Data'] = {"pars": indata_format,"actual": api_output}

        if api_output['Success'] == 'true':
            pars_api_output['msg'] = settings.SUCCESS_MSG_PULL

        pars_api_output['Success'] = api_output['Success']
        pars_api_output['Error'] = api_output['Error']
        logger.debug("unparsing get trip data : "+ str(pars_api_output))
        return pars_api_output
    except Exception as e:
        logger.error("get trip data : " + str(e))

def hurejection(api_output):
    #api_out_json = json.dumps(api_output)
    try:
        if "Error" in api_output.keys():
            if api_output["Error"] == "true":
                return {"Error":"true"}
            else:
                api_output["msg"] = settings.SUCCESS_MSG_PUSH
                return api_output
        else:
            return api_output
    except KeyError as e:
        logger.warning("hu-rejection unparsing key error %s", e)
        raise APIUnParsingError("hu-rejection un-parsing error")

def sendcompletetrip(api_output):
    """ send complete trip api reply
    """
    try:
        if "Error" in api_output.keys():
            if api_output["Error"] == "true":
                return {"Error":"true"}
            else:
                api_output["msg"] = settings.SUCCESS_COMPLETE_TRIP
                return api_output
        else:
            return api_output
    except KeyError as e:
        logger.warning("unparsing key error %s", e)
        raise APIUnParsingError("trip un-parsing error")

def getstorelist(api_output):
    """ get store list api reply
    """
    try:
        if "Error" in api_output.keys():
            if api_output["Error"] == "true":
                return {"Error":"true"}
            else:
                if "Message" in api_output.keys():
                    api_output["msg"] = api_output["Message"]
                else:
                    api_output["msg"] = settings.SUCCESS_GET_STORELIST
                return api_output
        else:
            return api_output
    except KeyError as e:
        logger.warning("unparsing key error %s", e)
        raise APIUnParsingError("getstorelist un-parsing error")

def getvendorlist(api_output):
    """ get store list api reply
    """
    try:
        if "Error" in api_output.keys():
            if api_output["Error"] == "true":
                return {"Error":"true"}
            else:
                if "Message" in api_output.keys():
                    api_output["msg"] = api_output["Message"]
                else:
                    api_output["msg"] = settings.SUCCESS_GET_VENDORLIST
                return api_output
        else:
            return api_output
    except KeyError as e:
        logger.warning("unparsing key error %s", e)
        raise APIUnParsingError("getstorelist un-parsing error")

def gethuoutward(api_output):
    """ get store list api reply
    """
    try:
        if "Error" in api_output.keys():
            if api_output["Error"] == "true":
                return {"Error":"true"}
            else:
                if "Message" in api_output.keys():
                    api_output["msg"] = api_output["Message"]
                else:
                    api_output["msg"] = settings.SUCCESS_GET_OUTWARD
                return api_output
        else:
            return api_output
    except KeyError as e:
        logger.warning("unparsing key error %s", e)
        raise APIUnParsingError("gethuoutward un-parsing error")

def tagcirculation(api_output):
    """
    """
    try:
        if "Error" in api_output.keys():
            if api_output["Error"] == "true":
                return {"Error":"true"}
            else:
                if "Message" in api_output.keys():
                    api_output["msg"] = api_output["Message"]
                else:
                    api_output["msg"] = settings.SUCCESS_GET_OUTWARD
                return api_output
        else:
            return api_output
    except KeyError as e:
        logger.warning("unparsing key error %s", e)
        raise APIUnParsingError("tag circulation un-parsing error")

def bulkencoding(api_output):
    """
    """
    try:
        if "Error" in api_output.keys():
            if api_output["Error"] == "true":
                return {"Error":"true"}
            else:
                if "Message" in api_output.keys():
                    api_output["msg"] = api_output["Message"]
                else:
                    api_output["msg"] = settings.SUCCESS_ENCODING
                return api_output
        else:
            return api_output
    except KeyError as e:
        logger.warning("unparsing key error %s", e)
        raise APIUnParsingError("bulkencoding un-parsing error")

def getepcbulkencoding(api_output):
    """
    """
    try:
        if "Error" in api_output.keys():
            if api_output["Error"] == "true":
                return {"Error":"true"}
            else:
                if "Message" in api_output.keys():
                    api_output["msg"] = api_output["Message"]
                else:
                    api_output["msg"] = settings.SUCCESS_GET_OUTWARD
                return api_output
        else:
            return api_output
    except KeyError as e:
        logger.warning("unparsing key error %s", e)
        raise APIUnParsingError("tag getepcbulkencoding un-parsing error")

def bulkdecodingpwd(api_output):
    """
    """
    try:
        if "Error" in api_output.keys():
            if api_output["Error"] == "true":
                return {"Error":"true"}
            else:
                if "Message" in api_output.keys():
                    api_output["msg"] = api_output["Message"]
                else:
                    api_output["msg"] = settings.SUCCESS_GET_OUTWARD
                return api_output
        else:
            return api_output
    except KeyError as e:
        logger.warning("unparsing key error %s", e)
        raise APIUnParsingError("bulkencodingpwd un-parsing error")

def getepcencode(api_output):
    """
    """
    try:
        if "Error" in api_output.keys():
            if api_output["Error"] == "true":
                return {"Error":"true"}
            else:
                if "Message" in api_output.keys():
                    api_output["msg"] = api_output["Message"]
                else:
                    api_output["msg"] = settings.SUCCESS_MSG_PULL
                return api_output
        else:
            return api_output

    except KeyError as e:
        logger.warning("unparsing key error %s", e)
        raise APIUnParsingError("getepcencode un-parsing error")

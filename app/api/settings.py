GET ={
    
}
POST = {
"token" : "token",
# To upload encoding logs
"scancount" : "scancount",
# to get trip detail call api or to get hu data same api need to call
"gettriphudata" : "gettriphudata",
# HU rejection, in any process if hu is rejected then need to call api
"hurejection" : "hurejection",
# To get sgtin list for encode rfid tag and password to write data into rfid tag.
# get store lists
"getstorelist" : "getStoreList",
# get vendor list
"getvendorlist" : "getVendorList",
# To hu 'HUverificationn' call api to get hu level sku detail to verify
"gethuoutward" : "getHUDetails",

"bulkdecoding" : "bulkencode",
"bulkdecodingpwd" : "getaccesspwd",
# To upload encoding logs
"bulkencoding" : "bulkencode",
# After verification completed upload logs to server
"sendhuqty" : "sendHUQty",
# Tag Circulation logs upload
"tagcirculation" : "tagcirculation",
# if inward from vendor need to call following api
# To get sgtin list for encode rfid tag and password to write data into rfid tag.
"getepcforencode" : "getepcforencode",
# to upload HU inward completed call api
"completetripdata" : "sendCompletTripData",
# to upload & mark trip completed or cancel call api
"sendcompletetrip" : "sendCompletTrip"
}
SUCCESS_MSG_PUSH = "Scanned data push to server"
SUCCESS_MSG_PULL = "Successfully Data received from server"

# send complete trip ..Complete grn
SUCCESS_COMPLETE_TRIP = "Trip Completed successfully"

# inward get trip hu from server
# huStatus value characters
RECIEVED_QTY = "C"
PENDING_QTY = "P"
REJECTED_QTY = "R"

# outward
SUCCESS_GET_STORELIST = "Successfully fetch storelist"
SUCCESS_GET_VENDORLIST = "Successfully fetch vendorlist"

# get hu details
SUCCESS_GET_OUTWARD = "Successfully get hu details"

SUCCESS_ENCODING = "Successfully uploaded encoding data"

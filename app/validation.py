import time
import logging
import logging.handlers as handlers

from datetime import datetime


logger = logging.getLogger(__name__)

class Validator:
    """Validation datettime access vehicle and block vehicle
    """
    def __init__(self) -> None:
        # print("validation.py class Validator init")
        pass

    def datecheck(self, fromdate, todate) -> bool:
        """
        this used for access date and block date,
        block time it will reverse.
        "fromDate": "01-02-2022",   # vehicle access date from to some date,
                                    # - use "A" use for all time access
        "toDate": "05-02-2022",     # "A" use for all days access
        "weekDay": "1,3,6",         # vehicle access day sunday to saturaday
        
        """
        try:
            valid = False
            # print(fromdate, todate)           
            
            today= time.strftime("%Y-%m-%d %H:%M:%S")            
            
            date_now = time.strptime(today,"%Y-%m-%d %H:%M:%S")            
            
            fromdate = fromdate.replace("0000-00-00","0001-01-01")
            from_date = time.strptime(fromdate ,"%Y-%m-%d %H:%M:%S")
            
            todate = todate.replace("00:00:00","23:59:59")   
            todate = todate.replace("0000-00-00","0001-01-01")         
            to_date = time.strptime(todate, "%Y-%m-%d %H:%M:%S")            

            valid = from_date <= date_now <= to_date

            return valid
        
        except Exception as e:            
            logger.error(e)
            print("access validation exception in datecheck > ",e)
            return valid

    def timecheck(self, fromTime, toTime) -> bool:
        """ 
        this used for access time and block time,
        block time it will reverse.
        access : True for access vehicle
        block : False for access vehicle and vise-versa
        "fromTime": "09:30",        # access vehicle from time to some time
        "toTime": "15:30"
        """
        try:
            valid = False
            
            today_from= time.strftime("%Y-%m-%d {}".format(fromTime))            
            
            today_to= time.strftime("%Y-%m-%d {}".format(toTime))
            
            today= time.strftime("%Y-%m-%d %H:%M:%S")
            
            from_time = time.strptime(today_from,"%Y-%m-%d %H:%M:%S")
            
            to_time = time.strptime(today_to,"%Y-%m-%d %H:%M:%S")
            
            datetime_now = time.strptime(today,"%Y-%m-%d %H:%M:%S")
           
            valid = from_time <= datetime_now <= to_time
            
            return valid
        
        except Exception as e:            
            logger.error(e)
            print("access validation exception in timecheck > ",e)
            return valid

    def daycheck(self, _day) -> bool:
        """
        checking blocked or not tagid
        True = blocked vehicle
        monday = 1......sunday = 7 means datetime.today().weekday() + 1
        """
        try:
            valid = False
            if "A" in _day or str(datetime.today().weekday()+1) in _day:
                return True
            return valid
        except Exception as e:
            logger.error(e)
            print("access validation exception in daycheck > ",e)
            return valid

    # def dayBlockCheck(self, _day) -> bool:


    def run(self, data) -> bool:
        """
        access vehicle validation
        """
        try:
            # print("inside validator : "+str(data))
            valid = False
           # self.datecheck(data[0][6], data[0][7])
            #self.timecheck(data[0][8], data[0][9])
            # access 
            #[2, '30361F46981138174876EDE0', 'None', '24-03-2022 16:53:32', 'None', 'None', 
            # '01-01-2023 00:00:00', '26-01-2023 00:00:00', '14:23:00', '20:58:00', 'A', 
            # '01-01-2023 00:00:00', '26-01-2023 00:00:00', '14:23:00', '20:58:00', '5,', 1]
           # print(self.datecheck(data[11], data[12]),self.timecheck(data[13], data[14]))
            # if data list is not in required format, make it in required format
            # data[0] = 2 -sr.no. not required here
            # data[1] = '30361F46981138174876EDE0' -tagId not required here
            # data[2] = 'None' -owner name not required here
            # data[3] = '24-03-2022 16:53:32' -registration date time not required here
            # data[4] = 'None' -flat no. not required here
            # data[5] = 'None' -vehicle no. not required here


            # data[6] = '2023-12-20 00:00:00' -access from date
            # data[7] = '2024-12-21 00:00:00' -access to date
            # data[8] = '14:23:00' -access from time
            # data[9] = '20:58:00' -access to time
            # data[10] = 'A' or '1' or '2-3-5' -access days 'A' means all days access

            # data[11] = '2023-12-20 00:00:00' -block from date
            # data[12] = '2024-12-21 00:00:00' -block to date
            # data[13] = '14:23:00' -block from time
            # data[14] = '20:58:00' -block to time
            # data[15] = 'A' or '1' or '2-3-5' -block days 'A' means all days block

            # data[16] = '0' or '1' -            
           
            # if data[6] == "00-00-0000 00:00:00" and data[7] == "00-00-0000 00:00:00":
            if data[6] == "0000-00-00 00:00:00" and data[7] == "0000-00-00 00:00:00":
                return True
                                    
            # if (data[11] == "00-00-0000 00:00:00" and data[12] == "00-00-0000 00:00:00") or data[16] and self.datecheck(data[11], data[12]) is False or (self.datecheck(data[11], data[12]) is True and (self.timecheck(data[13], data[14]) is False or self.daycheck(data[15]) is False)):
            # if (data[11] == "0000-00-00 00:00:00" and data[12] == "0000-00-00 00:00:00") or data[16] and self.datecheck(data[11], data[12]) is False or (self.datecheck(data[11], data[12]) is True and (self.timecheck(data[13], data[14]) is False or self.daycheck(data[15]) is False)):
            #     if self.datecheck(data[6], data[7]) and self.timecheck(data[8], data[9]):
            #         print("access done!")
            #         if self.daycheck(data[10]):
            #             valid = True               
            # return valid
            if (data[11] == "0000-00-00 00:00:00" and data[12] == "0000-00-00 00:00:00"):
              if self.datecheck(data[6], data[7]) and self.timecheck(data[8], data[9]):
                if self.daycheck(data[10]):  
                    valid = True
            else:
                if self.datecheck(data[11], data[12]) and self.timecheck(data[13], data[14]):
                    if self.daycheck(data[15]):  
                        valid = False
                    else:
                        valid = True
                else:
                    valid = True

            return valid

        except Exception as e:
            logger.error(e)
            print(e)

if __name__=="__main__":
    try:
        msg = ((1, "23424r35353464", "Ayush", "datetime", "G-123", "MH02GH4567",
        "11-02-2022 00:00:00", "22-02-2022 00:00:00","11:25:00","12:28:00",
        "A",
        "17-02-2022 00:00:00", "26-02-2022 00:00:00","10:23:00","17:23:00",
        "1",
        1),)
        data = Validator()
        status = data.run(msg)
        print(status)
    except Exception as e:
        logger.error(e)
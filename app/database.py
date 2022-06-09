#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from crypt import methods
from operator import le
import sqlite3
import logging
from logging import handlers

from .utils import get_datetime_stamp,read_local_config
from werkzeug.security import generate_password_hash, check_password_hash
from .settings import PATH_FILE_LOG,CONFIG_TOML_FILE
# from .main import TR_ACC1

#DATABASE_PATH = "itekAVI.sqlite3"
#####################################################################
# Setup logger
DB_PATH = PATH_FILE_LOG
PATH_FILE_LOG += "logs/"

formatter = logging.Formatter(
    "%(asctime)s::%(levelname)s::%(filename)s::%(lineno)d %(message)s"
)
logger = logging.getLogger("db")
logger.setLevel(logging.DEBUG)

# time logger
handler = handlers.TimedRotatingFileHandler(
    PATH_FILE_LOG + "db/db.log",
    when="midnight",
    backupCount=10,
    interval=1,
)
handler.setFormatter(formatter)
logger.addHandler(handler)
#handler.doRollover()

class Database:
    VEH_BLOCK = 0
    VEH_ACCESS = 1
    def __init__(self, settings):
        # print(" database.py class Database init")
        self._db_txn = "txndata"
        self._db_success = "success"
        self._db_failed = "failed"
        self._db_sys_status = "status"

        self._tb_userlists = "UserList"
        self._tb_config = "Config"
        self._tb_transaction = "Transactions"
        self._tb_loginuser = "User"
        self._tb_authority = "Authority"

        self._default_table = None
        self._default_col = "TAG_ID"
        self._datetime_col = "DATE_TIME"
        self._tag_id = None
        self._whr_col = "TAG_ID"
        self._whr_col_val = None 
        # print("database init")
        # print(settings)
        self._db_path = DB_PATH + settings["db_path"]
        self._max_trans_count = settings["max_trans_count"]
        self._max_vehicle_count = settings["max_vehicle_count"]
       
        # localconfig = read_local_config(CONFIG_TOML_FILE)        
        # print(localconfig)

        # create database
        self._db = sqlite3.connect(self._db_path, check_same_thread=False)
        self._cursor = self._db.cursor()

        try:
            self._cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS """
                + self._tb_userlists
                + """(
                SR_NO INTEGER PRIMARY KEY,
                TAG_ID TEXT, 
                OWNER_NAME TEXT,
                DATE_TIME DATETIME, 
                FLAT_NO TEXT, 
                VEHICLE_NO TEXT, 
                FROM_DATE DATE, TO_DATE DATE, 
                FROM_TIME TIME, TO_TIME TIME, 
                WEEK_DAY TEXT,
                BLK_FROM_DATE DATE, BLK_TO_DATE DATE, 
                BLK_FROM_TIME TIME, BLK_TO_TIME TIME, 
                BLK_WEEK_DAY TEXT,
                AUTH INTEGER);"""
            )
        except Exception:
            logger.exception("while creating %s table", self._tb_userlists)

        try:
            self._cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS """
                + self._tb_transaction
                + """ (
                SR_NO INTEGER PRIMARY KEY,
                TAG_ID TEXT, 
                DATE_TIME DATETIME,
                ANT_NAME TEXT,
                TR_FLAG TEXT);"""
            )
        except Exception:
            logger.exception("while creating %s table", self._tb_transaction)

        try:
            self._cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS """
                + self._tb_config
                + """(
                SR_NO INTEGER PRIMARY KEY AUTOINCREMENT,
                NAME TEXT, 
                VALUE TEXT);"""
            )   
        except Exception:
            logger.exception("while creating %s table", self._tb_config)

        try:
            self._cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS """
                + self._tb_authority
                + """ (
                SR_NO INTEGER PRIMARY KEY AUTOINCREMENT,
                AUTH INTEGER NOT NULL UNIQUE, 
                TITLE TEXT);"""
            )   
        except Exception:
            logger.exception("while creating %s table", self._tb_authority)
        
        try:
            self._cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS """
                + self._tb_loginuser
                + """(
                SR_NO INTEGER PRIMARY KEY AUTOINCREMENT,
                NAME TEXT,
                DATE_TIME DATETIME,
                EMAIL TEXT,
                PASSWD TEXT,
                AUTH INTEGER);"""
            )   
        except Exception:
            logger.exception("while creating %s table", self._tb_loginuser)

        self._db.commit()
        self._cursor.close()

        # following steps are performed when RiPi is new and project is just loaded in it
        # there is no database in RiPi so 1 default login user is created in it to login for first time
        # check if database has login user 
        

    def dbconnection(self):
        try:
            self._db = sqlite3.connect(self._db_path, check_same_thread=False)
            self._cursor = self._db.cursor()
        except Exception:
            logger.exception("while connecting %s database", self._db_path)

    # close sqlite connection
    def dbclose(self):
        if self._db:
            self._db.commit()
            self._db.close()
            
    def query(self, query):
        # logger.debug("excecute query > "+str(query))
        data_list = None
        try:
            self._cursor.execute(query)
        except Exception as e:
            logger.exception("while get data from!")
        return data_list

    def get(self):
        logger.debug("fetch all data!")
        data_list = None
        try:
            data_list = self._cursor.fetchall()
            # ((0,3,4),())
           # print(data_list)
        except Exception:
            logger.exception("while fetch all data!")
        return data_list

    def getone(self):
        logger.debug("fetch one data!")
        data_list = None
        try:
            data_list = self._cursor.fetchone()
            # (0,12,3)
        except Exception:
            logger.exception("while fetch one data!")
        return data_list[0]

    def get_from(self, table_name=None):
        logger.debug("select all data!")
        data_list = None
        try:
            if table_name is None:
                table_name = self._default_table
            self._cursor.execute("SELECT * FROM {}".format(table_name))
            data_list = self._cursor.fetchall()
        except Exception:
            logger.exception("while get data from!")
        return data_list
    
    def get_from_selectedcol(self, table_name=None, columns="*"):
        logger.debug("selected columns data!")
        data_list = None
        try:
            if table_name is None:
                table_name = self._default_table
            self._cursor.execute("SELECT {} FROM {}".format(columns, table_name))
            data_list = self._cursor.fetchall()
        except Exception:
            logger.exception("while selected columns data!")
        return data_list

    def _check_whr(self, whr_name, whr_value, table_name):
        data = lambda name, val: val if name is None else name        
        return data(whr_name, self._whr_col), data(whr_value, self._whr_col_val), data(table_name, self._default_table)

    def get_from_whr(self, table_name=None, whr_name=None, whr_value=None):
        logger.debug("select all data from column!")
        data_list = None
        try:
            whr_name, whr_value, table_name = self._check_whr(whr_name, whr_value, table_name)
            self._cursor.execute(
                "SELECT * FROM {} where {}={}"
                .format(table_name, whr_name, whr_value)
                )
            data_list = self._cursor.fetchall()
        except Exception:
            logger.exception("while get data from!")
        return data_list

    # update data
    def update_rows(self, col_name, value, table_name=None, whr_name=None, whr_value=None):
        logger.debug("update transaction!")
        try:
            whr_name, whr_value, table_name = self._check_whr(whr_name, whr_value, table_name)
            
            # self._cursor.execute(
            #     "UPDATE {} SET {}='{}' WHERE {}='{}'".format(
            #         table_name, 
            #         col_name, 
            #         value, 
            #         whr_name, 
            #         whr_value)
            # )
            self._cursor.execute(
                f"UPDATE {table_name} SET {col_name} = '{value}' WHERE {whr_name} = '{whr_value}'"
            )
            # print("table_name >",table_name)
            # print("col_name >",col_name)
            # print("value >",value)
            # print("whr_name >",whr_name)
            # print("whr_value >",whr_value)
            # print('\n\r')

        except Exception:
            print("update_row exception")
            logger.exception("while update rows")
    
    def delete_rows(self, table_name=None, whr_name=None, whr_value=None):
        logger.debug("delete rows")
        try:
            whr_name, whr_value, table_name = self._check_whr(whr_name, whr_value, table_name)
            self._cursor.execute(
                "DELETE FROM {} WHERE {}='{}'".format(table_name, whr_name, whr_value)
            )
        except Exception:
            logger.exception("while delete rows")

    def get_count(self, table_name=None, whr_name=None, whr_value=None):
        logger.debug("get count rows!")
        count = 0
        try:
            whr_name, whr_value, table_name = self._check_whr(whr_name, whr_value, table_name)
            # print(whr_name, whr_value, table_name)
            if whr_name is None or whr_value is None:
                self._cursor.execute(
                    "SELECT COUNT(*) FROM {}".format(table_name)
                )
            else:
                self._cursor.execute(
                    "SELECT COUNT(*) FROM {} WHERE {}='{}'".format(table_name, whr_name, whr_value)
                )            
            result = self._cursor.fetchone()
           # print(result)
            count = result[0]
        except Exception:
            logger.exception("while get count")
        return count

    def datetime_filter(self, table_name=None, whr_col1_name=None, whr_col1_value=None):
        logger.debug("get datetime_filter!")
        try:
            whr_col1_name, whr_col1_value, table_name = self._check_whr(whr_col1_name, whr_col1_value, table_name)
            
            dates = get_datetime_stamp("%Y-%m-%d")[:10] + "%"
                       
            self._cursor.execute(
                f"select COUNT(*) from {table_name} where DATE_TIME like '{dates}' AND {whr_col1_name} = '{whr_col1_value}'"
            )
        except Exception as e:
            print("while getting date time filter >",str(e))
            logger.exception("while getting date time filter >",str(e))

    def datetime_filter_multiColm(self, table_name=None, whr_col1_name=None, whr_col1_value=None, whr_col2_name=None, whr_col2_value=None):
        logger.debug("get datetime_filter_multicolmn!")
        try:
            whr_col1_name, whr_col1_value, table_name = self._check_whr(whr_col1_name, whr_col1_value, table_name)
            whr_col2_name, whr_col2_value, table_name = self._check_whr(whr_col2_name, whr_col2_value, table_name)
            dates = get_datetime_stamp("%Y-%m-%d")[:10] + "%"
            
            self._cursor.execute(
                f"select COUNT(*) from {table_name} where DATE_TIME like '{dates}' AND {whr_col1_name} = '{whr_col1_value}' AND {whr_col2_name} = '{whr_col2_value}'"
            )
        except Exception as e:
            print("while getting date time filter multiple columns >",str(e))
            logger.exception("while getting date time filter multiple columns >",str(e))

   
    # save transactions in database in table transactions
    def save_transaction(self, tag_id, ant_name, tr_flag):
        logger.debug("save transaction tag id {}".format(tag_id))
        txn_datetime = get_datetime_stamp("%Y-%m-%d %H:%M:%S")
        try:
            self.dbconnection()
            self._cursor.execute(
                "INSERT INTO {} (TAG_ID, DATE_TIME, ANT_NAME, TR_FLAG)VALUES('{}', '{}', '{}', '{}')".format(self._tb_transaction, tag_id, txn_datetime, ant_name, tr_flag)
            )
            self.dbclose()
        except Exception as e:
            print("error while saving transaction >",str(e))
            logger.exception("while save transaction entry")


        """21/04/2022
        here make one more save transaction function, keep th eabove one as it is,
        in this save transaction function, save the transaction in auto rotating format
        if transactions reach max limit, delete the top most transaction and add the new transaction
        use create trigger, delete, insert properly
       
        """
    def save_transaction_withLimit(self, tag_id, ant_name, tr_flag, limit):
        logger.debug("save transaction with limit tag id {}".format(tag_id))
        txn_datetime = get_datetime_stamp("%Y-%m-%d %H:%M:%S")

        try:
            self.dbconnection()
        # get how many transactions are in transaction table
            self._cursor.execute(
                    "SELECT COUNT(*) FROM {}".format(self._tb_transaction)
                )
            trCount = self._cursor.fetchone()
            # print("trCount is > ",trCount[0])
            if trCount[0] >= limit:
                self.query("select SR_NO from {} ORDER BY SR_NO LIMIT 1".format( self._tb_transaction))
                top_srno = self._cursor.fetchone()
                # print("top_srno > ",top_srno)
                self._cursor.execute(
                    "DELETE FROM {} LIMIT 1".format(self._tb_transaction)
                    )
                self._cursor.execute(
                    "INSERT INTO {} (TAG_ID, DATE_TIME, ANT_NAME, TR_FLAG)VALUES('{}', '{}', '{}', '{}')".format(self._tb_transaction, tag_id, txn_datetime, ant_name, tr_flag)
                    )
                # self._cursor.execute(
                #     "INSERT INTO {} (SR_NO, TAG_ID, DATE_TIME, ANT_NAME, TR_FLAG)VALUES('{}', '{}', '{}', '{}', '{}')".format(self._tb_transaction, top_srno[0], tag_id, txn_datetime, ant_name, tr_flag)
                #     )
            else:
                self._cursor.execute(
                    "INSERT INTO {} (TAG_ID, DATE_TIME, ANT_NAME, TR_FLAG)VALUES('{}', '{}', '{}', '{}')".format(self._tb_transaction, tag_id, txn_datetime, ant_name, tr_flag)
                    )
            self.dbclose()

        except Exception as e:
            self.dbclose()
            print("error while saving transaction with limit >",str(e))        
        


    # get data from date-time to date-time (not used yet)
    def get_betn_time(self, table_name, fromdate, todate):
        """
        get data filtered between from-datetime  and to-datetime
        """
        logger.debug("get data from date to date time")
        txn_datetime = get_datetime_stamp()
        try:
            self._cursor.execute(
                "select * from {} where date(datetime(timestamp, '{}'))  between {} and {}"
                .format(table_name, self._default_datetime, fromdate, todate)
            )
            data_list = self._cursor.fetchall()
        except Exception:
            logger.exception("while GET data from date to date")
        return data_list

    def vehicle_access(self, tagid):
        logger.debug("select all data from column!")
        data_list = 0
        try:
            self.dbconnection()
            self.query(
                "SELECT * FROM {} where {}='{}'".format(self._tb_userlists, "TAG_ID", tagid)
                )
            data_list = self.get()
            self.dbclose()
        except Exception:
            logger.exception("while get data from!")
        return data_list
    
    @staticmethod
    def avil_check(data, key):
        if key in data.keys():
            return data[key]
        else:
            return None
    
    @staticmethod
    def avil_date(data, key):
        if key in data.keys():            
            return data[key]
        else:
            return "0000-00-00 00:00:00"

    @staticmethod
    def avil_time(data, key):
        if key in data.keys():
            return data[key]
        else:
            return "00:00:00"

    @staticmethod
    def avil_day(data, key):
        if key in data.keys() and data[key] != '' and data[key] != None:
            return data[key]
        else:
            return "A"

    @staticmethod
    def avil_blkday(data, key):
        if key in data.keys() and data[key] != '' and data[key] != None:            
            return data[key]
        else:            
            return "0"

    @staticmethod
    def auth_check(data, key, auth):
        if key in data.keys():
            return data[key]
        else:
            return auth

    def add_user_vehicle(self, data_frame):
        logger.debug("inserting user vehicle !")
        datetime = get_datetime_stamp("%Y-%m-%d %H:%M:%S")
        return_val = 0
        try:
            # print("data frame database.py -> add_user_vehicle function")
            # print(data_frame)
            # print("in add_user_vehicle")
            self._default_table = self._tb_userlists
            self.dbconnection()
            vehicle_count = self.get_count(table_name=self._tb_userlists)
            # print("total vehicles in DB ", vehicle_count)
            if vehicle_count < self._max_vehicle_count:
                for _frame in data_frame:
                    # check if _frame tagId is not equal to none
                    if _frame["tagId"] != None:
                        found_tag = self.get_count(table_name=self._tb_userlists, whr_name="TAG_ID", whr_value=_frame["tagId"])
                        # print("user count :" +str(found_tag))                        
                        if vehicle_count < self._max_vehicle_count:
                            if found_tag == 0:
                                inser_query = """INSERT INTO """ + self._tb_userlists + """ (TAG_ID, 
                                    OWNER_NAME,
                                    DATE_TIME , 
                                    FLAT_NO, 
                                    VEHICLE_NO, 
                                    FROM_DATE , TO_DATE , 
                                    FROM_TIME , TO_TIME , 
                                    WEEK_DAY,
                                    BLK_FROM_DATE , BLK_TO_DATE , 
                                    BLK_FROM_TIME , BLK_TO_TIME , 
                                    BLK_WEEK_DAY,
                                    AUTH) VALUES """
                                query = inser_query +"('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', {})".format(
                                _frame["tagId"],
                                self.avil_check(_frame,"ownerName"),
                                datetime,
                                self.avil_check(_frame,"flatNo"), 
                                self.avil_check(_frame,"vehicleNo"),
                                self.avil_date(_frame,"fromDate"),self.avil_date(_frame,"toDate"),
                                self.avil_time(_frame,"fromTime"),self.avil_time(_frame,"toTime"),
                                self.avil_day(_frame,"weekDay"),
                                self.avil_date(_frame,"blkFromDate"),
                                self.avil_date(_frame,"blkToDate"),
                                self.avil_time(_frame,"blkFromTime"),
                                self.avil_time(_frame,"blkToTime"),
                                self.avil_blkday(_frame,"blkWeekDay"),
                                self.auth_check(_frame,"auth",self.VEH_ACCESS)                    
                                )
                            # print(query)
                                self._cursor.execute(query)
                            elif found_tag == 1:
                                # print("Tag is already in DB >",_frame["tagId"])
                                self._whr_col_val = _frame["tagId"]                    
                                self.update_rows("OWNER_NAME", self.avil_check(_frame,"ownerName"))
                                self.update_rows("FLAT_NO", self.avil_check(_frame,"flatNo"))
                                self.update_rows("VEHICLE_NO", self.avil_check(_frame,"vehicleNo"))

                                self.update_rows("FROM_DATE", self.avil_date(_frame,"fromDate"))
                                self.update_rows("TO_DATE", self.avil_date(_frame,"toDate"))
                                self.update_rows("FROM_TIME", self.avil_time(_frame,"fromTime"))
                                self.update_rows("TO_TIME", self.avil_time(_frame,"toTime"))
                                self.update_rows("WEEK_DAY", self.avil_day(_frame,"weekDay"))

                                self.update_rows("BLK_FROM_DATE", self.avil_date(_frame,"blkFromDate"))
                                self.update_rows("BLK_TO_DATE", self.avil_date(_frame,"blkToDate"))
                                self.update_rows("BLK_FROM_TIME", self.avil_time(_frame,"blkFromTime"))
                                self.update_rows("BLK_TO_TIME", self.avil_time(_frame,"blkToTime"))
                                self.update_rows("BLK_WEEK_DAY", self.avil_day(_frame,"blkWeekDay"))
                                self.update_rows("AUTH",self.auth_check(_frame,"auth",self.VEH_ACCESS))
                            return_val = 1
                        else:
                            return_val = 2
                            break
                
            else:
                return_val = 2

            self.dbclose()
            return return_val
        except Exception:
            self.dbclose()
            logger.exception("while adding vehicle!")


        
    def update_user_vehicle(self, data_frame, block_data=False):
        """
        block_data for block credientials filled
        """
        logger.debug("update user vehicle data!")
        # print("data frame to update user")
        # print(data_frame)
        try:
            print("in update_user_vehicle")
            self.dbconnection()
            
            for _frame in data_frame:
                self._whr_col_val = _frame["tagId"]
                self._default_table = self._tb_userlists
                if self.get_count():
                    # self.update_rows("OWNER_NAME", self.avil_check(_frame,"ownerName"))
                    # self.update_rows("FLAT_NO", self.avil_check(_frame,"flatNo"))
                    # self.update_rows("VEHICLE_NO", self.avil_check(_frame,"vehicleNo"))
                    if block_data:
                        # print("data frame while blocking vehicle")
                        # print(data_frame)
                        # print((_frame["tagId"]))
                        # print((_frame["fromDate"]))
                        # print((_frame["toDate"]))
                        # print((_frame["fromTime"]))
                        # print((_frame["toTime"]))
                        # print((_frame["weekDay"]))
                        
                        
                        self.update_rows("BLK_FROM_DATE", self.avil_date(_frame,"fromDate"))
                        self.update_rows("BLK_TO_DATE", self.avil_date(_frame,"toDate"))
                        self.update_rows("BLK_FROM_TIME", self.avil_time(_frame,"fromTime"))
                        self.update_rows("BLK_TO_TIME", self.avil_time(_frame,"toTime"))
                        self.update_rows("BLK_WEEK_DAY", self.avil_blkday(_frame,"weekDay"))
                    
                    else:
                        self.update_rows("FROM_DATE", self.avil_date(_frame,"fromDate"))
                        self.update_rows("TO_DATE", self.avil_date(_frame,"toDate"))
                        self.update_rows("FROM_TIME", self.avil_time(_frame,"fromTime"))
                        self.update_rows("TO_TIME", self.avil_time(_frame,"toTime"))
                        self.update_rows("WEEK_DAY", self.avil_day(_frame,"weekDay"))
            
            # self._whr_col_val made to None because it is used in dashboard display and 
            # if kept with tag id, it shows only one user in vehicle list 
            self._whr_col_val = None
            self.dbclose()

        except Exception as e:
            print("while updating user vehicle id {}! {}".format(str(_frame),str(e)))
            logger.warn("while updating user vehicle id {}! {}".format(str(_frame),str(e)))

    def block_user_vehicle(self, data_frame):
        logger.debug("block the user!")
        try:            
            self.update_user_vehicle(data_frame, block_data=True)
        except Exception:
            logger.warn("while blocking user vehicle!")

    def delete_user_vehicle(self, tagidlist):
        logger.debug("delete permenantly user!")
        try:
            print("in delete_user_vehicle")
            self.dbconnection()
            for tagid in tagidlist:
                if self.get_count(self._tb_userlists, "TAG_ID", tagid):
                    self.delete_rows(self._tb_userlists, "TAG_ID", tagid)
            # add one step here, if database is empty after delete, set sr. no. to zero
            # self.alter_table(self._tb_userlists)
            self.dbclose()
        except Exception:
            logger.warn("while deleting user vehicle id {}!".format(tagid))
    
    def alter_table(self, table_name):
        logger.debug("alter table's sr.no. after deleting vehicle")
        try:
            self._cursor.execute("ALTER TABLE {} AUTOINCREMENT=1".format(table_name))

        except Exception as e:
            print("error while altering table {} > {}".format(table_name,str(e)))
            logger.warn("while altering table {}".format(table_name))

    def get_userlist(self):
        logger.debug("get data from userlist!")
        allusers = []
        try:
            self.dbconnection()
            allusers = self.get_from(self._tb_userlists)
            self.dbclose()
        except Exception:
            logger.warn("while getting userlist!")
        return allusers

    def get_tanslist(self, fromdate, todate):
        logger.debug("get data from trans vehicle list!")
        alldata = []
        try:
            self.dbconnection()
            self.query("select * from {} where DATE_FORMAT(substring(DATE_TIME, 1, 10),'%d-%m-%Y') BETWEEN  '{}' AND '{}'".format(self._tb_transaction, fromdate, todate))
            alldata = self.get()
            self.dbclose()
        except Exception:
            logger.warn("while getting userlist!")
        return alldata

    def get_datefilter_value(self, table_name, fromdate, todate, whr_name, whr_value=None):
        logger.debug("get data from table where datetime!")
        alldata = []
        fromdate=fromdate[6:10] + '-' + fromdate[3:5] + '-' + fromdate[:2] + fromdate[10:]
        todate=todate[6:10] + '-' + todate[3:5] + '-' + todate[:2] + todate[10:]
        try:
            if whr_value == None:
                whr_value = "%"
            # print(fromdate, todate)
            self.dbconnection()
            # self.query("select * from {} where (STRFTIME('%d-%m-%Y %H:%M:%S', DATE_TIME) BETWEEN  '{}' AND '{}') and {} like '{}'".format(table_name, fromdate, todate, whr_name, whr_value))
            # self.query("select * from {} where (DATE_TIME BETWEEN  '{}' AND '{}') and {} like '{}'".format(table_name, fromdate, todate, whr_name, whr_value))
            
            self.query("select * from {} where (DATE_TIME BETWEEN '{}' AND '{}') and {} like '{}'".format(table_name, fromdate, todate, whr_name, whr_value))
            
            alldata = self.get()
            self.dbclose()
        except Exception:
            logger.warn("while getting userlist!")
        return alldata

    def getvehicle_logs(self, fromdate, todate, antName):
        logger.debug("get data from trans vehicle logs!")
        alldata = []
        try:
            if antName == "Select All":
                antName = "%"
            else:
                antName = antName + "%"
            alldata = self.get_datefilter_value(
                self._tb_transaction, fromdate +" 00:00:00", todate+" 23:59:59", whr_name="ANT_NAME", whr_value=antName
                )
        except Exception:
            logger.warn("while getting userlist!")
        return alldata

    def get_dashboardlogs(self, antNames : list):
        """
        return format : {'usercount': 2, 'ants': {'IN': (43, '30361F46981138174876EDE0', '11/03/2022 15:17:01', 'IN', None)}}
        """
        logger.debug("getting dashboard data!")
        alldata = {}
        default_count = [(0, '-', '-', '-', None)]
        # self._
        try:
            self.dbconnection()
            usercount = self.get_count(self._tb_userlists)
            alldata["usercount"] = usercount
           # print(alldata, antNames)
            alldata["ants"] = {}
            for ants in antNames:
                if ants != "NA":
                    # this query will give the last entry of database, whichever the last entry that 1 entry will be returned
                    self.query("select * from {} where ANT_NAME = '{}' ORDER BY SR_NO DESC LIMIT 1".format( self._tb_transaction, ants))
                    dataall = self.get()
                    # print(dataall)
                    
                    if len(dataall) > 0:
                        # self.datetime_filter(self._tb_transaction, 
                        #                         whr_col1_name="ANT_NAME", whr_col1_value=ants                        #                         
                        #                         )
                        self.datetime_filter_multiColm(self._tb_transaction, 
                                                        whr_col1_name="ANT_NAME", whr_col1_value=ants, 
                                                        whr_col2_name="TR_FLAG", whr_col2_value="Authorized"
                                                        ) #"Authorized"
                        today_count = self.getone()
                        # print("today_count >",today_count)
                        alldata["ants"][ants] = dataall
                        alldata["ants"][ants].append(today_count)
                    else:
                        alldata["ants"][ants] = default_count
                        alldata["ants"][ants].append(0)


            self.dbclose()
            # print(alldata)
            # 'ants': {'IN': [(43, '30361F46981138174876EDE0', '11/03/2022 15:17:01', 'IN', None), <today_count>]}
        except Exception as e:
            logger.warn("while getting dashboard data! - {}".format(str(e)))
        return alldata

    def get_taglists_name(self):
        logger.debug("getting tag lists name!")
        alldata = {}
        try:
            self.dbconnection()
            alldata = self.get_from_selectedcol(self._tb_userlists, "TAG_ID,OWNER_NAME")
            self.dbclose()
        except Exception as e:
            logger.warn("while getting tag lists name!! - {}".format(str(e)))
        return alldata

    def update_vehicle_accessblk(self, dataframe):
        logger.debug("update user vehicle data access /block!")
        try:
            if dataframe["accessBlk"] == '2':
                block_data=True
            else:
                block_data=False
            self.update_user_vehicle([dataframe], block_data=block_data)
            
        except Exception:
            logger.warn("while update user vehicle data access /block!")

class User(Database):
    BLOCK = 0
    SUPERADMIN = 1
    ADMIN = 2
    SIMPLEUSER = 3 
    def __init__(self, settings) -> None:
        # print("database.py class User init")
        try:
            Database.__init__(self, settings)
        except AttributeError as e:         
            logger.error("not found : "+str(e))
            raise AttributeError("not found")
        self.dbconnection()
        found_user = self.get_count(table_name=self._tb_loginuser)
        self.dbclose()
        if found_user == 0:
            self._create_user("iTEKAVI","Pi4@FsGt","info@infoteksoftware.com",1)
        
        self.dbconnection()
        found_user = self.get_count(table_name=self._tb_transaction)
        # DELETE FROM tbl_name WHERE NOT EXISTS in (SELECT id FROM tbl_name ORDER BY id LIMIT 100 );
        # delete from mytable order by id limit 1
        if found_user > self._max_trans_count:
            self._cursor.execute(
                "DELETE FROM {} ORDER BY '{}' LIMIT {}".format(self._tb_transaction,"SR_NO",(found_user - self._max_trans_count))
            )
            # self._cursor.execute(
            #     "DELETE FROM {} WHERE '{}' NOT EXISTS in (SELECT '{}' FROM {} ORDER BY '{}' LIMIT 100)".format(self._tb_transaction,"SR_NO","SR_NO",self._tb_transaction,"SR_NO")
            # )            
        self.dbclose()
    
    def _create_user(self, user, passwd, email=None, auth=SIMPLEUSER):
        logger.info("create new user > "+str(user))
        # print(user, passwd, email, auth)
        try:
            self.dbconnection()
            found_user = self.get_count(table_name=self._tb_loginuser, whr_name="NAME", whr_value=user)
           # print(found_user)
            if found_user == 0:
                self.query("INSERT INTO {} (NAME, DATE_TIME, PASSWD, EMAIL, AUTH) VALUES ('{}','{}','{}','{}',{})".format(self._tb_loginuser, user, get_datetime_stamp(), generate_password_hash(passwd, method='sha256'), email, auth))
            self.dbclose()
            if found_user == 0:
                return (1, "User Successfully Created!")
            else:
                return (0, "Already user Available!")
        except Exception as e:
            logger.error("while create user!" +str(e))

    def update_user(self,user,passwd):
        """
        """
        logger.info("updating login user " + str(user))
        try:
            self.dbconnection()
            found_user = self.get_count(table_name=self._tb_loginuser, whr_name="NAME", whr_value=user)
            if found_user == 1:
                # "UPDATE {} SET {}='{}' WHERE {}='{}'".format(table_name, col_name, value, whr_name, whr_value)
                # print("password formating")
                # print(generate_password_hash(passwd, method='sha256'))
                self.query("UPDATE {} SET {}='{}' WHERE {}='{}'".format(self._tb_loginuser,"PASSWD",generate_password_hash(passwd, method='sha256'),"NAME",user))
            else:
                self.dbclose()
                return (0, "User not available")
            
            self.dbclose()
            return (1, "User updated! ")
        except Exception as e:
            logger.error("while updating user >" + str(e))

                
        

    def _authorize(self, user=None, passwd=None):
        """_summary_

        Args:
            user (_type_, optional): _description_. Defaults to None.
            passwd (_type_, optional): _description_. Defaults to None.

        Returns:
            _type_: _description_
            
        """
        logger.info("check user authorization!")
        success = 0
        data_list = None
        try:
            self.dbconnection()
            self.query("SELECT PASSWD from {} where (EMAIL='{}' or NAME='{}')".format(self._tb_loginuser, user, user))
            user_passwd = self.getone()
            #print(user_passwd)
            if user_passwd and check_password_hash(user_passwd, passwd):
                self.query("SELECT * from {} where (EMAIL='{}' or NAME='{}')".format(self._tb_loginuser, user, user))
                data_list = self.get()
                #print(data_list)
            self.dbclose()
            if len(data_list) == 0 or data_list == None:
                data_list = "Athorization Failed!"
            else:
                success = 1
        except:
            logger.warn("while authorization!")
        return (success, data_list)
    
    def _set_permission(self, user, auth):
        logger.info("block or delete user!")
        try:
            self.dbconnection()
            self.update_rows(
                col_name="AUTH", 
                value=auth, 
                table_name=self._tb_loginuser, 
                whr_name="NAME", 
                whr_value=user
                )
            self.dbclose()
        except:
            logger.warn("while user block!")
    
    def _get_loginuser_list(self):
        logger.info("get user lists!")
        try:
            self.dbconnection()
            datalist = self.get_from(self._tb_loginuser)
            self.dbclose()
        except:
            logger.warn("while user block!")
        return datalist
    
    
    # def vehicle_access(self, tagid):
    #     logger.debug("select all data from column!")
    #     data_list = None
    #     try:
    #         self.dbconnection()
    #         self.query(
    #             "SELECT * FROM {} where {}='{}'".format(self._tb_userlists, "TAG_ID", tagid)
    #             )
    #         data_list = self.get()
    #         self.dbclose()
    #     except Exception:
    #         logger.exception("while get data from!")
    #     return data_list

    # def save_transaction(self, tag_id, ant_name):
    #     logger.debug("save transactions")
    #     txn_datetime = get_datetime_stamp()
    #     try:
    #         self.dbconnection()
    #         self.query(
    #             "INSERT INTO {} (TAG_ID, DATE_TIME, ANT_NAME)VALUES({}, {}, {})".format(self._tb_transaction, tag_id, txn_datetime, ant_name)
    #         )
    #         self.dbclose()
    #     except Exception:
    #         logger.exception("while save transaction entry")
"""
INSERT INTO UserList (TAG_ID, 
                OWNER_NAME,
                DATE_TIME, 
                FLAT_NO, 
                VEHICLE_NO, 
                FROM_DATE, TO_DATE, 
                FROM_TIME, TO_TIME, 
                WEEK_DAY,
                BLK_FROM_DATE, BLK_TO_DATE, 
                BLK_FROM_TIME, BLK_TO_TIME, 
                BLK_WEEK_DAY,
                AUTH) 
VALUES
("30361F46981138174876EDE0", "Ayush", "datetime", "G-123", "MH02GH4567",
        "11/02/2022", "22/02/2022","11:25","12:28",
        "A",
        "17/02/2022", "26/02/2022","10:23","17:23",
        "1",
        1);

"""
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import json
import argparse
import subprocess
from pathlib import Path

import sqlite3

APP_DESC = """
Export all tables in the database to respective .csv file.
"""


def get_tables(dbcon):
    tables = []
    for row in dbcon.execute("""SELECT name FROM sqlite_master WHERE type='table';"""):
        if not row[0].startswith("sqlite"):
            tables.append(row[0])

    return tables

def get_count(dbcon, table):
    count = -1
    for row in dbcon.execute("""SELECT COUNT(*) FROM {};""".format(table)):
        count = row[0]

    return count

def get_all_records(dbcon, table):
    records = []
    for row in dbcon.execute("""SELECT * FROM {};""".format(table)):
        records.append(row)

    return records

def create_csv(table, records):
    file = "table_" + table + ".csv"
    with open(file, "w") as csvfile:
        writer = csv.writer(csvfile, dialect="excel-tab", quoting=csv.QUOTE_MINIMAL)
        for record in records:
            writer.writerow(record)

def main():

    ap = argparse.ArgumentParser(description=APP_DESC, prog="itekcsv")
    ap.add_argument("-e", "--export", action="store_true", help="export all tables")
    ap.add_argument("file", help="database file")
    args = vars(ap.parse_args())
    # print(args)

    # Check file exits or not
    my_file = Path(args["file"])
    if not my_file.is_file():
        # file exists
        print(args["file"], "does not exits")
        return

    # Check if its sqlite3 database only
    # "<file>: SQLite 3.x database, last written using SQLite version 3027002"
    cmd = ["file", args["file"]]
    is_sqlite3 = False
    ret = subprocess.run(
        cmd, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if ret.returncode == 0 and ret.stdout != "":
        if ret.stdout.find("SQLite 3.x database") != -1:
            is_sqlite3 = True
    if is_sqlite3 is False:
        print(args["file"], "is not a SQLite 3.x database")
        return

    # connect to database
    print("Connecting to the database [", args["file"], "] ...", end="")
    try:
        dbcon = sqlite3.connect(args["file"])
    except Exception as e:
        print(" Failed, ", e)
        return
    else:
        print(" OK.")

    # Get all tables in the database
    print("Checking database for tables ... ", end="")
    tables = get_tables(dbcon)
    print(len(tables), "Found.")
    if len(tables) > 0:
        print("  ", tables)

    # Get records in each table
    for table in tables:
        print("Total records in '", table, "' is ", get_count(dbcon, table), sep="")

    if args["export"] is True:
        print("Starting exporting process ...")
        for table in tables:
            print("  Getting records from table=", table, end="")
            records = get_all_records(dbcon, table)
            print(" ... Ok")

            print("  Exporting table=", table, end="")
            create_csv(table, records)
            print(" ... Ok")
        print("... Finished")

    dbcon.close()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("exception", e)

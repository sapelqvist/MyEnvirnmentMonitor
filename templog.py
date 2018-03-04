#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Python Program to add the temperature readings to the DB, based on time now
#
# Author:  JSB
# Date:    29/12/2014
# Version: 6.0
#

# List of modules to import
import time
import gspread
import datetime
from time import gmtime, strftime





# reference the 'live file' that the temp sensor writes
temp_sensor_01 = '/sys/bus/w1/devices/28-0000066e6162/w1_slave'

# read the 2 lines from the 'live file'
def temp_raw_01():
    file_01 = open(temp_sensor_01, 'r')
    lines_01 = file_01.readlines()
    file_01.close()
    return lines_01

# check that it has read a temperature
def read_temp_01():
    lines_01 = temp_raw_01()

    while lines_01[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines_01 = temp_raw_01()

    temp_output_01 = lines_01[1].find('t=')

    if temp_output_01 != -1:
        temp_string_01 = lines_01[1].strip()[temp_output_01+2:]
        temp_01_now = float(temp_string_01) / 1000.0

        return temp_01_now

temp_01 = read_temp_01()

# This parses out the hour from the current time
localtime = strftime("%H", gmtime())
# or pick a number between 0 & 23 
#localtime = '0' # This hardwires the localtime, for testing purposes

# Get today's date ready for the local database
todaydb = datetime.date.today().strftime("%d/%m/%Y")

# Open the local database for writing
localdb = open('/hdd/Temperature/localdb.txt', 'a')

# These loops have been seperated out from the Google Spreadsheet loops
# so that it definitely records in the localdb file, even if the Internet
# connection is down or the spreadsheet errors.
#
# between midnight & 1 in the morning, localtime = 0
# so add a new row in the db for the new day, & datestamp it
if int(localtime) == 0:
    # add a new line & write the date in the local database
    localdb.write("\n")
    localdb.write(todaydb)


# Temp is read once an hour, so 24 readings
# Column A is the datestamp, so temp starts from column B
# Loop for each hour & increment column letter by 1
for j in range(24):
    if j == int(localtime):
        localdb.write("\t")
        localdb.write(str(temp_01))
        #print j, '*' # just for testing purposes

# Close the localdb file once the temp has been written
localdb.close()



# Now that wehave our local backup securely written,
# move onto the Google spreadsheet

# Login to Google Docs with my Google account
gc = gspread.login('MY_GOOGLE_EMAIL_ADDRESS', 'MY_GOOGLE_EMAIL_PASSWORD')

# Open the 'Garden' worksheet (sheet1)
wks = gc.open("Temperature").sheet1


# Set up the variables for the loop
current_col = 'A'
# align Google & Python, & create a datevalue that actually works
# & which isn't around ~2000 years out!
todayvalue = datetime.date.today().toordinal() - 693594



# between midnight & 1 in the morning, localtime = 0
# so add a new row in the db for the new day, & datestamp it
if int(localtime) == 0:
    # Add ONE new row because it's a brand new day
    wks.add_rows(1)
    # datestamp the first cell in the new row for today
    wks.update_acell('A' + str(wks.row_count), todayvalue)


# Temp is read once an hour, so 24 readings
# Column A is the datestamp, so temp starts from column B
# Loop for each hour & increment column letter by 1
for i in range(24):
    if i == int(localtime):
        current_col = chr(ord(current_col) + 1)
        wks.update_acell(str(current_col) + str(wks.row_count), temp_01)
        #print i, '*' # just for testing purposes
    else:
        current_col = chr(ord(current_col) + 1)
        #print i # just for testing purposes
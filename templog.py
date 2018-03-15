#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Python Program to log temperature readings to a DB from a DS18B20 sensor
#
# Author:  JSB
# Date:    30/12/2014
# Version: 9.0
#

# GROUNDWORK
#
# This script assumes that you have a Google spreadsheet called 'MyEnvirnmentMonitor'
# which has one or more tables called eg 'Study' &/or 'Garden'. The top row of
# each table is reserved for headers, the first column is date formatted & the
# next 24 columns are number formatted to 0.0 for the hourly temperature record
# It is important to delete all unused rows in each table, as the script adds
# a new row for each new day & uses 'rowcount' to update the right hourly cell
#
# Multiple DS18B20 temperature sensors can be connected in parallel
# with a single 4k7 resistor linking the dataline to the +3.3v GPIO pin
# 
# Add these two lines to the end of /etc/modules so they load on boot
# w1-gpio
# w1-therm
#
# Add the 'gspread' modules to your python installation using git clone
# git clone https://github.com/burnash/gspread.git
#
# gspread site: https://github.com/burnash/gspread
#
# The script is run at 1 minute past the hour from a crontab using crontab -e
# 1 * * * * /hdd/Temperature/Temp_03.py
#
# For multiple sensors, create a script for each, change the unique serial number
# for the sensor in SECTION 1 & the name of the local text file in SECTION 2

# List of modules to import
import time
import sys, os
try:
    import gspread
except ImportError:
    sys.exit("Please install gspread. (cd gspread && sudo python setup.py install && cd ..)")
import datetime
from time import gmtime, strftime
from math import floor


# This parses out the hour from the current time
localtime = strftime("%H", gmtime())   # Comment this line out to test
#
# To test your script, pick a number between 0 & 23 for an hour
#localtime = '0'    # This hardwires the localtime, for testing purposes





# SECTION 1
#
# This section checks that the sensor actually has a reading,
# extracts it from the 'live file', then formats it to
# +/- 1/2 a degree


# reference the 'live file' that the temp sensor writes
# Note that the FULL PATH is required for the crontab to run properly
# & that each sensor has its own unique serial number
temp_sensor_01 = '/home/pi/w1-devices/warmbeddirt/w1_slave'

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
        temp_01_now = float(temp_string_01) / 1000.000

        return temp_01_now

# Give a temp reading rounded to the nearest 1/2 degree
# with thanks to wayner for the code fix 02/01/2015
temp_01 = round(read_temp_01()*2,0)/2


### END OF SECTION 1



# SECTION 2
#
# This section writes the temp readings to a local text file
# in case the Internet connection goes down or Google has
# spreadsheet issues.



# Get today's date ready for the local database
# This is formatted for the UK as dd/mm/yyyy
todaydb = datetime.date.today().strftime("%d/%m/%Y")

# Open the local database for writing
# Note that the FULL PATH is required for the crontab to run properly
# run 'sudo touch localdb.txt' before running the script & change the
# name of the file if you have multiple sensors
localdb = open('/home/pi/MyEnvirnmentMonitor-data/localdb.txt', 'a')

# Between midnight & 1 in the morning, localtime = 0
# This is the trigger to add a new row in the db for the new day
# & then datestamp it
if int(localtime) == 0:
    # add a new line & write the date in the local database
    localdb.write("\n")
    # then datestamp it
    localdb.write(todaydb)


# Add a "Tab" to the end of the file to seperate the readings
localdb.write("\t")

# Add the Temperature reading to the end of the file
localdb.write(str(temp_01))

# Close the localdb file once the temp has been written
localdb.close()

### END OF SECTION 2



# SECTION 3
#
# Now that we have our local backup securely written,
# we move onto the Google spreadsheet to record our readings again

# Login to Google Docs with my Google account
gc = gspread.login('YOUR_GOOGLE_EMAIL_ADDRESS', 'YOUR_GOOGLE_PASSWORD')

# Open the 'WarmbedDirt' worksheet (sheet1)
wks = gc.open("MyEnvirnmentMonitor").worksheet("WarmbedDirt")

# Set up the variables for the loop to find the correct hour's cell
current_col = 'A'

# align Google & Python to create a datevalue that actually works
# & which isn't around ~2000 years out!
todayvalue = datetime.date.today().toordinal() - 693594

# Between midnight & 1 in the morning, localtime = 0
# so we add a new row in the db for the new day, & datestamp it
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

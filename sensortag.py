#!/usr/bin/env python
#
# author: Orestis Evangelatos, orestevangel@gmail.com
#
# Notes:
# pexpect uses regular expression so characters that have special meaning
# in regular expressions, e.g. [ and ] must be escaped with a backslash.
#
#   Copyright 2016 Orestis Evangelatos
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import pexpect
import sys
import time
from sensor_calcs import *
import json
import select
from Sensortag_classes import *
import requests
import warnings
import datetime
import traceback
import httplib
import math



flag_to_send = False #Flag to send data to database
reading_iterations = 1 #number of iterations to read data from the TAG


#defining variable for sending data to DB
API_BASE_URI = "http://tcstestbed.unige.ch/api/"
ble_id = "SensTag004"
resource_name = "temperature"
location = "&pos_x=1&pos_y=5.5&pos_z=1" #location of my desk

    
def hexTemp2C(raw_temperature):
	
	string_temp = raw_temperature[0:2]+' '+raw_temperature[2:4]+' '+raw_temperature[4:6]+' '+raw_temperature[6:8] #add spaces to string	
	#TODO:Fix the following line so that I don't have to add and to remove spaces
	raw_temp_bytes = string_temp.split() # Split into individual bytes
	raw_ambient_temp = int( '0x'+ raw_temp_bytes[3]+ raw_temp_bytes[2], 16) # Choose ambient temperature (reverse bytes for little endian)
	raw_IR_temp = int('0x' + raw_temp_bytes[1] + raw_temp_bytes[0], 16)
	IR_temp_int = raw_IR_temp >> 2 & 0x3FFF
	ambient_temp_int = raw_ambient_temp >> 2 & 0x3FFF # Shift right, based on from TI
	ambient_temp_celsius = float(ambient_temp_int) * 0.03125 # Convert to Celsius based on info from TI
	IR_temp_celsius = float(IR_temp_int)*0.03125
	ambient_temp_fahrenheit = (ambient_temp_celsius * 1.8) + 32 # Convert to Fahrenheit

	
	print "INFO: IR Celsius:    %f" % IR_temp_celsius
	print "INFO: Ambient Celsius:    %f" % ambient_temp_celsius
	#print "Fahrenheit: %f" % ambient_temp_fahrenheit		
	return (IR_temp_celsius, ambient_temp_celsius)
	
	
	
def hexLum2Lux(raw_luminance):
	
	m ="0FFF"
	e ="F000" 
	raw_luminance = int(raw_luminance,16)
	m = int(m, 16) #Assign initial values as per the CC2650 Optical Sensor Dataset
	exp = int(e, 16) #Assign initial values as per the CC2650 Optical Sensor Dataset	
	m = (raw_luminance & m) 		#as per the CC2650 Optical Sensor Dataset
	exp = (raw_luminance & exp) >> 12 	#as per the CC2650 Optical Sensor Dataset
	luminance = (m*0.01*pow(2.0,exp)) 	#as per the CC2650 Optical Sensor Dataset	
	return luminance #returning luminance in lux

def hexHum2RelHum(raw_humidity):

    humidity = float((int(raw_humidity,16)))/65536*100 #get the int value from hex and divide as per Dataset.    
    return humidity
    
    
    
def hexPress2Press(raw_pressure):

    pressure = int(raw_pressure,16)
    pressure = float(pressure)/100.0    
    return pressure
	
def send_to_DB(data_to_send, type):
	
	data_to_send =  str(int(data_to_send)) #getting rid of decimals
	timestamp = ('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())) #get the current date and time
	if type in ['Ambient']:
		resource_name = "Ambient Temperature"
		unit = "celsius"
	elif type in ['IR']:
		resource_name = "IR Temperature"
		unit = "celsius"
	elif type in ['luminance']:
		resource_name = "luminance"
		unit = "lux"
	elif type in ['humidity']:
		resource_name = "humidity"
		unit = "Rel.hum"
	elif type in ['barPressure']:
		resource_name = "barPressure"
		unit = "hPa"
	try:
		
		insert_value_DB = requests.get(API_BASE_URI+"insertValue.php?node_name="+str(ble_id) +"&resource_name="+resource_name+ "&value="+data_to_send+ "&unit="+unit+ "&timestamp="+timestamp+ location)
		insert_value_DB.raise_for_status()
		print "INFO: Send successfully value: "+str(data_to_send)+ ' '+ unit+ " to DB with node ID: " + str(ble_id)
		#print insert_value_DB #debugging: see the outcome of the request
		
	except:
		print "Error"
		warnings.warn("Could not get values from sensor:" + str(ble_id))
		traceback.print_exc()
	
	return


#datalog = sys.stdout


    

def main():
    global datalog
    global barometer
    
    bluetooth_adr = sys.argv[1]
    #data['addr'] = bluetooth_adr
    if len(sys.argv) > 2:
        datalog = open(sys.argv[2], 'w+')

    
    #print ('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()))   
    print "INFO: [re]starting.."

    tag  = SensorTag(bluetooth_adr) #pass the Bluetooth Address
    tag.char_write_cmd(0x24,01) #Enable temperature sensor
    
    
    
    count = 0
    while count < reading_iterations:
	        """GETTING THE IR AND AMBIENT TEMPERATURE"""
		IR_temp_celsius, Ambient_temp_celsius = hexTemp2C(tag.char_read_hnd(0x21, "temperature")) #get the hex value and parse it to get Celcius
		if flag_to_send == True:	
			print "INFO: Sending to Database..." 
			send_to_DB(IR_temp_celsius, "IR") 			# Send to database the IR temperature
			send_to_DB(Ambient_temp_celsius, "Ambient") # Send to database the Ambient temperature			
		time.sleep(0.5) #wait for a while
		count =count +1
		
    """GETTING THE LUMINANCE"""
    #tag2 = SensorTag(bluetooth_adr)
    tag.char_write_cmd(0x44,01)
    lux_luminance = hexLum2Lux(tag.char_read_hnd(0x41, "luminance"))
    if flag_to_send == True:	
	print "INFO: Sending to Database..." 
	send_to_DB(lux_luminance, "luminance") # Send to database the Ambient temperature	
    
      
    """GETTING THE HUMIDITY"""
    tag.char_write_cmd(0x2C,01)
    rel_humidity = hexHum2RelHum(tag.char_read_hnd(0x29, "humidity"))
    if flag_to_send == True:	
	print "INFO: Sending to Database..."
	send_to_DB(rel_humidity, "humidity") # Send to database the Relative Humidity	
	
    """GETTING THE Barometric Pressure"""
    tag.char_write_cmd(0x34,01)
    barPressure = hexPress2Press(tag.char_read_hnd(0x31, "barPressure"))
    if flag_to_send == True:	
	print "INFO: Sending to Database..."
	send_to_DB(rel_humidity, "barPressure") # Send to database the Barrometric Pressure in hPa (hectoPascal)	
    
    
    #tag.notification_loop()
    

if __name__ == "__main__":
    main()


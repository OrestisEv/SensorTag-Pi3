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
import json
import select
import requests
import warnings
import datetime
import traceback
import httplib
import math
import struct

from sensortag_classes import *
from sensortag_calcs import *

from base64 import b64encode, b64decode
from hashlib import sha256
from urllib import quote_plus, urlencode
from hmac import HMAC
import os

#**************************************************
#SEND DATA TO AZURE DATABASE
URI = 'jmlAzureIotHub.azure-devices.net'
KEY = 'wRnTNL70b7mcBYegVQJwV6bB86AiQHHpDajDqa7iJXM='
IOT_DEVICE_ID = 'jmlRPi1'
POLICY = 'iothubowner'

def generate_sas_token():
  expiry=3600
  ttl = time.time() + expiry
  sign_key = "%s\n%d" % ((quote_plus(URI)), int(ttl))
  signature = b64encode(HMAC(b64decode(KEY), sign_key, sha256).digest())

  rawtoken = {
    'sr' : URI,
    'sig': signature,
    'se' : str(int(ttl))
  }

  rawtoken['skn'] = POLICY

  return 'SharedAccessSignature ' + urlencode(rawtoken)
  

def send_message(token, message):
  url = 'https://{0}/devices/{1}/messages/events?api-version=2016-11-14'.format(URI, IOT_DEVICE_ID)
  headers = {
    "Content-Type": "application/json",
    "Authorization": token
  }
  data = json.dumps(message)
  #print data
  response = requests.post(url, data=data, headers=headers)  
#**************************************************
#SEND DATA TO A DATABASE
'''
reading_iterations = 1 #number of iterations to read data from the TAG
#defining variable for sending data to DB
API_BASE_URI = "http://tcstestbed.unige.ch/api/"
ble_id = "SensTag004"
resource_name = "temperature"
location = "&pos_x=1&pos_y=5.5&pos_z=1" #location of my desk


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
'''
#**************************************************

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

'''
The raw data consists of nine 16-bit signed values, one for each axis. 
The order in the data is Gyroscope, Accelerometer, Magnetomer.Gyroscope raw data make up 0-5 of the data from the movement service, 
in the order X, Y, Z axis. Data from each axis consists of two bytes, encoded as a signed integer. 
For conversion from gyroscope raw data to degrees/second, use the algorithm below on each of the first three 16-bit values in the incoming 
data, one for each axis. Note that the axis data from a disabled axis will be 0,so the size of the incoming data is always 18 bytes. 
When the WOM feature is enabled, the latest measured data will be continuously transmitted.  
'''
def hexGyro2Gyro(raw_movement):
  scale = 500.0/65536.0

  get_gyro_list = raw_movement[6:12]
  gyroX = (twos_complement(get_gyro_list[0],8)+twos_complement(get_gyro_list[1],8))*scale
  gyroY = (twos_complement(get_gyro_list[2],8)+twos_complement(get_gyro_list[3],8))*scale
  gyroZ = (twos_complement(get_gyro_list[4],8)+twos_complement(get_gyro_list[4],8))*scale
  return gyroX,gyroY,gyroZ

def hexAccel2Accel(raw_movement):
  scale_2G = 2.0/32768.0 
  
  get_accel_list = raw_movement[12:18]
  accelX = (twos_complement(get_accel_list[0],8)+twos_complement(get_accel_list[1],8))*scale_2G
  accelY = (twos_complement(get_accel_list[2],8)+twos_complement(get_accel_list[3],8))*scale_2G
  accelZ = (twos_complement(get_accel_list[4],8)+twos_complement(get_accel_list[4],8))*scale_2G
  return accelX,accelY,accelZ

def hexMagneto2Magneto(raw_movement):
  scale = 4912.0 / 32760
  
  get_magneto_list = raw_movement[18:24]
  magnetoX = (twos_complement(get_magneto_list[0],8)+twos_complement(get_magneto_list[1],8))*scale
  magnetoY = (twos_complement(get_magneto_list[2],8)+twos_complement(get_magneto_list[3],8))*scale
  magnetoZ = (twos_complement(get_magneto_list[4],8)+twos_complement(get_magneto_list[5],8))*scale
  
  return magnetoX,magnetoY,magnetoZ
    
  
def twos_complement(hexstr,bits):
  value = int(hexstr,16)
  if value & (1 << (bits-1)):
    value -= 1 << bits
  return value


def s16(value):
    # 0x8000 --> -32768
    # 0x7fff --> +32767
    return -(value & 0x8000) | (value & 0x7fff)  


def main():
  global datalog
  global barometer

  #bluetooth_adr = sys.argv[1] # this line to be uncommented if need to run from command prompt and there are several Sensor-Tags.
  bluetooth_adr = "98:07:2D:28:0A:02" # if you have only one Sensor-Tag then easier this way. Hardcode your Sensor-Tag MAC address here. 
  print "INFO: [re]starting.."
  tag  = SensorTag(bluetooth_adr) #pass the Bluetooth Address
  counter = 0  
  '''
  data['addr'] = bluetooth_adr
  if len(sys.argv) > 2:
    datalog = open(sys.argv[2], 'w+')
  #print ('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()))   
  '''
  # 2. Generate SAS Token
  token = generate_sas_token()

  #tag.char_write_cmd(0x27,01)# Enable temperature sensor,o more Temperature sensor in devices manufactured after June 2017
  tag.char_write_cmd(0x47,01) # Enable Luminance
  tag.char_write_cmd(0x2F,01) # Enable Humidity
  tag.char_write_cmd(0x37,01) # Enable Barometric
  tag.char_write_cmd(0x3F,'7F:00') #This should activate sensors (Gyr,Acc and Mag),disable the WOM and set the Acc Range to +/- 2G 
  time.sleep(0.5)
  
  flag_print_selection = dict(
    pressure= 'False',
    humidity= 'False',
    lightIntensity= 'False',
    gyroscope= 'False',
    acceleration= 'False',
    magnetometer= 'False'
    )

  flag_toDB_selection = dict(
     pressure= 'False',
     humidity= 'False',
     lightIntensity= 'False',
     gyroscope= 'False',
     acceleration= 'False',
     magnetometer= 'False'
    )

  flag_toAzureDB_selection = dict(
     pressure= 'False',
     humidity= 'False',
     lightIntensity= 'False',
     gyroscope= 'False',
     acceleration= 'False',
     magnetometer= 'False'
    )
  
  while True:
    # no more Temperature sensor exist in devices manufactured after June 2017
    """GETTING THE IR AND AMBIENT TEMPERATURE"""
    '''
    IR_temp_celsius, Ambient_temp_celsius = hexTemp2C(tag.char_read_hnd(0x24, "temperature")) #get the hex value and parse it to get Celcius
    if flag_to_send == True:	
      print "INFO: Sending to Database..." 
      send_to_DB(IR_temp_celsius, "IR") 			# Send to database the IR temperature
      send_to_DB(Ambient_temp_celsius, "Ambient") # Send to database the Ambient temperature			
    time.sleep(0.5) #wait for a while
    count =count +1
    '''

    """GETTING THE LUMINANCE"""
    lux_luminance = hexLum2Lux(tag.char_read_hnd(0x44, "luminance"))
    
    if flag_print_selection['lightIntensity'] == 'True':
      print 'lux_luminance: ',lux_luminance
    
    if flag_toDB_selection['lightIntensity'] == 'True':
      send_to_DB(lux_luminance, "luminance") # Send to database the Ambient temperature
      
    if flag_toAzureDB_selection['lightIntensity'] == 'True':
      message1 = { "lux_luminance": str(lux_luminance) }
      send_message(token, message1)	

    """GETTING THE HUMIDITY"""
    rel_humidity = hexHum2RelHum(tag.char_read_hnd(0x2C, "humidity"))

    if flag_print_selection['humidity'] == 'True':
      print 'humidity: ',rel_humidity

    if flag_toDB_selection['humidity']== 'True':
      send_to_DB(rel_humidity, "humidity") # Send to database the Relative Humidity
    
    if flag_toAzureDB_selection['humidity'] == 'True':
      message1 = { "humidity": str(rel_humidity) }
      send_message(token, message1)	        	

    """GETTING THE Barometric Pressure"""
    barPressure = hexPress2Press(tag.char_read_hnd(0x34, "barPressure"))

    if flag_print_selection['pressure'] == 'True':
      print 'pressure: ',barPressure
          
    if flag_toDB_selection['pressure']== 'True':
      send_to_DB(barPressure, "pressure") # Send to database the Barrometric Pressure in hPa (hectoPascal)
    
    if flag_toAzureDB_selection['pressure'] == 'True':
      message1 = { "pressure": str(barPressure) }
      send_message(token, message1)	
      	
    
    """GETTING THE Gyroscope"""
    rawMovementData = tag.char_read_hnd(0x3C,"movementSensor")
    GyroscopeData = hexGyro2Gyro(rawMovementData)
    
    if flag_print_selection['gyroscope'] == 'True':
      print 'gyroscope: ',GyroscopeData
      
    if flag_toAzureDB_selection['gyroscope']  == 'True':
      message1 = { "dataGyroX": str(GyroscopeData[0]) }      
      send_message(token, message1)	
      message2 = { "dataGyroY": str(GyroscopeData[1]) }
      send_message(token, message2)
      message3 = { "dataGyroZ": str(GyroscopeData[2]) }
      send_message(token, message3)
          
    """GETTING THE Acceleration"""
    AccelerationData1 = hexAccel2Accel(rawMovementData)
    
    if flag_print_selection['acceleration'] == 'True':
      print 'acceleration: ',AccelerationData1
      
    if flag_toAzureDB_selection['acceleration'] =='True':	
      message1 = { "acceleration_1X": str(AccelerationData1[0]) }      
      send_message(token, message1)	
      message2 = { "acceleration_1Y": str(AccelerationData1[1]) }
      send_message(token, message2)
      message3 = { "acceleration_1Z": str(AccelerationData1[2]) }
      send_message(token, message3)	
          
    """GETTING THE Acceleration utiizing library sensortag_calcs.py"""
    rawX = twos_complement(rawMovementData[12],8)+twos_complement(rawMovementData[13],8)
    rawY = twos_complement(rawMovementData[14],8)+twos_complement(rawMovementData[15],8)
    rawZ = twos_complement(rawMovementData[16],8)+twos_complement(rawMovementData[17],8)
    #AccelerationData2 = calcAccel(rawX, rawY, rawZ)
    #print 'acceleration_2 & magnitude: ',AccelerationData2
    
    """GETTING THE Magnetometer"""
    MagnetometerData = hexMagneto2Magneto(rawMovementData)
    
    if flag_print_selection['magnetometer'] == 'True':
      print 'magnetometer: ',MagnetometerData
      
    if flag_toAzureDB_selection['magnetometer'] =='True':	
      message1 = { "MagnetometerX": str(MagnetometerData[0]) }      
      send_message(token, message1)	
      message2 = { "MagnetometerY": str(MagnetometerData[1]) }
      send_message(token, message2)
      message3 = { "MagnetometerZ": str(MagnetometerData[2]) }
      send_message(token, message3)	
          
    """LOOP INTERVAL"""
    counter = counter+1
    print (counter)
    time.sleep(0.0)

    
if __name__ == "__main__":
  main()


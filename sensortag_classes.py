import pexpect
import sys
import time
import json
import select
#from sensortag_calcs import *

class SensorTag:

  def __init__( self, bluetooth_adr ):
    self.con = pexpect.spawn('gatttool -b ' + bluetooth_adr + ' --interactive')
    self.con.expect('\[LE\]>', timeout=600)
    print "INFO: Preparing to connect. Hold on a second...If nothing happens please press the power button..."
    self.con.sendline('connect')
    # test for success of connect
    self.con.expect('.*Connection successful.*\[LE\]>')
    print "INFO: Connection Successful!"
    # Earlier versions of gatttool returned a different message.  Use this pattern -
    #self.con.expect('\[CON\].*>')
    self.cb = {}
    return

    self.con.expect('\[CON\].*>')
    self.cb = {}
    return

  def char_write_cmd( self, handle, value ):
    # The 0%x for value is VERY naughty!  Fix this!
    #print "DEBUGGING:" + cmd
    #print type(value)
    if handle != 0x3F:
        cmd = 'char-write-cmd 0x%02x 0%x' % (handle, value) 
        self.con.sendline( cmd )
    else:
        self.con.sendline('char-write-cmd 0x3F 7F:00')    
    time.sleep(0.5) #delay for 1 second so that Tag can enable registers
    return

  def char_read_hnd( self, handle, sensortype ):
    self.con.sendline('char-read-hnd 0x%02x' % handle) #send the hex value to the Tag
    #print 'DEBUGGING: char-read-hnd 0x%02x' % handle        
    self.con.expect('.*descriptor:.* \r')
    reading = self.con.after
    #print "DEBUGGING: Reading from Tag... %s \n" % reading #print the outcome as it comes while reading the Tag
    rval = reading.split() #splitting the reading based on the spaces
    #print "DEBUGGING: rval" + str(rval)

    if  sensortype in ['temperature']:
      raw_measurement = rval[-4]+rval[-3]+rval[-2]+rval[-1]
    elif sensortype in ['luminance']:
      raw_measurement = rval[-1]+rval[-2]
    elif sensortype in ['humidity']:
      raw_measurement = rval[-1]+rval[-2]
    elif sensortype in ['barPressure']:
      raw_measurement = rval[-1]+rval[-2]+rval[-3]
    elif sensortype in ['movementSensor']:
      raw_measurement = rval   
    
    else:
      raw_measurement = 0
      
    return raw_measurement
                    

  # Notification handle = 0x0025 value: 9b ff 54 07
  def notification_loop( self ):
   while True:
    try:
      pnum = self.con.expect('Notification handle = .*? \r', timeout=4)
    except pexpect.TIMEOUT:
      print "TIMEOUT exception!" #was: print "TIMEOUT exception!"
      break
    
    if pnum==0:
      after = self.con.after
      hxstr = after.split()[3:]
      print "****"
      handle = long(float.fromhex(hxstr[0]))
      if True:
        self.cb[handle]([long(float.fromhex(n)) for n in hxstr[2:]])
        pass
      else:
        print "TIMEOUT!!"
        pass

  def register_cb( self, handle, fn ):
    self.cb[handle]=fn;
    return
        

class SensorCallbacks:

  data = {}
  def __init__(self,addr):
    self.data['addr'] = addr

  def tmp006(self,v):
    objT = (v[1]<<8)+v[0]
    ambT = (v[3]<<8)+v[2]
    targetT = calcTmpTarget(objT, ambT)
    self.data['t006'] = targetT
    print "T006 %.1f" % targetT


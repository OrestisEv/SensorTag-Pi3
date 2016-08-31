
import pexpect
import sys
import time
from sensor_calcs import *
import json
import select
import time




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
        cmd = 'char-write-cmd 0x%02x 0%x' % (handle, value)
        #print "DEBUGGING:" + cmd
        self.con.sendline( cmd )
        time.sleep(1) #delay for 1 second so that Tag can enable registers
        return

    def char_read_hnd( self, handle, sensortype ):
        self.con.sendline('char-read-hnd 0x%02x' % handle) #send the hex value to the Tag
        #print 'DEBUGGING: char-read-hnd 0x%02x' % handle        
        self.con.expect('.*descriptor:.* \r')
        reading = self.con.after
        print "DEBUGGING: Reading from Tag... %s \n" % reading #print the outcome as it comes while reading the Tag
        rval = reading.split() #splitting the reading based on the spaces
        print "DEBUGGING: rval" + str(rval)
        
        if  sensortype in ['temperature']:
			raw_measurement = rval[-4]+rval[-3]+rval[-2]+rval[-1]
        elif sensortype in ['luminance']:
			raw_measurement = rval[-1]+rval[-2]
        elif sensortype in ['humidity']:
			raw_measurement = rval[-1]+rval[-2]
        elif sensortype in ['barPressure']:
			raw_measurement = rval[-1]+rval[-2]+rval[-3]
        else:
			raw_measurement = 0
			
        print raw_measurement
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
            	#try:
	        if True:
                  self.cb[handle]([long(float.fromhex(n)) for n in hxstr[2:]])
            	#except:
                #  print "Error in callback for %x" % handle
                #  print sys.argv[1]
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

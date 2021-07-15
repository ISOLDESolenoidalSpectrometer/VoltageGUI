# -*- coding: utf-8 -*-

"""
The library for controlling the Mesytec MHV-4 high voltage unit via
the USB serial control interface.

Protocol data format is 9600 baud 8N1 (8 bit, no parity, 1 stop bit)
The input characters are echoed before the response from the unit.
"""
__author__ = "Joonas Konki"
__license__ = "MIT, see LICENSE for more details"
__copyright__ = "2018 Joonas Konki"

import serial
import time
import re

VOLTAGE_LIMIT = 251

class MHV4():
	def __init__(self,port,baud):
		self.port = port
		self.ser = serial.Serial( port=self.port, baudrate=baud, timeout=1 )
		
	def close(self):
		"""The function closes and releases the serial port connection attached to the unit. 

		"""
		self.ser.close()
		
	def send_command(self, command=''):
		"""The function sends a command to the unit and returns the response string. 

		"""
		if command == '': return ''
		self.ser.write( bytes(command, 'utf8') ) # works better with older Python3 versions (<3.5)
		#print("The sent command is: ",command)		
		time.sleep(0.1)
		self.ser.readline() # read out echoed command
		a=self.ser.readline() # return response from the unit
		#print("The returned command is: ",a)
		return a # return response from the unit
			
	def set_on(self,channel):
		"""The function turns the voltage ON for the given ``channel`` number. 
		The possible channel numbers are 0,1,2,3. Number 4 applies to ALL channels.
		
		:param channel: The channel number that is to be turned ON.
		"""
		
		if channel not in [0,1,2,3,4]: return
		response = self.send_command( 'ON %d\r' % channel )
		
	def set_off(self,channel):
		"""The function turns the voltage OFF for the given ``channel`` number. 
		The possible channel numbers are 0,1,2,3. Number 4 applies to ALL channels.
		
		:param channel: The channel number that is to be turned OFF.
		"""
		
		if channel not in [0,1,2,3,4]: return
		response = self.send_command( 'OFF %d\r' % channel )

	def get_voltage(self,channel):
		"""The function returns the measured voltage reading of the given ``channel`` number. 
		The possible channel numbers are 0,1,2,3. 
		Number 4 applies to ALL channels (not tested?).
		
		Note: Returns always 0, if the channel is turned OFF !
		
		:param channel: The channel number of which the voltage reading is requested. 
						The return value is positive or negative depending on the set polarity.
		"""
		response = self.send_command( 'RU %d\r' % channel )
		linestr = response.decode('utf8')
		pattern = re.match(r'.*([+-])(\d*.\d*)', linestr, re.IGNORECASE)
		
		if pattern is not None:
			voltage = float(pattern.group(2))
			#print("The voltage is ")
			#print (voltage)
			#print(pattern.group(2))
			if pattern.group(1) == '-':
				voltage = -voltage
			return voltage
		else :
			return 0.
			
	def get_voltage_preset(self,channel):
		"""The function returns the preset voltage reading of the given ``channel`` number.
		Note: This may not be the actual voltage, just what is set on the display.
		May not work on an older firmware of the module, and have to use get_voltage() instead. 
		The possible channel numbers are 0,1,2,3. 
		Number 4 applies to ALL channels (not tested?).
		
		:param channel: The channel number of which the preset voltage reading is requested. 
						The return value is positive regardless of what the polarity is set to.
		"""
		response = self.send_command( 'RUP %d\r' % channel )
		linestr = response.decode('utf8')
		pattern = re.match(r'.*([+-])(\d*.\d*)', linestr, re.IGNORECASE)
		
		if pattern is not None:
			voltage = float(pattern.group(2))
			if pattern.group(1) == '-':
				voltage = -voltage
			return voltage
		else :
			return 0.
			
	def get_current(self,channel):
		response = self.send_command( 'RI %d\r' % channel )
		linestr = response.decode('utf8')		
		pattern = re.match(r'.*([+-])(\d*.\d*)', linestr, re.IGNORECASE)
		
		if pattern is not None:
			current = float(pattern.group(2))
			if pattern.group(1) == '-':
				current = -current
			return current
		else :
			return 0.
			
	def get_current_limit(self,channel):
		""" not tested !"""
		response = self.send_command( 'RIL %d\r' % channel )
		linestr = response.decode('utf8')		
		pattern = re.match(r'.*([+-])(\d*.\d*)', linestr, re.IGNORECASE)
		
		if pattern is not None:
			current = float(pattern.group(2))
			if pattern.group(1) == '-':
				current = -current
			return current
		else :
			return 0.
			
	def get_polarity(self,channel):
		response = self.send_command( 'RP %d\r' % channel )
		polarity=response.decode('utf8')
		if "positive" in polarity:
			return 1
		if "negative" in polarity:
			return 0	
		#return returnValue
		
	def get_temp(self,inputc):
		""" not tested ! Get temperature at given input"""
		response = self.send_command( 'RT %d\r' % inputc )
		return response.decode('utf8')
	
	def get_temp_comp(self,channel):
		""" not tested ! Get complete settings for temperature compensation of 
		given channel"""
		response = self.send_command( 'RTC %d\r' % channel )
		return response.decode('utf8')
			
	def get_ramp(self):
		"""Get voltage ramp speed setting of the unit in V/s"""
		response = self.send_command( 'RRA\r')
		linestr = response.decode('utf8')		
		pattern = re.match(r'.*:.?(\d*).*V.*', linestr, re.IGNORECASE)		
		if pattern is not None:
			ramp = float(pattern.group(1))
			return ramp
		else :
			return -1
		
		
	def set_voltage(self,channel, voltage):
		"""The function sets the voltage of the given ``channel`` number to ``voltage``. 
		The possible channel numbers are 0,1,2,3. Number 4 applies to ALL channels.
		
		:param channel: The channel number that the voltage setting is applied to.
		:param voltage: The voltage that is to be set for the channel in Volts.
		"""
		if voltage > VOLTAGE_LIMIT: # safety check limit in the library
			return
		
		# MHV-4 protocol expects voltage in 0.1 V units
		response = self.send_command( 'SU %d %d\r' % (channel, voltage*10) ) 
		return response.decode('utf8')
		
	def set_current_limit(self,channel, limit):
		"""The function sets the current limit of the given ``channel`` number 
		to ``limit``. 
		The possible channel numbers are 0,1,2,3. Number 4 applies to ALL channels.
		
		:param channel: The channel number that the current limit setting is applied to.
		:param limit: The current limit value that is to be set for the channel in units of nA.
		"""
		
		# MHV-4 protocol expects current in nanoamps
		response = self.send_command( 'SIL %d %d\r' % (channel, limit) )
		return response.decode('utf8')
		
	def set_voltage_limit(self,channel, limit):
		"""The function sets the voltage limit of the given ``channel`` number 
		to ``limit``. 
		The possible channel numbers are 0,1,2,3. Number 4 applies to ALL channels.
		
		:param channel: The channel number that the voltage limit setting is applied to.
		:param limit: The voltage limit value that is to be set for the channel in units of Volts.
		"""
		# MHV-4 protocol expects voltage in 0.1 V units
		response = self.send_command( 'SUL %d %d\r' % (channel, limit*10) )
		return response.decode('utf8')
		
	def set_voltage_polarity(self,channel, pol):
		"""The function sets the voltage polarity (negative/positive) for the given ``channel`` number.
		The possible channel numbers are 0,1,2,3. Number 4 applies to ALL channels.
		
		Note:   SP c p , 
				where c = channel, p = polarity: p/+/1 or n/-/0 
				e.g.: SP 0 n sets the polarity of channel 0 to negative.
		    	
				For security reasons: if HV is on, it will be switched off automatically, 
				HV preset will be set to 0 V, polarity is switched when	HV is down.
				
				After switching: set presets again to desired values.
				
		:param channel: The channel number that the polarity change is applied to.
		:param pol: The desired polarity of the voltage for the channel 0 or 1.
		"""
		response = self.send_command( 'SP %d %d\r' % (channel, pol) )
		return response.decode('utf8')
		
	def set_ramp(self, n):
		"""The function sets the HV ramp speed of the whole unit.
		
		Note:   Options are:
		        n = 0: 5 V/s, 1: 25 V/s, 2: 100 V/s, 3: 500 V/s
								
		:param n: The desired ramp speed option (0, 1, 2 or 3).
		"""
		
		if n not in [0,1,2,3]: return
		
		response = self.send_command( 'SRA %d\r' % (n) )
		return response.decode('utf8')
		

# -*- coding: utf-8 -*-
"""
The library for controlling the iSeg NHR high voltage unit via
the USB serial control interface.

Protocol data format is 9600 baud 8N1 (8 bit, no parity, 1 stop bit)
The input characters are echoed before the response from the unit.
"""


import serial
import time
import re
import fasteners

VOLTAGE_LIMIT = 200
LOCK_TIMEOUT = 5
LOCK_PATH = '/tmp/'

class NHR():
	def __init__(self,port,baud,board):
		self.board = str(board) # lbus in the module
		lock_file = port[4:]+'.lock'
		self.lock = fasteners.InterProcessLock(LOCK_PATH + lock_file)
		if self.lock.acquire(timeout=LOCK_TIMEOUT):
			print('Lockfile acquired successfully: ' + LOCK_PATH + lock_file )
			self.port = port
			self.ser = serial.Serial( port=self.port, baudrate=baud, timeout=1 )
			time.sleep(0.1) # Wait 100 ms after opening the port before sending commands
			self.ser.flushInput() # Flush the input buffer of the serial port before sending any new commands
			time.sleep(0.1)
		else:
			print('Lockfile could not be acquired for port ' + port)
			print('Is there another program using nhrlib ??')
			return


	def close(self):
		"""The function closes and releases the serial port connection attached to the unit.

		"""
		self.ser.close()
		self.lock.release()

	def send_command(self, command=''):
		"""The function sends a command to the unit and returns the response string.

		"""
		if command == '': return ''
		self.ser.write( command.encode('utf-8') )
		time.sleep(0.1)
		self.ser.readline() # read out echoed command
		return self.ser.readline() # return response from the unit

	def flush_input_buffer(self):
		""" Flush the input buffer of the serial port.
		"""
		self.ser.flushInput()

	def set_on(self,channel):
		"""The function turns the voltage ON for the given ``board`` and ``channel`` number.
		The possible channel numbers are 0,1,2,3.

		:param channel: The channel number that is to be turned ON.
		"""

		if channel not in [0,1,2,3]: return
		response = self.send_command( ':VOLT ON,(@{ch})\r\n'.format(ch=channel) )

	def set_off(self,channel):
		"""The function turns the voltage OFF for the given ``board`` and ``channel`` number.
		The possible channel numbers are 0,1,2,3.

		:param channel: The channel number that is to be turned OFF.
		"""

		if channel not in [0,1,2,3]: return
		response = self.send_command( ':VOLT OFF,(@{ch})\r\n'.format(ch=channel) )

	def get_power(self,channel):
		"""The function returns the power status of the given ``channel`` number.
		Return value is 0 for OFF and 1 for ON
		The possible channel numbers are 0,1,2,3.

		:param channel: The channel number of which the voltage reading is requested.
		"""
		response = self.send_command( ':READ:VOLT:ON? (@{ch})\r\n'.format(ch=channel) )
		linestr = response.decode('utf8')

		return int(linestr.strip('\n').strip('\r'))



	def get_voltage(self,channel):
		"""The function returns the measured voltage reading of the given ``channel`` number.
		The possible channel numbers are 0,1,2,3.

		:param channel: The channel number of which the voltage reading is requested.
		"""
		response = self.send_command( ':MEAS:VOLT? (@{ch})\r\n'.format(ch=channel) )
		linestr = response.decode('utf8')
		pattern = re.match(r'[+\-]?[^A-Za-z]?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+)', linestr, re.IGNORECASE)

		if pattern is not None:
			voltage = float(pattern.group(0))
			return voltage
		else:
			return 0.

	def get_voltage_preset(self,channel):
		"""The function returns the preset voltage reading of the given ``channel`` number.
		The possible channel numbers are 0,1,2,3.

		:param channel: The channel number of which the preset voltage reading is requested.
		"""
		response = self.send_command( ':READ:VOLT? (@{ch})\r\n'.format(ch=channel) )
		linestr = response.decode('utf8')
		pattern = re.match(r'[+\-]?[^A-Za-z]?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+)', linestr, re.IGNORECASE)

		if pattern is not None:
			voltage = float(pattern.group(0))
			return voltage
		else:
			return 0.

	def get_voltage_limit(self,channel):
		"""The function returns the voltage max limit reading of the given ``channel`` number.
		The possible channel numbers are 0,1,2,3.

		:param channel: The channel number of which the preset voltage reading is requested.
		"""
		response = self.send_command( ':READ:VOLT:LIM? (@{ch})\r\n'.format(ch=channel) )
		linestr = response.decode('utf8')
		pattern = re.match(r'[+\-]?[^A-Za-z]?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+)', linestr, re.IGNORECASE)

		if pattern is not None:
			voltage = float(pattern.group(0))
			return voltage
		else:
			return 0.

	def get_current(self,channel):
		response = self.send_command( ':MEAS:CURR? (@{ch})\r\n'.format(ch=channel) )
		linestr = response.decode('utf8')
		pattern = re.match(r'[+\-]?[^A-Za-z]?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+)', linestr, re.IGNORECASE)

		if pattern is not None:
			current = float(pattern.group(0))
			return current * 1e6 # output is in A, we need uA
		else:
			return 0.

	def get_current_limit(self,channel):
		""" not tested !"""
		response = self.send_command( ':READ:CURR? (@{ch})\r\n'.format(ch=channel) )
		linestr = response.decode('utf8')
		pattern = re.match(r'[+\-]?[^A-Za-z]?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+)', linestr, re.IGNORECASE)

		if pattern is not None:
			current = float(pattern.group(0))
			return current * 1e6 # output is in A, we need uA
		else:
			return 0.

	def get_ramp_up(self,channel):
		"""Get voltage ramp up speed setting of the unit in V/s
		
		:param channel: The channel number in the module/board
		"""
		response = self.send_command( ':CONF:RAMP:UP? (@{ch})\r\n'.format(ch=channel) )
		linestr = response.decode('utf8')
		pattern = re.match(r'[+\-]?[^A-Za-z]?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+)', linestr, re.IGNORECASE)

		if pattern is not None:
			voltage = float(pattern.group(0))
			return voltage
		else:
			return 0.

	def get_ramp_down(self,channel):
		"""Get voltage ramp down speed setting of the unit in V/s
		
		:param channel: The channel number in the module/board
		"""
		response = self.send_command( ':CONF:RAMP:DOWN? (@{ch})\r\n'.format(ch=channel) )
		linestr = response.decode('utf8')
		pattern = re.match(r'[+\-]?[^A-Za-z]?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+)', linestr, re.IGNORECASE)

		if pattern is not None:
			voltage = float(pattern.group(0))
			return voltage
		else:
			return 0.

	def get_trip_time(self,channel):
		"""Get the trip time of the channel in ms
		
		:param channel: The channel number in the module/board
		"""
		response = self.send_command( ':CONF:TRIP:TIME? (@{ch})\r\n'.format(ch=channel) )
		linestr = response.decode('utf8')
		pattern = re.match(r'[+\-]?[^A-Za-z]?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+)', linestr, re.IGNORECASE)

		if pattern is not None:
			time = float(pattern.group(0))
			return time
		else:
			return 0.

	def get_polarity(self,channel):
		"""Get the polarity of the channel
		
		:param channel: The channel number in the module/board
		"""
		response = self.send_command( ':CONF:OUTP:POL? (@{ch})\r\n'.format(ch=channel) )
		linestr = response.decode('utf8')

		if linestr.strip('\n').strip('\r') == 'n':
			return 0
		elif linestr.strip('\n').strip('\r') == 'p':
			return 1
		else:
			return -1

	def get_serial_number(self):
		"""Get the serial number of the board/module"""
		response = self.send_command( ':SYS:USER:SERIAL?\r\n' )
		linestr = response.decode('utf8')
		return str(linestr)


	def get_status(self,channel):
		"""The function returns the status value of the given ``channel`` number.
		The possible channel numbers are 0,1,2,3.
		Number 4 applies to ALL channels (not tested?).

		:param channel: The channel number of which the voltage reading is requested.
		"""
		response = self.send_command( ':READ:CHAN:STAT? (@{ch})\r\n'.format(ch=channel) )
		linestr = response.decode('utf8')

		status = int(linestr.strip('\n').strip('\r'))
		if status & 16:
			print( "Ch{ch} is ramping".format(ch=channel) )
		if status & 8:
			print( "Ch{ch} is ON".format(ch=channel) )
		else:
			print( "Ch{ch} is OFF".format(ch=channel) )
		if status & 4:
			print( "Ch{ch} has input error".format(ch=channel) )
		if status & 2:
			print( "Ch{ch} is Arc".format(ch=channel) )
		if status & 1:
			print( "Ch{ch} is postive".format(ch=channel) )
		else:
			print( "Ch{ch} is negative".format(ch=channel) )

			
		return status
				

	def get_module_status(self):
		"""The function returns the status value of the module."""
		response = self.send_command( ':READ:MOD:STAT?\r\n' )
		linestr = response.decode('utf8')

		status = int(linestr.strip('\n').strip('\r'))
		if status & 16:
			print( "Module is service" )
		else:
			print( "Module not service" )
		if status & 8:
			print( "HV is on" )
		else:
			print( "HV is off" )
		if status & 1:
			print( "Module has fine adjustment" )
		else:
			print( "Module has no fine adjustment" )

			
		return status
				


	def set_voltage(self,channel, voltage):
		"""The function sets the voltage of the given ``channel`` number to ``voltage``.
		The possible channel numbers are 0,1,2,3.

		:param channel: The channel number that the voltage setting is applied to.
		:param voltage: The voltage that is to be set for the channel in Volts.
		"""
		if float(voltage) > VOLTAGE_LIMIT: # safety check limit in the library
			return

		response = self.send_command( ':VOLT {v},(@{ch})\r\n'.format(v=voltage,ch=channel) )
		return response.decode('utf8').strip('\n').strip('\r')


	def set_voltage_polarity(self,channel, pol):
		"""The function sets the voltage polarity (negative/positive) for the given ``channel`` number.
		The possible channel numbers are 0,1,2,3.

		:param channel: The channel number that the polarity change is applied to.
		:param pol: The desired polarity of the voltage for the channel 0 or 1.
		"""

		if pol == 0:
			polset = 'n'
		elif pol == 1:
			polset = 'p'
		else:
			return -1

		response = self.send_command( ':CONF:OUTP:POL {pn},(@{ch})\r\n'.format(pn=polset,ch=channel) )
		return response.decode('utf8').strip('\n').strip('\r')

	def set_current_limit(self,channel, limit):
		"""The function sets the current limit of the given ``channel`` number
		to ``limit``.
		The possible channel numbers are 0,1,2,3.

		:param channel: The channel number that the current limit setting is applied to.
		:param limit: The current limit value that is to be set for the channel in units of A.
		"""
		current = limit * 1e-6
		response = self.send_command( ':CURR {c},(@{ch})\r\n'.format(c=current,ch=channel) )
		return response.decode('utf8').strip('\n').strip('\r')


	def set_ramp_up(self,channel, n):
		"""The function sets the HV ramp up speed per channel.

		:param channel: The channel number in the module/board
		:param n: The desired ramp speed in V/s, minimum = 1, maximum = 50.
		"""

		if float(n) < 1.0 or float(n) > 250.0: return

		response = self.send_command( ':CONF:RAMP:UP {ramp},(@{ch})\r\n'.format(ramp=n,ch=channel) )
		return response.decode('utf8').strip('\n').strip('\r')


	def set_ramp_down(self,channel, n):
		"""The function sets the HV ramp up speed per channel.

		:param channel: The channel number in the module/board
		:param n: The desired ramp speed in V/s, minimum = 1, maximum = 50.
		"""

		if float(n) < 1.0 or float(n) > 50.0: return

		response = self.send_command( ':CONF:RAMP:DOWN {ramp},(@{ch})\r\n'.format(ramp=n,ch=channel) )
		return response.decode('utf8').strip('\n').strip('\r')


	def set_trip_time(self,channel, time):
		"""The function sets the trip time.

		:param channel: The channel number in the module/board
		:param t: The desired trip time in milliseconds minimum = 1 ms, maximum = 4095 s
		"""

		if int(time) < 1 or int(time) > 4095: return

		response = self.send_command( ':CONF:TRIP:TIME {t},(@{ch})\r\n'.format(t=time,ch=channel) )
		return response.decode('utf8').strip('\n').strip('\r')


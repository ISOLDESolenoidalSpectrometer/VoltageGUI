# -*- coding: utf-8 -*-
"""
The library for controlling the CAEN N1419 high voltage unit via
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

class N1419():
	def __init__(self,port,baud,board):
		self.board = str(board) # lbus in the N1419 module
		lock_file = '.n1419lib.'+port[4:]+'_'+str(board)+'.lock'
		self.lock = fasteners.InterProcessLock(LOCK_PATH + lock_file)
		if self.lock.acquire(timeout=LOCK_TIMEOUT):
			print('Lockfile acquired successfully: ' + LOCK_PATH + lock_file )
			self.port = port
			self.ser = serial.Serial( port=self.port, baudrate=baud, timeout=1, xonxoff=True )
			time.sleep(0.1) # Wait 100 ms after opening the port before sending commands
			self.ser.flushInput() # Flush the input buffer of the serial port before sending any new commands
			time.sleep(0.1)
		else:
			print('Lockfile could not be acquired for port ' + port)
			print('Is there another program using n1419lib ??')
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
		#self.ser.readline() # read out echoed command (no echo in N1419)
		return self.ser.readline() # return response from the unit

	def flush_input_buffer(self):
		""" Flush the input buffer of the serial port.
		"""
		self.ser.flushInput()

	def set_on(self,channel):
		"""The function turns the voltage ON for the given ``board`` and ``channel`` number.
		The possible channel numbers are 0,1,2,3. Number 4 applies to ALL channels.

		:param channel: The channel number that is to be turned ON.
		"""

		if channel not in [0,1,2,3,4]: return
		response = self.send_command( '$BD:{bd},CMD:SET,CH:{ch},PAR:ON\r'.format(bd=self.board,ch=channel) )

	def set_off(self,channel):
		"""The function turns the voltage OFF for the given ``board`` and ``channel`` number.
		The possible channel numbers are 0,1,2,3. Number 4 applies to ALL channels.

		:param channel: The channel number that is to be turned OFF.
		"""

		if channel not in [0,1,2,3,4]: return
		response = self.send_command( '$BD:{bd},CMD:SET,CH:{ch},PAR:OFF\r'.format(bd=self.board,ch=channel) )

	def get_power(self,channel):
		"""The function returns the power status of the given ``channel`` number.
		Return value is 0 for OFF and 1 for ON
		The possible channel numbers are 0,1,2,3.
		Number 4 applies to ALL channels (not tested?).

		:param channel: The channel number of which the voltage reading is requested.
		"""
		response = self.send_command( '$BD:{bd},CMD:MON,CH:{ch},PAR:STAT\r'.format(bd=self.board,ch=channel) )
		linestr = response.decode('utf8')
		pattern = re.match(r'#BD:(\d*),CMD:(\w*),VAL:(\d*)', linestr, re.IGNORECASE)

		if pattern is not None:
		
			if pattern.group(2) == 'OK':

				status = int(pattern.group(3))
				return status & 1
					
			else:
				print( pattern.group(2) )
				return -1

		else:
			return -1

	def get_status(self,channel):
		"""The function returns the status value of the given ``channel`` number.
		The possible channel numbers are 0,1,2,3.
		Number 4 applies to ALL channels (not tested?).

		:param channel: The channel number of which the voltage reading is requested.
		"""
		response = self.send_command( '$BD:{bd},CMD:MON,CH:{ch},PAR:STAT\r'.format(bd=self.board,ch=channel) )
		linestr = response.decode('utf8')
		pattern = re.match(r'#BD:(\d*),CMD:(\w*),VAL:(\d*)', linestr, re.IGNORECASE)

		if pattern is not None:
		
			if pattern.group(2) == 'OK':
			
				status = int(pattern.group(3))
				if status & 8192:
					print( "Ch{ch} has calibration error".format(ch=channel) )
				if status & 4096:
					print( "Ch{ch} is in INTERLOCK via front panel".format(ch=channel) )
				if status & 2048:
					print( "Ch{ch} is in KILL via front panel".format(ch=channel) )
				if status & 1024:
					print( "Ch{ch} is disabled".format(ch=channel) )
				if status & 512:
					print( "Ch{ch} is over temperature > 105˚C".format(ch=channel) )
				if status & 256:
					print( "Ch{ch} is over power > 0.11 W".format(ch=channel) )
				if status & 128:
					print( "Ch{ch} has tripped".format(ch=channel) )
				if status & 64:
					print( "Ch{ch} is in max voltage protection".format(ch=channel) )
				if status & 32:
					print( "Ch{ch} is under voltage".format(ch=channel) )
				if status & 16:
					print( "Ch{ch} is over voltage".format(ch=channel) )
				if status & 8:
					print( "Ch{ch} is over current".format(ch=channel) )
				if status & 4:
					print( "Ch{ch} is ramping DOWN".format(ch=channel) )
				if status & 2:
					print( "Ch{ch} is ramping UP".format(ch=channel) )
				if status & 1:
					print( "Ch{ch} is ON".format(ch=channel) )
				else:
					print( "Ch{ch} is OFF".format(ch=channel) )

					
				return status
				
			else:
				print( pattern.group(2) )
				return -1
				
		else:
			return -1


	def get_voltage(self,channel):
		"""The function returns the measured voltage reading of the given ``channel`` number.
		The possible channel numbers are 0,1,2,3.
		Number 4 applies to ALL channels (not tested?).

		:param channel: The channel number of which the voltage reading is requested.
		"""
		response = self.send_command( '$BD:{bd},CMD:MON,CH:{ch},PAR:VMON\r'.format(bd=self.board,ch=channel) )
		linestr = response.decode('utf8')
		pattern = re.match(r'#BD:(\d*),CMD:(\w*),VAL:(\d*.\d*)', linestr, re.IGNORECASE)

		if pattern is not None:
			if pattern.group(2) == 'OK':
				voltage = float(pattern.group(3))
				return voltage
			else:
				print( pattern.group(2) )
				return 0.
		else:
			return 0.

	def get_voltage_preset(self,channel):
		"""The function returns the preset voltage reading of the given ``channel`` number.
		The possible channel numbers are 0,1,2,3.
		Number 4 applies to ALL channels (not tested?).

		:param channel: The channel number of which the preset voltage reading is requested.
		"""
		response = self.send_command( '$BD:{bd},CMD:MON,CH:{ch},PAR:VSET\r'.format(bd=self.board,ch=channel) )
		linestr = response.decode('utf8')
		pattern = re.match(r'#BD:(\d*),CMD:(\w*),VAL:(\d*.\d*)', linestr, re.IGNORECASE)

		if pattern is not None:
			if pattern.group(2) == 'OK':
				voltage = float(pattern.group(3))
				return voltage
			else:
				print( pattern.group(2) )
				return 0.
		else:
			return 0.

	def get_voltage_limit(self,channel):
		"""The function returns the voltage max limit reading of the given ``channel`` number.
		The possible channel numbers are 0,1,2,3.
		Number 4 applies to ALL channels (not tested?).

		:param channel: The channel number of which the preset voltage reading is requested.
		"""
		response = self.send_command( '$BD:{bd},CMD:MON,CH:{ch},PAR:VMAX\r'.format(bd=self.board,ch=channel) )
		linestr = response.decode('utf8')
		pattern = re.match(r'#BD:(\d*),CMD:(\w*),VAL:(\d*.\d*)', linestr, re.IGNORECASE)

		if pattern is not None:
			if pattern.group(2) == 'OK':
				voltage = float(pattern.group(3))
				return voltage
			else:
				print( pattern.group(2) )
				return 0.
		else:
			return 0.

	def get_current(self,channel):
		response = self.send_command( '$BD:{bd},CMD:MON,CH:{ch},PAR:IMON\r'.format(bd=self.board,ch=channel) )
		linestr = response.decode('utf8')
		pattern = re.match(r'#BD:(\d*),CMD:(\w*),VAL:(\d*.\d*)', linestr, re.IGNORECASE)

		if pattern is not None:
			if pattern.group(2) == 'OK':
				current = float(pattern.group(3))
				return current
			else:
				print( pattern.group(2) )
				return 0.
		else:
			return 0.

	def get_current_limit(self,channel):
		""" not tested !"""
		response = self.send_command( '$BD:{bd},CMD:MON,CH:{ch},PAR:ISET\r'.format(bd=self.board,ch=channel) )
		linestr = response.decode('utf8')
		pattern = re.match(r'#BD:(\d*),CMD:(\w*),VAL:(\d*.\d*)', linestr, re.IGNORECASE)

		if pattern is not None:
			if pattern.group(2) == 'OK':
				current = float(pattern.group(3))
				return current
			else:
				print( pattern.group(2) )
				return 0.
		else:
			return 0.

	def get_ramp_up(self,channel):
		"""Get voltage ramp up speed setting of the unit in V/s
		
		:param channel: The channel number in the module/board
		"""
		response = self.send_command( '$BD:{bd},CMD:MON,CH:{ch},PAR:RUP\r'.format(bd=self.board,ch=channel) )
		linestr = response.decode('utf8')
		pattern = re.match(r'#BD:(\d*),CMD:(\w*),VAL:(\d*.\d*)', linestr, re.IGNORECASE)

		if pattern is not None:
			if pattern.group(2) == 'OK':
				ramp = float(pattern.group(3))
				return ramp
			else:
				print( pattern.group(2) )
				return 0.
		else:
			return -1

	def get_ramp_down(self,channel):
		"""Get voltage ramp down speed setting of the unit in V/s
		
		:param channel: The channel number in the module/board
		"""
		response = self.send_command( '$BD:{bd},CMD:MON,CH:{ch},PAR:RDW\r'.format(bd=self.board,ch=channel) )
		linestr = response.decode('utf8')
		pattern = re.match(r'#BD:(\d*),CMD:(\w*),VAL:(\d*.\d*)', linestr, re.IGNORECASE)

		if pattern is not None:
			if pattern.group(2) == 'OK':
				ramp = float(pattern.group(3))
				return ramp
			else:
				print( pattern.group(2) )
				return 0.
		else:
			return -1

	def get_trip_time(self,channel):
		"""Get the trip time of the channel in s
		
		:param channel: The channel number in the module/board
		"""
		response = self.send_command( '$BD:{bd},CMD:MON,CH:{ch},PAR:TRIP\r'.format(bd=self.board,ch=channel) )
		linestr = response.decode('utf8')
		pattern = re.match(r'#BD:(\d*),CMD:(\w*),VAL:(\d*.\d*)', linestr, re.IGNORECASE)

		if pattern is not None:
			if pattern.group(2) == 'OK':
				ramp = float(pattern.group(3))
				return ramp
			else:
				print( pattern.group(2) )
				return 0.
		else:
			return -1

	def get_polarity(self,channel):
		"""Get the polarity of the channel
		
		:param channel: The channel number in the module/board
		"""
		response = self.send_command( '$BD:{bd},CMD:MON,CH:{ch},PAR:POL\r'.format(bd=self.board,ch=channel) )
		linestr = response.decode('utf8')
		pattern = re.match(r'#BD:(\d*),CMD:(\w*),VAL:(\w*)', linestr, re.IGNORECASE)

		if pattern is not None:
			if pattern.group(2) == 'OK':
				pol = pattern.group(3)
				return pol
			else:
				print( pattern.group(2) )
				return 'ERROR'
		else:
			return 'ERROR'

	def get_serial_number(self):
		"""Get the serial number of the board/module"""
		response = self.send_command( '$BD:{bd},CMD:MON,PAR:BDSNUM\r'.format(bd=self.board) )
		linestr = response.decode('utf8')
		pattern = re.match(r'#BD:(\d*),CMD:(\w*),VAL:(\w*)', linestr, re.IGNORECASE)

		if pattern is not None:
			if pattern.group(2) == 'OK':
				pol = str(pattern.group(3)).rstrip('\r')
				return pol
			else:
				print( pattern.group(2) )
				return 0.
		else:
			return -1

	def get_alarm(self):
		"""Get alarm status from the board"""
		response = self.send_command( '$BD:{bd},CMD:MON,PAR:BDALARM\r'.format(bd=self.board) )
		linestr = response.decode('utf8')
		pattern = re.match(r'#BD:(\d*),CMD:(\w*),VAL:(\d*)', linestr, re.IGNORECASE)

		if pattern is not None:
			if pattern.group(2) == 'OK':
				alarm = int(pattern.group(3))
				
				if alarm & 64:
					print( "Internal HV clock FAIL" )
				if alarm & 32:
					print( "Board in OVER POWER" )
				if alarm & 16:
					print( "Board in POWER FAIL" )
				if alarm & 8:
					print( "Ch3 in Alarm status" )
				if alarm & 4:
					print( "Ch2 in Alarm status" )
				if alarm & 2:
					print( "Ch1 in Alarm status" )
				if alarm & 1:
					print( "Ch0 in Alarm status" )
					
				return alarm;

			else:
				print( pattern.group(2) )
				return 0.
		else:
			return -1

	def clear_alarm(self):
		"""Clear alarm status from the board"""
		response = self.send_command( '$BD:{bd},CMD:SET,PAR:BDCLR\r'.format(bd=self.board) )
		return response.decode('utf8')

	def set_voltage(self,channel, voltage):
		"""The function sets the voltage of the given ``channel`` number to ``voltage``.
		The possible channel numbers are 0,1,2,3. Number 4 applies to ALL channels.

		:param channel: The channel number that the voltage setting is applied to.
		:param voltage: The voltage that is to be set for the channel in Volts.
		"""
		if float(voltage) > VOLTAGE_LIMIT: # safety check limit in the library
			return

		#
		response = self.send_command( '$BD:{bd},CMD:SET,CH:{ch},PAR:VSET,VAL:{val}\r'.format(bd=self.board,ch=channel,val=voltage) )
		return response.decode('utf8')

	def set_current_limit(self,channel, limit):
		"""The function sets the current limit of the given ``channel`` number
		to ``limit``.
		The possible channel numbers are 0,1,2,3. Number 4 applies to ALL channels.

		:param channel: The channel number that the current limit setting is applied to.
		:param limit: The current limit value that is to be set for the channel in units of nA.
		"""

		response = self.send_command( '$BD:{bd},CMD:SET,CH:{ch},PAR:ISET,VAL:{val}\r'.format(bd=self.board,ch=channel,val=limit) )
		return response.decode('utf8')

	def set_voltage_limit(self,channel, limit):
		"""The function sets the voltage limit of the given ``channel`` number
		to ``limit``.
		The possible channel numbers are 0,1,2,3. Number 4 applies to ALL channels.

		:param channel: The channel number that the voltage limit setting is applied to.
		:param limit: The voltage limit value that is to be set for the channel in units of Volts.
		"""
		
		response = self.send_command( '$BD:{bd},CMD:SET,CH:{ch},PAR:MAXV,VAL:{val}\r'.format(bd=self.board,ch=channel,val=limit) )
		return response.decode('utf8')


	def set_ramp_up(self,channel, n):
		"""The function sets the HV ramp up speed per channel.

		:param channel: The channel number in the module/board
		:param n: The desired ramp speed in V/s, minimum = 1, maximum = 50.
		"""

		if float(n) < 1.0 or float(n) > 50.0: return

		response = self.send_command( '$BD:{bd},CMD:SET,CH:{ch},PAR:RUP,VAL:{val}\r'.format(bd=self.board,ch=channel,val=n) )
		return response.decode('utf8')

	def set_ramp_down(self,channel, n):
		"""The function sets the HV ramp down speed per channel.

		:param channel: The channel number in the module/board
		:param n: The desired ramp speed in V/s, minimum = 1, maximum = 50.
		"""

		if float(n) < 1.0 or float(n) > 50.0: return

		response = self.send_command( '$BD:{bd},CMD:SET,CH:{ch},PAR:RDW,VAL:{val}\r'.format(bd=self.board,ch=channel,val=n) )
		return response.decode('utf8')

	def set_trip_time(self,channel, t):
		"""The function sets the trip time.

		:param channel: The channel number in the module/board
		:param t: The desired trip time in seconds minimum = 0 s, maximum = 1000 s
		"""

		if float(t) < 0.0 or float(t) > 1000.0: return

		response = self.send_command( '$BD:{bd},CMD:SET,CH:{ch},PAR:TRIP,VAL:{val}\r'.format(bd=self.board,ch=channel,val=t) )
		return response.decode('utf8')

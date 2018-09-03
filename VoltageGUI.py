#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Example GUI in wxPython to control multiple Mesytec MHV-4 units
# connected to USB ports.
# Joonas Konki - 04/06/2018

import wx
import mhv4lib
import time
from serial.tools import list_ports
import threading
import queues #File with definition of queue and queue elements

RAMP_VOLTAGE_STEP = 1	# the amount of voltage which is changed at once while ramping
RAMP_WAIT_TIME = 2	# the time between to voltage steps
VOLTAGE_LIMIT = 100	# maximal voltage which can be applied
USING_NEW_FIRMWARE = True
START_VOLTAGE=0.1	# the voltage which is set after turning on a channel, this is to be sure, that channels which are turned on have a 				voltage unequal to zero
UPDATE_TIME=3		# the voltages and currents are updated in the GUI every 3 s

#------------------------Defintion of events----------------------------------------------
#The events are necessary to prevent the GUI from freezing. For any change in the appearance of the GUI, an event is used.
#The events are binded to a specific method which is called by the event.
#Event for changing voltage
myEVT_COUNT = wx.NewEventType()
EVT_COUNT = wx.PyEventBinder(myEVT_COUNT, 1)
class CountEvent(wx.PyCommandEvent):
       """Event to signal that a count value is ready"""
       def __init__(self, etype, eid, value=None):
            """Creates the event object"""
            wx.PyCommandEvent.__init__(self, etype, eid)
            self._value = value
    
       def GetValue(self):
           """Returns the value from the event.
           @return: the value of this event
   
           """
           return self._value

#Event for enable or disable a channel.
myEnableChange = wx.NewEventType()
EVT_EnableChange = wx.PyEventBinder(myEnableChange, 1)
class EnableChange(wx.PyCommandEvent):
       """Event to signal that a count value is ready"""
       def __init__(self, etype, eid, value=None):
            """Creates the event object"""
            wx.PyCommandEvent.__init__(self, etype, eid)
            self._value = value
    
       def GetValue(self):
           """Returns the value from the event.
           @return: the value of this event
   
           """
           return self._value

#Event for changing the polarity of a channel.
myPolarityChange = wx.NewEventType()
EVT_PolarityChange = wx.PyEventBinder(myPolarityChange, 1)
class PolarityChange(wx.PyCommandEvent):
       """Evento signal that a count value is ready"""
       def __init__(self, etype, eid, value=None):
            """Creates the event object"""
            wx.PyCommandEvent.__init__(self, etype, eid)
            self._value = value
    
       def GetValue(self):
           """Returns the value from the event.
           @return: the value of this event
   
           """
           return self._value

#Event for updating the displayed values.
myUpdate = wx.NewEventType()
EVT_Update = wx.PyEventBinder(myUpdate, 1)
class Update(wx.PyCommandEvent):
       """Evento signal that a count value is ready"""
       def __init__(self, etype, eid, value=None):
            """Creates the event object"""
            wx.PyCommandEvent.__init__(self, etype, eid)
            self._value = value
    
       def GetValue(self):
           """Returns the value from the event.
           @return: the value of this event
   
           """
           return self._value

#-------------------Thread------------------------------------------------
#Thread which checks every 3 s (UPDATE_TIME) the current values and in between if any button was pressed. 
#If so, the voltage / polarity or are changed, or the channel will be turned on or off.
class CheckAndUpdater(threading.Thread):
	def __init__(self,unitView):
		"""
		@param parent: The gui object that should recieve the value
		@param value: value to 'calculate' to
		"""
		threading.Thread.__init__(self)
		self._parent = unitView
		self._updateCounter=0	#will increase after every time.sleep until it's equal to the UPDATE_TIME                          
   
	def run(self):
		"""Overrides Thread.run. Don't call this directly its called internally
		when you call Thread.start().
		"""
		while 1:
			if self._parent.Vqueue.isEmpty()==False: #Check if there is an element in the voltage change queue
				element=self._parent.Vqueue.root
				while element!=None:
					i=element.channel
					cur=self._parent.channelViews[i].unit.mhv4unit.getVoltage(i) #get the current voltage of the channel
					#time.sleep(0.1) 
					wan=self._parent.channelViews[i].wantedVoltage #get the wanted voltage
					if cur==0:
						print("Voltage of channel "+str(i)+" of unit "+self._parent.mhv4unit.name+" turned unexpectedly to zero!")
						self._parent.channelViews[i].changeVol=False #Ramping will be stopped and the element removed from the queue
						b=element.next
						self._parent.Vqueue.remove(element)
						element=b
					else:
						if (cur != wan):
							if abs(cur-wan) <= RAMP_VOLTAGE_STEP: 
								self._parent.channelViews[i].changeVol=False
								Cvalue = wan
								b=element.next
								self._parent.Vqueue.remove(element)
								element=b
							else:
								element=element.next
								if (wan - cur > 0) : Cvalue=cur+RAMP_VOLTAGE_STEP# going up	
								else : Cvalue = cur-RAMP_VOLTAGE_STEP # coming down
							evt = CountEvent(myEVT_COUNT, -1, Cvalue) #create the event that tells the GUI to update
							wx.PostEvent(self._parent.channelViews[i], evt) 
							cur=self._parent.channelViews[i].unit.mhv4unit.mhv4.set_voltage(i,Cvalue) #set the new voltage
						else:
							b=element.next
							self._parent.Vqueue.remove(element) #if the wanted voltage is equal to the current, remove elment from the queue
							element=b
			
			if self._parent.Pqueue.isEmpty()==False: #Check if there is an element in the changing polarity and enable/disable queue
				element=self._parent.Pqueue.root
				while element!=None:
					i=element.channel
					if(element.option==1): #Option 1 is enable/disable a channel
						newvalue=element.value
						evt1 = EnableChange(myEnableChange, -1, newvalue)
						wx.PostEvent(self._parent.channelViews[i], evt1)
						if 1 == newvalue :
							self._parent.channelViews[i].unit.mhv4unit.enableChannel(i)
							self._parent.channelViews[i].unit.mhv4unit.mhv4.set_voltage(i,START_VOLTAGE)
						if 0 == newvalue : 
							self._parent.channelViews[i].unit.mhv4unit.disableChannel(i)
					else: #a change in the polarity was requested
						newpolarity=element.value
						evt2 = PolarityChange(myPolarityChange, -1, 1)
						wx.PostEvent(self._parent.channelViews[i], evt2)
						self._parent.channelViews[i].unit.mhv4unit.setPolarity(i,newpolarity)
						#self._parent.channelViews[i].changePol=False
					b=element.next
					self._parent.Pqueue.remove(element)
					element=b
					
			time.sleep(RAMP_WAIT_TIME)
			self._updateCounter=self._updateCounter+RAMP_WAIT_TIME
			
			if self._updateCounter>=UPDATE_TIME:
				self._updateCounter=0
				#print(self._parent.mhv4unit.name+"Check started")
				for i in range(4):
					self._parent.mhv4unit.updateValues(i)
					evt3 = Update(myUpdate, -1, 1)
					wx.PostEvent(self._parent.channelViews[i], evt3)
					time.sleep(0.1)
					self._updateCounter=self._updateCounter+0.1
				#print(self._parent.mhv4unit.name+"Check ended")

#------------------------------------------------------------------------------------------#

class Channel:
	def __init__(self, parent, number):
		self.channel = number
		self.voltage = 0.
		self.current = 0.
		self.polarity = 0
		self.enabled = 0.

class Unit:
	def __init__(self, serial, name):
		self.port = ''
		self.mhv4 = None
		self.name = name
		self.serial = serial
		self.rampspeed = 0
		self.channels = []
		for i in [0,1,2,3]:
			self.channels.append(Channel(self,i))
			
	def connect(self):
		self.mhv4 = mhv4lib.MHV4(self.port, baud=9600)
		
	def disconnect(self):
		self.mhv4.close()
		
	def updateValues(self, channel=4):
		
		if self.mhv4 is None: # FOR DEBUGGING
			print("MHV4 unit %s not found?" % self.name)
			return
			
		if channel < 4: # update values for only one channel in the unit
			self.channels[channel].voltage = self.getVoltage(channel)
			self.channels[channel].current = self.getCurrent(channel)
			self.channels[channel].polarity=self.getPolarity(channel)
			self.channels[channel].polarity=self.getPolarity(channel)
			if self.channels[channel].enabled != 1:
				if self.channels[channel].voltage > 0.1:
					self.channels[channel].enabled = 1
				if self.getVoltagePreset(channel)!=0:
					self.setVoltage(channel,0)
			elif self.channels[channel].voltage==0:
				self.mhv4.set_off(channel)
				self.channels[channel].enabled = 0
			
			
		else :	# update on all channels in the unit
			for ch in self.channels:
				self.channels[ch.channel].polarity=self.getPolarity(ch.channel)
				ch.voltage = self.getVoltage(ch.channel)
				ch.current = self.getCurrent(ch.channel)
				if ch.voltage >= 0.1 :
					self.channels[ch.channel].enabled = 1
				elif self.channels[ch.channel].enabled == 1:
					self.mhv4.set_off(ch.channel)
					self.channels[ch.channel].enabled = 0
				if self.channels[ch.channel].enabled == 0 and self.getVoltagePreset(ch.channel)!=0:
					self.setVoltage(ch.channel,0)
				time.sleep(0.1)
	
	#if the voltage of a channel is zero, it will be turned off when starting the GUI
	def startCheck(self):
		for ch in self.channels:
			ch.voltage = self.getVoltage(ch.channel)
			if ch.voltage == 0.0 :
				self.mhv4.set_off(ch.channel)
		
	def enableChannel(self,channel):
		if self.getVoltage(channel) > 0.1 : 
			print("Unit %s channel %d is already ON ?" % (self.name, channel) )
			return
		self.mhv4.set_on(channel)
	
	def disableChannel(self,channel):
		self.mhv4.set_off(channel)
	
	def setPolarity(self,channel,pol):
		curvoltage = self.getVoltage(channel)
		if curvoltage < 0.1:
			self.mhv4.set_voltage_polarity(channel,pol)
			self.channels[channel].polarity = int(pol)
		else:
			print("Channel " + str(channel) + " is ON. Turn it off first.")

	def getPolarity(self, channel):
		pol =  self.mhv4.get_polarity(channel)
		self.channels[channel].polarity = pol
		return pol		
	
	def setVoltage(self,channel,voltage):
		if voltage > VOLTAGE_LIMIT: 
			print("Set voltage too high (limit is " + str(VOLTAGE_LIMIT) + " V).")
			return
		
		# Ramp voltage slowly up or down
		curvoltage = self.getVoltage(channel)	
		curvoltage = self.channels[channel].voltage		
		while abs(voltage - curvoltage) > RAMP_VOLTAGE_STEP:
			newvoltage = curvoltage
			if (voltage - curvoltage > 0) : newvoltage = int(curvoltage)+RAMP_VOLTAGE_STEP # going up
			else : newvoltage = int(curvoltage)-RAMP_VOLTAGE_STEP # coming down
			self.mhv4.set_voltage(channel, newvoltage)
			time.sleep(RAMP_WAIT_TIME) # wait time before taking the next voltage step
			curvoltage = self.getVoltage(channel)
			curvoltage = self.channels[channel].voltage
			self.updateValues(channel)
		
		# Finally after ramping, set the final requested value
		self.mhv4.set_voltage(channel, voltage)
		time.sleep(RAMP_WAIT_TIME)
		self.updateValues(channel)		

	def getVoltage(self,channel):
		return abs(self.mhv4.get_voltage(channel))
		
	def getVoltagePreset(self,channel): # Not in old firmware !
		return self.mhv4.get_voltage_preset(channel)
		
	def getCurrent(self,channel):
		return self.mhv4.get_current(channel)
			
class ChannelView(wx.StaticBox):
	def __init__(self,parent,number):
		wx.StaticBox.__init__(self, parent,number,"HV"+str(number),size=(220,160))
		self.number = number
		self.unit = parent

		#For Enable/Disable, change Polarity (elements are put in the queue only if these values are false
		self.EnDisable=False
		self.changePol=False
		self.changeVol=False

		#Event Handlers
		self.Bind(EVT_COUNT, self.voltageChange)
		self.Bind(EVT_EnableChange, self.EnDisabler)
		self.Bind(EVT_PolarityChange, self.polarityChanger)
		self.Bind(EVT_Update, self.updateValuesEvent)

		#self.voltageBox1 = wx.StaticBox(self, -1, "HV"+str(number), size=(220,180))
		self.bsizer1 = wx.GridBagSizer()
		self.voltageLabel = wx.StaticText(self, -1, "Voltage (V):")
		self.currentLabel = wx.StaticText(self, -1, "Current (uA):")
		self.voltageValue = wx.TextCtrl(self, -1, "0.0", size=(100, -1), style=wx.ALIGN_RIGHT|wx.TE_READONLY)
		self.currentValue = wx.TextCtrl(self, -1, "0.0", size=(100, -1), style=wx.ALIGN_RIGHT|wx.TE_READONLY)
		self.setVoltageValue = wx.TextCtrl(self, -1, "0", size=(100, -1), style=wx.ALIGN_RIGHT)
		self.setVoltageButton = wx.Button(self, number, "SET", (20, 80))
		self.Bind(wx.EVT_BUTTON, self.OnClickSetVoltageButton, self.setVoltageButton)
		
		self.polList = ['+', '-']
		self.polSizer = wx.BoxSizer(wx.VERTICAL)
		self.polrb = wx.RadioBox(
				self, -1, "Polarity", wx.DefaultPosition, wx.DefaultSize,
				self.polList, 2, wx.RA_SPECIFY_COLS
				)
		self.polrb.SetToolTip(wx.ToolTip("Select voltage polarity (+ or -)"))		
		self.Bind(wx.EVT_RADIOBOX, self.EvtPolarityRadioBox, self.polrb)
		
		self.enableList = ['ON', 'OFF']
		self.enableSizer = wx.BoxSizer(wx.VERTICAL)
		self.enablerb = wx.RadioBox(
				self, -1, "Enable channel", wx.DefaultPosition, wx.DefaultSize,
				self.enableList, 2, wx.RA_SPECIFY_COLS
				)
		self.enablerb.SetToolTip(wx.ToolTip("Set channel ON or OFF"))		
		self.Bind(wx.EVT_RADIOBOX, self.EvtEnableRadioBox, self.enablerb)
		
		self.bsizer1.Add(self.voltageLabel, (0,1), flag=wx.EXPAND )
		self.bsizer1.Add(self.voltageValue, (0,2), flag=wx.EXPAND )
		self.bsizer1.Add(self.currentLabel, (1,1), flag=wx.EXPAND )
		self.bsizer1.Add(self.currentValue, (1,2), flag=wx.EXPAND )
		self.bsizer1.Add(self.setVoltageValue, (2,1), flag=wx.EXPAND )
		self.bsizer1.Add(self.setVoltageButton, (2,2), flag=wx.EXPAND )
		self.bsizer1.Add(self.polrb, (3,1), flag=wx.EXPAND )
		self.bsizer1.Add(self.enablerb, (3,2), flag=wx.EXPAND )
		
		self.SetSizer(self.bsizer1)
		
		self.unit.mhv4unit.updateValues() # Get initial values from the unit
		self.wantedVoltage=self.unit.mhv4unit.channels[self.number].voltage	
		self.updateValues()               # Update GUI with the initial values
		
	def updateValues(self):
		curvoltage = self.unit.mhv4unit.channels[self.number].voltage
		curcurrent = self.unit.mhv4unit.channels[self.number].current
		curpolarity = self.unit.mhv4unit.channels[self.number].polarity
		curenable = self.unit.mhv4unit.channels[self.number].enabled
		curpolaritysel = 1 if (curpolarity == 0) else 0	# invert the selection that comes from the RadioBox !
		curenablesel   = 1 if (curenable == 0)   else 0 # invert the selection that comes from the RadioBox !
		if curenable == 1 : 
			self.enablerb.SetForegroundColour('#ff0000')
			self.polrb.Enable(False)
		else: 
			self.enablerb.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT))
			self.polrb.Enable(True)
		
		self.voltageValue.SetValue(str(curvoltage))
		self.currentValue.SetValue(str(curcurrent))
		self.polrb.SetSelection(curpolaritysel)
		self.enablerb.SetSelection(curenablesel)

	def updateValuesEvent(self,evt3):
		curvoltage = self.unit.mhv4unit.channels[self.number].voltage
		curcurrent = self.unit.mhv4unit.channels[self.number].current
		curpolarity = self.unit.mhv4unit.channels[self.number].polarity
		curenable = self.unit.mhv4unit.channels[self.number].enabled
		curpolaritysel = 1 if (curpolarity == 0) else 0	# invert the selection that comes from the RadioBox !
		curenablesel   = 1 if (curenable == 0)   else 0 # invert the selection that comes from the RadioBox !
		if curenable == 1 : 
			self.enablerb.SetForegroundColour('#ff0000')
			self.polrb.Enable(False)
		else: 
			self.enablerb.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT))
			self.polrb.Enable(True)
		
		self.voltageValue.SetValue(str(curvoltage))
		self.currentValue.SetValue(str(curcurrent))
		self.polrb.SetSelection(curpolaritysel)
		self.enablerb.SetSelection(curenablesel)
		
	def OnClickSetVoltageButton(self, event):
		newvoltage = float( self.setVoltageValue.GetValue() )
		if self.unit.mhv4unit.channels[self.number].enabled==0:
			print("Channel %d of unit %s is turned OFF, turn it ON first" % (self.number,self.unit.mhv4unit.name) )
			return
		
		if newvoltage > VOLTAGE_LIMIT: 
			print("Set voltage too high (limit is " + str(VOLTAGE_LIMIT) + " V).")
			return
		print("Set voltage of unit %s channel %d to %.2f" % (self.unit.mhv4unit.name, self.number, newvoltage) )
		self.wantedVoltage=newvoltage
		if self.changeVol==False: #if the channel is not already in the voltage change queue, an element representing the channel is put in the queue
			self.changeVol=True
			self.unit.Vqueue.add(queues.Element(self.number))

	def voltageChange(self,evt):
		newvoltage=evt.GetValue()
		self.unit.mhv4unit.channels[self.number].voltage = newvoltage
		self.voltageValue.SetValue(str(newvoltage))
		
		
	def EvtPolarityRadioBox(self, event):
		if self.unit.mhv4unit.channels[self.number].enabled == 1 or self.unit.mhv4unit.channels[self.number].voltage > 0.1 :
			print("Unit %s Channel %d is ON. Turn it off first." % (self.unit.mhv4unit.name, self.number) )
			return
		
		selection = self.polrb.GetSelection()
		newpolarity = 1 if (selection == 0) else 0 # invert the selection that comes from the RadioBox !
		print("Set polarity of unit %s channel %d to %d" % (self.unit.mhv4unit.name, self.number, newpolarity) )
			
		curpolaritysel = 1 if (newpolarity == 0) else 0	# invert the selection that comes from the RadioBox !
		self.polrb.SetSelection(curpolaritysel)		
		self.unit.Pqueue.add(queues.Element2(self.number,0,newpolarity))
		

	def polarityChanger(self,evt1):
		newpolarity=evt1.GetValue()
		curpolaritysel = 1 if (newpolarity == 0) else 0	# invert the selection that comes from the RadioBox !
		self.polrb.SetSelection(curpolaritysel)
		
		
	def EvtEnableRadioBox(self, event):
		selection = self.enablerb.GetSelection()
		if selection==1 and self.unit.mhv4unit.channels[self.number].voltage>0:
			self.wantedVoltage=0 #instead of turning the channel directly off an element is put in the voltage change queue changing the voltage to zero
			if self.changeVol==False:
				self.changeVol=True
				print("Set voltage of unit %s channel %d to %.2f" % (self.unit.mhv4unit.name, self.number, 0) )
				self.unit.Vqueue.add(queues.Element(self.number))
			
		else:
			newvalue = 1 if (selection == 0) else 0 # invert the selection that comes from the RadioBox !
			print("Set enable of unit %s channel %d to %d" % (self.unit.mhv4unit.name, self.number, newvalue) )
			self.unit.mhv4unit.channels[self.number].enabled = newvalue
			self.unit.Pqueue.add(queues.Element2(self.number,1,newvalue))

	def EnDisabler(self, evt2):
		newvalue=evt2.GetValue()
		if 1 == newvalue :
			self.voltageValue.SetValue(str(START_VOLTAGE))			
		self.unit.mhv4unit.channels[self.number].enabled = newvalue
		self.EnDisable=False
		selection = 1 if (newvalue == 0) else 0 
		self.enablerb.SetSelection(selection)
		if newvalue == 1 : 
			self.enablerb.SetForegroundColour('#ff0000')
			self.polrb.Enable(False)
		else: 
			self.enablerb.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT))
			self.polrb.Enable(True)

class UnitView(wx.Panel):	
	"""
	Class that displays all of the channels of one unit in one wx.Panel
	"""
   
	def __init__(self,parent, mhv4unit):
		wx.Panel.__init__(self, parent, size=(250,-1))
		self.mhv4unit = mhv4unit
		
		#self.SetBackgroundColour('#ededed') # Normal gray
		self.SetBackgroundColour('#f0f000') # Mesytec yellow
		self.unitNameLabel = wx.StaticText(self, label=self.mhv4unit.name)
		self.mhvPanSizer = wx.GridBagSizer()		
		self.mhvPanSizer.Add(self.unitNameLabel, (0, 0), span=(0,2), flag=wx.ALIGN_CENTER)
		
		self.channelViews = []
		#VoltageChange Queue
		self.Vqueue=queues.DoubleQueue()
		#Queue for Polarity Changes and Enable/Disable
		self.Pqueue=queues.DoubleQueue()
		
		for i in range(4):
			self.channelViews.append(ChannelView(self,i))
			self.mhvPanSizer.Add(self.channelViews[i], (2+i, 1))
			
		self.SetSizer(self.mhvPanSizer)
		#Thread Definition
		self.updater=CheckAndUpdater(self)
		self.updater.start()
	

class MHV4GUI(wx.Frame):

	def __init__(self, parent, mytitle, mymhv4units):
	
		self.mhv4units = mymhv4units
		width = 270+270*(abs(len(mymhv4units)-1))
		super(MHV4GUI, self).__init__(parent, title=mytitle,size=(width,740))

		self.InitUI()
		self.Centre()

	def InitUI(self):

		panel = wx.Panel(self)
		panel.SetBackgroundColour('#4f5049')
		vbox = wx.BoxSizer(wx.HORIZONTAL)
		
		for unit in self.mhv4units: # Create a view for each MHV4 unit
			vbox.Add(UnitView(panel, unit), wx.ID_ANY, wx.EXPAND | wx.ALL, 5)

		panel.SetSizer(vbox)


def main():

	mhv4units = []
	mhv4units.append(Unit('0318132','Recoil dE'))
	mhv4units.append(Unit('0318131','Recoil E' ))
	mhv4units.append(Unit('0318134','S1 & dE-E'))
	#mhv4units.append(Unit('0318133','dE-E'))
	
	print('Looking up ports for the MHV4 units in (/dev/tty*) ...')
	ports = list_ports.comports()
	print(ports[0].serial_number)
	print(ports[1].serial_number)
	foundmhv4units = []
	for unit in mhv4units:
		for port in ports:
			if port.serial_number == unit.serial:
				unit.port = port.device
				print("Found MHV-4 unit (" + str(unit.serial) + "," + str(unit.name) + ") in port: " + str(unit.port) )
				break
		if unit.port == '':
			print("MHV-4 unit (" + str(unit.serial) + "," + str(unit.name) + ") was not found.")	
			#foundmhv4units.append(unit) # UNCOMMENT HERE TO DEBUG AND TEST WITH 'DUMMY' UNITS
		else :
			foundmhv4units.append(unit)
			unit.connect()
			unit.startCheck()
			unit.updateValues()

			#unit.mhv4unit.updateValues()
	
	if ( 0 == len(foundmhv4units) ) :
		print('No MHV-4 units found in any of the USB ports with the given serial numbers!')
		print('Exiting....')
		exit()
		
	app = wx.App()
	gui = MHV4GUI(None, 'MHV4GUI', foundmhv4units)
	gui.Show()
	app.MainLoop()


if __name__ == '__main__':
	main()
	

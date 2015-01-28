# -*- Mode: Python; coding: utf-8; indent-tabs-mode: tab; tab-width: 2 -*-
### BEGIN LICENSE
# Copyright (C) 2010 <Atreju Tauschinsky> <Atreju.Tauschinsky@gmx.de>
# This program is free software: you can redistribute it and/or modify it 
# under the terms of the GNU General Public License version 3, as published 
# by the Free Software Foundation.
# 
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranties of 
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR 
# PURPOSE.  See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along 
# with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE

'''interface to NIDAQmx analog input cards'''

import ctypes


import logging
logger = logging.getLogger('starkalyzer')

##############################
# Setup some typedefs and constants
# to correspond with values in
# C:\Program Files\National Instruments\NI-DAQ\DAQmx ANSI C Dev\include\NIDAQmx.h
# the typedefs

#pylint: disable=C0103

int32 = ctypes.c_long
uInt32 = ctypes.c_ulong
uInt64 = ctypes.c_ulonglong
float64 = ctypes.c_double
TaskHandle = uInt32
# the constants
DAQmx_Val_Cfg_Default = int32(-1)
DAQmx_Val_Volts = 10348
DAQmx_Val_Rising = 10280
DAQmx_Val_FiniteSamps = 10178
DAQmx_Val_ContSamps = 10123
DAQmx_Val_GroupByChannel = 0
DAQmx_Val_GroupByScanNumber = 1
DAQmx_Val_DMA = 10054 
DAQmx_Val_Interrupts = 10204
DAQmx_Val_ProgrammedIO = 10264
##############################


class NIDAQInputSimulator:
	'''simulator, used only if hardware is absent'''
	#pylint: disable=C0321,C0111,R0913,C0103,W0613 
	def __init__(self): pass
	@staticmethod
	def DAQmxCreateTask(TaskName, handle): logger.debug("Called DAQmxCreateTask in Simulator")
	@staticmethod
	def DAQmxStartTask(handle): logger.debug("Called DAQmxStartTask in Simulator")
	@staticmethod
	def DAQmxStopTask(handle): logger.debug("Called DAQmxStopTask in Simulator")
	@staticmethod	
	def DAQmxClearTask(handle): logger.debug("Called DAQmxClearTask in Simulator")
	@staticmethod
	def DAQmxCfgSampClkTiming(handle, Source, Rate, ActiveEdge, SampleMode, sampsPerChanToAcquire): logger.debug("Called DAQmxCfgSampleClkTiming in Simulator")
	@staticmethod
	def DAQmxCreateAOVoltageChan(handle, PhysicalChannel, NameToAssignToChannel, MinVal, MaxVal, Units, CustomScaleName): pass # logger.debug("Called DAQmxCreateAOVoltageChan in Simulator")
	@staticmethod
	def DAQmxWriteAnalogF64(handle, NumSampsPerChan, AutoStart, Timeout, DataLayout, WriteArray, sampsPerChanWritten, Reserved): logger.debug("Called DAQmxWriteAnalogF64 in Simulator")
	@staticmethod
	def DAQmxCfgDigEdgeStartTrig(handle, startTrigger, startEdge): logger.debug("Called DAQmxCfgDigEdgeStartTrig in Simulator")
	@staticmethod
	def DAQmxGetErrorString(error, buff, buffersize): pass
	@staticmethod
	def DAQmxCfgOutputBuffer(handle, buffersize): pass
	@staticmethod
	def DAQmxSetAODataXferMech(handle, PhysicalChannel, value): pass
	@staticmethod
	def DAQmxCreateAIVoltageChan(taskHandle, physicalChannel, nameToAssignToChannel, terminalConfig, minVal, maxVal, units, customScaleName): pass
	@staticmethod
	def DAQmxReadAnalogF64(handle, noSamples, timeout, fillMode, readArray, arraySizeInSamps, sampsPerChanRead, reserved): pass
	@staticmethod
	def DAQmxSetStartTrigType(taskHandle, data): pass
	@staticmethod
	def DAQmxCfgDigEdgeRefTrig(taskHandle, triggerSource, triggerEdge, pretriggerSamples): pass


class NIDAQInputController:
	'''interface to DAQmx controlled NI analog output cards'''
	def __init__(self):
		try:
			self.__nidaq = ctypes.windll.nicaiu # load the DLL
		except AttributeError: # on error, use the simulator
			logger.warn("can't load NIDAQ driver, using simulator")
			self.__nidaq = NIDAQInputSimulator()
		self.taskIsConfigured = False
		self.taskIsRunning = False
		
	def initialize(self, noSamples, samplesPerSecond, channels):
		'''initializing NIDAQ Input Hardware'''
		if self.taskIsConfigured:
			logger.error('tried to re-initialize nidaq controller while task was not cleared, call shutdown first')
			return
			
				
		logger.debug('initializing NIDAQ AI')
		self.__taskHandle = TaskHandle(0)
		self.CHK(self.__nidaq.DAQmxCreateTask("", ctypes.byref(self.__taskHandle)))
		
		
		# apparently these have to be sorted in the order of the data array below
		# limits still need ot be set properly?!
		
		for dev in sorted(channels.keys()):
			self.CHK(self.__nidaq.DAQmxCreateAIVoltageChan(self.__taskHandle, dev, "", -1, float64(channels[dev][0]), float64(channels[dev][1]), DAQmx_Val_Volts, None))
		
		self.CHK(self.__nidaq.DAQmxCfgSampClkTiming(self.__taskHandle, "", float64(samplesPerSecond), DAQmx_Val_Rising, DAQmx_Val_FiniteSamps, uInt64(noSamples)))

		self.CHK(self.__nidaq.DAQmxSetStartTrigType(self.__taskHandle, int32(10150)))
		self.CHK(self.__nidaq.DAQmxCfgDigEdgeRefTrig(self.__taskHandle, "/dev3/PFI0", int32(10280), uInt32(noSamples/2)))
		
		self.noChannels = len(channels)
		self.noSamples = noSamples
		
		self.taskIsConfigured = True
		
		logger.info("NIDAQ Controller initialized")


	def CHK( self, err ):
		"""a simple error checking routine"""
		if err is None:
			return
		if err < 0:
			buf_size = 200
			buf = ctypes.create_string_buffer('\000' * buf_size)
			self.__nidaq.DAQmxGetErrorString(err, ctypes.byref(buf), buf_size)
			logger.error('nidaq call failed with error %d: %s'%(err, repr(buf.value)))
		if err > 0:
			buf_size = 200
			buf = ctypes.create_string_buffer('\000' * buf_size)
			self.__nidaq.DAQmxGetErrorString(err, ctypes.byref(buf), buf_size)
			logger.error('nidaq generated warning %d: %s'%(err, repr(buf.value)))
	
	def readData(self):
		sRead = int32(0)
		tmp = self.noSamples*self.noChannels
		buffType = float64*tmp
		buff = buffType(*[0]*tmp)

		self.__nidaq.DAQmxReadAnalogF64(self.__taskHandle, int32(self.noSamples), float64(200), DAQmx_Val_GroupByChannel, ctypes.byref(buff), uInt32(tmp), ctypes.byref(sRead), None)
		
		logger.debug(str(sRead.value) + " samples read")
		return buff	
	
	def startTask(self):
		'''start task'''
		logger.debug('starting NIDAQ tasks')
		self.CHK(self.__nidaq.DAQmxStartTask(self.__taskHandle))
		self.taskIsRunning = True
		
	def stopTask(self):
		'''stop task'''
		logger.debug('stopping NIDAQ tasks')
		self.CHK(self.__nidaq.DAQmxStopTask(self.__taskHandle))
		self.taskIsRunning = False

	def shutdown(self):
		'''shutdown interface'''
		self.CHK(self.__nidaq.DAQmxClearTask(self.__taskHandle))
		self.taskIsConfigured = False


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

'''interface to control viewpoint dio64 card'''


from labalyzer.LabalyzerSettings import settings
import ctypes

import time # only for testing purposes

import logging
logger = logging.getLogger('labalyzer')

##############################
# Setup some typedefs and constants

DIO64_CLCK_INTERNAL = 0
DIO64_CLCK_EXTERNAL = 1
DIO64_CLCK_TRIG_0 = 2
DIO64_CLCK_OCXO = 3

DIO64_STRT_NONE = 0
DIO64_STRT_EXTERNAL = 1
DIO64_STRT_TRIG_2 = 2
DIO64_STRT_PXI_STAR = 3

DIO64_STRTTYPE_LEVEL = 0
DIO64_STRTTYPE_EDGETOEDGE = 2
DIO64_STRTTYPE_EDGE = 4

DIO64_STOP_NONE = 0
DIO64_STOP_EXTERNAL = 1
DIO64_STOP_TRIG_3_IN = 2
DIO64_STOP_OUTPUT_FIFO = 3

DIO64_STOPTYPE_EDGE = 0

DIO64_TRIG_RISING = 0
DIO64_TRIG_FALLING = 1

DIO64_AI_NONE = 0

DIO64_ATTR_OUTPUTBUFFERSIZE	=	3

USHORT = ctypes.c_ushort
ULONG = ctypes.c_ulong

class DIO64STAT (ctypes.Structure):
	'''needed to interface with c library'''
	_fields_ = [("pktsize", USHORT), ("portCount", USHORT), ("writePtr", USHORT), ("readPtr", USHORT),
							("time", USHORT*2), ("fifoSize", ULONG), ("fifo0", USHORT), ("ticks", ULONG),
							("flags", USHORT), ("clkControl", USHORT), ("startControl", USHORT), ("stopControl", USHORT),
							("AIControl", ULONG), ("AICurrent", USHORT), ("startTime", USHORT*2), ("stopTime", USHORT*2), ("user", USHORT*4)]

class ViewpointSimulator:
	'''simulate dio64 on computers where hardware is not available, used only for development'''
	#pylint: disable=C0321,C0111,R0913,C0103,W0613 
	def __init__(self): self._startTime = None
	@staticmethod
	def DIO64_Open(board, baseio): logger.debug("Called DIO64_Open in Simulator")
	@staticmethod
	def DIO64_Mode(board, mode): logger.debug("Called DIO64_Mode in Simulator")
	@staticmethod
	def DIO64_Load(board, rbfFile, intputHint, outputHint): logger.debug("Called DIO64_Load in Simulator")
	@staticmethod
	def DIO64_Close(board): logger.debug("Called DIO64_Close in Simulator")
	@staticmethod
	def DIO64_In_Start(board, ticks, mask, maskLength, flags, clkControl, startType, startSource, stopType, stopSource, AIControl, scanRate): logger.debug("Called DIO64_In_Start in Simulator")
	@staticmethod
	def DIO64_Out_Config(board, ticks, mask, maskLength, flags, clkControl, startType, startSource, stopType, stopSource, AIControl, reps, ntrans, scanRate): logger.debug("Called DIO64_Out_Config in Simulator")
	def DIO64_Out_Start(self, board):
		self._startTime = time.time()
		logger.debug("Called DIO64_Out_Start in Simulator")
	def DIO64_Out_Status(self, board, scansAvail, status):
		if self._startTime:
			delta_t = (time.time() - self._startTime)*1000
			ust2 = ctypes.c_ushort * 2
			ust4 = ctypes.c_ushort * 4
			dt = int(delta_t*settings['DigitalSamplesPerMillisecond'])
			ub = dt & 0x0000FFFF
			lb = dt >> 16
			os = DIO64STAT(0, 0, 0, 0, ust2(ub, lb), 0, 0, 0, 0, 0, 0, 0, 0, 0, ust2(0, 0), ust2(0, 0), ust4(0, 0, 0, 0))
			# logger.debug("Called DIO64_Out_Status in Simulator")
			return os
	@staticmethod
	def DIO64_Out_Write(board, buff, bufsize, status): logger.debug("Called DIO64_Out_Write in Simulator")
	@staticmethod
	def DIO64_Out_Stop(board): logger.debug("Called DIO64_Out_Stop in Simulator")
	@staticmethod
	def DIO64_SetAttr(board, attrID, value): logger.debug("Called DIO64_SetAttr in Simulator")
	@staticmethod
	def DIO64_GetAttr(board, attrID, value): logger.debug("Called DIO64_GetAttr in Simulator")
	@staticmethod
	def DIO64_Out_ForceOutput(board, buff, mask): logger.debug("Called DIO64_Out_ForcedOutput in Simulator")


class ViewpointController:
	'''interface to viewpoint dio64 card'''
	# still has to be extended to cater to two boards!
	def __init__(self):
		try:
			self.__dio = ctypes.windll.dio64_32 # load the DLL
			self.simulate = False
		except AttributeError: # on error, use the simulator
			logger.warn("can't load DIO driver, using simulator!")
			self.__dio = ViewpointSimulator()
			self.simulate = True

	def initialize(self):
		'''initialize dio64 hardware'''
		self.__dio.DIO64_Open(0, 0) # second parameter (base IO) is for backwards compatibility only, and not relevant here. the first is the board number
		self.__dio.DIO64_SetAttr(0, DIO64_ATTR_OUTPUTBUFFERSIZE, 16777216) # set output buffer size, strange things happen otherwise
		self.__dio.DIO64_Load(0, "", 0, 4) # use only output ports. the right programme for the FPGA is automatically loaded if hints about number of input/output ports are supplied

		maskType = ctypes.c_ushort*4
		mask = maskType(0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF)
		scanrate = ctypes.c_double(0)
		self.__dio.DIO64_Out_Config(0, 3, ctypes.byref(mask), 4, 0, DIO64_CLCK_INTERNAL, DIO64_STRTTYPE_LEVEL+DIO64_TRIG_RISING, DIO64_STRT_NONE, DIO64_STOPTYPE_EDGE+DIO64_TRIG_RISING, DIO64_STOP_NONE, 0, 1, 0, ctypes.byref(scanrate))
		# second parameter: 4 ticks (always add one) means 10 MHz for the 40 MHz clock source we have
		logger.info("Viewpoint Controller initialized")

	def programmeChannels(self, diodata):
		'''programme TF data to dio64 hardware'''
		logger.debug('programming viewpoint')
		dioStatus = DIO64STAT()
		scansAvailable = ctypes.c_uint16(0)

		maskType = ctypes.c_ushort*4
		mask = maskType(0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF)
		scanrate = ctypes.c_double(0)
		self.__dio.DIO64_Out_Config(0, 3, ctypes.byref(mask), 4, 0, DIO64_CLCK_INTERNAL, DIO64_STRTTYPE_LEVEL+DIO64_TRIG_RISING, DIO64_STRT_NONE, DIO64_STOPTYPE_EDGE+DIO64_TRIG_RISING, DIO64_STOP_NONE, 0, 1, 0, ctypes.byref(scanrate))
		# second parameter: 4 ticks (always add one) means 10 MHz for the 40 MHz clock source we have

		self._timeframeLength = (diodata[-6]	| diodata[-5] << 16)/settings['DigitalSamplesPerMillisecond']
		self.__dio.DIO64_Out_Status(0, ctypes.byref(scansAvailable), ctypes.byref(dioStatus)) # necessary?
		self.__dio.DIO64_Out_Write(0, diodata.ctypes.data, len(diodata)/6, ctypes.byref(dioStatus))

	def start(self):
		'''start exection of programmed data'''
		logger.debug('starting viewpoint output')
		self.__dio.DIO64_Out_Start(0)
		
	def directOutput(self, data, port):
		'''force direct output'''
		# data is 16 bit data to be written to port
		# port is 0-3, thus addressing port A-D.
		# each port is addressed separately, this function 
		# does not allow to update two ports (e.g. A and B) to 
		# update simultaneously.
		# however, all lines within a port need to be updated 
		# together.
		bufftype = 4*ctypes.c_uint16
		buff = bufftype(data, data, data, data)
		self.__dio.DIO64_Out_ForceOutput(0, ctypes.byref(buff), 2**port)

	def getPercentageComplete(self):
		'''find out how far along in a timeframe we are'''
		dioStatus = DIO64STAT()
		scansAvailable = ctypes.c_uint16(0)
		if self.simulate:
			dioStatus = self.__dio.DIO64_Out_Status(0, ctypes.byref(scansAvailable), ctypes.byref(dioStatus))
		else:
			self.__dio.DIO64_Out_Status(0, ctypes.byref(scansAvailable), ctypes.byref(dioStatus))
		elapsedTime = (dioStatus.time[1]<<16 | dioStatus.time[0])/settings['DigitalSamplesPerMillisecond']
		return 1.*elapsedTime/self._timeframeLength

	def stop(self):
		'''stop task'''
		self.__dio.DIO64_Out_Stop(0)
		

	def shutdown(self):
		'''shutdown'''
		self.__dio.DIO64_Out_Stop(0)
		self.__dio.DIO64_Close(0)

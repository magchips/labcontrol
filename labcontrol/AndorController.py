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

'''controller for andor cameras'''

import ctypes # dll interface
import numpy  # buffer allocation


# only for testing
#############################
from math import exp # only for test images!
import time # only for test images
#########################

from labalyzer.LabalyzerSettings import settings

import logging
logger = logging.getLogger('labalyzer')


# defines from atmcd32d.h
DRV_SUCCESS = 20002
DRV_IDLE = 20073
DRV_ACQUIRING = 20072


class AndorSimulator:
	'''simulator, used only if hardware not present'''
	#pylint: disable=C0321,C0111,R0913,C0103,W0613 
	def __init__(self): pass
	def Initialize(self, directory): pass
	def SetADChannel(self, channel): pass
	def SetHSSpeed(self, speedType, index): pass
	def SetVSSpeed(self, index): pass
	def GetVSSpeed(self, index, speed): pass
	def GetHSSpeed(self, a, b, c, d): pass
	def SetShutter(self, typ, mode, closingtime, openingtime): pass
	def SetTriggerMode(self, mode): pass
	def GetDetector(self, xpixels, ypixels): pass
	def SetPreAmpGain(self, index): pass
	def GetPreAmpGain(self, index, gain): pass
	def SetTemperature(self, temperature): pass
	def CoolerON(self): pass
	def CoolerOFF(self): pass
	def GetTemperature(self, temperature): pass
	def GetNumberNewImages(self, first, last): pass
	def GetStatus(self, status): pass
	def GetOldestImage(self, arr, size): pass
	def GetOldestImage16(self, arr, size): pass
	def GetMostRecentImage(self, arr, size): pass
	def SetReadMode(self, mode): pass
	def SetImage(self, hBin, vBin, hStart, hEnd, vStart, vEnd): pass
	def SetAcquisitionMode(self, mode): pass
	def SetNumberAccumulations(self, number): pass
	def SetNumberKinetics(self, number): pass
	def SetExposureTime(self, exposureTime): pass
	def StartAcquisition(self): pass
	def Shutdown(self): pass

class AndorController:
	'''interface to andor camera'''
	def __init__(self):
		try:
			self.__andor = ctypes.windll.atmcd32d
			self.simulate = False
		except:
			logger.warn("can't load Andor driver, using simulator")
			self.__andor = AndorSimulator()
			self.simulate = True
		# for testing only!
		############################
		if self.simulate:
			width = 600
			height = 800
			self.darkImage = numpy.asarray(200.*numpy.random.random((width, height)), dtype=numpy.uint16)
			self.lightImage = 65000.*numpy.ones([width, height], dtype=numpy.uint16)
			#self.absImage = numpy.empty([width, height], dtype=numpy.uint16)
			self.baseImage = numpy.empty([width, height], dtype=numpy.float)
			for i in range(width):
				for j in range(height):
					#self.absImage[i][j] = 65000. - 64000*exp(-(i-width/2.-100)**2/120**2 - (j-height/2.-100)**2/90**2)
					self.baseImage[i][j] = 1.*exp(-(i-width/2.-100)**2/120**2 - (j-height/2.-100)**2/90**2)
			self.imageCounter = 0
			self.startTime = 0
			self.cycleCount = 0
		###############################

	def initialize(self):
		'''initialize camera'''
		self.__andor.Initialize("")
		self.__andor.SetADChannel(1)
		self.__andor.SetHSSpeed(0, 0) #CHECK! first parameter might have to be 1
		hspeed = ctypes.c_float(0)
		self.__andor.GetHSSpeed(0, 0, 0, ctypes.byref(hspeed)) # first parameter is AD channel, same as in SetADChannel above
		self.__andor.SetVSSpeed(1)
		vspeed = ctypes.c_float(0)
		self.__andor.GetVSSpeed(1, ctypes.byref(vspeed))
		self.__andor.SetShutter(0, 1, 0, 0) # typ = 0: TTL Low to open; mode = 1: always open
		self.__andor.SetTriggerMode(1) # 1 = External
		xpx = ctypes.c_int(0)
		ypx = ctypes.c_int(0)
		self.__andor.GetDetector(ctypes.byref(xpx), ctypes.byref(ypx))
		self.__andor.SetPreAmpGain(2) # 2 is the index of the gain we want. stupid...
		gain = ctypes.c_float(0)
		self.__andor.GetPreAmpGain(2, ctypes.byref(gain)) # now we get an actual number out
		self.__andor.SetTemperature(settings['andor.temp'])
		self.__andor.CoolerON()
		logger.info("Andor Controller Initialized")

	def startAcquisition(self, data):
		'''start acquisition'''
		logger.debug('starting camera acquisition')
		self.__andor.SetReadMode(4)
		self.__andor.SetImage(data["Binning"], data["Binning"], data["X min"], data["X max"], data["Y min"], data["Y max"])
		self.size_x = data["X max"] - data["X min"] + 1
		self.size_y = data["Y max"] - data["Y min"] + 1

		self.__andor.SetAcquisitionMode(3)
		self.__andor.SetNumberAccumulations(1)
		self.__andor.SetNumberKinetics(3)
		#self.__andor.SetExposureTime(ctypes.c_float(data["Exposure"]))
		self.__andor.SetExposureTime(ctypes.c_float(0))
		self.__andor.StartAcquisition()

		## only for testing
		##########################
		if self.simulate:
			self.startTime = time.time()
			self.cycleComplete = False
		##########################

	def shutdown(self):
		'''turn off camera'''
		self.__andor.CoolerOFF()
		self.__andor.Shutdown()

	def getImage(self):
		'''retrieve oldest image available'''
		logger.debug('retrieving image from andor camera')
		if self.simulate:
			if self.imageCounter == 0:
				self.imageCounter += 1
				self.cycleCount += 1
				ind = self.cycleCount % 10 + 1
				mul = 64000*exp(-(ind-5)**2)
				return self.lightImage - self.baseImage*mul
			if self.imageCounter == 1:
				self.imageCounter += 1
				return self.lightImage
			if self.imageCounter == 2:
				self.imageCounter = 0
				return self.darkImage
		# TODO: Size is wrong if Binning is != 1
		img = numpy.zeros((self.size_y, self.size_x), dtype=numpy.uint16)
		self.__andor.GetOldestImage16(img.ctypes.data, self.size_x*self.size_y)
		return img

	def getNumberAvailableImages(self):
		'''return number of images available on camera'''
		# only for testing
		########################
		if self.simulate:
			if self.cycleComplete:
				return 0
			dt = time.time()-self.startTime
			rt = 0
			if dt > 7:
				self.cycleComplete = True
				rt = 3
			elif dt > 6:
				rt = 2
			elif dt > 5:
				rt = 1
			return rt
		################
		status = ctypes.c_int(0)
		self.__andor.GetStatus(ctypes.byref(status))
		if status.value != DRV_IDLE:
			return 0
		first = ctypes.c_long(0)
		last = ctypes.c_long(0)
		self.__andor.GetNumberNewImages(ctypes.byref(first), ctypes.byref(last))
		print first, last
		return last.value - first.value + 1

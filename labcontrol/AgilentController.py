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

''' Controller for Agilent 33250A Function Generator, via VISA. could also control other visa devices'''

import logging
logger = logging.getLogger('starkalyzer')

class AgilentSimulator:
	'''simulator, if visa is not present'''
	#pylint: disable=C0321,C0111,R0913,C0103,W0613 
	def __init__(self):
		self.lastCommand = None
	
	def read(self): 
		return None
	def write(self, string): 
		'''visa command write function'''
		self.lastCommand = string


class AgilentController:
	'''interface to Tektronix oscilloscopes'''
	def __init__(self):
		try:
			import visa #pylint: disable=F0401
			# try-clause
			self.__agilent = visa.instrument('TCPIP0::10.0.0.3::gpib0,10::INSTR', timeout = 1)
		except ImportError:
			logger.warn("can't load visa driver for Agilent function generator, using simulator")
			self.__agilent = AgilentSimulator()


	def initialize(self):
		'''hardware initialization'''
		pass
		
	
	def setFrequency(self, frequency):
		self.__agilent.write('FREQ ' + str(frequency*1e6))
	
	def setAmplitude(self, amplitude):
		self.__agilent.write('VOLT ' + str(amplitude))
	
	def setOffset(self, offset):
		self.__agilent.write('VOLT:OFFS ' + str(offset))
	
	def setSine(self, frequency, amplitude, offset):
		self.__agilent.write('APPL:SIN ' + str(frequency*1e6) + ',' + str(amplitude) + ',' + str(offset))
	
	def setDC(self, voltage):
		self.__agilent.write('APPL:DC DEF,DEF,' + str(voltage)) 
	
		
	def toggleOutput(self, outputOn):
		pass
		
	def setImpedance(self, impedanceHigh=True):
		pass

		
if __name__ == '__main__':
	pass

	

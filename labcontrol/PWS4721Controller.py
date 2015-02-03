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

''' Controller for Tektronix PWS4721 Voltage Supply, via VISA. could also control other visa devices'''


import logging
logger = logging.getLogger('labalyzer')

class PWS4721Simulator:
	'''simulator, if visa is not present'''
	#pylint: disable=C0321,C0111,R0913,C0103,W0613 
	def __init__(self):
		self.lastCommand = None
	
	def read(self): 
		return None
	def write(self, string): 
		'''visa command write function'''
		self.lastCommand = string


class PWS4721Controller:
	'''interface to Tektronix oscilloscopes'''
	def __init__(self):
		try:
			import visa #pylint: disable=F0401
			self.__pws = visa.instrument('USB0::0x0699::0x0394::081003126669001010::INSTR', timeout = 1)
			logger.warn('PWS4721 programmable voltage source loaded')
		except:
			logger.warn("can't load visa driver for PWS4721, using simulator")
			self.__pws = PWS4721Simulator()

	def startOutput(self,data):
		voltage=data["Voltage"]
		self.setVoltage(voltage)
		logger.debug('Voltage generator set to ' + str(data['Voltage']) + ' Volts')   

	def initialize(self):
		'''hardware initialization'''
		self.__pws.write('VOLTAGE ' + str(0))
		
	
	def setVoltage(self, voltage):
		self.__pws.write('VOLTAGE ' + str(voltage))
		self.__pws.write('OUTPUT ON') # urgs should not be here


		
if __name__ == '__main__':
	pass

	

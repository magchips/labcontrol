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

''' Controller for Tektronix 3054C, via VISA. could also control other visa devices'''

# from labalyzer.LabalyzerSettings import settings
from array import array

import logging
logger = logging.getLogger('labalyzer')

class ScopeSimulator:
	'''simulator, if visa is not present'''
	#pylint: disable=C0321,C0111,R0913,C0103,W0613 
	def __init__(self):
		self.lastCommand = None
	
	def read(self): 
		'''visa command read function'''
		if self.lastCommand == 'WFMP?':
			# return waveform header
			return '2;16;BIN;RI;LSB;10000;"Ch1, DC coupling, 1.0E-3 V/div, 4.0E-5 s/div, 10000 points, Sample mode";Y;4.0E-8;0;-8.16E-5;"s";1.5625E-7;0.0E0;7.424E3;"V"'
		elif self.lastCommand == 'CURVE?':
			# return waveform data
			ar = array('h', 10000*[0])
			return '#520000' + ar.tostring()
		elif self.lastCommand == 'WFMP:XZERO?': return '-8.16E-5'
		elif self.lastCommand == 'WFMP:XINCR?': return '4.0E-8'
		elif self.lastCommand == 'WFMP:YZERO?': return '0.0E0'
		elif self.lastCommand == 'WFMP:YMULT?': return '1.5625E-7'
		elif self.lastCommand == 'WFMP:YOFF?': return '7.424E3'
		else:
			return None
	def write(self, string): 
		'''visa command write function'''
		self.lastCommand = string


class ScopeController:
	'''interface to Tektronix oscilloscopes'''
	def __init__(self):
		try:
			import visa #pylint: disable=F0401
			# try-clause
			self.__scope = visa.instrument('TCPIP0::192.168.1.206::inst0::INSTR', timeout = 1) # used to be 192.168.1.221
		except ImportError:
			logger.warn("can't load visa/Scope driver, using simulator")
			self.__scope = ScopeSimulator()
		except:
			self.__scope = ScopeSimulator()
			print "UNDIAGNOSED SCOPE PROBLEM"


	def initialize(self):
		'''hardware initialization'''
		self.__scope.write('DAT:WID 2')
		self.__scope.write('DAT:ENC SRI')
		
	
	def getTrace(self, channel):
		'''measure trace from scope, using channel number "channel"'''
		try: 
			import visa #urgh, that's what I get for importing modules in __init__
		except ImportError:
			pass
		try:
			self.__scope.write('DAT:SOU Ch' + str(channel))
			self.__scope.write('WFMP:XZERO?')
			x0 = float(self.__scope.read())
			self.__scope.write('WFMP:XINCR?')
			xIncr = float(self.__scope.read())
			self.__scope.write('WFMP:YZERO?')
			y0 = float(self.__scope.read())
			self.__scope.write('WFMP:YMULT?')
			yMult = float(self.__scope.read())
			self.__scope.write('WFMP:YOFF?')
			yOff = float(self.__scope.read())

			self.__scope.write('CURVE?')
			data = self.__scope.read()
			startIndex = 2 + int(data[1]) # there is a 'second header' of sorts, saying how long the data is; we don't need it.
			yval = array('h')
			try:
				yval.fromstring(data[startIndex:])
			except ValueError:
				print "ERROR converting scope data!"
				return None, None
		
			xvalues = [x0 + xIncr*x for x in range(10000)]
			yvalues = [(y - yOff)*yMult + y0 for y in yval]
			return xvalues, yvalues
		except visa.VisaIOError:
			logger.error('Timeout occured while acquiring scope data!. Make sure there is a trace to acquire!')
			return None

		
if __name__ == '__main__':
	s = ScopeController()
	s.initialize()
	import matplotlib.pyplot as plt
	import csv
	
	results = []
	for c in [1]:
		results.extend(s.getTrace(c))
		with open('test_scope.csv', 'wb') as ifile:
			writer = csv.writer(ifile, delimiter='\t')
			for row in zip(*results):
				writer.writerow(row)
				
	plt.plot(results[0], results[1])
	plt.show()

	

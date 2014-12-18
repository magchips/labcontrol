# -*- coding: utf-8 -*-
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

class AgilentSimulator:
    '''simulator, if visa is not present'''
    #pylint: disable=C0321,C0111,R0913,C0103,W0613
    def __init__(self):
        self.lastCommand = None

    def read(self):
        return None

    def startOutput(self, data):
        if data["PulseLength"] is not 0:
            print "Timeframe settings are initialized, pulse period isn zero."
            print "Pulse period is set to " + str(data["PulseLength"])
        else:
            print "Timeframe settings are initialized, pulse period was zero."
            print "Frequency is set to " + str(data["Freq"]) + ". Amplitude was set to " + str(data["Amp"])

    def write(self, string):
        '''visa command write function'''
        self.lastCommand = string

class AgilentController2:
    '''interface to Tektronix oscilloscopes'''
    def __init__(self,logID):
        if logID == 'labalyzer':
            logger=logging.getLogger('labalyzer')
        elif logID == 'starkalyzer':
            logger=logging.getLogger('starkalyzer')
        try:
            import visa #pylint: disable=F0401
            # try-clause
            self.__agilent = visa.instrument('TCPIP0::10.0.0.3::gpib0,9::INSTR', timeout = 1)
            logger.warn("Agilent 2 function generator loaded")
        except:
            logger.warn("can't load visa driver for Agilent function generator, using simulator")
            self.__agilent = AgilentSimulator()


    def initialize(self):
        '''hardware initialization'''
        self.__agilent.write('OUTPUT ON')

    def startOutput(self,data):
        if not(data["PulseLength"] == 0):
            self.__agilent.write('VOLT:HIGH 5')
            self.__agilent.write('VOLT:LOW 0')
            self.__agilent.write('FUNC PULS')
            self.__agilent.write('PULS:PER 0.01')
            self.__agilent.write('PULS:WIDT ' + str(data["PulseLength"]) + 'ns')
            self.__agilent.write('BURS:MODE TRIG')
            self.__agilent.write('TRIG:SOUR EXT')
            self.__agilent.write('BURS:NCYC 1')
            self.__agilent.write('BURS:STAT ON')
            self.__agilent.write('OUTPUT ON')
        else:
            self.__agilent.write('BURS:STAT OFF')
            self.__agilent.write('FUNC SIN')
            self.__agilent.write('FREQ ' + str(data["Freq"]))
            self.__agilent.write('VOLT ' + str(data["Amp"]))
            self.__agilent.write('OUTPUT ON')

    def setFrequency(self, frequency):
        self.__agilent.write('FREQ ' + str(frequency))

    def setAmplitude(self, amplitude):
        self.__agilent.write('VOLT ' + str(amplitude))

    def setOffset(self, offset):
        self.__agilent.write('VOLT:OFFS ' + str(offset))

    def setSine(self):
        self.__agilent.write('BURS:STAT OFF')
        self.__agilent.write('APPL:SIN')

    def setDC(self, voltage):
        self.__agilent.write('APPL:DC DEF,DEF,' + str(voltage))

    def setPulse(self, pulse_length):
        self.__agilent.write('VOLT:HIGH 5')
        self.__agilent.write('VOLT:LOW 0')
        self.__agilent.write('FUNC PULS') # set the function to pulse
        self.__agilent.write('PULS:PER 0.01')
        self.__agilent.write('PULS:WIDT ' + str(pulse_length) + 'ns' )
        print "Agilent: Pulse period is set to " + str(pulse_length) + " s."
        # add commands to set edge time, high lvl and low lvl voltage to get TTL

    def setBurstMode(self):
        self.setFrequency(1000)
        self.__agilent.write('PULS:PER 0.01')
        self.__agilent.write('FUNC PULS')
        self.__agilent.write('BURS:MODE TRIG')
        self.__agilent.write('BURS:NCYC 1')
        self.__agilent.write('BURS:STAT ON')


    def updateBurstMode(self, mode):
        if mode == "Ext":
            self.__agilent.write('TRIG:SOUR EXT')
            print "Agilent: Trigger is set to external."
        else:
            self.__agilent.write('TRIG:SOUR BUS')
            print "Agilent: Trigger is set to BUS. Trig button should be gloing."


    def toggleOutput(self, outputOn):
        pass

    def setImpedance(self, impedanceHigh=True):
        pass


if __name__ == '__main__':
    pass

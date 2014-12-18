# -*- coding: utf-8 -*-
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

''' Controller for Rhode Schwarz microwave source, via VISA. could also control other visa devices'''

import logging
import numpy as np
import math
import os
import sys

class RohSchSimulator:
    '''simulator, if visa is not present'''
    #pylint: disable=C0321,C0111,R0913,C0103,W0613
    def __init__(self):
        self.lastCommand = None

    def read(self):
        return None

    def write(self, string):
        '''visa command write function'''
        self.lastCommand = string


class RohSchController:
    '''interface to Rhode&Schwarz microwave source'''
    def __init__(self,logID):
        if logID == 'labalyzer':
            logger=logging.getLogger('labalyzer')
        elif logID == 'starkalyzer':
            logger=logging.getLogger('starkalyzer')
        try:
            import visa #pylint: disable=F0401
            # try-clause
            
            self.__rohsch = visa.instrument('TCPIP0::10.0.0.3::gpib0,28::INSTR', timeout = 1)
            logger.warn("RohSch function generator loaded")
        except:
            logger.warn("can't load visa driver for RohSch function generator, using simulator")
            self.__rohsch = RohSchSimulator()

    def initialize(self):
        '''hardware initialization'''
        self.__rohsch.write('*RST;*CLS')
        self.__rohsch.write('OUTP:STAT ON')
        localfolder = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
        file_name = "E:/code/labalyzer6_8/rsCalibrationCurve1.2mW.csv"
        file_name = os.path.join(localfolder, "ressources/rsCalibrationCurve1.2mW.csv")
        self.__table = np.loadtxt(file_name, delimiter=',', skiprows=1)
        self.setFrequency(300*10**6)
        self.__rohsch.write('POW ' + str(-12.0) + 'dBm')

    def startOutput(self,data):
        freq = data["Freq"] #in Hz
        output = data["Output"]
        power = 0
        

             
        count = 0
        point_found = False
        
        for point in self.__table:
            point_freq = point[0] * 10**6
            if point_freq > freq and not point_found:
                #linear interpolation
                y1 = self.__table[count - 1][1]
                y2 = point[1]
                x1 = self.__table[count - 1][0]
                x2 = point[0]

                point_found = True

                power = y1 + ((y2-y1)/(x2-x1)) * (freq * 10**(-6) - x1)
                
            elif point_freq == freq:
                power = point[1]
                point_found = True
                
            count += 1

        self.setFrequency(freq)
        self.setPower(power)

    def setFrequency(self, frequency):
        self.__rohsch.write('FREQ ' + str(frequency))

    def setPower(self, power):
        self.__rohsch.write('POW ' + str(power) + 'dBm')

    def setAmplitude(self, amplitude):
        self.__rohsch.write('VOLT ' + str(amplitude))

    def setOffset(self, offset):
        self.__rohsch.write('VOLT:OFFS ' + str(offset))

    def setSine(self, frequency, amplitude, offset):
        self.__rohsch.write('APPL:SIN ' + str(frequency * 1e6) + ','
         + str(amplitude) + ',' + str(offset))

    def setDC(self, voltage):
        self.__rohsch.write('APPL:DC DEF,DEF,' + str(voltage))


    def toggleOutput(self, outputOn):
        pass

    def setImpedance(self, impedanceHigh=True):
        pass


if __name__ == '__main__':
    pass
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
from labalyzer import constants

class SRSPulseSimulator:
    '''simulator, if visa is not present'''
    #pylint: disable=C0321,C0111,R0913,C0103,W0613
    def __init__(self):
        self.lastCommand = None
        print "The SRSPulsesim is made" 

    def write(self, string):
        '''visa command write function'''
        self.lastCommand = string


class SRSPulseController:
    '''interface to Stanfor Research System Four Channel Digital Pulse Generator Model DG535'''
    def __init__(self,logID):
        if logID == 'labalyzer':
            logger=logging.getLogger('labalyzer')
        elif logID == 'starkalyzer':
                        logger=logging.getLogger('starkalyzer')
        try:
            import visa #pylint: disable=F0401
            # try-clause
            self.__pulse = visa.instrument('TCPIP0::10.0.0.3::gpib0,15::INSTR', timeout = 1)
            logger.warn("SRS pulse generator loaded")
        except:
            logger.warn("can't load visa driver for SRS Pulse generator, using simulator")
            self.__pulse = SRSPulseSimulator()


    def initialize(self):
        '''hardware initialization'''
        pass


    def startOutput(self, srsPulseSettings):

        self.__pulse.write("TM 1")    # set trigger to Ext (external)
        self.__pulse.write("OM 4,0")  # set AB output channel to TTL
        self.__pulse.write("OM 7,0")  # set CD output channel to TTL
        self.__pulse.write("TZ 0,0")  # set Trigger input impendance to 50 Ohm
        self.__pulse.write("TZ 4,0")  # set AB output impendance to 50 Ohm
        self.__pulse.write("TZ 7,1")  # set CD output impendance to High

        RD = srsPulseSettings["RelativeDelay"] + constants.DELAY_REDBLUE
        if srsPulseSettings["PulseLength"] == 0:
            if RD < 0:
                self.__pulse.write("DT 5,1,0")
                self.__pulse.write("DT 6,5," + str(srsPulseSettings["CDPulseLength"]) + "E-9")
                self.__pulse.write("DT 2,1," + str(RD * -1.0) + "E-9")
                print "!!!!DT 2,1," + str(RD * -1.0) + "E-9"
                self.__pulse.write("DT 3,2," + str(srsPulseSettings["ABPulseLength"]) + "E-9")

            elif RD == 0:
                self.__pulse.write("DT 5,1,0")
                self.__pulse.write("DT 6,5," + str(srsPulseSettings["CDPulseLength"]) + "E-9")
                self.__pulse.write("DT 2,1," + str(RD) + "E-9")

                print "!!DT 2,1," + str(RD) + "E-9"
                self.__pulse.write("DT 3,2," + str(srsPulseSettings["ABPulseLength"]) + "E-9")

            elif RD > 0:
                print "RD is larger than 0"
                self.__pulse.write("DT 2,1,0")
                self.__pulse.write("DT 3,2," + str(srsPulseSettings["ABPulseLength"]) + "E-9")
                self.__pulse.write("DT 5,1," + str(RD) + "E-9")
                print "!DT 5,1," + str(RD) + "E-9"
                self.__pulse.write("DT 6,5," + str(srsPulseSettings["CDPulseLength"]) + "E-9")

        else:
            if srsPulseSettings["RelativeDelay"] <= 0:
                self.__pulse.write("DT 5,1,0")
                self.__pulse.write("DT 6,5," + str(srsPulseSettings["PulseLength"]) + "E-9")
                self.__pulse.write("DT 2,1," + str(srsPulseSettings["RelativeDelay"] * -1.0 + constants.DELAY_REDBLUE) + "E-9")
                self.__pulse.write("DT 3,2," + str(srsPulseSettings["PulseLength"]) + "E-9")

            elif srsPulseSettings["RelativeDelay"] > 0:
                print "RD is larger than 0"
                self.__pulse.write("DT 2,1,0")
                self.__pulse.write("DT 3,2," + str(srsPulseSettings["PulseLength"]) + "E-9")
                self.__pulse.write("DT 5,1," + str(srsPulseSettings["RelativeDelay"] + constants.DELAY_REDBLUE) + "E-9")
                self.__pulse.write("DT 6,5," + str(srsPulseSettings["PulseLength"]) + "E-9")



    def preparePulse(self, channel_conf, mode):
        if mode == "Ext":
            self.__pulse.write("TM 1")    # set trigger to Ext (external)
            print "External mode initialized"

        elif mode == "SS":
            self.__pulse.write("TM 2")    # set trigger to SS (single shot)
            print "Single shot mode initialized"

        self.__pulse.write("OM 4,0")  # set AB output channel to TTL
        self.__pulse.write("OM 7,0")  # set CD output channel to TTL
        self.__pulse.write("TZ 0,0")  # set Trigger input impendance to 50 Ohm
        self.__pulse.write("TZ 4,0")  # set AB output impendance to 50 Ohm
        self.__pulse.write("TZ 7,1")  # set CD output impendance to High

        if channel_conf["RD"] <= 0:
            self.__pulse.write("DT 5,1,0")
            self.__pulse.write("DT 6,5," + str(channel_conf["CD"]) + "E-9")
            self.__pulse.write("DT 2,1," + str(channel_conf["RD"] * -1.0) + "E-9")
            self.__pulse.write("DT 3,2," + str(channel_conf["AB"]) + "E-9")

        elif channel_conf["RD"] > 0:
            print "RD is larger than 0"
            self.__pulse.write("DT 2,1,0")
            self.__pulse.write("DT 3,2," + str(channel_conf["AB"]) + "E-9")
            print "DT 3,2," + str(channel_conf["AB"]) + "E-9"
            self.__pulse.write("DT 5,1," + str(channel_conf["RD"]) + "E-9")
            print "DT 4,2," + str(channel_conf["RD"]) + "E-9"
            self.__pulse.write("DT 6,5," + str(channel_conf["CD"]) + "E-9")
            print "DT 5,4," + str(channel_conf["CD"]) + "E-9"


    def sendPulse(self):
        self.__pulse.write("SS")



if __name__ == '__main__':
    pass

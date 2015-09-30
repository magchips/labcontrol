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

'''interface to NI DAQmx analog output cards'''

from labalyzer.constants import (MODE_DIRECT)
from labalyzer.LabalyzerSettings import settings
import ctypes


import logging
logger = logging.getLogger('labalyzer')

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


class NIDAQOutputSimulator:
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



class NIDAQOutputController:
    '''interface to DAQmx controlled NI analog output cards'''
    def __init__(self):
        try:
            self.__nidaq = ctypes.windll.nicaiu # load the DLL
        except: # on error, use the simulator
            logger.warn("can't load NIDAQ driver, using simulator")
            self.__nidaq = NIDAQOutputSimulator()
        self.taskIsConfigured = False
        self.taskIsRunning = False
        
    def initialize(self):
        '''initilaize hardware'''
        if self.taskIsConfigured:
            logger.error("tried to re-initialize nidaq controller"
            "while task was not cleared, call shutdown first")
            return
        
        self.__taskHandle = [TaskHandle(0), TaskHandle(0), TaskHandle(0)]
        self.CHK(self.__nidaq.DAQmxCreateTask("",
        ctypes.byref(self.__taskHandle[0])))
        self.CHK(self.__nidaq.DAQmxCreateTask("",
        ctypes.byref(self.__taskHandle[1])))
        self.CHK(self.__nidaq.DAQmxCreateTask("",
        ctypes.byref(self.__taskHandle[2])))
        
        # apparently these have to be sorted in the order of the data array below
        # limits still need ot be set properly?!
        devByChannel = {}
        for k, v in settings['AnalogChannels'].iteritems():
            keys = devByChannel.setdefault(v.channelNumber, [])
            keys.append(k)
        
        for channel in sorted(devByChannel):
            for entry in devByChannel[channel]:
                v = settings['AnalogChannels'][entry]
                if v.boardNumber not in [0, 1, 2]:
                    logger.error("there was a channel which did not"
                    " belong to a known device! boardNumber was %d",
                    v.boardNumber)
                else:
                    self.CHK(self.__nidaq.DAQmxCreateAOVoltageChan( 
                        self.__taskHandle[v.boardNumber], v.GetDeviceString(), 
                        "", float64(-10), float64(10), DAQmx_Val_Volts, None)
                        )
        
        self.taskIsConfigured = True
        
        logger.info("NIDAQ Controller initialized")


    def CHK( self, err ):
        """a simple error checking routine"""
        if err is None:
            return 0
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
        return 1

    def programmeChannels(self, aodata):
        '''programme timeframe data to hardware'''
        logger.debug("programming NIDAQ channels")
        periodLength = len(aodata[0])/8
        # determine sample timing
        # setting the source to "PFI0" means that each sample is output only after a trigger is received on PFI0
        self.CHK(self.__nidaq.DAQmxCfgSampClkTiming( self.__taskHandle[0], "PFI0", float64(settings['SamplesPerMillisecond']*1000), DAQmx_Val_Rising, DAQmx_Val_FiniteSamps, uInt64(periodLength))) # has to be after create AO Channel, but before writing to it; setting the source terminal to "PFI0" should enable to trigger from the DIO card!
        self.CHK(self.__nidaq.DAQmxCfgSampClkTiming( self.__taskHandle[1], "PFI0", float64(settings['SamplesPerMillisecond']*1000), DAQmx_Val_Rising, DAQmx_Val_FiniteSamps, uInt64(periodLength))) # has to be after create AO Channel, but before writing to it; setting the source terminal to "PFI0" should enable to trigger from the DIO card!
        self.CHK(self.__nidaq.DAQmxCfgSampClkTiming( self.__taskHandle[2], "PFI0", float64(settings['SamplesPerMillisecond']*1000), DAQmx_Val_Rising, DAQmx_Val_FiniteSamps, uInt64(periodLength))) # has to be after create AO Channel, but before writing to it; setting the source terminal to "PFI0" should enable to trigger from the DIO card!
        sampsWritten = ctypes.c_int32(0)

        self.CHK(self.__nidaq.DAQmxWriteAnalogF64( self.__taskHandle[0], int32(periodLength), 0, float64(-1), DAQmx_Val_GroupByScanNumber, aodata[0].ctypes.data, ctypes.byref(sampsWritten), None))
        logger.info(str(sampsWritten.value) + ' samples written to Dev1')
        self.CHK(self.__nidaq.DAQmxWriteAnalogF64( self.__taskHandle[1], int32(periodLength), 0, float64(-1), DAQmx_Val_GroupByScanNumber, aodata[1].ctypes.data, ctypes.byref(sampsWritten), None))
        logger.info(str(sampsWritten.value) + ' samples written to Dev2')
        self.CHK(self.__nidaq.DAQmxWriteAnalogF64( self.__taskHandle[2], int32(periodLength), 0, float64(-1), DAQmx_Val_GroupByScanNumber, aodata[2].ctypes.data, ctypes.byref(sampsWritten), None))
        logger.info(str(sampsWritten.value) + ' samples written to Dev3')
    def startTask(self):
        '''start task'''
        logger.debug('starting NIDAQ tasks')
        self.CHK(self.__nidaq.DAQmxStartTask(self.__taskHandle[0]))
        self.CHK(self.__nidaq.DAQmxStartTask(self.__taskHandle[1]))
        self.CHK(self.__nidaq.DAQmxStartTask(self.__taskHandle[2]))
        self.taskIsRunning = True
        
    def stopTask(self):
        '''stop task'''
        logger.debug('stopping NIDAQ tasks')
        self.CHK(self.__nidaq.DAQmxStopTask(self.__taskHandle[0]))
        self.CHK(self.__nidaq.DAQmxStopTask(self.__taskHandle[1]))
        self.CHK(self.__nidaq.DAQmxStopTask(self.__taskHandle[2]))
        self.taskIsRunning = False

    def shutdown(self):
        '''shutdown interface'''
        self.CHK(self.__nidaq.DAQmxClearTask(self.__taskHandle[0]))
        self.CHK(self.__nidaq.DAQmxClearTask(self.__taskHandle[1]))
        self.CHK(self.__nidaq.DAQmxClearTask(self.__taskHandle[2]))
        self.taskIsConfigured = False

    def setMode(self, mode):
        '''set mode: direct control or programmed'''
        if self.taskIsRunning:
            self.stopTask()

        devByChannel = {} # we'll need this in either case
        for k, v in settings['AnalogChannels'].iteritems():
            keys = devByChannel.setdefault(v.channelNumber, [])
            keys.append(k)  

        if mode == MODE_DIRECT:
            # 0 buffer size
            # not sure if this is the right thing to do
            self.shutdown()
            self.initialize()
            
            self.CHK(self.__nidaq.DAQmxCfgOutputBuffer(self.__taskHandle[0], ctypes.c_uint32(0)))
            self.CHK(self.__nidaq.DAQmxCfgOutputBuffer(self.__taskHandle[1], ctypes.c_uint32(0)))
            self.CHK(self.__nidaq.DAQmxCfgOutputBuffer(self.__taskHandle[2], ctypes.c_uint32(0)))

            for channel in sorted(devByChannel):
                for entry in devByChannel[channel]:
                    v = settings['AnalogChannels'][entry]
                    if v.boardNumber not in [0, 1, 2]:
                        logger.error("there was a channel which did not belong to a known device! boardNumber was %d", v.boardNumber)
                    else:
                        self.CHK(self.__nidaq.DAQmxSetAODataXferMech(self.__taskHandle[v.boardNumber], v.GetDeviceString(), DAQmx_Val_ProgrammedIO))
            self.CHK(self.__nidaq.DAQmxCfgSampClkTiming( self.__taskHandle[0], "ao/SampleClockTimebase", float64(1), DAQmx_Val_Rising, DAQmx_Val_FiniteSamps, uInt64(1)))
            self.CHK(self.__nidaq.DAQmxCfgSampClkTiming( self.__taskHandle[1], "ao/SampleClockTimebase", float64(1), DAQmx_Val_Rising, DAQmx_Val_FiniteSamps, uInt64(1)))
            self.CHK(self.__nidaq.DAQmxCfgSampClkTiming( self.__taskHandle[2], "ao/SampleClockTimebase", float64(1), DAQmx_Val_Rising, DAQmx_Val_FiniteSamps, uInt64(1)))
        else: # we presume all other cases are timeframe-output
            self.shutdown() # this is ugly, why do I have to shutdown and recreate the task after switching to direct control? but not doing this gives weird errors
            self.initialize()
            # extend buffer size
            # not sure if this is the right thing to do
            self.CHK(self.__nidaq.DAQmxCfgOutputBuffer(self.__taskHandle[0], ctypes.c_uint32(10**5))) 
            self.CHK(self.__nidaq.DAQmxCfgOutputBuffer(self.__taskHandle[1], ctypes.c_uint32(10**5)))
            self.CHK(self.__nidaq.DAQmxCfgOutputBuffer(self.__taskHandle[2], ctypes.c_uint32(10**5)))

            for channel in sorted(devByChannel):
                for entry in devByChannel[channel]:
                    v = settings['AnalogChannels'][entry]
                    if v.boardNumber not in [0, 1, 2]:
                        logger.error("there was a channel which did not belong to a known device! boardNumber was %d", v.boardNumber)
                    else:
                        self.CHK(self.__nidaq.DAQmxSetAODataXferMech(self.__taskHandle[v.boardNumber], v.GetDeviceString(), DAQmx_Val_DMA))
    def directOutput(self, aodata):
        '''force direct output'''
        self.taskIsRunning = True
        sampsWritten = ctypes.c_int32(0)
        if (self.CHK(self.__nidaq.DAQmxWriteAnalogF64(self.__taskHandle[0], int32(1), 1, float64(-1), DAQmx_Val_GroupByScanNumber, aodata[0].ctypes.data, ctypes.byref(sampsWritten), None))) > 0:
                #print sampsWritten, 'samples written on dev1'
                #print aodata[0]
                pass
        if (self.CHK(self.__nidaq.DAQmxWriteAnalogF64(self.__taskHandle[1], int32(1), 1, float64(-1), DAQmx_Val_GroupByScanNumber, aodata[1].ctypes.data, ctypes.byref(sampsWritten), None))) > 0:
                #print sampsWritten, 'samples written on dev2'
                #print aodata[1]
                pass
        if (self.CHK(self.__nidaq.DAQmxWriteAnalogF64(self.__taskHandle[2], int32(1), 1, float64(-1), DAQmx_Val_GroupByScanNumber, aodata[2].ctypes.data, ctypes.byref(sampsWritten), None))) > 0:
                #print sampsWritten, 'samples written on dev3'
                #print aodata[1]
                pass

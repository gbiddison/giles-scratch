#!/usr/bin/env python
"""Neuron class"""
from pickletoxml import PickleToXML
from link import Link
import random

class Neuron(PickleToXML):
    __pickle_to_xml__ = ['Name','Incoming','Outgoing','Gating'
        ,'MembraneConductance','MembraneCapacitance','ThresholdVoltage'
        ,'MinFiringFrequency', 'Gain', 'IntrinsicCurrent', 'LIC', 'HIC', 'LowIC', 'HighIC']
    __next_id = 0 # static id for unnamed neurons

    TimeConstant = 1.0 / 200.0 # Seconds per simulated time step
    ICType_VInf = 0
    ICType_Random = 1
    ICType_None = 2

    def __init__(self, name=None):
        if name == None:
            name = 'neuron-%d' % Neuron.__next_id
            Neuron.__next_id += 1

        self.Name = name                        # friendly name of this neuron, must be unique
        self.Incoming = []                      # list of Incoming Links used to determine this neuron's activation
        self.Outgoing = []                      # list of Outgoing Links used for display purposes
        self.Gating = []                        # list of Outgoing Gating links used for display purposes

        self.MembraneConductance = 5e-007       # conductance (1/resistance) in mhos defaults to 1/(2Mohm)
        self.MembraneCapacitance = 1e-008       # capacitance
        self.ThresholdVoltage = 0               # min input voltage before triggering
        self.MinFiringFrequency = 0             # 
        self.Gain = 1000                        #

        self.IntrinsicCurrent = Neuron.ICType_None
        self.LIC = [0.0, 0.0, 0.0]
        self.HIC = [0.0, 0.0]
        self.LowIC = 0.0
        self.HighIC = 0.0

        #self.SensorType <-- TODO sensors (these should be a sub type of neuron or mixin on the input layer)
        #self.ParamsSensorCurrent_1
        #self.ParamsSensorCurrent_2

        #self.MotorType <-- TODO motors (these should be a sub type of neuron or mixin on the output layer
        #self.MotorName
        #self.MotorConst

        # unsaved state variables
        self._current = 0                       # current current -- calculated during update, effects intrinsic current
        self._voltage = 0                       # current voltage
        self._firingFrequency = 0               # current firing frequency

        self._stateChanged = False              # whether or not the activation state of this neuron changed used to trigger net state changed callback
        self._nextVoltage = 0                   # temporary voltage to update next sim step
        self._nextFiringFrequency = 0           # temporary firing frequency to update next sim step

        self._isHighIC = False
        self._lastChangeTimeIC = 0
        self._maxChangeTimeIC = 0

        self._sensory_current = 0
        
    class LinkCantBeNullError(Exception):
        pass

    def set_incoming(self, link):
        if link is None:
            raise LinkCantBeNullError()
        if link in self.Incoming:
            return
        self.Incoming.append(link)

    def set_outgoing(self, link):
        if link is None:
            raise LinkCantBeNullError()
        if link in self.Outgoing:
            return
        self.Outgoing.append(link)

    def set_gating(self, link):
        if link is None:
            raise LinkCantBeNullError()
        if link in self.Gating:
            return
        self.Gating.append(link)

    def remove_link(self, link):
        if link in self.Incoming:
            self.Incoming.remove(link)
        if link in self.Outgoing:
            self.Outgoing.remove(link)
        if link in self.Gating:
            self.Gating.remove(link)

    def is_connected_outgoing(self, target):
        for link in self.Outgoing:
            if link.Target == target:
                return link
        return None

    def is_connected_incoming(self, source):
        for link in self.Incoming:
            if link.Source == source:
                return link
        return None

    def is_connected_gating(self, gate_source):
        for link in self.Gating:
            if link.GateSource == gate_source:
                return link
        return None

    def is_state_changed(self):
        return self._stateChanged

    def set_IsHighIC(self, state):
        self._lastChangeTimeIC = 0
        self._isHighIC = state
        if state:
            if self.IntrinsicCurrent == Neuron.ICType_VInf:
                self._maxChangeTimeIC = self.HIC[0]
            else: # random type
                self._maxChangeTimeIC = (random.randint(0, (int)(1000.0 * (self.HIC[1] - self.HIC[0]))) + 1000.0 * self.HIC[0]) / 1000.0
        else:
            if self.IntrinsicCurrent == Neuron.ICType_Random:
                self._maxChangeTimeIC = (random.randint(0, (int)(1000.0 * (self.LIC[1] - self.LIC[0]))) + 1000.0 * self.LIC[0]) / 1000.0

    

    def updateState(self):
        self._stateChanged = False
        debug = self.Name == 'FOOTL1'
        if debug: print()
        # calculate current (based on activation of incoming links)
        current = 0.0
        for link in self.Incoming:
            if debug:  print(self.Name + " link from " + link.Source.Name + " ff " + str(link.Source._firingFrequency) + " w " + str(link.Weight))
            activity = link.Source._firingFrequency * link.Weight # frequency * weight = current ... apparently
            if link.GateSource is not None:
                if debug: print(self.Name + " gated by " + link.GateSource.Name)
                gated_activity = link.GateSource._firingFrequency * link.GateWeight
                if link.GateType == Link.GateType_Gate:
                    activity *= link.GateState + gated_activity * 1e9
                elif gated_activity >= 0:
                    activity *= 1 + gated_activity * 1e9
                else:
                    activity /= 1 - gated_activity * 1e9
            current += activity # sum the current incoming from all links  

        # add intrinsic current if any
        if self.IntrinsicCurrent != Neuron.ICType_None:
            self._lastChangeTimeIC += Neuron.TimeConstant
            if not self._isHighIC and self.IntrinsicCurrent == Neuron.ICType_VInf:
                volts = self._current / self.MembraneConductance
                if volts > self.LIC[0]: self._maxChangeTimeIC = self.LIC[1] - self.LIC[2] * volts
                else:                   self._maxChangeTimeIC = float('inf')
            if (self._voltage < self.ThresholdVoltage and self._nextVoltage >= self.ThresholdVoltage) or (not self._isHighIC and self._lastChangeTimeIC >= self._maxChangeTimeIC):
                self.set_IsHighIC(True) # turn on intrinsic current                 
            elif self._isHighIC and self._lastChangeTimeIC >= self._maxChangeTimeIC:
                self.set_IsHighIC(False) # turn off intrinsic current                 
                
            current += self.LowIC 
            if self._isHighIC:
                current += (self.HighIC - self.LowIC)
            
        # APPLY SENSORY CURRENT FROM EXTERNAL SOURCE
        current += self._sensory_current  #  getSensorCurrent(np->sensorType, np->name, np->paramsSensorCurrent);
        # self._sensory_current = 0 # clear immediately or hold?

        self._current = current  # store calculated current

        if debug: print(self.Name + " current_1 " + str(current))

        # calculate new Voltage
        current = (current - self._voltage * self.MembraneConductance) / self.MembraneCapacitance
        self._nextVoltage = self._voltage + current * Neuron.TimeConstant
        if abs(self._nextVoltage < 1e-30): self._nextVoltage = 0.0 # floor to epsilon instead of overflow

        if debug: print(self.Name + " current_2 " + str(current))
        if debug: print(self.Name + " nextVolts " + str(self._nextVoltage))
        if debug: print(self.Name + " threshold " + str(self.ThresholdVoltage))

        # calculate new FiringFrequency
        if self._nextVoltage < self.ThresholdVoltage:
            self._nextFiringFrequency = 0.0
        else:
            min_activity = self.MinFiringFrequency - self.Gain * self.ThresholdVoltage
            if debug: print(self.Name + " minFreq" + str(self.MinFiringFrequency))
            if debug: print(self.Name + " gain " + str(self.Gain))
            if debug: print(self.Name + " activity " + str(min_activity))
            if self._nextVoltage < ((1.0 - min_activity)/self.Gain):
                self._nextFiringFrequency = self.Gain * self._nextVoltage + min_activity
            else:
                self._nextFiringFrequency = 1.0
        
        if debug: print(self.Name + " frequency " + str(self._nextFiringFrequency))

    def changeState(self):
        if self._nextFiringFrequency != self._firingFrequency or self._nextVoltage != self._voltage:
            self._stateChanged = True
            self._firingFrequency = self._nextFiringFrequency
            self._voltage = self._nextVoltage


#!/usr/bin/env python
import sys
from neuraledit_element import NeuralEditNeuralNet

# read a NerveSim .neu file and generate both a NeuralEditNeuralNet and a NeuralNet
# NeuralEditNeuralNet contains UI positions for the neurons
# NeuralNet contains neuron properties and links

class NerveSimReader:
    def __init__(self, path):
        self.Net = NeuralEditNeuralNet()

        with open(path) as f:
            num_neurons = int(f.readline().split()[1])
            elements = []
            for i in range(num_neurons):
                name = f.readline().split()[1]
                net_element = self.Net.add_named_element(((i+5)/float(num_neurons+10),(i+5)/float(num_neurons+10)), name)
                neuron = self.Net.lookup_neuron(net_element)

                neuron.MembraneConductance = float(f.readline().split()[1])
                neuron.MembraneCapacitance = float(f.readline().split()[1])
                neuron.ThresholdVoltage = float(f.readline().split()[1])
                neuron._voltage = neuron._nextVoltage = neuron.ThresholdVoltage  # start at threshold
                neuron.MinFiringFrequency = float(f.readline().split()[1])
                neuron.Gain = float(f.readline().split()[1])

                sense_type = f.readline().split()[1] # TODO
                paramsSensorCurrent_0 = f.readline().split()[1] # TODO
                paramsSensorCurrent_1 = f.readline().split()[1] # TODO
                motor_type = f.readline().split()[1] # TODO
                motor_name = f.readline().split()[1] # TODO
                motorConst = f.readline().split()[1] # TODO
                ic = int(f.readline().split()[1])
                nc = int(f.readline().split()[1])

                elements.append((net_element, nc, ic))

            num_intrinsics = int(f.readline().split()[1])
            intrinsics = []
            for i in range(num_intrinsics):
                intrinsic_current_type = int(f.readline().split()[1])
                low = float(f.readline().split()[1])
                paramsLIC_0 = float(f.readline().split()[1])
                paramsLIC_1 = float(f.readline().split()[1])
                paramsLIC_2 = float(f.readline().split()[1])
                high = float(f.readline().split()[1])
                paramsHIC_0 = float(f.readline().split()[1])
                paramsHIC_1 = float(f.readline().split()[1])
                isHigh = f.readline().split()[1]
                timeSinceLastChange = f.readline().split()[1]
                maxTimeSinceLastChange = f.readline().split()[1]

                intrinsics.append( (intrinsic_current_type, low, high, paramsLIC_0, paramsLIC_1, paramsLIC_2, paramsHIC_0, paramsHIC_1))

            num_connections = int(f.readline().split()[1])
            connections = []
            for i in range(num_connections):
                sourceName = f.readline().split()[1]
                source = f.readline().split()[1]
                sourceWeight = float(f.readline().split()[1])
                gate_type = int(f.readline().split()[1])
                targetName	 = f.readline().split()[1]
                target = f.readline().split()[1]
                targetWeight = float(f.readline().split()[1])
                ungatedState = int(f.readline().split()[1])
                n = int(f.readline().split()[1])

                connections.append( (sourceName, n, sourceWeight, targetName, targetWeight, ungatedState, gate_type))

            # link neurons using the connections list
            for (end, n, i) in elements:
                # assign intrinsics
                if i != -1:
                    t, l, h, pl0, pl1, pl2, ph0, ph1 = intrinsics[i]
                    neuron = self.Net.lookup_neuron(end)
                    neuron.IntrinsicCurrent = t
                    neuron.LowIC = l
                    neuron.HighIC = h
                    neuron.LIC = [pl0, pl1, pl2]
                    neuron.HIC = [ph0, ph1]
                
                # assign connections
                while n != -1:
                    s, n, w, t, tw, gs, gt = connections[n]
                    start = self.find_element(elements, s)
                    link = self.Net.add_link( start, end)
                    link.Weight = w
                    gate_source = self.find_element(elements, t)
                    if gate_source is not None:
                        link.GateSource = self.Net.lookup_neuron(gate_source)
                        link.GateWeight = tw
                        link.GateState = gs
                        link.GateType = gt
                        
                    
                    

    def find_element(self, elements, name):
        for (e, n, i) in elements:
            if e.Name == name:
                return e
        return None
        
    
        


#!/usr/bin/env python

# avoid circular import problem by not using from xxx import xxx, 
# since this requires the module to have defined its classes already
import neuron
import neuralnetio
import neuralnet

"""
    SubNet class

    Encapsulates a NeuralNet within a Neuron for recursive networks
"""

class SubNet(neuron.Neuron):
    __pickle_to_xml__ = ['Path'] + neuron.Neuron.__pickle_to_xml__
    def __init__(self, name=None, path=None):
        neuron.Neuron.__init__(self, name)
        self.Path = path
        if path is None:
            self.Net = neuralnet.NeuralNet()
        else:
            self.Net = neuralnetio.NeuralNetIO().read(path)
        
    def set_incoming(self, link):
        inputs = self.Net.get_input_neurons()
        if len(inputs) == 0:
            link.Target = None
            return        
        neuron.Neuron.set_incoming(self, link)
        inputs[0].Incoming.append(link)

    def set_outgoing(self, link):
        outputs = self.Net.get_output_neurons()
        if len(outputs) == 0:
            link.Source = None
            return
        neuron.Neuron.set_outgoing(self, link)
        outputs[0].Outgoing.append(link)
        # also rewire the link.Source to point at the internal neuron
        link.Source = outputs[0]

    def remove_link(self, link):
        neuron.Neuron.remove_link(self, link)
        self.Net.remove_link(link)
  
    def is_connected_outgoing(self, target):
        return neuron.Neuron.is_connected_outgoing(self, target)

    def is_connected_incoming(self, source):
        return neuron.Neuron.is_connected_incoming(self, source)

    def is_state_changed(self):
        return neuron.Neuron.is_state_changed(self)

    def updateState(self):
        self._stateChanged = False
        # walk through all the neurons, update there state based on
        # current state of all connections
        for n in self.Net.Neurons:
            n.updateState()
        
    def changeState(self):
        # walk through all the neurons, apply the current state
        for n in self.Net.Neurons:
            n.changeState()
            self._stateChanged = self._stateChanged or n.is_state_changed()


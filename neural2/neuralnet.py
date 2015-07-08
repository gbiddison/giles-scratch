#!/usr/bin/env python
"""NeuralNet class"""
from threading import Thread
from time import sleep
from pickletoxml import PickleToXML
from neuron import Neuron
from link import Link

# avoid circular import problem by not using from xxx import xxx, 
# since this requires the module to have defined its classes already
import subnet

class NeuralNet(PickleToXML):
    __pickle_to_xml__ = ['Neurons']
    __min_period = 0.1
    
    def __init__(self):
        self.Neurons = []
        self.__thread = None
        self.__running = False
        self.__stop = False
        self.__period = 0.0
        self.__state_change_callback = None

    def set_callback(self, callback):
        self.__state_change_callback = callback

    def lookup_neuron_by_name(self, name):
        for n in self.Neurons:
            if n.Name == name: return n
        return None

    def get_unique_name(self, name):
        if not name:
            name = "neuron"
        new_name = name
        next_id = 2
        while not new_name or self.lookup_neuron_by_name(new_name) is not None:
            new_name = '%s-%d' % (name, next_id)
            next_id += 1
        return new_name
       
    def add_neuron(self):
        n = Neuron(self.get_unique_name("neuron"))
        self.Neurons.append(n)
        return n

    def remove_neuron(self, neuron):
        dead_links = []
                
        # remove all links to this neuron (target == self)
        incoming = neuron.Incoming[:]
        for link in incoming:
            if neuron != link.Target:
                neuron.remove_link(link)
            link.Source.remove_link(link)
            link.Target.remove_link(link)
            dead_links.append(link)
            
        # remove all links from this neuron (source == self)
        outgoing = neuron.Outgoing[:]
        for link in outgoing:
            if neuron != link.Source:
                neuron.remove_link(link)
            link.Source.remove_link(link)
            link.Target.remove_link(link)
            dead_links.append(link)

        # in the case where we're removing a neuron that a subnet has an outgoing
        # link to, we have to walk the entire net in order to find the link 
        # out of the subnet to the neuron we've removed
        for n in self.Neurons:
            for link in dead_links:
                if link in n.Outgoing:
                    n.Outgoing.remove(link)
                #if link in n.Incoming:
                #    n.Incoming.remove(link)

        # remove the neuron from the network
        self.Neurons.remove(neuron)
        
    def add_link(self, source, target, weight=1.0):
        # if we've already got a link between these two neurons, return it
        # otherwise add a new one
        l = source.is_connected_outgoing(target)
        if l is not None:
            return l        
        l = Link(source, target, weight)
        return l

    def remove_link(self, link):
        for n in self.Neurons:
            n.remove_link(link)

    def get_input_neurons(self):
        rval = []
        for n in self.Neurons:
            if len(n.Incoming) == 0:
                rval.append(n)
        return rval

    def get_output_neurons(self):
        rval = []
        for n in self.Neurons:
            if len(n.Outgoing) == 0:
                rval.append(n)
        return rval

    def update(self):
        state_changed = False
        # walk through all the neurons, update their state based on
        # current state of all connections
        for neuron in self.Neurons:
            neuron.updateState()

        # walk through all the neurons, apply the current state
        for neuron in self.Neurons:
            neuron.changeState()
            state_changed = state_changed or neuron.is_state_changed()

        if state_changed and self.__state_change_callback is not None:
            self.__state_change_callback()
       
    def start(self):
        self.__stop = False
        self.__thread = Thread(target=self.run)
        self.__thread.start()

    def stop(self):
        if self.__thread == None:
            return
        self.__stop = True
        self.__thread.join()

    def interruptable_sleep(self, period):
        counter = period
        while counter > 0 and not self.__stop:
            sleep_time = min(self.__min_period, counter)
            counter -= sleep_time
            sleep(sleep_time)

    def run(self):
        self.__running = True
        while not self.__stop:
            self.update()
            self.interruptable_sleep(self.__period)
        self.__running = False

    def set_period(self, period):
        if self.__running and period == 0:
            self.stop()
        self.__period = period
        if not self.__running and period != 0:
            self.start()

    #####---- subnet support ----#####
    def add_subnet(self, name, path):
        n = neural2.subnet.SubNet(self.get_unique_name(name), path)
        self.Neurons.append(n)
        return n


#!/usr/bin/env python
"""NeuralNetWriter class"""
import xml.dom.minidom as dom
import os
import pickletoxml# neural2.pickletoxml
#import neuralnet #neural2.neuralnet
import subnet #neural2.subnet

class NeuralIO:
    """
    NeuralIO is a helper class that wraps  pickle / unpickle to xml
    """
    def __init__(self, path=None):
        pass

    @classmethod
    def create(cls, path):
        # NeuralIO is the IO module for the UI representation of the net (x&y coords of the nodes) class is NeuralEditNeuralNet defined in wxneural/neuraledit_element.py
        net = NeuralIO().read(path)

        # the UI repr is linked to the functional repr by a path attribute contained in the UI repr
        dir_name, file_name = os.path.split(path)
        net_path = os.path.normpath(os.path.join( dir_name, net.NetPath))

        # NeuralNetIO is the IO module for the functional representation of the net (nodes, edges, state) class is NeuralNet defined in neuralnet.py
        # non-ui oriented programs should directly hit NeuralNetIO instead of the full UI
        stream = NeuralNetIO()
        net.Net = stream.read(net_path)
        net.rebuild_lookup_table()      # the lookup table connects the UI repr to the functional repr
        return net

    def write(self, filename, net):
        node = pickletoxml.pickle(net)
        doc = dom.Document()
        doc.appendChild(node)
        f = open(filename, 'w')
        doc.writexml(f, addindent="\t", newl="\n", encoding="UTF-8")
        f.close()
        doc.unlink()

    def read(self, filename):
        net = pickletoxml.unpickle(dom.parse(filename).documentElement)
        return net

class NeuralNetIO(NeuralIO):
    def __init__(self):
        NeuralIO.__init__(self)

    def write(self, filename, net):
        # we re-write all subnet outgoing links so that
        # they point back (link.Source==) to the subnet rather than to the internal 
        # neuron.  Only need to go one level deep since we're only writing the outer 
        # level net
        self._unlink_subnets(net)     
        NeuralIO.write(self, filename, net)
        # we then need to restore the original links when we leave
        self._link_subnets(net)
    

    def read(self, filename):
        net = NeuralIO.read(self, filename)

        # recursively unpickle subnets
        for neuron in net.Neurons:
            if not isinstance(neuron, subnet.SubNet):
                continue
            dir_name, file_name = os.path.split(filename)
            path = os.path.normpath(os.path.join( dir_name, neuron.Path))
            neuron.Net = self.read(path)                

        # we now need to restore the outgoing links so that they point to 
        # internal neurons rather than the subnet itself
        self._link_subnets(net)
        return net

    def _unlink_subnets(self, net):
        for neuron in net.Neurons:
            if not isinstance(neuron, subnet.SubNet):
                continue            

            # clear incoming boundary crossing connections
            for link in neuron.Incoming:
                for n in neuron.Net.Neurons:
                    if link in n.Incoming:                         
                        n.Incoming = [] # assumption: only one incoming boundary link allowed per neuron
            
            # clear outgoing boundary crossing connections            
            # 'temporarily' set ougoing boundary crossing link Sources to the subnet neuron
            for link in neuron.Outgoing:
                link.Source.Outgoing = [] # assumption: only one outgoing boundary link allowed per neuron
                link.Source = neuron

    def _link_subnets(self, net):
        for neuron in net.Neurons:
            if not isinstance(neuron, subnet.SubNet):
                continue

            #re-link incoming boundary crossing connections
            inputs = neuron.Net.get_input_neurons()
            for i in range(len(neuron.Incoming)):
                inputs[i].Incoming = [neuron.Incoming[i]]
           
            #re-link outgoing boundary crossing connections
            outputs = neuron.Net.get_output_neurons()            
            for i in range(len(neuron.Outgoing)):
                outputs[i].Outgoing = [neuron.Outgoing[i]]
                neuron.Outgoing[i].Source = outputs[i]
                

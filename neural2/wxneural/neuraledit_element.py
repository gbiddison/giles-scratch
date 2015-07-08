"""
neuraledit_element.py
UI -> neuralnet transition / wrapper classes
"""

from pickletoxml import PickleToXML
from neuralnet import NeuralNet

class NeuralEditNeuralNet(PickleToXML):
    __pickle_to_xml__ = ['NetPath', 'Elements']
    # The idea with pickling this is to save a REFERENCE to the Net file
    # and pickle the Net in its own file - the editor handles 
    # saving and restoring the net as well as re-establishing the self.Net property
    # 
    
    def __init__(self):
        self.Net = NeuralNet()
        self.NetPath = None # set during pickle op
        self.Elements = []
        self.LookupTable = {}
       
    def element_from_point(self, point):
        for e in reversed(self.Elements): # reverse order of hit test from painting
            if e.HitTest(point):
                return e
        return None

    def rebuild_lookup_table(self):
        self.LookupTable = {}
        for e in self.Elements:
            self.LookupTable[e.Name] = (self.Net.lookup_neuron_by_name(e.Name), e)

    def lookup_neuron(self, element):
        return None if element is None else self.LookupTable[element.Name][0]

    def lookup_element(self, neuron):
        return None if neuron is None else self.LookupTable[neuron.Name][1]

    def add_named_element(self, position, name):
        neuron = self.Net.add_neuron()
        neuron.Name = name
        element = NeuralEditElement(name, position)
        self.Elements.append(element)
        self.LookupTable[name] = (neuron, element)
        return element

    def add_element(self, position, neuron_type, path):
        if path == None:
            neuron = self.Net.add_neuron()
        else:
            neuron = self.Net.add_subnet(neuron_type, path)
            
        element = NeuralEditElement(neuron.Name, position)
        self.Elements.append(element)
        self.LookupTable[neuron.Name] = (neuron, element)
        return element

    def add_link(self, start_element, end_element):
        return self.Net.add_link(self.lookup_neuron(start_element), self.lookup_neuron(end_element))

    def remove_element(self, element):
        (neuron, element) = self.LookupTable[element.Name]
        self.Elements.remove(element)
        self.Net.remove_neuron(neuron)
        self.LookupTable.pop(element.Name)        

    def rename_element(self, element, name):
        (neuron, element) = self.LookupTable[element.Name]
        self.LookupTable.pop(element.Name)
        neuron.Name="" #temp to let get_unique_name reuse our name
        name = self.Net.get_unique_name(name)
        neuron.Name = name
        element.Name = name
        self.LookupTable[neuron.Name] = (neuron, element)
        
class NeuralEditElement(PickleToXML):
    __pickle_to_xml__ = ['Name', 'Position']

    def __init__(self, name="unknown", position=(0, 0), size=(0.05, 0.05)):
        self.Name = name
        self.Position = position
        self.Size = size

    def HitTest(self, position):
        dx = position[0] - self.Position[0]
        dy = position[1] - self.Position[1]
        hit_x = dx >= 0 and dx < self.Size[0]
        hit_y = dy >= 0 and dy < self.Size[1]
        return hit_x and hit_y


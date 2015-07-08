#!/usr/bin/env python
"""Neural Net Test Code"""
import unittest
from neural.neuron import Neuron
from neural.link import Link
from neural.neuralnet import NeuralNet
from neural.neuralnetio import NeuralNetIO
from neural.subnet import SubNet

_MIN_FREQ_ = 10 # default min ticks to run tests for

class TestLink(unittest.TestCase):
    def setUp(self):
        pass
        
    def test_CreateLink(self):
        lnk = Link()
        self.assertTrue( lnk.Source is None)
        self.assertTrue( lnk.Target is None)
        
    def test_CreateIncomingLink(self):
        n1 = Neuron()
        lnk = Link(n1)
        self.assertTrue(lnk.Source == n1)
        self.assertTrue(lnk.Target is None)
        self.assertTrue(len(n1.Incoming) == 0)
        self.assertTrue(len(n1.Outgoing) == 1)
        self.assertTrue(n1.Outgoing[0] == lnk)

    def test_CreateOutgoingLink(self):
        n1 = Neuron()
        lnk = Link(None,n1)
        self.assertTrue(lnk.Source is None)
        self.assertTrue(lnk.Target == n1)
        self.assertTrue(len(n1.Incoming) == 1)
        self.assertTrue(len(n1.Outgoing) == 0)
        self.assertTrue(n1.Incoming[0] == lnk)

    def test_CreateFullLink(self):
        n1 = Neuron()
        n2 = Neuron()
        lnk = Link(n1, n2)
        self.assertTrue(lnk.Source == n1)
        self.assertTrue(lnk.Target == n2)
        self.assertTrue(len(n1.Incoming) == 0)
        self.assertTrue(n1.Outgoing[0] == lnk)
        self.assertTrue(n2.Incoming[0] == lnk)
        self.assertTrue(len(n2.Outgoing) == 0)
        
    def test_LinkHasWeight(self):
        lnk = Link()
        self.assertEqual(lnk.Weight, 1.0)
        
    def test_LinkWeightSettable(self):
        lnk = Link()
        lnk.Weight = -1.0
        self.assertEqual(lnk.Weight, -1.0)

class TestNeuron(unittest.TestCase):
    def setUp(self):
        self.n = Neuron()

    def test_CreateNeuron(self):
        self.assertTrue(self.n is not None)
        
    def test_NeuronHasLowThreshold(self):
        self.assertEqual(self.n.LowThreshold, 1.0)

    def test_NeuronHasHighThreshold(self):
        self.assertEqual(self.n.HighThreshold, 1.0)

    def test_NeuronLowThresholdSettable(self):
        self.n.LowThreshold = -1.0
        self.assertEqual(self.n.LowThreshold, -1.0)

    def test_NeuronHighThresholdSettable(self):
        self.n.HighThreshold = -1.0
        self.assertEqual(self.n.HighThreshold, -1.0)

    def test_NeuronHasActivity(self):
        self.assertEqual(self.n.Activation, 0.0)

    def test_NeuronActivitySettable(self):
        self.n.Activation = 1.0
        self.assertEqual(self.n.Activation, 1.0)

class TestNeuralNet(unittest.TestCase):
    def setUp(self):
        pass

    def test_CreateNetwork(self):
        net = NeuralNet()
        self.assertTrue(net is not None)
        
    def test_AddNeuronToNetwork(self):
        net = NeuralNet()
        net.add_neuron()
        self.assertTrue(len(net.Neurons) == 1)

    def test_AddTwoNeuronsToNetwork(self):
        net = NeuralNet()
        net.add_neuron()
        net.add_neuron()
        self.assertTrue(len(net.Neurons) == 2)
        
    def test_CreateTwoSeparateDifferentSizedNetworks(self):
        net1 = NeuralNet()
        net1.add_neuron()
        net1.add_neuron()
        net2 = NeuralNet()
        net2.add_neuron()
        net2.add_neuron()
        net2.add_neuron()
        self.assertTrue(len(net1.Neurons) == 2)
        self.assertTrue(len(net2.Neurons) == 3)
        self.assertFalse(net1 == net2)

    def test_LinkTwoNeurons(self):
        net = NeuralNet()
        n1 = net.add_neuron()
        n2 = net.add_neuron()
        lnk = net.add_link(n1, n2)
        self.assertTrue(len(net.Neurons) == 2)
        self.assertTrue(len(n1.Incoming) == 0)
        self.assertTrue(len(n1.Outgoing) == 1)
        self.assertTrue(n1.Outgoing[0] == lnk)
        self.assertTrue(len(n2.Incoming) == 1)
        self.assertTrue(len(n2.Outgoing) == 0)
        self.assertTrue(n2.Incoming[0] == lnk)
        self.assertEqual(n1.is_connected_outgoing(n2), lnk)
        self.assertEqual(n1.is_connected_incoming(n2), None)
        self.assertEqual(n2.is_connected_outgoing(n1), None)
        self.assertEqual(n2.is_connected_incoming(n1), lnk)

    def test_CantCreateTwoLinksInSameDirection(self):
        net = NeuralNet()
        n1 = net.add_neuron()
        n2 = net.add_neuron()
        lnk1 = net.add_link(n1, n2)
        lnk2 = net.add_link(n1, n2)
        self.assertEqual(lnk1, lnk2)

    def test_CanCreateTwoLinksInOppositeDirection(self):
        net = NeuralNet()
        n1 = net.add_neuron()
        n2 = net.add_neuron()
        lnk1 = net.add_link(n1, n2)
        lnk2 = net.add_link(n2, n1)
        self.assertNotEqual(lnk1, lnk2)

    def test_RemoveNeuronNoLinks(self):
        net = NeuralNet()
        n1 = net.add_neuron()
        n2 = net.add_neuron()
        self.assertTrue(len(net.Neurons) == 2)
        net.remove_neuron(n2)
        self.assertTrue(len(net.Neurons) == 1)
        self.assertTrue(net.Neurons[0] == n1)
        n2 = net.add_neuron()
        self.assertTrue(len(net.Neurons) == 2)
        net.remove_neuron(n1)
        self.assertTrue(len(net.Neurons) == 1)
        self.assertTrue(net.Neurons[0] == n2)

    def test_RemoveNeuronWithLinks(self):
        net = NeuralNet()
        n1 = net.add_neuron()
        n2 = net.add_neuron()
        lnk = net.add_link(n1, n2)
        self.assertTrue(len(net.Neurons) == 2)
        self.assertTrue(len(n1.Incoming) == 0)
        self.assertTrue(len(n1.Outgoing) == 1)
        self.assertTrue(n1.Outgoing[0] == lnk)
        self.assertTrue(len(n2.Incoming) == 1)
        self.assertTrue(len(n2.Outgoing) == 0)
        self.assertTrue(n2.Incoming[0] == lnk)
        self.assertEqual(n1.is_connected_outgoing(n2), lnk)
        self.assertEqual(n1.is_connected_incoming(n2), None)
        self.assertEqual(n2.is_connected_outgoing(n1), None)
        self.assertEqual(n2.is_connected_incoming(n1), lnk)
        net.remove_neuron(n1)
        self.assertTrue(len(net.Neurons) == 1)
        self.assertTrue(len(n1.Incoming) == 0)
        self.assertTrue(len(n1.Outgoing) == 0)
        self.assertTrue(len(n2.Incoming) == 0)
        self.assertTrue(len(n2.Outgoing) == 0)
        self.assertEqual(n1.is_connected_outgoing(n2), None)
        self.assertEqual(n1.is_connected_incoming(n2), None)
        self.assertEqual(n2.is_connected_outgoing(n1), None)
        self.assertEqual(n2.is_connected_incoming(n1), None)

    def test_RemoveLink(self):
        net = NeuralNet()
        n1 = net.add_neuron()
        n2 = net.add_neuron()
        lnk = net.add_link(n1, n2)
        self.assertTrue(len(net.Neurons) == 2)
        self.assertTrue(len(n1.Incoming) == 0)
        self.assertTrue(len(n1.Outgoing) == 1)
        self.assertTrue(n1.Outgoing[0] == lnk)
        self.assertTrue(len(n2.Incoming) == 1)
        self.assertTrue(len(n2.Outgoing) == 0)
        self.assertTrue(n2.Incoming[0] == lnk)
        self.assertEqual(n1.is_connected_outgoing(n2), lnk)
        self.assertEqual(n1.is_connected_incoming(n2), None)
        self.assertEqual(n2.is_connected_outgoing(n1), None)
        self.assertEqual(n2.is_connected_incoming(n1), lnk)
        net.remove_link(lnk)
        self.assertTrue(len(net.Neurons) == 2)
        self.assertTrue(len(n1.Incoming) == 0)
        self.assertTrue(len(n1.Outgoing) == 0)
        self.assertTrue(len(n2.Incoming) == 0)
        self.assertTrue(len(n2.Outgoing) == 0)
        self.assertEqual(n1.is_connected_outgoing(n2), None)
        self.assertEqual(n1.is_connected_incoming(n2), None)
        self.assertEqual(n2.is_connected_outgoing(n1), None)
        self.assertEqual(n2.is_connected_incoming(n1), None)

class TestNeuralNetWriter(unittest.TestCase):
    def setUp(self):
        net = NeuralNet()
        n1 = net.add_neuron()
        n1.Name = "input"
        n2 = net.add_neuron()
        n2.Name = "output"
        net.add_link(n1, n2)
        self.net = net

    def test_PickleToXMLNet(self):
        stream = NeuralNetIO()
        stream.write('test.pickle.xml', self.net)
        net = stream.read('test.pickle.xml')
        n1 = net.Neurons[0]
        n2 = net.Neurons[1]
        self.assertTrue(len(net.Neurons) == 2)
        self.assertTrue(len(n1.Incoming) == 0)
        self.assertTrue(len(n1.Outgoing) == 1)
        lnk = n1.Outgoing[0]
        self.assertTrue(n1.Outgoing[0] == lnk)
        self.assertTrue(len(n2.Incoming) == 1)
        self.assertTrue(len(n2.Outgoing) == 0)
        self.assertTrue(n2.Incoming[0] == lnk)
        self.assertEqual(n1.is_connected_outgoing(n2), lnk)
        self.assertEqual(n1.is_connected_incoming(n2), None)
        self.assertEqual(n2.is_connected_outgoing(n1), None)
        self.assertEqual(n2.is_connected_incoming(n1), lnk)

class TestNeuralNetActivity(unittest.TestCase):
    def setUp(self):
        net = NeuralNet()
        self.in1 = net.add_neuron()
        self.in2 = net.add_neuron()
        self.mid1 = net.add_neuron()
        self.out1 = net.add_neuron()
        self.out2 = net.add_neuron()
        net.add_link(self.in1, self.mid1, 1.0)
        net.add_link(self.in2, self.mid1, 1.0)
        net.add_link(self.mid1, self.out1, 1.0)
        net.add_link(self.mid1, self.out2, 1.0)
        self.net = net
        self.in1.Name = "input-1"
        self.in2.Name = "input-2"
        self.mid1.Name = "mid-1"
        self.out1.Name = "output-1"
        self.out2.Name = "output-2"
        
    def test_AllOff(self):

        for i in range(0, _MIN_FREQ_):  # update at least _MIN_FREQ_ times to make sure we've exceeded any MinFrequency thresholds
            self.net.update()

        self.assertEqual(self.in1.Activation, 0.0)
        self.assertEqual(self.in2.Activation, 0.0)
        self.assertEqual(self.mid1.Activation, 0.0)
        self.assertEqual(self.out1.Activation, 0.0)
        self.assertEqual(self.out2.Activation, 0.0)
        
    def test_TurningIn1OnTurnsOnNothingElse(self):
        self.in1.Activation = 1.0

        for i in range(0, _MIN_FREQ_):  # update at least _MIN_FREQ_ times to make sure we've exceeded any MinFrequency thresholds
            self.net.update()

        self.assertEqual(self.in1.Activation, 1.0)
        self.assertEqual(self.in2.Activation, 0.0)
        self.assertEqual(self.mid1.Activation, 0.0)
        self.assertEqual(self.out1.Activation, 0.0)
        self.assertEqual(self.out2.Activation, 0.0)

    def test_TurningIn2OnTurnsOnNothingElse(self):
        self.in2.Activation = 1.0

        for i in range(0, _MIN_FREQ_):  # update at least _MIN_FREQ_ times to make sure we've exceeded any MinFrequency thresholds
            self.net.update()

        self.assertEqual(self.in1.Activation, 0.0)
        self.assertEqual(self.in2.Activation, 1.0)
        self.assertEqual(self.mid1.Activation, 0.0)
        self.assertEqual(self.out1.Activation, 0.0)
        self.assertEqual(self.out2.Activation, 0.0)

    def test_TurningBothInputsOnTurnsOnBothOutputs(self):
        self.in1.Activation = 1.0
        self.in2.Activation = 1.0
              
        for i in range(0, _MIN_FREQ_):  # update at least _MIN_FREQ_ times to make sure we've exceeded any MinFrequency thresholds
            self.net.update()

        self.assertEqual(self.in1.Activation, 1.0)
        self.assertEqual(self.in2.Activation, 1.0)
        self.assertEqual(self.mid1.Activation, 1.0)
        self.assertEqual(self.out1.Activation, 1.0)
        self.assertEqual(self.out2.Activation, 1.0)
        
    def test_ActivationWorksAfterPickling(self):
        stream = NeuralNetIO()
        stream.write('test2.pickle.xml', self.net)
        self.net = stream.read('test2.pickle.xml')

        self.in1 = self.net.Neurons[0]
        self.in2 = self.net.Neurons[1]
        self.mid1 = self.net.Neurons[2]
        self.out1 = self.net.Neurons[3]
        self.out2 = self.net.Neurons[4]

        self.test_TurningBothInputsOnTurnsOnBothOutputs()

    def state_changed(self):
        self.state_latch += 1

    def test_StateChangedCallback(self):
        self.net.set_callback(self.state_changed)
        self.state_latch = 0
        self.in1.Activation = 1.0
        self.in2.Activation = 1.0
        self.assertEqual(0, self.state_latch)

        for i in range(0, _MIN_FREQ_):  # update at least _MIN_FREQ_ times to make sure we've exceeded any MinFrequency thresholds
            self.net.update()

        self.assertEqual(2, self.state_latch)
        self.state_latch = 0

        for i in range(0, _MIN_FREQ_):  # update at least _MIN_FREQ_ times to make sure we've exceeded any MinFrequency thresholds
            self.net.update()

        self.assertEqual(0, self.state_latch)
        
class TestNeuralNetInhibition(unittest.TestCase):
    def setUp(self):
        net = NeuralNet()
        self.in1 = net.add_neuron()
        self.in2 = net.add_neuron()
        self.mid1 = net.add_neuron()
        self.out1 = net.add_neuron()
        self.out2 = net.add_neuron()
        net.add_link(self.in1, self.mid1, 1.0)
        net.add_link(self.in2, self.mid1, -1.0)
        net.add_link(self.mid1, self.out1, 1.0)
        net.add_link(self.mid1, self.out2, 1.0)
        self.net = net

    def test_Inhibition(self):
        self.in1.Activation = 1.0
        self.in2.Activation = 1.0

        for i in range(0, _MIN_FREQ_):  # update at least _MIN_FREQ_ times to make sure we've exceeded any MinFrequency thresholds
            self.net.update()

        self.assertEqual(self.in1.Activation, 1.0)
        self.assertEqual(self.in2.Activation, 1.0)
        self.assertEqual(self.mid1.Activation, 0.0)
        self.assertEqual(self.out1.Activation, 0.0)
        self.assertEqual(self.out2.Activation, 0.0)

class TestSubNetBasics(unittest.TestCase):
    def test_CreateSubNet(self):
        self.sub = SubNet()
        self.assertIsNotNone(self.sub)
        self.assertTrue(isinstance(self.sub, SubNet))
        self.assertTrue(isinstance(self.sub, Neuron))
        self.assertIsNotNone(self.sub.Net)
        self.assertTrue(isinstance(self.sub.Net, NeuralNet))

    def test_AddSubNetToNetwork(self):
        net = NeuralNet()
        net.add_subnet('test2', 'test2.pickle.xml')
        self.assertTrue(len(net.Neurons) == 1)

class TestSubNet(unittest.TestCase):
    def setUp(self):
        self.net = net = NeuralNet()
        # this should load a subnet, as a neuron
        self.sub = net.add_subnet('test2', 'test2.pickle.xml')
        # add neurons to our net to attach to the subnet's interface
        self.in1 = net.add_neuron()
        self.in2 = net.add_neuron()
        self.out1 = net.add_neuron()
        self.out2 = net.add_neuron()

    def test_OpenedSomething(self):
        self.assertIsNotNone(self.sub)
        self.assertTrue(isinstance(self.sub, SubNet))
        self.assertTrue(isinstance(self.sub, Neuron))
        self.assertIsNotNone(self.sub.Net)
        self.assertTrue(isinstance(self.sub.Net, NeuralNet))
        self.assertIsNotNone(self.sub.Net.Neurons)
        self.assertEqual(len(self.sub.Net.Neurons), 5)
        self.assertEqual(self.sub.Net.Neurons[0].Name, "input-1")
        self.assertEqual(self.sub.Net.Neurons[1].Name, "input-2")
        self.assertEqual(self.sub.Net.Neurons[2].Name, "mid-1")
        self.assertEqual(self.sub.Net.Neurons[3].Name, "output-1")
        self.assertEqual(self.sub.Net.Neurons[4].Name, "output-2")        

    def test_AddSubnetLinks(self):
        sub = self.sub
        net = self.net
        in1 = self.in1
        in2 = self.in2
        out1 = self.out1
        out2 = self.out2
        sub_in1 = sub.Net.Neurons[0]
        sub_in2 = sub.Net.Neurons[1]
        sub_out1 = sub.Net.Neurons[3]
        sub_out2 = sub.Net.Neurons[4]

        #add some links into the subnet from the net        
        link1 = net.add_link(in1, sub)
        link2 = net.add_link(in2, sub)

        #add some links out of the subnet to the net        
        link3 = net.add_link(sub, out1)
        link4 = net.add_link(sub, out2)

        # adding a link into a subnet should establish the standard neuron connections: 
        #
        # 1: Set link.Source to the source neuron external from subnet --> link.Source is the internal neuron's Activation source
        # 2: Set link.Target to subnet --> link.Target is used to locate endpoint to render links       
        # 3: Put the link into sub.Incoming --> sub.Incoming is used to render the shape of neurons
        # 4: Put the link into neuron.Outgoing --> neuraledit draws links by walking a neuron's outgoing link list        

        #1
        self.assertIsNotNone(link1.Source)
        self.assertEqual(link1.Source, in1)
        self.assertIsNotNone(link2.Source)
        self.assertEqual(link2.Source, in2)

        #2
        self.assertIsNotNone(link1.Target)
        self.assertEqual(link1.Target, sub)
        self.assertIsNotNone(link2.Target)
        self.assertEqual(link2.Target, sub)

        #3 
        self.assertEqual(2, len(sub.Incoming))
        self.assertEqual(link1, sub.Incoming[0])
        self.assertEqual(link2, sub.Incoming[1])

        #4 
        self.assertEqual(1, len(in1.Outgoing))
        self.assertEqual(link1, in1.Outgoing[0])
        self.assertEqual(1, len(in2.Outgoing))
        self.assertEqual(link2, in2.Outgoing[0])

        # Additionally, the link should be wired to the subnet's internal network:
        #
        # 5: internal[N].Incoming == link --> link.Source is 
        # where N was the next available neuron at the time the link was added
        # in the future maybe I'll support more sophisticated linking into a subnet
        # but for now its just Add links in order

        #5 
        self.assertEqual(1, len(sub_in1.Incoming))
        self.assertEqual(link1, sub_in1.Incoming[0])
        self.assertEqual(1, len(sub_in2.Incoming))
        self.assertEqual(link2, sub_in2.Incoming[0])


        # adding a link out of a subnet should establish these connections
        #
        # 1: Set link.Source to subnet internal neuron --> link.Source is the net neuron's Activation source
        # 2: Set link.Target to net neuron --> link.Target is used to locate endpoint to render links       
        # 3: Put the link into neuron.Incoming --> sub.Incoming is used to render the shape of neurons
        # 4: Put the link into sub.Outgoing --> neuraledit draws links by walking a neuron's outgoing link list        

        #1
        self.assertIsNotNone(link3.Source)
        self.assertEqual(link3.Source, sub_out1)
        self.assertIsNotNone(link4.Source)
        self.assertEqual(link4.Source, sub_out2)

        #2
        self.assertIsNotNone(link3.Target)
        self.assertEqual(link3.Target, out1)
        self.assertIsNotNone(link4.Target)
        self.assertEqual(link4.Target, out2)

        #3 
        self.assertEqual(1, len(out1.Incoming))
        self.assertEqual(link3, out1.Incoming[0])
        self.assertEqual(1, len(out2.Incoming))
        self.assertEqual(link4, out2.Incoming[0])

        #4 
        self.assertEqual(2, len(sub.Outgoing))
        self.assertEqual(link3, sub.Outgoing[0])
        self.assertEqual(link4, sub.Outgoing[1])

        # Additionally, the link should be wired to the subnet's internal network:
        #
        # 5: internal[N].Outgoing == link --> link.Target is 
        # where N was the next available neuron at the time the link was added
        # in the future maybe I'll support more sophisticated linking into a subnet
        # but for now its just Add links in order

        #5 
        self.assertEqual(1, len(sub_out1.Outgoing))
        self.assertEqual(link3, sub_out1.Outgoing[0])
        self.assertEqual(1, len(sub_out2.Outgoing))
        self.assertEqual(link4, sub_out2.Outgoing[0])

    def test_AddBogusSubnetLinks(self):
        sub = self.sub
        net = self.net
        in1 = self.in1
        in2 = self.in2
        out1 = self.out1
        out2 = self.out2
        sub_in1 = sub.Net.Neurons[0]
        sub_in2 = sub.Net.Neurons[1]
        sub_out1 = sub.Net.Neurons[3]
        sub_out2 = sub.Net.Neurons[4]

        #add some links into the subnet from the net        
        link1 = net.add_link(in1, sub)
        link2 = net.add_link(in2, sub)
        link3 = net.add_link(sub, out1)
        link4 = net.add_link(sub, out2)

        #try adding a link into a full subnet
        in3 = net.add_neuron()
        link5 = net.add_link(in3, sub)
        self.assertIsNotNone(link5)
        self.assertEqual(link5.Source, in3)
        self.assertEqual(1, len(in3.Outgoing))
        self.assertEqual(link5, in3.Outgoing[0])
        self.assertIsNone(link5.Target)

        #make sure we can discard the link
        net.remove_link(link5)
        self.assertEqual(link5.Source, in3)
        self.assertEqual(0, len(in3.Outgoing))

        #try adding a link out of a full subnet
        out3 = net.add_neuron()
        link6 = net.add_link(sub, out3)
        self.assertIsNotNone(link6)
        self.assertIsNotNone(link6.Target)
        self.assertEqual(link6.Target, out3)
        self.assertEqual(1, len(out3.Incoming))
        self.assertEqual(link6, out3.Incoming[0])
        self.assertIsNone(link6.Source)

        #make sure we can discard the link
        net.remove_link(link6)
        self.assertEqual(link6.Target, out3)
        self.assertEqual(0, len(out3.Incoming))
       
    def test_RemoveSubnetLinks(self):
        sub = self.sub
        net = self.net
        in1 = self.in1
        in2 = self.in2
        out1 = self.out1
        out2 = self.out2
        sub_in1 = sub.Net.Neurons[0]
        sub_in2 = sub.Net.Neurons[1]
        sub_out1 = sub.Net.Neurons[3]
        sub_out2 = sub.Net.Neurons[4]

        #add some links into the subnet from the net        
        link1 = net.add_link(in1, sub)
        link2 = net.add_link(in2, sub)

        #add some links out of the subnet to the net        
        link3 = net.add_link(sub, out1)
        link4 = net.add_link(sub, out2)

        # removing a link into a subnet should remove the standard neuron connections: 
        #
        # 1: remove link from link.Source.Outgoing where link.Source is a neuron external from subnet
        # 2: remove link from link.Target.Incoming where link.Target is the subnet itself
        # 3: remove link from sub internal neuron Incoming 

        self.assertTrue(link1 in in1.Outgoing)
        self.assertTrue(link2 in in2.Outgoing)
        self.assertTrue(link1 in sub.Incoming)
        self.assertTrue(link2 in sub.Incoming)
        self.assertTrue(link1 in sub_in1.Incoming)
        self.assertTrue(link2 in sub_in2.Incoming)

        net.remove_link(link1)
        net.remove_link(link2)

        #1
        self.assertFalse(link1 in in1.Outgoing)
        self.assertFalse(link2 in in2.Outgoing)

        #2
        self.assertFalse(link1 in sub.Incoming)
        self.assertFalse(link2 in sub.Incoming)

        #3 
        self.assertFalse(link1 in sub_in1.Incoming)
        self.assertFalse(link2 in sub_in2.Incoming)

        # removing a link out of a subnet should remove these connections
        #
        # 1: Remove link from subnet internal neuron Outgoing
        # 2: Remove link from external neuron Incoming
        # 3: Remove link from sub Outgoing

        self.assertTrue(link3 in sub_out1.Outgoing)
        self.assertTrue(link4 in sub_out2.Outgoing)
        self.assertTrue(link3 in out1.Incoming)
        self.assertTrue(link4 in out2.Incoming)
        self.assertTrue(link3 in sub.Outgoing)
        self.assertTrue(link4 in sub.Outgoing)

        net.remove_link(link3)
        net.remove_link(link4)

        #1
        self.assertFalse(link3 in sub_out1.Outgoing)
        self.assertFalse(link4 in sub_out2.Outgoing)

        #2
        self.assertFalse(link3 in out1.Incoming)
        self.assertFalse(link4 in out2.Incoming)

        #3 
        self.assertFalse(link3 in sub.Outgoing)
        self.assertFalse(link4 in sub.Outgoing)

    def test_RemoveSubnetWithAttachedNeuron(self):
        sub = self.sub
        net = self.net
        in1 = self.in1
        in2 = self.in2
        out1 = self.out1
        out2 = self.out2
        sub_in1 = sub.Net.Neurons[0]
        sub_in2 = sub.Net.Neurons[1]
        sub_out1 = sub.Net.Neurons[3]
        sub_out2 = sub.Net.Neurons[4]

        #add some links into the subnet from the net        
        link1 = net.add_link(in1, sub)
        link2 = net.add_link(in2, sub)

        #add some links out of the subnet to the net        
        link3 = net.add_link(sub, out1)
        link4 = net.add_link(sub, out2)

        # removing the subnet should sever all links 

        #
        # 1: remove link from link.Source.Outgoing where link.Source is a neuron external from subnet
        # 2: remove link from link.Target.Incoming where link.Target is the subnet itself
        # 3: remove link from sub internal neuron Incoming 
        #
        # 4: Remove link from subnet internal neuron Outgoing
        # 5: Remove link from external neuron Incoming
        # 6: Remove link from sub Outgoing

        self.assertTrue(sub in net.Neurons)
        self.assertTrue(link1 in in1.Outgoing)
        self.assertTrue(link2 in in2.Outgoing)
        self.assertTrue(link1 in sub.Incoming)
        self.assertTrue(link2 in sub.Incoming)
        self.assertTrue(link1 in sub_in1.Incoming)
        self.assertTrue(link2 in sub_in2.Incoming)
        self.assertTrue(link3 in sub_out1.Outgoing)
        self.assertTrue(link4 in sub_out2.Outgoing)
        self.assertTrue(link3 in out1.Incoming)
        self.assertTrue(link4 in out2.Incoming)
        self.assertTrue(link3 in sub.Outgoing)
        self.assertTrue(link4 in sub.Outgoing)

        net.remove_neuron(sub)

        self.assertFalse(sub in net.Neurons)

        #1
        self.assertFalse(link1 in in1.Outgoing)
        self.assertFalse(link2 in in2.Outgoing)

        #2
        self.assertFalse(link1 in sub.Incoming)
        self.assertFalse(link2 in sub.Incoming)

        #3 
        self.assertFalse(link1 in sub_in1.Incoming)
        self.assertFalse(link2 in sub_in2.Incoming)

        #4
        self.assertFalse(link3 in sub_out1.Outgoing)
        self.assertFalse(link4 in sub_out2.Outgoing)

        #5
        self.assertFalse(link3 in out1.Incoming)
        self.assertFalse(link4 in out2.Incoming)

        #6 
        self.assertFalse(link3 in sub.Outgoing)
        self.assertFalse(link4 in sub.Outgoing)

    def test_RemoveNeuronWithAttachedSubNet(self):
        sub = self.sub
        net = self.net
        in1 = self.in1
        in2 = self.in2
        out1 = self.out1
        out2 = self.out2
        sub_in1 = sub.Net.Neurons[0]
        sub_in2 = sub.Net.Neurons[1]
        sub_out1 = sub.Net.Neurons[3]
        sub_out2 = sub.Net.Neurons[4]

        #add some links into the subnet from the net        
        link1 = net.add_link(in1, sub)
        link2 = net.add_link(in2, sub)

        #add some links out of the subnet to the net        
        link3 = net.add_link(sub, out1)
        link4 = net.add_link(sub, out2)

        # removing a neuron should sever all links to and from that neuron

        #
        # 1: remove link from link.Source.Outgoing where link.Source is a neuron external from subnet
        # 2: remove link from link.Target.Incoming where link.Target is the subnet itself
        # 3: remove link from sub internal neuron Incoming 
        #
        # 4: Remove link from subnet internal neuron Outgoing
        # 5: Remove link from external neuron Incoming
        # 6: Remove link from sub Outgoing

        self.assertTrue(sub in net.Neurons)
        self.assertTrue(link1 in in1.Outgoing)
        self.assertTrue(link2 in in2.Outgoing)
        self.assertTrue(link1 in sub.Incoming)
        self.assertTrue(link2 in sub.Incoming)
        self.assertTrue(link1 in sub_in1.Incoming)
        self.assertTrue(link2 in sub_in2.Incoming)
        self.assertTrue(link3 in sub_out1.Outgoing)
        self.assertTrue(link4 in sub_out2.Outgoing)
        self.assertTrue(link3 in out1.Incoming)
        self.assertTrue(link4 in out2.Incoming)
        self.assertTrue(link3 in sub.Outgoing)
        self.assertTrue(link4 in sub.Outgoing)

        net.remove_neuron(in1)

        self.assertTrue(sub in net.Neurons)
        self.assertFalse(in1 in net.Neurons)
        self.assertFalse(link1 in in1.Outgoing)
        self.assertTrue(link2 in in2.Outgoing)
        self.assertFalse(link1 in sub.Incoming)
        self.assertTrue(link2 in sub.Incoming)
        self.assertFalse(link1 in sub_in1.Incoming)
        self.assertTrue(link2 in sub_in2.Incoming)
        self.assertTrue(link3 in sub_out1.Outgoing)
        self.assertTrue(link4 in sub_out2.Outgoing)
        self.assertTrue(link3 in out1.Incoming)
        self.assertTrue(link4 in out2.Incoming)
        self.assertTrue(link3 in sub.Outgoing)
        self.assertTrue(link4 in sub.Outgoing)

        net.remove_neuron(out1)

        self.assertTrue(sub in net.Neurons)
        self.assertFalse(in1 in net.Neurons)
        self.assertFalse(out1 in net.Neurons)
        self.assertFalse(link1 in in1.Outgoing)
        self.assertTrue(link2 in in2.Outgoing)
        self.assertFalse(link1 in sub.Incoming)
        self.assertTrue(link2 in sub.Incoming)
        self.assertFalse(link1 in sub_in1.Incoming)
        self.assertTrue(link2 in sub_in2.Incoming)
        self.assertFalse(link3 in sub_out1.Outgoing)
        self.assertTrue(link4 in sub_out2.Outgoing)
        self.assertFalse(link3 in out1.Incoming)
        self.assertTrue(link4 in out2.Incoming)
        self.assertFalse(link3 in sub.Outgoing)
        self.assertTrue(link4 in sub.Outgoing)


class TestSubNetNeuralNetWriter(unittest.TestCase):
    def setUp(self):
        self.net = net = NeuralNet()
        # this should load a subnet, as a neuron
        self.sub = net.add_subnet('test2', 'test2.pickle.xml')
        # add neurons to our net to attach to the subnet's interface
        self.in1 = net.add_neuron()
        self.in2 = net.add_neuron()
        self.out1 = net.add_neuron()
        self.out2 = net.add_neuron()
        # attach outer net to inner net
        self.link1 = net.add_link(self.in1, self.sub)
        self.link2 = net.add_link(self.in2, self.sub)
        self.link3 = net.add_link(self.sub, self.out1)
        self.link4 = net.add_link(self.sub, self.out2)

    def test_PickleToXMLNet(self):
        stream = NeuralNetIO()
        stream.write('test3.pickle.xml', self.net)
        net = net = stream.read('test3.pickle.xml')
        sub = net.Neurons[0]
        in1 = net.Neurons[1]
        in2 = net.Neurons[2]
        out1 = net.Neurons[3]
        out2 = net.Neurons[4]        
        sub_in1 = sub.Net.Neurons[0]
        sub_in2 = sub.Net.Neurons[1]
        sub_out1 = sub.Net.Neurons[3]
        sub_out2 = sub.Net.Neurons[4]
        link1 = in1.Outgoing[0]
        link2 = in2.Outgoing[0]
        link3 = out1.Incoming[0]
        link4 = out2.Incoming[0]

        self.assertEqual(sub.Path, 'test2.pickle.xml')
        self.assertIsNotNone(link1.Source)
        self.assertEqual(link1.Source, in1)
        self.assertIsNotNone(link2.Source)
        self.assertEqual(link2.Source, in2)
        self.assertIsNotNone(link1.Target)
        self.assertEqual(link1.Target, sub)
        self.assertIsNotNone(link2.Target)
        self.assertEqual(link2.Target, sub)
        self.assertEqual(2, len(sub.Incoming))
        self.assertEqual(link1, sub.Incoming[0])
        self.assertEqual(link2, sub.Incoming[1])
        self.assertEqual(1, len(in1.Outgoing))
        self.assertEqual(link1, in1.Outgoing[0])
        self.assertEqual(1, len(in2.Outgoing))
        self.assertEqual(link2, in2.Outgoing[0])
        self.assertEqual(1, len(sub_in1.Incoming))
        self.assertEqual(link1, sub_in1.Incoming[0])
        self.assertEqual(1, len(sub_in2.Incoming))
        self.assertEqual(link2, sub_in2.Incoming[0])
        self.assertIsNotNone(link3.Source)
        self.assertEqual(link3.Source, sub_out1)
        self.assertIsNotNone(link4.Source)
        self.assertEqual(link4.Source, sub_out2)
        self.assertIsNotNone(link3.Target)
        self.assertEqual(link3.Target, out1)
        self.assertIsNotNone(link4.Target)
        self.assertEqual(link4.Target, out2)
        self.assertEqual(1, len(out1.Incoming))
        self.assertEqual(link3, out1.Incoming[0])
        self.assertEqual(1, len(out2.Incoming))
        self.assertEqual(link4, out2.Incoming[0])
        self.assertEqual(2, len(sub.Outgoing))
        self.assertEqual(link3, sub.Outgoing[0])
        self.assertEqual(link4, sub.Outgoing[1])
        self.assertEqual(1, len(sub_out1.Outgoing))
        self.assertEqual(link3, sub_out1.Outgoing[0])
        self.assertEqual(1, len(sub_out2.Outgoing))
        self.assertEqual(link4, sub_out2.Outgoing[0])
        
class TestSubNetActivity(unittest.TestCase):
    def setUp(self):
        self.net = net = NeuralNet()
        self.sub = net.add_subnet('test2', 'test2.pickle.xml')
        # add neurons to our net to attach to the subnet's interface
        self.in1 = net.add_neuron()
        self.in2 = net.add_neuron()
        self.out1 = net.add_neuron()
        self.out2 = net.add_neuron()
        # attach outer net to inner net
        self.link1 = net.add_link(self.in1, self.sub)
        self.link2 = net.add_link(self.in2, self.sub)
        self.link3 = net.add_link(self.sub, self.out1)
        self.link4 = net.add_link(self.sub, self.out2)

    def test_SubNetAllOff(self):

        for i in range(0, _MIN_FREQ_):  # update at least _MIN_FREQ_ times to make sure we've exceeded any MinFrequency thresholds
            self.net.update()

        self.assertEqual(self.in1.Activation, 0.0)
        self.assertEqual(self.in2.Activation, 0.0)
        self.assertEqual(self.out1.Activation, 0.0)
        self.assertEqual(self.out2.Activation, 0.0)
        
    def test_SubNetTurningIn1OnTurnsOnNothingElse(self):
        self.in1.Activation = 1.0

        for i in range(0, _MIN_FREQ_):  # update at least _MIN_FREQ_ times to make sure we've exceeded any MinFrequency thresholds
            self.net.update()

        self.assertEqual(self.in1.Activation, 1.0)
        self.assertEqual(self.in2.Activation, 0.0)
        self.assertEqual(self.out1.Activation, 0.0)
        self.assertEqual(self.out2.Activation, 0.0)

    def test_SubNetTurningIn2OnTurnsOnNothingElse(self):
        self.in2.Activation = 1.0

        for i in range(0, _MIN_FREQ_):  # update at least _MIN_FREQ_ times to make sure we've exceeded any MinFrequency thresholds
            self.net.update()

        self.assertEqual(self.in1.Activation, 0.0)
        self.assertEqual(self.in2.Activation, 1.0)
        self.assertEqual(self.out1.Activation, 0.0)
        self.assertEqual(self.out2.Activation, 0.0)

    def test_SubNetTurningBothInputsOnTurnsOnBothOutputs(self):
        self.in1.Activation = 1.0
        self.in2.Activation = 1.0

        for i in range(0, _MIN_FREQ_):  # update at least _MIN_FREQ_ times to make sure we've exceeded any MinFrequency thresholds
            self.net.update()

        self.assertEqual(self.in1.Activation, 1.0)
        self.assertEqual(self.in2.Activation, 1.0)
        self.assertEqual(self.out1.Activation, 1.0)
        self.assertEqual(self.out2.Activation, 1.0)
        
    def test_ActivationWorksAfterPickling(self):
        stream = NeuralNetIO()
        stream.write('test3.pickle.xml', self.net)
        self.net = stream.read('test3.pickle.xml')
        self.in1 = self.net.Neurons[1]
        self.in2 = self.net.Neurons[2]
        self.out1 = self.net.Neurons[3]
        self.out2 = self.net.Neurons[4]
        self.test_SubNetTurningBothInputsOnTurnsOnBothOutputs()

class TestSubNetInhibition(unittest.TestCase):
    def setUp(self):
        self.net = net = NeuralNet()
        self.sub = sub = net.add_subnet('test2', 'test2.pickle.xml')
        self.in1 = net.add_neuron()
        self.in2 = net.add_neuron()
        self.out1 = net.add_neuron()
        self.out2 = net.add_neuron()
        net.add_link(self.in1, sub, 1.0)
        net.add_link(self.in2, sub, -1.0)
        net.add_link(sub, self.out1, 1.0)
        net.add_link(sub, self.out2, 1.0)

    def test_Inhibition(self):
        self.in1.Activation = 1.0
        self.in2.Activation = 1.0

        for i in range(0, _MIN_FREQ_):  # update at least _MIN_FREQ_ times to make sure we've exceeded any MinFrequency thresholds
            self.net.update()

        self.assertEqual(self.in1.Activation, 1.0)
        self.assertEqual(self.in2.Activation, 1.0)
        self.assertEqual(self.out1.Activation, 0.0)
        self.assertEqual(self.out2.Activation, 0.0)
                       
if __name__ == '__main__':
    unittest.main()

#!/usr/bin/env python
"""Neural Net XMLRPC Server Test Code"""
import unittest
import  xmlrpclib
from neural.netserver import NetServer
from neural.neuron import Neuron
from time import sleep
from datetime import datetime, timedelta
import unbuffered_print

_MIN_FREQ_ = 10 # default min ticks to run tests for

class TestServer(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.server = NetServer(logRequests=False)
        self.client = xmlrpclib.ServerProxy('http://127.0.0.1:8080')
        self.client.load_net('test.pickle.xml')

    @classmethod
    def tearDownClass(self):
        self.server.stop()
        
    def setUp(self):
        pass

    def test_BogusRequest(self):
        self.assertRaises(xmlrpclib.Fault,self.client.BogusRequest)

    def test_ListMethods(self):
       test_methods = ['get_activation',
                       'get_high_threshold',
                       'get_input_list',
                       'get_links_incoming',
                       'get_links_outgoing',
                       'get_low_threshold',
                       'get_neuron_list',
                       'get_output_list',
                       'get_update_period',
                       'get_weight',
                       'load_net',
                       'set_activation',
                       'set_high_threshold',
                       'set_low_threshold',
                       'set_update_period',
                       'set_weight',
                       'system.listMethods',
                       'system.methodHelp',
                       'system.methodSignature',
                       'update']
       methods = self.client.system.listMethods()
       self.assertEqual(methods, test_methods)

    def test_load_net(self):
        net = self.server.State.Net
        n1 = net.Neurons[0]
        n2 = net.Neurons[1]
        self.assertTrue(len(net.Neurons) == 2)
        self.assertTrue(len(n1.Incoming) == 0)
        self.assertTrue(len(n1.Outgoing) == 1)
        link = n1.Outgoing[0]
        self.assertTrue(n1.Outgoing[0] == link)
        self.assertTrue(len(n2.Incoming) == 1)
        self.assertTrue(len(n2.Outgoing) == 0)
        self.assertTrue(n2.Incoming[0] == link)
        self.assertEqual(n1.is_connected_outgoing(n2), link)
        self.assertEqual(n1.is_connected_incoming(n2), None)
        self.assertEqual(n2.is_connected_outgoing(n1), None)
        self.assertEqual(n2.is_connected_incoming(n1), link)

    def test_get_neuron_list(self):
        lval = self.client.get_neuron_list()
        self.assertTrue(len(lval) == 2)
        self.assertTrue(lval[0][:7] == 'input')
        self.assertTrue(lval[1][:7] == 'output')

    def test_get_input_list(self):
        lval = self.client.get_input_list()
        self.assertTrue(len(lval) == 1)
        self.assertTrue(lval[0][:7] == 'input')

    def test_get_output_list(self):
        lval = self.client.get_output_list()
        self.assertTrue(len(lval) == 1)
        self.assertTrue(lval[0][:7] == 'output')

    def test_get_links_incoming(self):
        neurons = self.client.get_neuron_list()
        self.assertEqual(self.client.get_links_incoming(neurons[0]), 0)
        self.assertEqual(self.client.get_links_incoming(neurons[1]), 1)

    def test_get_links_outgoing(self):
        neurons = self.client.get_neuron_list()
        self.assertEqual(self.client.get_links_outgoing(neurons[0]), 1)
        self.assertEqual(self.client.get_links_outgoing(neurons[1]), 0)

    def test_get_weight(self):
        neurons = self.client.get_output_list()
        self.assertEqual(self.client.get_weight(neurons[0], 0), 1.0)
        self.assertEqual(self.client.get_weight(neurons[0], 1), 0.0)
        self.assertEqual(self.client.get_weight(neurons[0], -1), 0.0)
        self.assertEqual(self.client.get_weight("bogus", 0), 0.0)

    def test_get_low_threshold(self):
        neurons = self.client.get_neuron_list()
        self.assertEqual(self.client.get_low_threshold(neurons[0]), 1.0)
        self.assertEqual(self.client.get_low_threshold(neurons[1]), 1.0)
        self.assertEqual(self.client.get_low_threshold("bogus"), 0.0)

    def test_get_high_threshold(self):
        neurons = self.client.get_neuron_list()
        self.assertEqual(self.client.get_high_threshold(neurons[0]), 1.0)
        self.assertEqual(self.client.get_high_threshold(neurons[1]), 1.0)
        self.assertEqual(self.client.get_high_threshold("bogus"), 0.0)

    def test_get_activation(self):
        neurons = self.client.get_neuron_list()
        self.assertEqual(self.client.get_activation(neurons[0]), 0.0)
        self.assertEqual(self.client.get_activation(neurons[1]), 0.0)
        self.assertEqual(self.client.get_activation("bogus"), 0.0)

    def test_get_update_period(self):
        self.assertEqual(self.client.get_update_period(), 0.0)

    def test_set_weight(self):
        neurons = self.client.get_output_list()
        self.assertEqual(self.client.get_weight(neurons[0], 0), 1.0)
        self.assertTrue(self.client.set_weight(neurons[0], 0, 0.5))
        self.assertEqual(self.client.get_weight(neurons[0], 0), 0.5)
        self.assertTrue(self.client.set_weight(neurons[0], 0, 1.0))
        self.assertEqual(self.client.get_weight(neurons[0], 0), 1.0)

    def test_set_low_threshold(self):
        neurons = self.client.get_neuron_list()
        self.assertTrue(self.client.get_low_threshold(neurons[0]), 1.0)
        self.assertTrue(self.client.set_low_threshold(neurons[0], 0.5))
        self.assertTrue(self.client.get_low_threshold(neurons[0]), 0.5)
        self.assertTrue(self.client.set_low_threshold(neurons[0], 1.0))
        self.assertTrue(self.client.get_low_threshold(neurons[0]), 1.0)

    def test_set_high_threshold(self):
        neurons = self.client.get_neuron_list()
        self.assertTrue(self.client.get_high_threshold(neurons[0]), 1.0)
        self.assertTrue(self.client.set_high_threshold(neurons[0], 0.5))
        self.assertTrue(self.client.get_high_threshold(neurons[0]), 0.5)
        self.assertTrue(self.client.set_high_threshold(neurons[0], 1.0))
        self.assertTrue(self.client.get_high_threshold(neurons[0]), 1.0)

    def test_set_activation(self):
        neurons = self.client.get_input_list()
        self.assertEqual(self.client.get_activation(neurons[0]), 0.0)
        self.assertTrue(self.client.set_activation(neurons[0], 1.0))
        self.assertEqual(self.client.get_activation(neurons[0]), 1.0)
        self.assertTrue(self.client.set_activation(neurons[0], 0.0))
        self.assertEqual(self.client.get_activation(neurons[0]), 0.0)

    def test_set_period(self):
        neurons = self.client.get_neuron_list()
        self.assertTrue(self.client.set_update_period(0.01))
        self.assertTrue(self.client.set_activation(neurons[0], 1.0))
        sleep(0.1)
        self.assertEqual(self.client.get_activation(neurons[1]), 1.0)
        self.assertTrue(self.client.set_activation(neurons[0], 0.0))
        sleep(0.1)
        self.assertEqual(self.client.get_activation(neurons[1]), 0.0)
        self.assertTrue(self.client.set_update_period(0))

    def test_PeriodIsInterruptable(self):
        start = datetime.now()
        expire = timedelta(seconds=1.0)
        self.assertTrue(self.client.set_update_period(5.0))
        self.assertTrue(self.client.set_update_period(0.0))
        self.assertTrue( datetime.now() - start < expire)

    def test_update(self):
        neurons = self.client.get_neuron_list()
        self.assertTrue(self.client.set_activation(neurons[0], 1.0))
        self.assertEqual(self.client.get_activation(neurons[1]), 0.0)

        for i in range(0, _MIN_FREQ_):  # update at least _MIN_FREQ_ times to make sure we've exceeded any MinFrequency thresholds
            self.client.update()

        self.assertEqual(self.client.get_activation(neurons[1]), 1.0)
        self.assertTrue(self.client.set_activation(neurons[0], 0.0))
        self.assertEqual(self.client.get_activation(neurons[1]), 1.0)

        for i in range(0, _MIN_FREQ_):  # update at least _MIN_FREQ_ times to make sure we've exceeded any MinFrequency thresholds
            self.client.update()

        self.assertEqual(self.client.get_activation(neurons[1]), 0.0)
#'''
if __name__ == '__main__':
    unittest.main()

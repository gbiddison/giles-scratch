#!/usr/bin/env python

import wx
import xmlrpclib
import random
from threading import Thread, Lock
from time import sleep
from neural.netserver import NetServer
from neural.wxneural.neuralgraph import NeuralGraphWindow

class TestThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self._server = NetServer(logRequests=False)
        self._client = xmlrpclib.ServerProxy('http://127.0.0.1:8080')
        self._client.load_net("test2.pickle.xml")
        
        self._graph_lock = Lock()
        self._graph = {}
        outputs = self._client.get_output_list()
        for name in outputs:
            self._graph[NeuralGraphWindow(name, self.graph_closed).graph] = name

        self._running = False
        self.start()
        while not self._running:
            sleep(0)

    def graph_closed(self, graph):
        with self._graph_lock:
            del self._graph[graph]
        if len(self._graph) == 0:
            self.stop()

    def stop(self):
        self._running = False
        self.join()
        self._server.stop()

    def run(self):
        #start pinging our input neurons, randomly
        self._running = True
        inputs = self._client.get_input_list()
        activation = 0
        while( self._running):
            i = random.randint(0, len(inputs)-1)
            activation = 1.0 if random.random() > 0.25 else 0.0
            self._client.set_activation(inputs[i], activation)
            self._client.update()
            
            with self._graph_lock:
                for graph,name in self._graph.iteritems():
                    graph.update(self._client.get_activation(name))
            sleep(0.03)


if __name__ == '__main__':

    app = wx.App(1) #zero if you want stderr/stdout to console instead of a window, but this seems unreliableS

    tester = TestThread()
    app.MainLoop()
    tester.stop()
    
#!/usr/bin/env python
"""
# XML RPC Server for Neural Network
# --
# API
# --
#
#  load_net
#    param: absolute or relative path to net file
#
#  Getters
#   get_neuron_list
#       returns list containing names of all neurons in net
#   get_input_list
#       returns list containing names of all neurons in input layer (no links To this neuron)
#   get_output_list
#       returns list containing names of all neurons in output layer (no inks From this neuron)
#   get_links_incoming
#       param: neuron name
#       returns count of links to the named neuron
#   get_links_outgoing
#       param: neuron name
#       returns count of links from the named neuron
#   get_weight
#       param: neuron name
#       param: link id (zero based)
#       returns weight of specified link to this neuron
#   get_low_threshold
#       param: neuron name
#       returns low activation threshold of named neuron
#   get_high_threshold
#       param: neuron name
#       returns high activation threshold of named neuron
#   get_activation
#       param neuron name
#       returns activation value of named neuron
#   get_update_period:
#       returns update period in seconds
#
#  Setters
#   set_weight
#       param: neuron name
#       param: link id (zero based)
#       sets input weight for the link to the named neuron
#   set_low_threshold
#       param: neuron name
#       sets low firing threshold for the named neuron
#   set_high_threshold
#       param: neuron name
#       sets high firing threshold for the named neuron
#   set_activation
#       param: neuron name
#       sets activation value of named neuron
#   set_update_period:
#       param: update period in seconds non-zero starts update thread.  Zero value stops update thread
#       returns False on lookup failure
#   update
#       Iterates through a single network update
#       returns False on lookup failure
"""
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
from http.server import SimpleHTTPRequestHandler
from threading import Thread
from time import sleep
from neural2.neuralnetio import NeuralNetIO

#import BaseHTTPServer
#def not_insane_address_string(self):
#    host, port = self.client_address[:2]
#    return '%s (no getfqdn)' % host #used to call: socket.getfqdn(host)
#BaseHTTPServer.BaseHTTPRequestHandler.address_string = not_insane_address_string

class NetServer(Thread):

    def __init__(self, port=8080, logRequests=True):
        Thread.__init__(self)
        self.__port = port
        self.__logRequests = logRequests
        self.__server = None
        self.__running = False
        self.State = None
        self.start()
        while not self.__running:
            sleep(0)

    def stop(self):
        if self.State is not None:
            self.State.set_update_period(0)
        self.__server.shutdown()
        self.__server.server_close()
        self.join()

    def run(self):
        #register API
        self.State = NetServerState() # accessor for state object for tests and shutting down, etc
        self.__server = SimpleXMLRPCServer(("127.0.0.1", self.__port), CrossDomainXMLRPCRequestHandler, logRequests=self.__logRequests)
        self.__server.register_instance(self.State)
        self.__server.register_introspection_functions()

        #start server
        self.__running = True
        self.__server.serve_forever()

# --> Using this allows XSS requests to go through, making things much easier to debug

class CrossDomainXMLRPCRequestHandler(SimpleXMLRPCRequestHandler,
                                      SimpleHTTPRequestHandler):
    """ SimpleXMLRPCRequestHandler subclass which attempts to do CORS
    
    CORS is Cross-Origin-Resource-Sharing (http://www.w3.org/TR/cors/)
    which enables xml-rpc calls from a different domain than the xml-rpc server
    (such requests are otherwise denied)
    """
    def do_OPTIONS(self):
        """ Implement the CORS pre-flighted access for resources """
        print( "options!")
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-METHODS", "POST,GET,OPTIONS")
        #self.send_header("Access-Control-Max-Age", "60")
        self.send_header("Content-length", "0")
        self.end_headers()
    
    def do_GET(self):
        """ Handle http requests to serve html/image files only """
        print( self.path, self.translate_path(self.path))
        permitted_extensions = ['.html','.png','.svg','.jpg', '.js']
        if not os.path.splitext(self.path)[1] in permitted_extensions:
            self.send_error(404, 'File Not Found/Allowed')
        else:
            SimpleHTTPRequestHandler.do_GET(self)
    
    def end_headers(self):
        """ End response header with adding Access-Control-Allow-Origin
        
        This is done to enable CORS request from all clients """
        self.send_header("Access-Control-Allow-Origin", "*")
        SimpleXMLRPCRequestHandler.end_headers(self)


class NetServerState:
    """RPC state object -- currently a single neural network visible to all clients
    """

    def __init__(self):
        self.Net = None
        
    def __lookup_neuron_by_name(self, name):
        for n in self.Net.Neurons:
            if n.Name == name: return n
        return None

    def load_net(self, path):
        """load_net
           param: absolute or relative path to net file
           returns False on load failure
        """
        stream = NeuralNetIO()
        self.Net = stream.read(path)
        return True

    def get_neuron_list(self):
        """get_neuron_list
           returns list containing names of all neurons in net, empty list on lookup failure
        """
        if self.Net is None: return []
        return [x.Name for x in self.Net.Neurons]

    def get_input_list(self):
        """get_input_list
           returns list containing names of all neurons in input layer (no links From other neurons), empty list on lookup failure
        """
        if self.Net is None: return []
        return [x.Name for x in self.Net.get_input_neurons()]

    def get_output_list(self):
        """get_output_list
           returns list containing names of all neurons in output layer (no links To other neurons), empty list on lookup failure
        """
        if self.Net is None: return []
        return [x.Name for x in self.Net.get_output_neurons()]
        
    def get_links_incoming(self, name):
        """get_links_incoming
           param: neuron name
           returns count of links to the named neuron, 0 on lookup failure
        """
        if self.Net is None: return 0
        n = self.__lookup_neuron_by_name(name)
        if n is None: return 0
        return len(n.Incoming)

    def get_links_outgoing(self, name):
        """get_links_outgoing:
           param: neuron name
           returns count of links from the named neuron, 0 on lookup failure
        """
        if self.Net is None: return 0
        n = self.__lookup_neuron_by_name(name)
        if n is None: return 0
        return len(n.Outgoing)

    def get_weight(self, name, link):
        """get_weight:
            param: neuron name
            param: link id (zero based)
            returns weight of specified link to this neuron, 0.0 on lookup failure
        """
        if self.Net is None: return 0.0
        n = self.__lookup_neuron_by_name(name)
        if n is None: return 0.0
        if link < 0 or link > len(n.Incoming)-1: return 0.0
        return n.Incoming[link].Weight

    def get_low_threshold(self, name):
        """get_low_threshold:
            param: neuron name
            returns low activation threshold of named neuron, 0.0 on lookup failure
        """
        if self.Net is None: return 0.0
        n = self.__lookup_neuron_by_name(name)
        if n is None: return 0.0
        return n.LowThreshold

    def get_high_threshold(self, name):
        """get_high_threshold:
            param: neuron name
            returns high activation threshold of named neuron, 0.0 on lookup failure
        """
        if self.Net is None: return 0.0
        n = self.__lookup_neuron_by_name(name)
        if n is None: return 0.0
        return n.HighThreshold

    def get_activation(self, name):
        """get_activation:
            param neuron name
            returns activation value of named neuron, 0.0 on lookup failure
        """
        if self.Net is None: return 0.0
        n = self.__lookup_neuron_by_name(name)
        if n is None: return 0.0
        return n.Activation

    def get_update_period(self):
        """get_update_period:
            returns update period in seconds
        """
        if self.Net is None: return 0.0
        return self.Net._NeuralNet__period

    def set_weight(self, name, link, weight):
        """set_weight
            param: neuron name
            param: link id (zero based)
            param: new weight value
            sets input weight for the link to the named neuron
            returns False on lookup failure
        """
        if self.Net is None: return False
        n = self.__lookup_neuron_by_name(name)
        if n is None: return False
        if link < 0 or link > len(n.Incoming)-1: return False
        n.Incoming[link].Weight = weight
        return True

    def set_low_threshold(self, name, threshold):
        """set_low_threshold
            param: neuron name
            sets low firing threshold for the named neuron
            returns False on lookup failure
        """
        if self.Net is None: return False
        n = self.__lookup_neuron_by_name(name)
        if n is None: return False
        n.LowThreshold = threshold
        return True

    def set_high_threshold(self, name, threshold):
        """set_high_threshold
            param: neuron name
            sets high_firing threshold for the named neuron
            returns False on lookup failure
        """
        if self.Net is None: return False
        n = self.__lookup_neuron_by_name(name)
        if n is None: return False
        n.HighThreshold = threshold
        return True

    def set_activation(self, name, activation):
        """set_activation
            param: neuron name
            sets activation value of named neuron
            returns False on lookup failure
        """
        if self.Net is None: return False
        n = self.__lookup_neuron_by_name(name)
        if n is None: return False
        n.Activation = activation
        return True

    def set_update_period(self, period):
        """set_update_period:
            param: update period in seconds non-zero starts update thread.  Zero value stops update thread
            returns False on lookup failure
        """
        if self.Net is None: return False
        self.Net.set_period(period)
        return True

    def update(self):
        """update
            Iterates through a single network update
            returns False on lookup failure
        """
        if self.Net is None: return False
        print( "update")

        self.Net.update()
        return True

if __name__ == '__main__':
    print( "Net Server Listening on port 8080 - press ctrl-c to exit")
    server = NetServer()
    try:
        while True:
            sleep(0.1)
    except KeyboardInterrupt:
        pass        
    server.stop()    

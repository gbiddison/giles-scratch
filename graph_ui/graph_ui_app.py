#! /usr/bin/env python3

import json
import logging
import os
import time


import tornado.auth
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.autoreload
from tornado.ioloop import IOLoop

from tornado import gen
from datetime import datetime

UPDATE_RATE =  1./40 # seconds

UPDATE_KEY = 'update'
COMMAND_KEY = 'command'
SENSOR_KEY = 'sensor'
PAYLOAD_KEY = 'payload'
angular_app_path = os.path.join(os.path.dirname(__file__))

class WebSocketBridge(object):
    """
    Class to manage module connections and logging (no more globals)

    """

    def __init__(self):

        # non-blocking periodic polling in tornado
        self.update_rate = UPDATE_RATE
        self.last_frame = datetime.now()
        self.last_transmitted_state = {}

        # websocket callback for push messages
        self.ws_callback = None

        import sys
        sys.path.append('../neural2')
        sys.path.append('../neural2/gui')
        from neuralnetio import NeuralIO
        path = '../neural2/nets/nerve_sim_layout_1.nui'
        self.net = NeuralIO.create(path)

        #from gui.nervesimreader import NerveSimReader
        #path = '../neural2/nets/newer neurons.neu'
        #self.net = NerveSimReader(path).Net

        #from neuralnetio import NeuralNetIO
        #stream = NeuralNetIO()
        #stream.write("../neural2/nets/nerve_sim_layout_1.net", self.net.Net)

    def sync_state(self):
        '''
        :return: json structure representing the graph nodes and edges for UI repr

        '''

        return self.net.to_json()

        # return {
        #     'nodes': {
        #         'node1': {'x': 0.0, 'y': 0.0},
        #         'node2': {'x': 155.0, 'y': 0.0},
        #         'node3': {'x': 310.0, 'y': 0.0},
        #         'node4': {'x': 465.0, 'y': 0.0}
        #     },
        #     'edges': [
        #         ['node1', 'node2'],
        #         ['node2', 'node3'],
        #         ['node2', 'node4'],
        #         ['node3', 'node4']
        #     ],
        #     'outputs': [
        #        'node1', 'node2'
        #     ],
        #     'inputs': [
        #        'node1', 'node2'
        #     ]
        #
        # }

    def update_sensors(self, payload):
        for neuron in self.net.Net.Neurons:
            if neuron.Name in payload.keys():
                neuron._sensory_current = payload[neuron.Name]
        # { 'node1': 0.0, 'node2': 0.0 }

    @gen.engine
    def device_loop(self):

        # yield here skips the first update and calls us again after the update period expires
        # the code continues on the next line
        yield gen.Task(IOLoop.instance().add_timeout, time.time() + self.update_rate)

        # update the network
        self.net.Net.update()
        payload = {}
        for neuron in self.net.Net.Neurons:
            activity = neuron.get_activity()
            if neuron.Name not in self.last_transmitted_state or self.last_transmitted_state[neuron.Name] != activity:
                payload[neuron.Name] = activity
            # payload[neuron.Name] = activity

        import random as rnd
        payload['random_value'] = rnd.randint(0, 65535)

        frame = datetime.now()
        delta = (frame - self.last_frame).total_seconds()
        self.last_frame = frame

        payload['time_delta'] = delta

        # p loop
        desired_rate = UPDATE_RATE
        kp = 0.001
        error = desired_rate - delta
        self.update_rate += kp * error

        if self.ws_callback is not None:
            self.ws_callback(UPDATE_KEY, payload)

        self.last_transmitted_state = payload

        # call ourselves again so that the yield loop completes
        self.device_loop()

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/ws", WSHandler),
            (r"/simws", WSHandler),
            (r"^/(.*)$", MainHandler),
        ]
        settings = dict(
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            debug=True,
            autoreload=True,
            xsrf_cookies=False,
        )
        tornado.web.Application.__init__(self, handlers, **settings)

        self.disable_tornado_logging()

    def disable_tornado_logging(self):
        access_log = logging.getLogger("tornado.access")
        app_log = logging.getLogger("tornado.application")
        gen_log = logging.getLogger("tornado.general")

        access_log.disabled = False
        app_log.disabled = False
        gen_log.disabled = False


class BaseHandler(tornado.web.RequestHandler):
    # previously had user auth functions here
    pass

class MainHandler(BaseHandler):
    def get(self, filename):
        if filename == "" or os.path.isdir(os.path.join("/static", filename)):
            filename = os.path.join("/static", filename, "index.html")
            print ("a:" + filename)
        elif os.path.splitext(filename) == ".html":
            filename = "/static/%s" % filename
            print ("b:" + filename)
        else:
            filename = "/static/%s.html" % filename
            print ("c:" + filename)

        with open(angular_app_path + filename, 'r') as f:
            self.write(f.read())

class WSHandler(tornado.websocket.WebSocketHandler):
    connections = set()
    ws_open = False

    def check_origin(self, origin):
        return True

    def allow_draft76(self):
        # for iOS 5.0 Safari
        return True

    def open(self):
        self.connections.add(self)
        self.application.wsbridge.ws_callback = self.send_message

    def send_message(self, command, payload, callback_id=-1):

        msg = {
            'status': 'success',
            'payload': payload,
            'command': command,
            'callback_id': callback_id
        }

        [con.write_message(msg) for con in self.connections]

    def on_close(self):
        self.application.wsbridge.ws_callback = None
        self.connections.remove(self)
        self.ws_open = False

    # messages from the frontend
    def on_message(self, message):

        self.ws_open = True

        # assume all messaging is done with json-encoded strings
        message_dict = json.loads(message)

        return_msg = None
        if (COMMAND_KEY in message_dict.keys()) and 'init' in message_dict[COMMAND_KEY]:
            return_msg = {
                COMMAND_KEY: 'init response',
                PAYLOAD_KEY: self.application.wsbridge.sync_state()
            }
        elif (COMMAND_KEY in message_dict.keys()) and (PAYLOAD_KEY in message_dict.keys()) \
                and ('sensor' in message_dict[COMMAND_KEY]):
            self.application.wsbridge.update_sensors(message_dict[PAYLOAD_KEY])
        else:
            print(message_dict)
        # else:
            # This is for handling return messages on the server side
            #return_msg = self.application.wsbridge.switchboard(message_dict)

        if return_msg:
            [con.write_message(return_msg) for con in self.connections]


if __name__ == '__main__':
    _port = 8888
    _host = '0.0.0.0'

    app = Application()
    app.listen(_port, address=_host)
    app.wsbridge = WebSocketBridge()

    io_loop = tornado.ioloop.IOLoop.instance()
    io_loop.add_callback(app.wsbridge.device_loop)
    io_loop.start()


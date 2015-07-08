
import json
import logging
import os
import sys
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

UPDATE_KEY = 'update'
COMMAND_KEY = 'command'
PAYLOAD_KEY = 'payload'
angular_app_path = os.path.join(os.path.dirname(__file__))

class WebSocketBridge(object):
    """
    Class to manage module connections and logging (no more globals)

    """

    def __init__(self):

        # non-blocking periodic polling in tornado
        self.update_rate = 0.1

        # websocket callback for push messages
        self.ws_callback = None

    def generate_initial_mapping(self):
        '''
        :return: json structure representing the graph nodes and edges

        '''

        from neuralnetio import NeuralIO
        path = '/Users/gbiddison/source/pwn/python/neural2/nets/nerve_sim_layout_1.nui'

        net = NeuralIO.create(path)

        # convert NET positions to json
        mapping = {'nodes': {}, 'edges': []}
        for e in net.Elements:
            mapping['nodes'][e.Name] = {'x': e.Position[0], 'y': e.Position[1]}

            # add edges
            neuron = net.lookup_neuron(e)
            if len(neuron.Outgoing) == 0:
                continue
            for link in neuron.Outgoing:
                target = net.lookup_element(link.Target)
                mapping['edges'].append([e.Name, target.Name])
        return mapping

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
        #     ]
        #
        # }

    @gen.engine
    def device_loop(self):

        # yield here skips the first update and calls us again after the update period expires
        # the code continues on the next line
        yield gen.Task(IOLoop.instance().add_timeout, time.time() + self.update_rate)

        # the update code

        import random as rnd
        r1, g1, b1 = rnd.randint(0, 255), rnd.randint(0, 255), rnd.randint(0, 255)
        r2, g2, b2 = rnd.randint(0, 255), rnd.randint(0, 255), rnd.randint(0, 255)

        if self.ws_callback is not None:
            self.ws_callback(UPDATE_KEY, {
                'random_value': r1,
                'LCS': [r1, g1, b1],
                'ES': [r2, g2, b2]
            })

        # call ourselves again so that the yield loop completes
        self.device_loop()

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/ws", WSHandler),
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
    def get(self):
        with open(angular_app_path + "/static/index.html", 'r') as f:
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
                PAYLOAD_KEY: self.application.wsbridge.generate_initial_mapping()
            }

        # else:
            # This is for handling return messages on the server side
            #return_msg = self.application.wsbridge.switchboard(message_dict)

        if return_msg:
            [con.write_message(return_msg) for con in self.connections]



app = Application()
app.listen(8888, address='0.0.0.0')
app.wsbridge = WebSocketBridge()

io_loop = tornado.ioloop.IOLoop.instance()
io_loop.add_callback(app.wsbridge.device_loop)
io_loop.start()


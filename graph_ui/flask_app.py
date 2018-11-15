#!/usr/bin/env python

from flask import Flask, render_template
from flask_socketio import SocketIO
import jinja2
import os
import logging
import time

UPDATE_RATE = 1. / 30  # seconds
MAX_SAFE_PID_DISTANCE = 0.25 # how far off do we really think the loop time is before we just give up? - avoid weird edges and reset

logging.basicConfig(format='%(asctime)s %(levelname)s (%(name)s) %(message)s', level=logging.DEBUG)
_logger = logging.getLogger(__file__)

app = Flask(__name__)
app.config['SECRET_KEY'] = '8f86c03170811938fd9f798a60ad9ed4d4eed080'
socketio = SocketIO(app, debug=False)

app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)))
static_path = os.path.join(app_path, 'static')

# make flask load from 'static/' instead of 'templates/'
app.jinja_loader = jinja2.FileSystemLoader(static_path)

app.network_state = None

@app.route('/')
def index():
    return render_template('flask_graph.html')

@app.route('/sim')
def sim_index():
    return render_template('flask_sim.html')


@socketio.on('connect')
def handle_connect():
    _logger.info('connected')
    app.network_state.connected = True

@socketio.on('disconnect')
def handle_disconnect():
    _logger.info('disconnected')
    app.network_state.connected = False


@socketio.on('json')
def handle_json(message):
    #_logger.info('json message received: {}'.format(message))
    if 'command' in message:
        if message['command'] == 'init':
            socketio.emit('message', {'command': 'init response', 'payload': app.network_state.sync_state()})
        elif message['command'] == 'sensors':
            app.network_state.update_sensors(message['payload'])


class NetworkState(object):
    """
    Class to manage module connections and logging

    """
    def __init__(self):
        def reset_update_rate_pid_params():
            self.update_rate = UPDATE_RATE
            self.smooth_delta = 0.0
            self.prev_error = 0.0
            self.cumulative_error = 0.0
        reset_update_rate_pid_params()
        # non-blocking periodic polling in tornado
        self.last_frame = time.time()
        self.last_transmitted_state = {}
        self.connected = False

        # websocket callback for push messages

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
        """
        :return: json structure representing the graph nodes and edges for UI repr

        e.g. {
            'nodes': {
                'node1': {'x': 0.0, 'y': 0.0},
                'node2': {'x': 155.0, 'y': 0.0},
                'node3': {'x': 310.0, 'y': 0.0},
                'node4': {'x': 465.0, 'y': 0.0}
            },
            'edges': [
                ['node1', 'node2'],
                ['node2', 'node3'],
                ['node2', 'node4'],
                ['node3', 'node4']
            ],
            'outputs': [
               'node1', 'node2'
            ],
            'inputs': [
               'node1', 'node2'
            ]

        }
        """
        return self.net.to_json()

    def update_sensors(self, payload):
        for neuron in self.net.Net.Neurons:
            if neuron.Name in payload.keys():
                neuron._sensory_current = payload[neuron.Name]

    def device_loop(self):
        # yield here skips the first update and calls us again after the update period expires
        # the code continues on the next line
        socketio.sleep(self.update_rate)
        if not self.connected:
            socketio.start_background_task(target=self.device_loop)
            return

        # update the network
        self.net.Net.update()
        payload = {'neurons': {}}
        for neuron in self.net.Net.Neurons:
            activity = neuron.get_activity()
            if neuron.Name not in self.last_transmitted_state or self.last_transmitted_state[neuron.Name] != activity:
                payload['neurons'][neuron.Name] = {"value": activity,
                                                   "is_output": (len(neuron.Outgoing) == 0 and len(neuron.Incoming) != 0)}
            # payload['neurons'][neuron.Name] = activity

        import random as rnd
        payload['random_value'] = rnd.randint(0, 65535)

        frame = time.time()
        delta = (frame - self.last_frame)
        self.last_frame = frame

		# smooth_delta is a display feature,  no smoothing in actual delta calc currently
        self.smooth_delta = 0.99 * self.smooth_delta + 0.01 * delta
        payload['time_delta'] = self.smooth_delta

        # p loop
        desired_rate = UPDATE_RATE
        kp = 0.0175
        ki = 0.00005
        kd = -0.00001
        error = desired_rate - delta
        error_rate = (error - self.prev_error)
        self.prev_error = error
        self.cumulative_error += error
        rate_change = kp * error + kd * error_rate + ki * self.cumulative_error
        _logger.debug('rate:{:7.4f} ({:7.4f}) [p:{:7.4f} i:{:7.4f} d:{:7.4f}]'.format(self.update_rate, rate_change*100.0, error, self.cumulative_error, error_rate))
        self.update_rate += rate_change

		# don't go crazy ... reset; ie if processor is lagging heavily, ignore the noise
        distance = abs(desired_rate - self.update_rate);
        if distance > MAX_SAFE_PID_DISTANCE:
            # reset
            _logger.debug("reset rate")
            self.__init__.reset_update_rate_pid_params()

        if len(payload) > 2:
            socketio.emit('message', {'command': 'update', 'payload': payload})
        self.last_transmitted_state = payload

        socketio.start_background_task(target=self.device_loop)


if __name__ == '__main__':
    # app.run(port=8888, debug=True)
    # support for websockets via flask-socketio
    app.network_state = NetworkState()

    # from threading import Thread
    # foo = Thread(target=app.network_state.device_loop, daemon=True)
    # foo.start()

    socketio.start_background_task(target=app.network_state.device_loop)
    logging.getLogger('socketio').setLevel(logging.WARN)
    logging.getLogger('engineio').setLevel(logging.WARN)

    socketio.run(app, host='0.0.0.0', port=8888)



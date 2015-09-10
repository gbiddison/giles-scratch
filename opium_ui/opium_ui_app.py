#!/usr/bin/env python

import json
import logging
import os
import time
import uuid

import tornado.auth
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.autoreload
from tornado.ioloop import IOLoop
#from tornado import httpclient

from tornado import gen

import couchdb
from DBOrders import WorkOrder
from datetime import datetime


UPDATE_KEY = 'update'
COMMAND_KEY = 'command'
PAYLOAD_KEY = 'payload'
STATUS_KEY = 'status'
CALLBACK_KEY = 'callback_id'

angular_app_path = os.path.join(os.path.dirname(__file__))

couch_url = "localhost:5984"
syn_url = "localhost:9080"

class WebSocketBridge(object):
    """
    Class to manage module connections and logging (no more globals)

    """
    CACHE_LIMIT = 10
    CACHE_CULL = 0.75

    def __init__(self):

        # non-blocking periodic polling in tornado
        self.update_rate = 0.5

        # websocket callback for push messages
        self.ws_callback = None

        # handle to couch API
        self.couch_db = couchdb.Server("http://%s/" % couch_url)

        # handle to work-order API
        self.work_order_db = WorkOrder(server=syn_url)

        # cache names of work-orders that we've looked up so we don't hit SAD 10 times a sec
        self.name_cache = {}

    def add_name_to_cache(self, workid, name):
        """
        limit the cache to a max size by expiring 50% oldest items once a certain size is reached
        :param workid:
        :param name:
        :return:
        """
        if len(self.name_cache) >= self.CACHE_LIMIT:
            # sort keys by timestamp
            sorted_keys = sorted(self.name_cache.keys(), key=lambda x: self.name_cache[x]['time_stamp'])
            for i in range(int(self.CACHE_LIMIT * self.CACHE_CULL)):
                del self.name_cache[sorted_keys[i]]

        self.name_cache[workid] = {'name': name, 'time_stamp': datetime.now()}

    def list_work_orders(self):
        """
        Query couch for the list of active plates
        :return:
        return a dictionary keyed by work order id, where the value is a list of plates under that work order

        eg:     { 'work_id': { 'name':"Human readable name", 'plates': { 'plate_id'a list of plates } } }

        eg:     { 'work_id': { 'name': "Human readable name", 'plates': [plate_couch_doc] },
                  'ABCDEF123': { 'name': "optional", 'plates': [ couch1, couch2] },
                  'ASDFAS123': { 'name': "optional", 'plates': [ couch3, couch4] },
                  'FOOFOO881': { 'name': "optional", 'plates': [ couch5] }};*/
        """
        try:
            db = self.couch_db["plates"]

            rows = db.iterview(name="plates/unfinished_workorders", batch=1000)

            work = {}
            for row in rows:
                doc = db[row.id]
                if 'workorderid' not in doc:
                    continue
                workid = doc['workorderid']
                if workid not in work:
                    work[workid] = {'name': workid, 'plates': {}}

                    # check if name is in cache
                    if workid in self.name_cache.keys():
                        work[workid]['name'] = self.name_cache[workid]['name']
                        self.name_cache[workid]['time_stamp'] = datetime.now()

                    else:
                        # try to query SAD for human readable
                        result = self.work_order_db.get_full_workorder(workid)
                        print(result)
                        if 'human_readable_name' in result:
                            name = result['human_readable_name']
                            print(name)
                            work[workid]['name'] = name
                            self.add_name_to_cache(workid, name)    # put SAD response in cache
                        else:
                            print("no name!")
                            self.add_name_to_cache(workid, workid)  # stuff it in cache anyway

                plates = work[workid]['plates']
                plateid = row.id
                plates[plateid] = doc

            # sort the plates by name in reverse, so that SynthegoCartridge is always near top
            import collections
            for wo in work.keys():
                work[wo]['plates'] = collections.OrderedDict(sorted(work[wo]['plates'].items(), reverse=True))

            # if not work:
            #
            #     return {"work_id_0":
            #                 {'name': "Test data, couch is empty or missing", 'plates':
            #                     {"why is this key necessary":
            #                          {'_id': "test plate 0", 'task_index_next': "1", 'task_wip_index': "1", 'tasks':
            #                              [{'name': "task 1"}, {'name': "task 2"}, {'name': "task 3"}]
            #                           }
            #                      }
            #                  },
            #             "work_id_1":
            #                 {'name': "Fun Work", 'plates':
            #                     {"huh why isn't this a list":
            #                          {'id_': "plate 1"},
            #                      "wtf why is there a key here":
            #                          {'id_': "plate 2"}
            #                      }
            #                  },
            #             "work_id_2":
            #                 {'name': "Something awful", 'plates':
            #                     {"huh why isn't this a list":
            #                          {'id_': "plate 1"},
            #                      "wtf why is there a key here":
            #                          {'id_': "plate 2"}
            #                      }
            #                  },
            #             "work_id_3":
            #                 {'name': "Impending Doom", 'plates':
            #                     {"huh why isn't this a list":
            #                          {'id_': "plate 1"},
            #                      "wtf why is there a key here":
            #                          {'id_': "plate 2"}
            #                      }
            #                  },
            #             }
            return work
        except:
            return None

    @gen.engine
    def device_loop(self):

        # yield here skips the first update and calls us again after the update period expires
        # the code continues on the next line
        yield gen.Task(IOLoop.instance().add_timeout, time.time() + self.update_rate)

        # query couch, update state
        payload = ["nothing"]

        # transfer state to javascript
        if self.ws_callback is not None:
            payload = self.list_work_orders()
            if payload is not None:
                self.ws_callback(UPDATE_KEY, payload)

        # call ourselves again so that the yield loop completes
        self.device_loop()


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/ws", WSHandler),
            (r"^/(.*)$", MainHandler),
        ]
        settings = dict(
            cookie_secret=uuid.uuid4().hex,  # we will eventually save this for session management?
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            debug=True,
            autoreload=True,
            xsrf_cookies=False,
        )
        tornado.web.Application.__init__(self, handlers, **settings)

        self.disable_tornado_logging()

    @staticmethod
    def disable_tornado_logging():
        access_log = logging.getLogger("tornado.access")
        app_log = logging.getLogger("tornado.application")
        gen_log = logging.getLogger("tornado.general")

        access_log.disabled = False
        app_log.disabled = False
        gen_log.disabled = False


class BaseHandler(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass
    # previously had user auth functions here


class MainHandler(BaseHandler):
    def get(self, filename):
        if filename == "" or os.path.isdir(os.path.join("/static", filename)):
            filename = os.path.join("/static", filename, "index.html")
        elif os.path.splitext(filename) == ".html":
            filename = "/static/%s" % filename
        else:
            filename = "/static/%s.html" % filename

        with open(angular_app_path + filename, 'r') as f:
            self.write(f.read())


class WSHandler(tornado.websocket.WebSocketHandler):

    connections = set()
    ws_open = False

    def check_origin(self, origin):
        return True

    def open(self):
        self.connections.add(self)
        self.application.wsbridge.ws_callback = self.send_message

    def send_message(self, command, payload, callback_id=-1):

        msg = {
            STATUS_KEY: 'success',
            PAYLOAD_KEY: payload,
            COMMAND_KEY: command,
            CALLBACK_KEY: callback_id
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
                PAYLOAD_KEY: self.application.wsbridge.list_work_orders()
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

app = Application()
app.listen(8888, address='0.0.0.0')
app.wsbridge = WebSocketBridge()

io_loop = tornado.ioloop.IOLoop.instance()
io_loop.add_callback(app.wsbridge.device_loop)
io_loop.start()


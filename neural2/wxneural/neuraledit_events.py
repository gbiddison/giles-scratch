"""
Custom events used by neuraledit panel
"""

import wx

#
# --- posted by neuraledit panel, received by neuralprops
# 
myEVT_SELECTION_CHANGED = wx.NewEventType()
EVT_SELECTION_CHANGED = wx.PyEventBinder(myEVT_SELECTION_CHANGED)
class SelectionChangedEvent(wx.PyEvent):
    def __init__(self, element, neuron):
        wx.PyEvent.__init__(self)
        self.SetEventType(myEVT_SELECTION_CHANGED)
        self.Element = element
        self.Neuron = neuron

#
# --- posted by neuraledit panel, received by app
# 
myEVT_ELEMENT_ADDED = wx.NewEventType()
EVT_ELEMENT_ADDED = wx.PyEventBinder(myEVT_ELEMENT_ADDED)
class ElementAddedEvent(wx.PyEvent):
    def __init__(self, element):
        wx.PyEvent.__init__(self)
        self.SetEventType(myEVT_ELEMENT_ADDED)
        self.Element = element

#
# --- posted by neuraledit panel, received by app
# 
myEVT_ELEMENT_REMOVED = wx.NewEventType()
EVT_ELEMENT_REMOVED = wx.PyEventBinder(myEVT_ELEMENT_REMOVED)
class ElementRemovedEvent(wx.PyEvent):
    def __init__(self, element):
        wx.PyEvent.__init__(self)
        self.SetEventType(myEVT_ELEMENT_ADDED)
        self.Element = element

#
# --- posted by neuraltools, received by neuralprops (to update graph)
#
myEVT_NET_STATE_CHANGED = wx.NewEventType()
EVT_NET_STATE_CHANGED = wx.PyEventBinder(myEVT_NET_STATE_CHANGED)
class NetStateChangedEvent(wx.PyEvent):
    def __init__(self):
        wx.PyEvent.__init__(self)
        self.SetEventType(myEVT_NET_STATE_CHANGED)

#
# --- posted by neuralprops panel, received by neuraledit
# 
myEVT_ELEMENT_RENAMED = wx.NewEventType()
EVT_ELEMENT_RENAMED = wx.PyEventBinder(myEVT_ELEMENT_RENAMED)
class ElementRenamedEvent(wx.PyEvent):
    def __init__(self, neuron, name):
        wx.PyEvent.__init__(self)
        self.SetEventType(myEVT_ELEMENT_RENAMED)
        self.Neuron = neuron
        self.Name = name

#
# --- posted by neuralprops panel, received by neuraledit
#
myEVT_REMOVE_LINK = wx.NewEventType()
EVT_REMOVE_LINK = wx.PyEventBinder(myEVT_REMOVE_LINK)
class RemoveLinkEvent(wx.PyEvent):
    def __init__(self, link):
        wx.PyEvent.__init__(self)
        self.SetEventType(myEVT_REMOVE_LINK)
        self.Link = link

#
# --- posted by neuralprops panel, received by neuraledit
#
myEVT_REMOVE_LINKS = wx.NewEventType()
EVT_REMOVE_LINKS = wx.PyEventBinder(myEVT_REMOVE_LINKS)
class RemoveLinksEvent(wx.PyEvent):
    def __init__(self, links):
        wx.PyEvent.__init__(self)
        self.SetEventType(myEVT_REMOVE_LINKS)
        self.Links = links

#
# --- posted by neuraltools, received by neuraledit & app
#
myEVT_FILE_NEW = wx.NewEventType()
EVT_FILE_NEW = wx.PyEventBinder(myEVT_FILE_NEW)
class FileNewEvent(wx.PyEvent):
    def __init__(self):
        wx.PyEvent.__init__(self)
        self.SetEventType(myEVT_FILE_NEW)

#
# --- posted by neuraltools, received by neuraledit & app
#
myEVT_FILE_OPEN = wx.NewEventType()
EVT_FILE_OPEN = wx.PyEventBinder(myEVT_FILE_OPEN)
class FileOpenEvent(wx.PyEvent):
    def __init__(self, path):
        wx.PyEvent.__init__(self)
        self.SetEventType(myEVT_FILE_OPEN)
        self.Path = path

#
# --- posted by neuraltools, received by neuraledit & app
#
myEVT_FILE_SAVE = wx.NewEventType()
EVT_FILE_SAVE = wx.PyEventBinder(myEVT_FILE_SAVE)
class FileSaveEvent(wx.PyEvent):
    def __init__(self, path):
        wx.PyEvent.__init__(self)
        self.SetEventType(myEVT_FILE_SAVE)
        self.Path = path

#
# --- posted by neuraltools, received by neuraledit
#
myEVT_SIM_START = wx.NewEventType()
EVT_SIM_START = wx.PyEventBinder(myEVT_SIM_START)
class SimStartEvent(wx.PyEvent):
    def __init__(self):
        wx.PyEvent.__init__(self)
        self.SetEventType(myEVT_SIM_START)

#
# --- posted by neuraltools, received by neuraledit
#
myEVT_SIM_STOP = wx.NewEventType()
EVT_SIM_STOP = wx.PyEventBinder(myEVT_SIM_STOP)
class SimStopEvent(wx.PyEvent):
    def __init__(self):
        wx.PyEvent.__init__(self)
        self.SetEventType(myEVT_SIM_STOP)

#
# --- posted by neuraltools, received by neuraledit
#
myEVT_NEURON_TYPE_CHANGED = wx.NewEventType()
EVT_NEURON_TYPE_CHANGED = wx.PyEventBinder(myEVT_NEURON_TYPE_CHANGED)
class NeuronTypeChangedEvent(wx.PyEvent):
    def __init__(self, new_type, path):
        wx.PyEvent.__init__(self)
        self.SetEventType(myEVT_NEURON_TYPE_CHANGED)
        self.NeuronType = new_type
        self.Path = path



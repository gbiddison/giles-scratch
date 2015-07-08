#!/usr/bin/env python
"""
wxneural_app.py
a neural network editing ui
"""

import wx
try:
    from agw import aui
except ImportError:
    import wx.lib.agw.aui as aui
from neuraledit import NeuralEditPanel
from neuraledit_events import *
from neuralprops import NeuralPropertiesPanel
from neuraltools import NeuralToolsPanel

from threading import Thread
from time import sleep
from random import random

#import unbuffered_print

class WxNeuralAppFrame(wx.Frame):
    """
    WxNeuralAppFrame
    Main frame for wxneural_app, a neural network editing ui
    """
    def __init__(self):
        wx.Frame.__init__(self, None, title="neural")

        self.aui = aui.AuiManager(self)
        self.aui.SetAGWFlags(self.aui.GetAGWFlags() ^ aui.AUI_MGR_LIVE_RESIZE)
        self.editor = editor = NeuralEditPanel(self)
        self.props = props = NeuralPropertiesPanel(self)
        self.tools = tools = NeuralToolsPanel(self)

        editor.Bind(EVT_SELECTION_CHANGED, props.on_edit_selection_changed)
        editor.Bind(EVT_ELEMENT_ADDED, self.on_element_added)
        editor.Bind(EVT_ELEMENT_REMOVED, self.on_element_removed)
        editor.Bind(EVT_NET_STATE_CHANGED, props.on_state_changed)

        props.Bind(EVT_ELEMENT_RENAMED, editor.on_neuron_renamed)
        props.Bind(EVT_REMOVE_LINK, editor.on_remove_link)
        props.Bind(EVT_REMOVE_LINKS, editor.on_remove_links)

        tools.Bind(EVT_FILE_NEW, editor.on_file_new)
        tools.Bind(EVT_FILE_OPEN, editor.on_file_open)
        tools.Bind(EVT_FILE_SAVE, editor.on_file_save)
        tools.Bind(EVT_SIM_START, editor.on_sim_start)
        tools.Bind(EVT_SIM_STOP, editor.on_sim_stop)
        tools.Bind(EVT_NEURON_TYPE_CHANGED, editor.set_neuron_type)

        tools.Bind(EVT_FILE_NEW, self.on_file_new)
        tools.Bind(EVT_FILE_OPEN, self.on_file_open)
        tools.Bind(EVT_FILE_SAVE, self.on_file_save)

        self.Bind(wx.EVT_CLOSE, self.on_close)

        self.aui.AddPane(tools, aui.AuiPaneInfo().Top().CaptionVisible(False).Resizable(False))
        self.aui.AddPane(props, aui.AuiPaneInfo().Left().CloseButton(False)
            .Caption('properties').CaptionVisible(True).MinSize(props.Size))
        self.aui.AddPane(editor, aui.AuiPaneInfo().CenterPane().MinSize(editor.Size))
        self.aui.Update()

        self.Fit()
        self.Show()

#        thread = Thread(target=self.run)
#        thread.daemon = True
#        thread.start()
#
#    def run(self):
#        neural.neuron.Neuron._Neuron__minTicksPerStateChange = 0
#        while True:
#            if len(self.editor.Net.Net.Neurons) != 0:
#                neuron = self.editor.Net.Net.Neurons[0]
#                test = random()
#                neuron.Activation =  test if test < 0.5 else 1.0
#                self.editor.Net.Net.update()
#                self.editor.Refresh()
#            sleep(0.02)

    def on_close(self, event):
        event.Skip() # allow other handlers to process event
        self.editor.Net.Net.stop()
        self.aui.UnInit()

    def on_file_new(self, event):
        event.Skip() # allow other handlers to process event
        self.Title = 'neural'

    def on_file_open(self, event):
        event.Skip() # allow other handlers to process event
        self.Title = 'neural - %s' % event.Path

    def on_file_save(self, event):
        event.Skip() # allow other handlers to process event
        self.Title = 'neural - %s' % event.Path

    def on_element_added(self, event):
        event.Skip() # allow other handlers to process event
        self.tools.enable_saveas(len(self.editor.Net.Elements) > 0)
        
    def on_element_removed(self, event):
        event.Skip() # allow other handlers to process event
        self.tools.enable_saveas(len(self.editor.Net.Elements) > 0)

if __name__ == '__main__':
    App = wx.App(0) #zero if you want stderr/stdout to console instead of a window, but this seems unreliable
    App.SetTopWindow(WxNeuralAppFrame())
    App.MainLoop()


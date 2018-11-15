"""
UI for neuron properties used by wxneural_app
"""

import wx
from neuraledit_events import *
from neuralgraph import NeuralGraphPanel

class NeuralPropertiesPanel(wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        wx.Panel.__init__(self, parent, size=(200,200), *args, **kwargs)
        self.__Neuron = None
        margin = 3
        default_size = (40, -1)
        #dummy = wx.BoxSizer() # just to get a border around the vertical static box sizer
        vertical = wx.BoxSizer(wx.VERTICAL) #wx.StaticBoxSizer(wx.StaticBox(self, label="Properties"), wx.VERTICAL)
        #dummy.Add(vertical, proportion=1, flag=wx.ALL|wx.EXPAND, border=margin)

        label = wx.StaticText(self, label="Neuron")
        self.neuron_name = wx.TextCtrl(self, size=default_size)       
        horizontal = wx.BoxSizer(wx.HORIZONTAL)
        vertical.Add(horizontal, flag=wx.ALL|wx.EXPAND)
        horizontal.Add(label, proportion=1, flag=wx.ALL|wx.EXPAND, border=margin)
        horizontal.Add(self.neuron_name, proportion=1, flag=wx.ALL|wx.EXPAND, border=margin)

        label = wx.StaticText(self, label="Threshold Voltage")
        self.threshold = wx.TextCtrl(self, size=default_size)
        horizontal = wx.BoxSizer(wx.HORIZONTAL)
        vertical.Add(horizontal, flag=wx.ALL|wx.EXPAND)
        horizontal.Add(label, proportion=1, flag=wx.ALL|wx.EXPAND, border=margin)
        horizontal.Add(self.threshold, proportion=1, flag=wx.ALL|wx.EXPAND, border=margin)

        label = wx.StaticText(self, label="Gain")
        self.gain = wx.TextCtrl(self, size=default_size) # was high_threshold TODO
        horizontal = wx.BoxSizer(wx.HORIZONTAL)
        vertical.Add(horizontal, flag=wx.ALL|wx.EXPAND)
        horizontal.Add(label, proportion=1, flag=wx.ALL|wx.EXPAND, border=margin)
        horizontal.Add(self.gain, proportion=1, flag=wx.ALL|wx.EXPAND, border=margin)

        label = wx.StaticText(self, label="Min Firing Frequency")
        self.min_frequency = wx.TextCtrl(self, size=default_size)
        horizontal = wx.BoxSizer(wx.HORIZONTAL)
        vertical.Add(horizontal, flag=wx.ALL|wx.EXPAND)
        horizontal.Add(label, proportion=1, flag=wx.ALL|wx.EXPAND, border=margin)
        horizontal.Add(self.min_frequency, proportion=1, flag=wx.ALL|wx.EXPAND, border=margin)

        label = wx.StaticText(self, label="Membrane Conductance")
        self.conductance = wx.TextCtrl(self, size=default_size)
        horizontal = wx.BoxSizer(wx.HORIZONTAL)
        vertical.Add(horizontal, flag=wx.ALL|wx.EXPAND)
        horizontal.Add(label, proportion=1, flag=wx.ALL|wx.EXPAND, border=margin)
        horizontal.Add(self.conductance, proportion=1, flag=wx.ALL|wx.EXPAND, border=margin)

        label = wx.StaticText(self, label="Membrane Capacitance")
        self.capacitance = wx.TextCtrl(self, size=default_size)
        horizontal = wx.BoxSizer(wx.HORIZONTAL)
        vertical.Add(horizontal, flag=wx.ALL|wx.EXPAND)
        horizontal.Add(label, proportion=1, flag=wx.ALL|wx.EXPAND, border=margin)
        horizontal.Add(self.capacitance, proportion=1, flag=wx.ALL|wx.EXPAND, border=margin)

        label = wx.StaticText(self, label="Connections")
        label2 = wx.StaticText(self, label="Incoming")
        label3 = wx.StaticText(self, label="Outgoing")
        label4 = wx.StaticText(self, label="Weight")
        self.incoming_choice = wx.Choice(self)
        self.outgoing_choice = wx.Choice(self)
        self.incoming_weight = wx.TextCtrl(self, size=default_size)
        self.outgoing_weight = wx.TextCtrl(self, size=default_size)
        self.cut_incoming = wx.Button(self, label="cut")
        self.clear_incoming = wx.Button(self, label="clear")
        self.cut_outgoing = wx.Button(self, label="cut")
        self.clear_outgoing = wx.Button(self, label="clear")

        horizontal = wx.BoxSizer(wx.HORIZONTAL)
        vertical.Add(horizontal, flag=wx.ALL|wx.EXPAND)

        # left side of connections/weight grid
        inner_vertical = wx.BoxSizer(wx.VERTICAL)
        horizontal.Add(inner_vertical, proportion=1, flag=wx.ALL|wx.EXPAND)
        inner_vertical.Add(label, flag=wx.ALL|wx.EXPAND, border=margin)                
        inner_horizontal = wx.BoxSizer(wx.HORIZONTAL)
        inner_vertical.Add(inner_horizontal, flag=wx.ALL|wx.EXPAND)
        inner_horizontal.Add(label2, flag=wx.ALL, border=margin)
        inner_horizontal.Add(self.incoming_choice, proportion=1, flag=wx.ALL|wx.EXPAND, border=margin)
        inner_horizontal = wx.BoxSizer(wx.HORIZONTAL)
        inner_vertical.Add(inner_horizontal, flag=wx.ALL|wx.EXPAND)
        inner_horizontal.Add(label3, flag=wx.ALL, border=margin)
        inner_horizontal.Add(self.outgoing_choice, proportion=1, flag=wx.ALL|wx.EXPAND, border=margin)

        # right side of connections/weight grid
        inner_vertical = wx.BoxSizer(wx.VERTICAL)
        horizontal.Add(inner_vertical, proportion=1, flag=wx.ALL|wx.EXPAND)
        inner_vertical.Add(label4, flag=wx.ALL|wx.EXPAND, border=margin)
        inner_horizontal = wx.BoxSizer(wx.HORIZONTAL)
        inner_vertical.Add(inner_horizontal, flag=wx.ALL|wx.EXPAND)
        inner_horizontal.Add(self.incoming_weight, proportion=1, flag=wx.ALL|wx.EXPAND, border=margin)
        inner_horizontal.Add(self.cut_incoming)
        inner_horizontal.Add(self.clear_incoming, flag=wx.RIGHT, border=margin)
        inner_horizontal = wx.BoxSizer(wx.HORIZONTAL)
        inner_vertical.Add(inner_horizontal, flag=wx.ALL|wx.EXPAND)
        inner_horizontal.Add(self.outgoing_weight, proportion=1, flag=wx.ALL|wx.EXPAND, border=margin)
        inner_horizontal.Add(self.cut_outgoing)
        inner_horizontal.Add(self.clear_outgoing, flag=wx.RIGHT, border=margin)

        self.graph_panel = NeuralGraphPanel(self)
        vertical.Add( self.graph_panel, flag=wx.ALL|wx.EXPAND)
                
        self.enable(False)
        
        #self.SetSizer(dummy)
        #dummy.Fit(self)
        self.SetSizer(vertical)
        vertical.Fit(self)

        self.bind_events(True)

    def bind_events(self, bind):
        if bind:
            self.incoming_choice.Bind(wx.EVT_CHOICE, self.on_incoming_choice)
            self.outgoing_choice.Bind(wx.EVT_CHOICE, self.on_outgoing_choice)
            self.neuron_name.Bind(wx.EVT_TEXT, self.on_name_changed)
            self.threshold.Bind(wx.EVT_TEXT, self.on_threshold_changed)
            self.gain.Bind(wx.EVT_TEXT, self.on_gain_changed)
            self.min_frequency.Bind(wx.EVT_TEXT, self.on_min_frequency_changed)
            self.conductance.Bind(wx.EVT_TEXT, self.on_conductance_changed)
            self.capacitance.Bind(wx.EVT_TEXT, self.on_capacitance_changed)
            self.incoming_weight.Bind(wx.EVT_TEXT, self.on_incoming_weight_changed)
            self.outgoing_weight.Bind(wx.EVT_TEXT, self.on_outgoing_weight_changed)
            self.cut_incoming.Bind(wx.EVT_BUTTON, self.on_cut_incoming)
            self.clear_incoming.Bind(wx.EVT_BUTTON, self.on_clear_incoming)
            self.cut_outgoing.Bind(wx.EVT_BUTTON, self.on_cut_outgoing)
            self.clear_outgoing.Bind(wx.EVT_BUTTON, self.on_clear_outgoing)
        else:
            self.incoming_choice.Unbind(wx.EVT_CHOICE)
            self.outgoing_choice.Unbind(wx.EVT_CHOICE)
            self.neuron_name.Unbind(wx.EVT_TEXT)
            self.threshold.Unbind(wx.EVT_TEXT)
            self.gain.Unbind(wx.EVT_TEXT)
            self.min_frequency.Unbind(wx.EVT_TEXT)
            self.conductance.Unbind(wx.EVT_TEXT)
            self.capacitance.Unbind(wx.EVT_TEXT)
            self.incoming_weight.Unbind(wx.EVT_TEXT)
            self.outgoing_weight.Unbind(wx.EVT_TEXT)
            self.cut_incoming.Unbind(wx.EVT_BUTTON)
            self.clear_incoming.Unbind(wx.EVT_BUTTON)
            self.cut_outgoing.Unbind(wx.EVT_BUTTON)
            self.clear_outgoing.Unbind(wx.EVT_BUTTON)
                

    def enable(self, enable):
        self.neuron_name.Enabled = enable
        self.threshold.Enabled = enable
        self.gain.Enabled = enable
        self.min_frequency.Enabled = enable
        self.conductance.Enabled = enable
        self.capacitance.Enabled = enable

        incoming_enable = enable and len(self.__Neuron.Incoming) > 0
        outgoing_enable = enable and len(self.__Neuron.Outgoing) > 0
        
        self.incoming_weight.Enabled = incoming_enable
        self.incoming_choice.Enabled = incoming_enable
        self.cut_incoming.Enabled = incoming_enable
        self.clear_incoming.Enabled = incoming_enable
        self.outgoing_choice.Enabled = outgoing_enable
        self.outgoing_weight.Enabled = outgoing_enable
        self.cut_outgoing.Enabled = outgoing_enable
        self.clear_outgoing.Enabled = outgoing_enable

    def on_edit_selection_changed(self, event):
        event.Skip() # allow other handlers to process event
        self.do_edit_selection_changed(event.Neuron)

    def do_edit_selection_changed(self, neuron):  
        self.bind_events(False)
        enable = neuron is not None      
        # store the selected neuron for later updates       
        self.__Neuron = neuron

        #run enable logic
        self.enable(enable)

        # update displayed properties
        self.neuron_name.Value = "" if not enable else neuron.Name
        self.threshold.Value = "" if not enable else "{:.2e}".format( neuron.ThresholdVoltage)
        self.gain.Value = "" if not enable else "{:.2e}".format( neuron.Gain)
        self.min_frequency.Value = "" if not enable else "{:.2e}".format( neuron.MinFiringFrequency)
        self.conductance.Value = "" if not enable else "{:.2e}".format( neuron.MembraneConductance)
        self.capacitance.Value = "" if not enable else "{:.2e}".format( neuron.MembraneCapacitance)
        self.incoming_weight.Value = "" if not enable or len(neuron.Incoming) <= 0 else "{:.2e}".format( neuron.Incoming[0].Weight)
        self.outgoing_weight.Value = "" if not enable or len(neuron.Outgoing) <= 0 else "{:.2e}".format( neuron.Outgoing[0].Weight)

        self.fill_choice(True)
        self.fill_choice(False)

        self.bind_events(True)

    def fill_choice(self, incoming):
        neuron = self.__Neuron
        choice = self.incoming_choice if incoming else self.outgoing_choice
        choice.Clear()        
        if neuron is None:
            choice.Enabled = False
            return
        source = neuron.Incoming if incoming else neuron.Outgoing
        for lnk in source:
            choice.Append(lnk.Source.Name if incoming else lnk.Target.Name)
        if len(source) > 0:
            choice.Select(0)

    def on_incoming_choice(self, event):
        event.Skip() # allow other handlers to process event
        neuron = self.__Neuron
        enable = neuron is not None
        index = self.incoming_choice.Selection
        self.incoming_weight.Value = "" if not enable or len(neuron.Incoming) <= 0 else "{:.2e}".format( neuron.Incoming[index].Weight)

    def on_outgoing_choice(self, event):
        event.Skip() # allow other handlers to process event
        neuron = self.__Neuron
        enable = neuron is not None
        index = self.outgoing_choice.Selection
        self.outgoing_weight.Value = "" if not enable or len(neuron.Outgoing) <= 0 else "{:.2e}".format( neuron.Outgoing[index].Weight)

    def on_name_changed(self, event):
        event.Skip() # allow other handlers to process event
        if self.__Neuron is None:
            return
        event = ElementRenamedEvent(neuron=self.__Neuron, name=self.neuron_name.Value)
        wx.PostEvent(self, event)

    def on_threshold_changed(self, event):
        event.Skip() # allow other handlers to process event
        if self.__Neuron is None:
            return
        self.__Neuron.ThresholdVoltage = float(self.threshold.Value)

    def on_gain_changed(self, event):
        event.Skip() # allow other handlers to process event
        if self.__Neuron is None:
            return
        self.__Neuron.Gain = float(self.gain.Value)

    def on_min_frequency_changed(self, event):
        event.Skip() # allow other handlers to process event
        if self.__Neuron is None:
            return
        self.__Neuron.MinFiringFrequency = float(self.min_frequency.Value)

    def on_conductance_changed(self, event):
        event.Skip() # allow other handlers to process event
        if self.__Neuron is None:
            return
        self.__Neuron.MembraneConductance = float(self.conductance.Value)

    def on_capacitance_changed(self, event):
        event.Skip() # allow other handlers to process event
        if self.__Neuron is None:
            return
        self.__Neuron.MembraneCapacitance = float(self.capacitance.Value)

    def on_incoming_weight_changed(self, event):
        event.Skip() # allow other handlers to process event
        if self.__Neuron is None:
            return
        if not self.incoming_weight.Enabled:
            return
        index = self.incoming_choice.Selection
        self.__Neuron.Incoming[index].Weight = float(self.incoming_weight.Value)

    def on_outgoing_weight_changed(self, event):
        event.Skip() # allow other handlers to process event
        if self.__Neuron is None:
            return
        if not self.outgoing_weight.Enabled:
            return
        index = self.outgoing_choice.Selection
        self.__Neuron.Outgoing[index].Weight = float(self.outgoing_weight.Value)

    def on_cut_incoming(self, event):
        event.Skip() # allow other handlers to process event
        if self.__Neuron is None:
            return
        index = self.incoming_choice.Selection
        event = RemoveLinkEvent(self.__Neuron.Incoming[index])
        wx.PostEvent(self, event)
        
    def on_cut_outgoing(self, event):
        event.Skip() # allow other handlers to process event
        if self.__Neuron is None:
            return
        index = self.outgoing_choice.Selection
        event = RemoveLinkEvent(self.__Neuron.Outgoing[index])
        wx.PostEvent(self, event)

    def on_clear_incoming(self, event):
        event.Skip() # allow other handlers to process event
        if self.__Neuron is None:
            return
        links = self.__Neuron.Incoming[:]        
        event = RemoveLinksEvent(links)
        wx.PostEvent(self, event)

    def on_clear_outgoing(self, event):
        event.Skip() # allow other handlers to process event
        if self.__Neuron is None:
            return
        links = self.__Neuron.Outgoing[:]
        event = RemoveLinksEvent(links)
        wx.PostEvent(self, event)

    def on_state_changed(self, event):
        neuron = self.__Neuron
        if neuron is None:
            return
        self.graph_panel.update(neuron._firingFrequency)

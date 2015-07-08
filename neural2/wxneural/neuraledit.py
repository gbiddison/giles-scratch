"""
neuraledit.py
definition for the main editing panel used by wxneural_app.py
"""
import wx
import os
from dragmonitor import DragMonitor
from neuraledit_element import NeuralEditNeuralNet
from neuraledit_events import *
from neuralnetio import NeuralNetIO, NeuralIO
from nervesimreader import NerveSimReader

__EDITOR_SIM_PERIOD__ = 0.05

class NeuralEditPanel(wx.Panel, DragMonitor):
    """panel to edit neural network neurons and associated connections"""
    def __init__(self, parent, *args, **kwargs):
        wx.Panel.__init__(self, parent, size=(300, 300), *args, **kwargs)
        DragMonitor.__init__(self)

        self.Net = NeuralEditNeuralNet()
        self.__DragElement = None
        self.__DragLinkStart = None
        self.__DragLinkEnd = None
        self.__SelectedElement = None

        self.__WhiteBrush = wx.Brush("WHITE")
        self.__ActivationBrush = wx.Brush("GREEN YELLOW")

        self.__BlackPen = wx.Pen("BLACK", 1, wx.SOLID)
        self.__SelectedElementPen = wx.Pen(wx.Colour(204,102,0), 2, wx.SOLID)
        self.__OutgoinLinkPen = wx.Pen("GREEN YELLOW", 2, wx.SOLID)
        self.__IncomingLinkPen = wx.Pen("PINK", 2, wx.SOLID)
        self.__FadedLinkPen = wx.Pen(wx.Colour(0,0,255, 55), 1, wx.SOLID)

        self.__Font = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, False, 'Segoe UI')

        self.__NeuronType = None
        self.__NeuronPath = None
        
        self.Bind(wx.EVT_LEFT_DOWN, self.on_click)
        self.Bind(wx.EVT_RIGHT_DOWN, self.on_click)
        self.Bind(wx.EVT_LEFT_DCLICK, self.on_left_dbl_click)
        self.Bind(wx.EVT_RIGHT_DCLICK, self.on_right_dbl_click)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.on_erase)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_KEY_UP, self.on_key_up)

    def on_sim_start(self, event):
        event.Skip() # allow other handlers to process event
        self.Net.Net.set_period(__EDITOR_SIM_PERIOD__)
        self.Net.Net.set_callback(self.on_state_change)
        self.Net.Net.start()

    def on_sim_stop(self, event):
        event.Skip() # allow other handlers to process event
        self.Net.Net.stop()

    def on_state_change(self):
        event = NetStateChangedEvent()
        wx.PostEvent(self, event)
        self.Refresh(False)
       
    def device_to_logical(self, point):
        return (point[0]*self.scale[0], point[1]*self.scale[1])

    def logical_to_device(self, point):
        return (point[0]/self.scale[0], point[1]/self.scale[1])

    def FireSelectionChangedEvent(self, element):        
        self.__SelectedElement = element
        event = SelectionChangedEvent(element=element, neuron=self.Net.lookup_neuron(element))
        wx.PostEvent(self, event)
        self.Refresh(False)

    def on_remove_link(self, event):
        self.Net.Net.remove_link(event.Link)
        self.FireSelectionChangedEvent(self.__SelectedElement)

    def on_remove_links(self, event):
        for lnk in event.Links:
            self.Net.Net.remove_link(lnk)
        self.FireSelectionChangedEvent(self.__SelectedElement)

    def on_key_up(self, event):
        event.Skip() # allow other handlers to process event
        if event.KeyCode == wx.WXK_DELETE:
            if self.__SelectedElement is not None:
                self.Net.remove_element(self.__SelectedElement)
                event = ElementRemovedEvent(element=self.__SelectedElement)
                wx.PostEvent(self, event)
                self.FireSelectionChangedEvent(None)
  
    def on_size(self, event):
        event.Skip() # allow other handlers to process event
        if self.Size.x == 0 or self.Size.y == 0:
            self.scale = (1.0, 1.0)
        else:
            smaller_dimension = min(self.Size.x, self.Size.y)
            factor = 1.0/smaller_dimension
            self.scale = (factor, factor)
        self.Refresh()

    def on_click(self, event):
        event.Skip() # allow other handlers to process event
        element = self.Net.element_from_point(self.device_to_logical(event.Position))
        self.FireSelectionChangedEvent(element)
        
    def on_begin_drag_left(self, initial_point):
        self.__DragElement = self.Net.element_from_point(self.device_to_logical(initial_point))

    def on_drag_left(self, inital_point, current_point, delta):
        if self.__DragElement is None:
            return
        l_delta = self.device_to_logical(delta)       
        x = self.__DragElement.Position[0] + l_delta[0]
        y = self.__DragElement.Position[1] + l_delta[1]
        x = max( 0, min( 1 - self.__DragElement.Size[0], x))
        y = max( 0, min( 1 - self.__DragElement.Size[0], y))        
        self.__DragElement.Position = (x,y)
        self.Refresh()

    def on_end_drag_left(self, final_point):
        self.__DragElement = None

    def on_begin_drag_right(self, initial_point):
        if self.__DragElement is not None: # no link dragging while dragging a neuron already
            return
        self.__DragElement = self.Net.element_from_point(self.device_to_logical(initial_point))
        self.__DragLinkStart = self.__DragLinkEnd = initial_point

    def on_drag_right(self, initial_point, current_point, delta):
        if self.__DragElement is None:
            return
        self.__DragLinkEnd = current_point
        self.Refresh()            

    def on_end_drag_right(self, final_point):
        if self.__DragElement is None:
            return
        element = self.Net.element_from_point(self.device_to_logical(final_point))
        if element is not None:
            self.Net.add_link(self.__DragElement, element)    
            self.FireSelectionChangedEvent(self.__SelectedElement)
        self.__DragElement = None
        self.__DragLinkStart = None
        self.__DragLinkEnd = None
        self.Refresh()

    def on_left_dbl_click(self, event):
        event.Skip() # allow other handlers to process event
        l_position = self.device_to_logical(event.GetPosition())
        element = self.Net.add_element(l_position, self.__NeuronType, self.__NeuronPath)
        event = ElementAddedEvent(element=element)
        wx.PostEvent(self, event)
        self.FireSelectionChangedEvent(element)

    def on_right_dbl_click(self, event):
        event.Skip() # allow other handlers to process event

        element = self.Net.element_from_point(self.device_to_logical(event.GetPosition()))
        if element is None:
            return
        neuron = self.Net.lookup_neuron(element)
        neuron._firingFrequency = 1.0 if neuron._firingFrequency == 0.0 else 0.0
        neuron._nextFiringFrequency = neuron._firingFrequency
        if element != self.__SelectedElement:
            self.FireSelectionChangedEvent(element)
        else:
            self.Refresh(False)

    def on_neuron_renamed(self, event):
        event.Skip() # allow other handlers to process event
        element = self.Net.lookup_element(event.Neuron)
        self.Net.rename_element(element, event.Name)
        self.FireSelectionChangedEvent(element)        

    def on_file_new(self, event):
        event.Skip() # allow other handlers to process event
        self.Net = NeuralEditNeuralNet()
        self.FireSelectionChangedEvent(None)

    def on_file_open(self, event):
        event.Skip() # allow other handlers to process event

        extension = os.path.splitext(event.Path)[1]
        if extension == ".neu":
            reader = NerveSimReader(event.Path)
            self.Net = reader.Net
            self.FireSelectionChangedEvent(None)
            return
        
        edit_stream = NeuralIO()
        self.Net = edit_stream.read(event.Path)        

        dir_name, file_name = os.path.split(event.Path)
        net_path = os.path.normpath(os.path.join( dir_name, self.Net.NetPath))

        stream = NeuralNetIO()
        self.Net.Net = stream.read(net_path)
        self.Net.rebuild_lookup_table()

        self.FireSelectionChangedEvent(None)

    def on_file_save(self, event):
        event.Skip() # allow other handlers to process event
        dir_name, file_name = os.path.split(event.Path)
        net_path = os.path.splitext(file_name)[0] + '.net'

        self.Net.NetPath = net_path
        edit_stream = NeuralIO()
        edit_stream.write(event.Path, self.Net)               

        stream = NeuralNetIO()
        stream.write(net_path, self.Net.Net)

    def on_erase(self, event):
        pass

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDCFactory(self)
        #dc.BeginDrawing()
        self.paint(dc)
        #dc.EndDrawing()

    def paint(self, dc):
        dc.Clear()
        gc = wx.GraphicsContext.Create(dc) # allows drawing w/ alpha channel
        # draw links first so they're obscured by elements
        for e in self.Net.Elements: 
            self.draw_links(gc, e)
        for e in self.Net.Elements:
            self.draw_neuron(gc, e)
        self.draw_drag_link(gc)

    def draw_links(self, dc, element):
        neuron = self.Net.lookup_neuron(element)

        if len(neuron.Outgoing) == 0:
            return

        for link in neuron.Outgoing:
            target = self.Net.lookup_element(link.Target)
            if self.__SelectedElement == target:
                dc.SetPen(self.__IncomingLinkPen)
            elif self.__SelectedElement == element:
                dc.SetPen(self.__OutgoinLinkPen)
            else:
                dc.SetPen(self.__FadedLinkPen)

            (start_x, start_y) = self.logical_to_device(element.Position)
            (start_w, start_h) = self.logical_to_device(element.Size)
            (end_x, end_y) = self.logical_to_device(target.Position)
            (end_w, end_h) = self.logical_to_device(target.Size)
            dc.StrokeLine( start_x + start_w, start_y + start_h / 2, end_x, end_y + end_h / 2);
        
    def draw_neuron(self, dc, element):
        dc.SetBrush(self.__WhiteBrush)
        if self.__SelectedElement == element:
            dc.SetPen( self.__SelectedElementPen)
        else:
            dc.SetPen( self.__BlackPen)    
        
        neuron = self.Net.lookup_neuron(element)
        has_incoming = len(neuron.Incoming) > 0
        has_outgoing = len(neuron.Outgoing) > 0
                    
        (x,y) = self.logical_to_device(element.Position)
        (w,h) = self.logical_to_device(element.Size)        

        if not has_incoming: #input neuron
            dc.DrawEllipse(x, y, w, h)
        elif has_outgoing:   #intermediate layer
            dc.DrawRectangle(x, y, w, h)
        else:                #output neuron
            points = ((x, y), (x, y + h), (x + w, y + h / 2.0), (x, y))
            dc.DrawLines(points)

        dc.SetFont(self.__Font, wx.Colour(0,0,0))
        (tw, th) = dc.GetTextExtent(neuron.Name)
        dc.DrawText(neuron.Name, x + w / 2.0 - tw / 2.0, y + h + th / 8.0)
        
        #draw activation as percent fill
        (fill_w, fill_h) = self.logical_to_device((min(element.Size[0], neuron._firingFrequency * element.Size[0]), min(element.Size[1], neuron._firingFrequency * element.Size[1])))
        dc.SetBrush(self.__ActivationBrush)
        if not has_incoming: #input neuron
            dc.DrawEllipse(x + w / 2.0 - fill_w / 2.0, y + h / 2.0 - fill_h / 2.0, fill_w, fill_h)
        elif has_outgoing:   #intermediate layer
            dc.DrawRectangle(x, y, fill_w, h)
        else:
            points = ((x, y), (x, y + h), (x + fill_w, y + h / 2.0), (x, y))
            dc.DrawLines(points)

    def draw_drag_link(self, dc):
        if self.__DragLinkStart is None:
            return
        dc.SetPen(self.__OutgoinLinkPen)            
        dc.StrokeLine( self.__DragLinkStart[0], self.__DragLinkStart[1], self.__DragLinkEnd[0], self.__DragLinkEnd[1]) 

    def set_neuron_type(self, event):
        self.__NeuronType = event.NeuronType
        self.__NeuronPath = event.Path


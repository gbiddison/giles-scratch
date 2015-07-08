import wx
from collections import deque
from threading import Lock
from time import time

_GRID_LINES = 10
_DATA_SIZE = 250
_MIN_UPDATE_INTERVAL = 0.1

class NeuralGraphWindow():
    def __init__(self, xxtitle, close_handler=None):
        frame = wx.Frame(None, title=xxtitle)
        self.graph = NeuralGraphPanel(frame)
        self._close_handler = close_handler
        frame.Bind( wx.EVT_CLOSE, self.on_close)
        frame.Fit()
        frame.Show()
        
    def on_close(self, event):
        event.Skip() # allow other handlers to process event
        if self._close_handler is not None:
            self._close_handler(self.graph)

class NeuralGraphPanel(wx.Panel):
    """panel to graph neuron activity via provided xmlprc connection"""
    def __init__(self, parent, *args, **kwargs):
        wx.Panel.__init__(self, parent, size=(200,200), *args, **kwargs)
        self.last_update_time = 0
        self.data = deque([0 for x in range(_DATA_SIZE)])
        self.data_lock = Lock()
        self.grid_pen = wx.Pen(wx.Colour(0,128,255),1, wx.SOLID)
        self.rising_line_pen = wx.Pen(wx.Colour(255,128,0),1, wx.SOLID)
        self.falling_line_pen = wx.Pen(wx.Colour(0,255,0),1, wx.SOLID)
        self.flat_line_pen = wx.Pen(wx.Colour(192, 192, 0), 1, wx.SOLID)
 
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.Bind( wx.EVT_ERASE_BACKGROUND, self.on_erasebackground)
        self.Bind( wx.EVT_PAINT, self.on_paint)
        self.Bind( wx.EVT_SIZE, self.on_size)
        #self.Bind( wx.EVT_MOTION, self.OnMotion)

        self.do_size() # initialize backing buffer

    def on_erasebackground(self, event):
        pass

    def on_size(self, event):
        event.Skip() # allow other handlers to process event
        self.do_size()

    def do_size(self):
        size = self.GetClientSize()
        #self._buffer = wx.Bitmap('buffer') #size[0], size[1])
        #self._buffer.SetSize(size)
        self.Refresh(False)

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDCFactory(self)
        #self.PrepareDC(dc)
        #dc.BeginDrawing()
        self.paint(dc)
        #dc.EndDrawing()

    def paint(self, dc):
        dc.SetBackground( wx.Brush( "Blue"))
        dc.Clear()
        self.draw_grid(dc)
        self.draw_data(dc)
        
    def draw_grid(self, dc):
        count = _GRID_LINES
        size = self.GetClientSize()
        left, right, top, bottom = (0.0, size[0], 0, size[1])
        width = right-left
        height = bottom-top
        w_step = width / float(count)
        h_step = height / float(count)
        dc.SetPen(self.grid_pen)
        for x in range(1, count):
            dc.DrawLinePoint( (left + w_step * x, top), (left + w_step * x, bottom))
            dc.DrawLinePoint( (left, top + h_step * x), (right, top + h_step * x))
            
    def draw_data(self, dc):
        with self.data_lock:
            data_copy = deque(self.data)

        biggest = max(data_copy) #reduce(lambda _1, _2: max(_1,_2), data_copy)
        smallest = min(data_copy) #reduce(lambda _1, _2: min(_1,_2), data_copy)
        count = _DATA_SIZE
        size = self.GetClientSize()
        left, right, top, bottom = (0.0, size[0], 0, size[1])
        width = right-left
        height = bottom-top
        w_step = width / float(count)
        h_scale = 0.75;
        h_scaled = h_scale * height;
        h_border = (height - h_scaled) / 2
        h_step = h_scaled / float(biggest-smallest) if (biggest-smallest) != 0.0 else 0.0

        # special case where biggest == smallest is a straight line across at a fixed value
        # draw this case at the bottom if its zero, otherwise at the top
        if biggest == smallest:
            dc.SetPen(self.flat_line_pen)
            h_point = height - h_border if biggest == 0.0 else h_border
            dc.DrawLinePoint((left, h_point), (right, h_point))
            return

        # normalize points so that smallest value is at bottom, largest is at top
        #
        # norm = (data - smallest) * height / (biggest-smallest)
        # h_next & h_previous order is inverted since screen zero is upperleft
        #
        h_previous = height - (h_border + (data_copy[0] - smallest) * h_step)
        dc.SetPen(self.flat_line_pen)
        dc.DrawLinePoint((left, h_previous), (left + w_step, h_previous))
        for x in range(1, count):
            x1 = left + w_step * x
            x2 = left + w_step * (x+1)
            h_next = height - (h_border + (data_copy[x] - smallest) * h_step)
            # draw vertical
            if h_next != h_previous:
                dc.SetPen( self.rising_line_pen if h_next < h_previous else self.falling_line_pen)
            dc.DrawLinePoint((x1, h_previous), (x1, h_next))
            # draw horizontal
            dc.SetPen(self.flat_line_pen)
            dc.DrawLinePoint((x1, h_next), (x2, h_next))
            h_previous = h_next

    def update(self, point):
        with(self.data_lock):
            self.data.popleft()
            self.data.append(point)
        self.Refresh(False)
        # only UPDATE every so often, otherwise the repaint hogs the CPU and we hang
        if(time() - self.last_update_time > _MIN_UPDATE_INTERVAL):        
            self.last_update_time = time()
            self.Update()
        #dc = wx.ClientDC(self) if wx.Window.IsDoubleBuffered(self) else wx.BufferedDC(wx.ClientDC(self), self._buffer)
        #self.paint(dc)

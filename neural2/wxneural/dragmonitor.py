import wx

class DragMonitor:
    """DragMonitor - Mix-in class to monitor mouse dragging"""

    __drag_threshold__ = 3
    
    def __init__(self):
        self.LeftDown = False
        self.LeftDragging = False
        self.RightDown = False
        self.RightDragging = False
        self.InitialLeftPoint = (0,0)
        self.InitialRightPoint = (0,0)
        self.LeftPoint = (0,0)
        self.RightPoint = (0,0)
        
        self.Bind(wx.EVT_LEFT_DOWN, self.__OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.__OnLeftUp)
        self.Bind(wx.EVT_RIGHT_DOWN, self.__OnRightDown)
        self.Bind(wx.EVT_RIGHT_UP, self.__OnRightUp)
        self.Bind(wx.EVT_MOTION, self.__OnMotion)
        self.Bind(wx.EVT_MOUSE_CAPTURE_LOST, self.__OnCaptureLost)

    def on_begin_drag_left(self, initial_point): pass
    def on_end_drag_left(self, final_point): pass
    def on_drag_left(self, initial_point, current_point, delta): pass
    def on_begin_drag_right(self, initial_point): pass
    def on_end_drag_right(self, final_point): pass
    def on_drag_right(self, initial_point, current_point, delta): pass

    def __OnLeftDown(self, event):
        event.Skip() # continue propagating event 
        self.CaptureMouse()
        self.LeftDown = True
        self.InitialLeftPoint = self.LeftPoint = event.GetPosition()
    
    def __OnLeftUp(self, event):
        event.Skip() # continue propagating event
        if not self.LeftDown: 
            return
        self.ReleaseMouse() 
        self.LeftDown = False
        if self.LeftDragging:
            self.LeftDragging = False
            self.on_end_drag_left(event.GetPosition())

    def __OnRightDown(self, event):
        event.Skip() # continue propagating event 
        self.CaptureMouse()
        self.RightDown = True
        self.InitialRightPoint = self.RightPoint = event.GetPosition()

    def __OnRightUp(self, event):
        event.Skip() # continue propagating event 
        if not self.RightDown:
            return
        self.ReleaseMouse()
        self.RightDown = False
        if self.RightDragging:
            self.RightDragging = False
            self.on_end_drag_right(event.GetPosition())

    def __OnCaptureLost(self, event):
        event.Skip() # continue propagating event
        if self.LeftDown:
            self.LeftDown = False
            self.LeftDragging = False
            self.on_end_drag_left(wx.GetMousePosition())
        if self.RightDown:
            self.RightDown = False
            self.RightDragging = False
            self.on_end_drag_right(wx.GetMousePosition())

    def passed_drag_threshold(self, delta):
        dx, dy = abs(delta.x), abs(delta.y)
        return dx >= self.__drag_threshold__ or dy >= self.__drag_threshold__
       
    def __OnMotion(self, event):
        event.Skip() # continue propagating event 
        position = event.GetPosition()                
        if self.LeftDown:
            if not self.LeftDragging:
                if not self.passed_drag_threshold(position - self.InitialLeftPoint):
                    return
                self.LeftDragging = True
                self.on_begin_drag_left(self.InitialLeftPoint)
            self.on_drag_left(self.InitialLeftPoint, position, position - self.LeftPoint)
            self.LeftPoint = position
        if self.RightDown:
            if not self.RightDragging:
                if not self.passed_drag_threshold(position - self.InitialRightPoint):
                    return
                self.RightDragging = True
                self.on_begin_drag_right(self.InitialRightPoint)
            self.on_drag_right(self.InitialRightPoint, position, position - self.RightPoint)
            self.RightPoint = position
            

"""
UI for neuron tools used by wxneural_app
"""

import wx
import os
import fnmatch
from neuraledit_events import *

try:
    from agw import aui
except ImportError:
    import wx.lib.agw.aui as aui
    

class NeuralToolsPanel(aui.AuiToolBar):
    def __init__(self, parent, *args, **kwargs):
        aui.AuiToolBar.__init__(self, parent, agwStyle=aui.AUI_TB_HORZ_LAYOUT)
        w, h = (48, 48)
        self.__last_path = None
        self.__ids = ids = { 'new':0, 'open':1, 'save':2, 'saveas':3, 'start':4, 'stop':5, 'pick':6}
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icons')
        bmp_new = wx.BitmapFromImage(wx.Image(os.path.join(icon_path, 'document.png')).Scale(w, h, wx.IMAGE_QUALITY_HIGH))
        bmp_open = wx.BitmapFromImage(wx.Image(os.path.join(icon_path, 'folder.png')).Scale(w, h, wx.IMAGE_QUALITY_HIGH))
        bmp_save = wx.BitmapFromImage(wx.Image(os.path.join(icon_path, 'save.png')).Scale(w, h, wx.IMAGE_QUALITY_HIGH))
        bmp_saveas = wx.BitmapFromImage(wx.Image(os.path.join(icon_path, 'saveas.png')).Scale(w, h, wx.IMAGE_QUALITY_HIGH))
        bmp_start = wx.BitmapFromImage(wx.Image(os.path.join(icon_path, 'gear.png')).Scale(w, h, wx.IMAGE_QUALITY_HIGH))
        bmp_stop = wx.BitmapFromImage(wx.Image(os.path.join(icon_path, 'stop.png')).Scale(w, h, wx.IMAGE_QUALITY_HIGH))
        bmp_pick = wx.BitmapFromImage(wx.Image(os.path.join(icon_path, 'search.png')).Scale(w, h, wx.IMAGE_QUALITY_HIGH))
        
        self.SetToolBitmapSize((w,h))
        self.AddSimpleTool(ids['new'], label="New", short_help_string="New", bitmap=bmp_new)
        self.AddSeparator()
        self.AddSimpleTool(ids['open'], label="Open", short_help_string="Open nui file", bitmap=bmp_open)
        self.AddSimpleTool(ids['save'], label="Save", short_help_string="Save nui file", bitmap=bmp_save)
        self.AddSimpleTool(ids['saveas'], label="Save as", short_help_string="Save nui file", bitmap=bmp_saveas)

        # add a label and a drop down list for picking what to add when dbl-click 
        self.AddSeparator()
        self.NeuronType = wx.Choice(self, -1)
        self.NeuronType.SetToolTip(wx.ToolTip("Neuron type"))
        self.NeuronTypeItem = self.AddControl(self.NeuronType, label="Neuron type")
        self.AddSimpleTool(ids['pick'], label="Pick folder", short_help_string="Pick subnet folder", bitmap=bmp_pick)

        self.AddSeparator()
        self.AddSimpleTool(ids['start'], label="Start", short_help_string="Start running neural net sim", bitmap=bmp_start)
        self.AddSimpleTool(ids['stop'], label="Stop", short_help_string="Stop running neural net sim", bitmap=bmp_stop)

        self.Bind(wx.EVT_TOOL, self.on_tool)
        self.Bind(wx.EVT_CHOICE, self.on_choice)

        self.set_neuron_type_list()
        
        self.EnableTool(ids['saveas'], False)
        self.EnableTool(ids['save'], False)
        self.EnableTool(ids['stop'], False)
        self.Realize()
              
    def on_tool(self, event):
        event.Skip() # allow other handlers to process event
        #tool = (name for name,value in self.ids.items() if value==event.Id).next()
        #wx.MessageDialog(self, "%s" % tool, "click", wx.OK).ShowModal()
    
        if event.Id == self.__ids['new']:      event = self.do_file_new()
        elif event.Id == self.__ids['open']:   event = self.do_file_open()
        elif event.Id == self.__ids['save']:   event = self.do_file_save()
        elif event.Id == self.__ids['saveas']: event = self.do_file_save_as()
        elif event.Id == self.__ids['start']:  event = self.do_sim_start()
        elif event.Id == self.__ids['stop']:   event = self.do_sim_stop()
        elif event.Id == self.__ids['pick']:   event = self.do_pick_folder()
        else: 
            return
        if event == None:
            return
        wx.PostEvent(self, event)

    def do_file_new(self):
        self.__last_path = None
        self.EnableTool(self.__ids['save'], False)
        self.EnableTool(self.__ids['saveas'], False)
        self.Realize()
        return FileNewEvent()

    def do_file_open(self):
        wildcard = "Neuron UI Files (*.nui)|*.nui|" \
                   "All files (*.*)|*.*"
        dlg = wx.FileDialog(
            self, message="Choose a file",
            defaultDir=os.getcwd(), 
            defaultFile="",
            wildcard=wildcard,
            style=wx.FD_OPEN | wx.FD_CHANGE_DIR
            )
        if dlg.ShowModal() == wx.ID_OK:
            self.__last_path = dlg.GetPath()
            self.EnableTool(self.__ids['save'], True)
            self.EnableTool(self.__ids['saveas'], True)
            self.Realize()
            return FileOpenEvent(self.__last_path)
        return None

    def  enable_saveas(self, enable):
        self.EnableTool(self.__ids['saveas'], enable)
        self.Realize()

    def do_file_save(self):
        return FileSaveEvent(self.__last_path)

    def do_file_save_as(self):
        wildcard = "Neuron UI Files (*.nui)|*.nui|" \
                   "All files (*.*)|*.*"
        dlg = wx.FileDialog(
            self, message="Save file as",
            defaultDir=os.getcwd(), 
            defaultFile="",
            wildcard=wildcard,
            style=wx.SAVE | wx.OVERWRITE_PROMPT | wx.CHANGE_DIR
            )
        if dlg.ShowModal() == wx.ID_OK:
            self.__last_path = dlg.GetPath()
            self.EnableTool(self.__ids['save'], True)
            self.Realize()
            return FileSaveEvent(self.__last_path)
        return None

    def do_sim_start(self):
        self.EnableTool(self.__ids['start'], False)
        self.EnableTool(self.__ids['stop'], True)
        self.Realize()
        return SimStartEvent()

    def do_sim_stop(self):
        self.EnableTool(self.__ids['start'], True)
        self.EnableTool(self.__ids['stop'], False)
        self.Realize()
        return SimStopEvent()

    def do_pick_folder(self):
        wildcard = "Neuron UI Files (*.nui)|*.nui|" \
                   "All files (*.*)|*.*"
        dlg = wx.FileDialog(
            self, message="Choose a file from the folder you want to use as the subnet reference folder",
            defaultDir=os.getcwd(), 
            defaultFile="",
            wildcard=wildcard,
            style=wx.OPEN | wx.CHANGE_DIR
            )
        if dlg.ShowModal() == wx.ID_OK:
            dir_name, file_name = os.path.split(dlg.GetPath())
            self.set_neuron_type_list(dir_name)
        return None

    def set_neuron_type_list(self, path=None):
        listing = ['neuron']
        self.__SubNetPath = None
        try:
            if path == None:
                path = os.path.join(os.getcwd(), 'nets')            
            if not os.path.exists(path):
                return
            listing = listing + [os.path.splitext(x)[0] for x in fnmatch.filter(os.listdir(path), '*.nui')]
        finally:
            self.__SubNetPath = path
            choice = self.NeuronType
            choice.Items = listing
            choice.Select(0)
            self.fire_neuron_type_changed_event()
            
    def on_choice(self, event):
            self.fire_neuron_type_changed_event()

    def fire_neuron_type_changed_event(self):
            neuron_type = self.NeuronType.StringSelection            
            path = None
            if not neuron_type == 'neuron':
                path = os.path.join(self.__SubNetPath, neuron_type + '.net')
            wx.PostEvent(self, NeuronTypeChangedEvent(neuron_type, path))

    


#!/usr/bin/env python
"""Link class"""
from pickletoxml import PickleToXML

class Link(PickleToXML):
    GateType_Gate = 0
    GateType_Modulation = 1
    
    def __init__(self, source=None, target=None, weight=1.0, gate_source=None, gate_weight=1.0, gate_state=0, gate_type=GateType_Gate): 
        self.Source = source
        self.Target = target
        self.Weight = weight

        self.GateSource = gate_source  # a second neuron gates the activity of this link
        self.GateWeight = gate_weight
        self.GateState = gate_state    # 0 for inhibit gates, 1 for additive gates
        self.GateType = gate_type      # Gate or Modulation
        
        if source is not None:
            source.set_outgoing(self)
        if target is not None:
            target.set_incoming(self)       
        if gate_source is not None:
            source.set_gating(self)            
    

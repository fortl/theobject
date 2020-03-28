class OSCValue:
    """Single value OSC address"""
    def __init__(self, value, address, updateable=False):
        self.value = value
        self.address = address
        self.updateable = updateable

    def osc_address_prefixes(self):
        return [self.address]
    
    def handle_message(self, address, value):
        self.value = value
    
    def serialize(self):
        if self.updateable:
            return [{"address": self.address, "values": self.value}]
        return []

    

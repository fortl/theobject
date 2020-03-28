class OSCValue:
    """Single value OSC address"""
    def __init__(self, value, address,):
        self.value = value
        self.address = address

    def osc_address_prefixes(self):
        return [self.address]
    
    def handle_message(self, address, value):
        self.value = value
        return None

    def serialize(self):
        return [{"address": self.address, "values": self.value}]

    

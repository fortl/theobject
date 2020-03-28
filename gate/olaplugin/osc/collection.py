class OSCControlsCollection:
    def __init__(self):
        self.controls = []
    
    def add(self, *controls):
        self.controls.extend(controls)
        return self
    
    def handle_message(self, address, value):
        for control in self.controls:
            for prefix in control.osc_address_prefixes():
                if address.startswith(prefix):
                    return control.handle_message(address, value)
    
    def serialize(self):
        messages = []
        for control in self.controls:
            messages.extend(control.serialize())
        return messages

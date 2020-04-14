from olaplugin.osc.feedback import Feedback

class Control:
    def handle_message(self, address, value):
        pass

    def osc_address_prefixes(self):
        pass

    def message(self, address, value):
        for prefix in self.osc_address_prefixes():
            if address.startswith(prefix):
                return self.handle_message(address, value)
        return Feedback()

    def serialize(self, prefix):
        return Feedback()

    def controls(self):
        return self


class Value(Control):
    """Single value OSC address"""
    def __init__(self, value, address):
        self.value = value
        self.address = address

    def osc_address_prefixes(self):
        return [self.address]
    
    def handle_message(self, address, value):
        self.value = value
        return Feedback()

    def get_value(self):
        return self.value**2

    def serialize(self):
        return Feedback({"address": self.address, "values": self.value})

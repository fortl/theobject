import random 

class FlashSparksEffect:
    def __init__(self, units_count: int, controll=None, fade=None, brightness=None, sparks=None):
        self.controll = controll
        self.fade = fade
        self.brightness = brightness
        self.sparks = sparks
        self.value = 0
    
    def handle(self, data):
        units = self.controll.get_selected_units()
        if len(units) == 0:
            return
        if self.controll.read_tapped():
            self.value = 255*self.brightness.get_value()
        if self.value is 0:
            return
        for unit in units:
            value = self.value - random.randint(0, int(self.value*self.sparks.value))
            if value > 255:
                value = 255
            if data[unit] < value:
                data[unit] = value
        self.value -= 150 * self.fade.get_value() + 5
        if self.value < 0:
            self.value = 0
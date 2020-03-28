import math

class StripsMode:
    def __init__(self, units_count: int, brightness=None, speed=None, scale=None, width=None):
        self.units_count = units_count
        self.brightness = brightness
        self.speed = speed
        self.scale = scale
        self.width = width
        self.time = 0
    
    def set_units(self, data, units):
        value = self.brightness.value if self.brightness else 1
        self.time += .01 + self.speed.value /10
        scale = self.scale.value / 5
        for unit in units:
            if math.modf(self.time + unit*scale)[0] > (self.width.value*.85 + .05):
                data[unit] = int(255*value)
            else:
                data[unit] = 0

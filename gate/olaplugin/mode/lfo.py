import math

class LFOMode:
    def __init__(self, units_count: int, brightness=None, speed=None, scale=None):
        self.units_count = units_count
        self.brightness = brightness
        self.speed = speed
        self.scale = scale
        self.time = 0
    
    def set_units(self, data, units):
        value = self.brightness.value if self.brightness else 1
        self.time += .01 + self.speed.value * 2
        scale = self.scale.value
        for unit in units:
            data[unit] = int((math.sin(self.time + unit*scale)*126 + 127)*value)

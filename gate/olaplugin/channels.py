import time
import math
from olaplugin.osc.controls import Control 

MIN_STROBE_INTERVAL = .1

class NoneChannel:
    def __init__(self, *controls):
        self.controls = controls
        pass

    def set_units(self, data, units):
        pass

class Artnet(NoneChannel):
    def __init__(self, units_count: int):
        super().__init__()
        self.units_count = units_count
        self.values = [0]*units_count
    
    def set_data(self, data):
        self.values = data

    def set_units(self, data, units):
        for unit in units:
            data[unit] = self.values[unit]

class Sound(NoneChannel):
    def __init__(self, units_count: int):
        super().__init__()
        self.units_count = units_count
        self.values = [0]*units_count
    
    def set_data(self, data):
        self.values = data

    def set_units(self, data, units):
        for unit in units:
            data[unit] = self.values[unit]

class Light(NoneChannel):
    def __init__(self, units_count: int, brightness=Control):
        super().__init__(brightness)
        self.units_count = units_count
        self.brightness = brightness
    
    def set_units(self, data, units):
        value = self.brightness.get_value()
        for unit in units:
            data[unit] = int(value*255)

class Strobo(NoneChannel):
    def __init__(self, units_count: int, brightness=Control, speed=Control):
        super().__init__(brightness, speed)
        self.units_count = units_count
        self.brightness = brightness
        self.speed = speed
        self.state = 1

    def half_intervals_since_last_tap(self):
        return math.floor((time.time() - self.speed.last_tap)*2 / (self.speed.interval))

    def set_units(self, data, units):
        if self.speed.interval > MIN_STROBE_INTERVAL:
            self.state = (self.half_intervals_since_last_tap())%2
        else:
            self.state = 0 if self.state == 1 else 1

        value = self.brightness.get_value() if self.brightness else 1
        for unit in units:
            data[unit] = int(self.state*value*255)

class Strips(NoneChannel):
    def __init__(self, units_count: int, brightness=None, speed=None, scale=None, width=None):
        super().__init__(brightness, speed, scale, width)
        self.units_count = units_count
        self.brightness = brightness
        self.speed = speed
        self.scale = scale
        self.width = width
        self.time = 0
    
    def set_units(self, data, units):
        value = self.brightness.get_value() if self.brightness else 1
        self.time += .01 + self.speed.value /10
        scale = self.scale.value / 5
        for unit in units:
            if math.modf(self.time + unit*scale)[0] > (self.width.value*.85 + .05):
                data[unit] = int(255*value)
            else:
                data[unit] = 0

class LFO(NoneChannel):
    def __init__(self, units_count: int, brightness=None, speed=None, scale=None, waveform=None):
        super().__init__(brightness, speed, scale, waveform)
        self.units_count = units_count
        self.brightness = brightness
        self.speed = speed
        self.scale = scale
        self.waveform = waveform
        self.time = 0
    
    def set_units(self, data, units):
        value = self.brightness.get_value() if self.brightness else 1
        self.time += (self.speed.value-.5)
        scale = self.scale.value / 2
        if self.waveform.state == 0:
            for unit in units:
                data[unit] = int((math.sin((self.time + unit*scale)*math.pi)*126 + 127)*value)
        else:
            for unit in units:
                data[unit] = int((((self.time + unit*scale)*126 + 127)%255)*value)

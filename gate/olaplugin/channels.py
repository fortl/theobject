import time
import math
from olaplugin.osc.controls import Control 
from olaplugin.config import config

MIN_STROBE_INTERVAL = .1

class NoneChannel:
    def __init__(self, *controls):
        self.controls = controls
        self.first_control = controls[0] if controls else None
        pass

    def set_units(self, data, units):
        pass

    def get_first_control(self):
        return self.first_control

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

    def get_first_control(self):
        return None

class Strobo(NoneChannel):
    def __init__(self, units_count: int, brightness=Control, speed=Control):
        super().__init__(speed, brightness)
        self.units_count = units_count
        self.brightness = brightness
        self.speed = speed
        self.state = 1

    def half_interval_since_last_tap(self):
        return math.floor((time.time() - self.speed.last_tap)*2 / (self.speed.interval+MIN_STROBE_INTERVAL))

    def set_units(self, data, units):
        self.state = (self.half_interval_since_last_tap()+1)%2

        value = self.brightness.get_value() if self.brightness else 1
        for unit in units:
            data[unit] = int(self.state*value*255)

class Strips(NoneChannel):
    def __init__(self, units_count: int, brightness=None, speed=None, scale=None, width=None):
        super().__init__(width, speed, scale, brightness)
        self.units_count = units_count
        self.brightness = brightness
        self.speed = speed
        self.scale = scale
        self.width = width
        self.time = 0
    
    def set_units(self, data, units):
        value = self.brightness.get_value() if self.brightness else 1
        interval = config['leds']['update_interval']
        self.time += interval/20 + self.speed.value*interval/2
        scale = self.scale.value/5
        for unit in units:
            if math.modf(self.time + unit*scale)[0] > (self.width.value*.85 + .05):
                data[unit] = int(255*value)
            else:
                data[unit] = 0

class LFO(NoneChannel):
    def __init__(self, units_count: int, brightness=None, speed=None, scale=None, waveform=None):
        super().__init__(speed, scale, waveform, brightness)
        self.units_count = units_count
        self.brightness = brightness
        self.speed = speed
        self.scale = scale
        self.waveform = waveform
        self.time = 0
    
    def set_units(self, data, units):
        value = self.brightness.get_value() if self.brightness else 1
        interval = config['leds']['update_interval']
        self.time += (self.speed.value-.49)*interval*15
        scale = self.scale.value / 2
        if self.waveform.state == 0:
            for unit in units:
                data[unit] = int((math.sin((self.time + unit*scale)*math.pi)*126 + 127)*value)
        else:
            for unit in units:
                data[unit] = int((((self.time + unit*scale)*126 + 127)%255)*value)

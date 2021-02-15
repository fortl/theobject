import random 
import math

from olaplugin.config import config

class Effect:
    def __init__(self, *controls):
        self.controls = controls

    def tap(self, units):
        pass


class FlashRandom(Effect):
    def __init__(self, units_count: int, fade=None, brightness=None, units=None):
        super().__init__(fade, brightness, units)
        self.fade = fade
        self.units = units
        self.brightness = brightness
        self.units_count = units_count
        self.values = [0]*units_count
    
    def tap(self, units):
        flash_units = int(self.units.get_value()*(self.units_count-1))
        if flash_units > len(units):
            flash_units = len(units)
        start_unit = random.randint(0, len(units)-flash_units)
        for i in sorted(units)[start_unit:start_unit+flash_units+1]:
            self.values[i] = 255

    def loop(self, data, units):
        if all(v == 0 for v in self.values):
            return
        interval = config['leds']['update_interval']
        fade_value = (150*self.fade.get_value() + 5)*interval*5
        for unit in units:
            self.set_data_unit(data, unit)
            self.values[unit] -= fade_value 
            if self.values[unit] < 0:
                self.values[unit] = 0
        
    def set_data_unit(self, data, unit: int):
        value = self.values[unit] * self.brightness.get_value()
        if data[unit] < value:
            data[unit] = value


class FlashSparks(Effect):
    def __init__(self, units_count: int, fade=None, brightness=None, sparks=None):
        super().__init__(fade, brightness, sparks)
        self.fade = fade
        self.brightness = brightness
        self.sparks = sparks
        self.value = 0
    
    def tap(self, units):
        self.value = 255*self.brightness.get_value()

    def loop(self, data, units):
        if self.value is 0:
            return
        interval = config['leds']['update_interval']
        self.value -= (50 * self.fade.get_value() + 5)*interval*5
        if self.value < 0:
            self.value = 0
        self.set_data_units(data, units)

    def set_data_units(self, data, units):
        if self.value is 0 or len(units) == 0:
            return
        for unit in units:
            value = self.value - random.randint(0, int(self.value*self.sparks.value))
            if value > 255:
                value = 255
            if data[unit] < value:
                data[unit] = value


class Shadow(FlashRandom):
    def set_data_unit(self, data, unit: int):
        value = int(math.sqrt(self.values[unit]*self.brightness.get_value()))
        if value > 0:
            data[unit] = data[unit]/value

class Sound(Effect):
    def __init__(self, units_count: int, sensitivity=None, brightness=None, freq=None):
        super().__init__(sensitivity, brightness, freq)
        self.brightness = brightness
        self.freq = freq
        self.sensitivity = sensitivity
        self.units_count = units_count
        self.values = [0]*units_count
    
    def set_data(self, timeline, average):
        sens = (1-self.sensitivity.get_value())*10
        slices = len(average)
        freq = int(self.freq.get_value()*3)
        if sens == 0:
            sens = 1
        def scale(data, index):
            if index == 0:
                return data[index]/(sens) 
            if index/slices < 0.8: 
                return data[index]*60/sens
            return data[index]*200/sens

        self.values = [0]*self.units_count
        for i in range(self.units_count):
            center_index = int(abs((self.units_count)/2-i))
            time_index = int(abs((self.units_count-.5)/2-i)*2*len(timeline)/(self.units_count*2))
            value = int(scale(average, freq%slices) / (1+center_index/4)
                - scale(timeline[time_index], (2+freq)%slices)/4)*2
            if value > 255:
                value = 255
            if value < 0:
                value = 0
            self.values[i] = value

    def loop(self, data, units):
        for unit in units:
            value = self.values[unit] * self.brightness.get_value()
            if data[unit] < value:
                data[unit] = value


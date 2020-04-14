import random 
import math

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
        fade_value = 150 * self.fade.get_value() + 5
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
        self.value -= 50 * self.fade.get_value() + 5
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

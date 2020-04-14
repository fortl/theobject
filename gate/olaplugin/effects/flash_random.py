import random 

class FlashRandomEffect:
    def __init__(self, units_count: int, controll=None, fade=None, brightness=None, units=None):
        self.controll = controll
        self.fade = fade
        self.brightness = brightness
        self.units_count = units_count
        self.units = units
        self.values = [0]*units_count
    
    def set_random_units(self, units):
        flash_units = int(self.units.get_value()*self.units_count) + 1
        if flash_units > len(units):
            flash_units = len(units)
        start_unit = random.randint(0, len(units)-flash_units)
        for i in sorted(units)[start_unit:start_unit+flash_units-1]:
            self.values[i] = 255

    def handle(self, data):
        units = self.controll.get_selected_units()
        if len(units) == 0:
            return
        if self.controll.read_tapped():
            self.set_random_units(units)
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

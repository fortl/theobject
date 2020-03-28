class LightMode:
    def __init__(self, units_count: int, brightness=None):
        self.units_count = units_count
        self.brightness = brightness
    
    def set_units(self, data, units):
        value = self.brightness.value
        for unit in units:
            data[unit] = int(value*255)

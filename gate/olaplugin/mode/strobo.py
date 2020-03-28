class StroboMode:
    def __init__(self, units_count: int, brightness=None, speed=None):
        self.units_count = units_count
        self.brightness = brightness
        self.speed = speed
        self.counter = 0
        self.state = 1
    
    def set_units(self, data, units):
        self.counter += 1
        if self.counter > int((1-self.speed.value)*10):
            self.counter = 0
            self.state = 0 if self.state else 1
        value = self.brightness.value if self.brightness else 1
        for unit in units:
            data[unit] = int(self.state*value*255)

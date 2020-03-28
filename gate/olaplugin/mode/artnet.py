class ArtnetMode:
    def __init__(self, units_count: int):
        self.units_count = units_count
        self.values = [0]*units_count
    
    def set_data(self, data):
        self.values = data

    def set_units(self, data, units):
        for unit in units:
            data[unit] = self.values[unit]

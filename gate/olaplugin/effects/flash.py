class FlashEffect:
    def __init__(self, units_count: int, controll=None):
        self.controll = controll
        self.value = 0
    
    def handle(self, data):
        if self.controll.read_tapped():
            self.value = 255
        if self.value is 0:
            return
        units = self.controll.get_selected_units()
        for unit in units:
            if data[unit] < self.value:
                data[unit] = self.value
        self.value -= 50
        if self.value < 0:
            self.value = 0
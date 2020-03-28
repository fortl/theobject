class FlashEffect:
    def __init__(self, units_count: int, controll=None, fade=None):
        self.controll = controll
        self.fade = fade
        self.value = 0
    
    def handle(self, data):
        units = self.controll.get_selected_units()
        if len(units) == 0:
            return
        if self.controll.read_tapped():
            self.value = 255
        if self.value is 0:
            return
        for unit in units:
            if data[unit] < self.value:
                data[unit] = self.value
        self.value -= 255 * self.fade.value + 3
        if self.value < 0:
            self.value = 0
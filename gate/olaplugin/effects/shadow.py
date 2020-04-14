from olaplugin.effects.flash_random import FlashRandomEffect

import math

class ShadowEffect(FlashRandomEffect):
    def set_data_unit(self, data, unit: int):
        value = int(math.sqrt(self.values[unit]*self.brightness.get_value()))
        if value > 0:
            data[unit] = data[unit]/value

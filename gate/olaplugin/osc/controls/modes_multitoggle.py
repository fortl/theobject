from olaplugin.osc.controls.effects_multitoggle import OSCEffectsMultiToggle

class OSCModesMultiToggle(OSCEffectsMultiToggle):
    """ pads multi-toggle splited into adjoining blocks"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for i in range(self.units_count):
            self.values[0][i] = 1

    def set_value(self, unit: int, target_group: int, value: float):
        for group in range(self.groups_count):
            self.values[group][unit] = 0    
        self.values[target_group][unit] = 1

    def handle_message(self, address: str, value: float):
        super().handle_message(address, value)
        return self.serialize()

class OSCEffectsMultiToggle:
    """Idenedent pads multi-toggle splited into adjoining blocks"""
    def __init__(self, 
                units_count: int = 20, 
                units_per_block: int = 10,
                blocks_count: int = 2,
                groups_count: int = 4, 
                address: str = None):
        self.units_count = units_count
        self.units_per_block = units_per_block
        self.groups_count = groups_count
        self.blocks = [{'address': address + 'Block' + str(i+1), 'index': i} for i in range(blocks_count)]
        self.values = [[0 for i in range(units_count)] for j in range(groups_count)]
        self.init_values()

    def init_values(self):
        for i in range(int(self.units_count/2)):
            self.values[0][i*2] = 1
            self.values[1][i*2+1] = 1

    def osc_address_prefixes(self):
        return [block['address'] for block in self.blocks]
    
    def get_block(self, address: str):
        for block in self.blocks:
            if address.startswith(block['address']):
                return block

    def handle_message(self, address: str, value: float):
        block = self.get_block(address)
        cell = address[len(block['address']) + 1:]
        unit, group = cell.split('/')
        unit = int(unit) - 1 + block['index']*self.units_per_block
        group = int(group)-1
        self.set_value(unit, group, value)
        return None

    def set_value(self, unit: int, target_group: int, value: float):
        self.values[target_group][unit] = value

    def serialize(self):
        messages = []
        units_shift = 0
        for block in self.blocks:
            flatten_values = [self.values[group][unit + units_shift]  
                for group in range(self.groups_count)
                for unit in range(self.units_per_block)]
            messages.append({'address': block['address'], 'values': flatten_values})
            units_shift += self.units_per_block
        return messages
    
    def get_units(self, groups):
        units = set()
        for group in groups:
            units.update(set(index for index in range(self.units_count) if self.values[group][index]))
        return units

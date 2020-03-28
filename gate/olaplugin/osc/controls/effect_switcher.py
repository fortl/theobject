class OSCEffectSwitcher:
    def __init__(self, groups_count: int, name: str, groups_selector=None):
        self.address = name
        self.groups_selector = groups_selector
        self.groups_count = groups_count
        self.values = [0] * groups_count
        self.groups = set()
        self.tapped = False

    def osc_address_prefixes(self):
        return [self.address]
        
    def set_all(self):
        self.values = [1] * self.groups_count
        self.groups = set(i for i in range(self.groups_count))
    
    def handle_message(self, address: str, value: float):
        row = address[len(self.address) + 1:]
        if row == 'all':
            self.set_all()
        elif row == 'tap':
            self.tapped = True
        else:
            group_id = int(row[2:])-1
            if value:
                self.groups.add(group_id)
                self.values[group_id] = 1
            else:
                self.groups.discard(group_id)
                self.values[group_id] = 0

    def serialize(self):
        return [{'address': self.address, 'values': self.values}]
    
    def get_selected_groups(self):
        return self.groups
    
    def get_selected_units(self):
        return self.groups_selector.get_units(self.groups)

    def read_tapped(self):
        tapped = self.tapped
        self.tapped = False
        return tapped
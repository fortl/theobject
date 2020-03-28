class OSCModeSwitchers:
    """A set of multiple modes selectors by group.
    
    [./mode1/all] [./mode2/all] - select that mode for all groups 
    |  multi    | |  multi    | - multitoggle for selecting mode by group
    | toggle1   | | toggle2   |
    | ./mode1/  | | ./mode2/  |
    """
    def __init__(self, groups_count: int, modes):
        self.groups_count = groups_count
        self.modes = [{'address': mode, 'values': ([0] * groups_count)} for mode in modes]
        self.modes[0]['values'] = [1] * groups_count
        self.groups = {mode: set() for mode in modes}
        self.groups[modes[0]] = set(i for i in range(groups_count))

    def osc_address_prefixes(self):
        return [mode['address'] for mode in self.modes]
    
    def get_mode(self, address: str):
        for mode in self.modes:
            if address.startswith(mode['address']):
                return mode
    
    def set_all(self, mode):
        for mode_item in self.modes:
            if mode_item == mode:
                mode['values'] = [1] * self.groups_count
                self.groups[mode['address']] = set(i for i in range(self.groups_count))
            else:
                mode_item['values'] = [0] * self.groups_count
                self.groups[mode_item['address']] = set()
    
    def handle_message(self, address: str, value: float):
        mode = self.get_mode(address)
        row = address[len(mode['address']) + 1:]
        if row == 'all':
            self.set_all(mode)
        else:
            group_id = int(row[2:])-1
            for every_mode in self.modes:
                every_mode['values'][group_id] = 0
            mode['values'][group_id] = 1
            for group in self.groups.values():
                group.discard(group_id)
            self.groups[mode['address']].add(group_id)

    def serialize(self):
        return self.modes
    
    def get_selected_groups(self, mode: str):
        return self.groups[mode]
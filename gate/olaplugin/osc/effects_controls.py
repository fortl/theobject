from olaplugin.osc.controls import Control
from olaplugin.osc.feedback import Feedback

import re

class Groups(Control):
    """Idenedent pads multi-toggle splited into adjoining blocks"""
    def __init__(self, 
                units_count: int = 20, 
                units_per_block: int = 10,
                blocks_count: int = 2,
                groups_count: int = 4, 
                address: str = ''):
        self.units_count = units_count
        self.units_per_block = units_per_block
        self.groups_count = groups_count
        self.blocks = [{'address': address + 'Block' + str(i+1), 'index': i} for i in range(blocks_count)]
        self.values = [[0 for i in range(units_count)] for j in range(groups_count)]
        self.init_values()

    def init_values(self):
        for i in range(self.units_count):
            self.values[i%self.groups_count][i] = 1
        # for i in range(int(self.units_count/2)):
        #     self.values[0][i*2] = 1
        #     self.values[1][i*2 + 1] = 1

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
        return Feedback()

    def set_value(self, unit: int, target_group: int, value: float):
        self.values[target_group][unit] = value

    def serialize(self):
        feedback = Feedback()
        units_shift = 0
        for block in self.blocks:
            flatten_values = [self.values[group][unit + units_shift]  
                for group in range(self.groups_count)
                for unit in range(self.units_per_block)]
            feedback.add_message({'address': block['address'], 'values': flatten_values})
            units_shift += self.units_per_block
        return feedback
    
    def get_units(self, groups):
        units = set()
        for group in groups:
            units.update(set(index for index in range(self.units_count) if self.values[group][index]))
        return units


class Effects:
    def __init__(self, controls_prefix: str, groups_count: int, groups: Groups, effects):
        self.controls_prefix = controls_prefix
        self.groups_count = groups_count
        self.groups = groups
        self.effects = effects
        self.effects_selectors = {effect: Selector(groups_count, '') for effect in effects.keys()}
    
    
    def message(self, address: str, value: float):
        feedback = Feedback()
        if not address.startswith(self.controls_prefix):
            return feedback
        address = address[len(self.controls_prefix) + 1:]
        feedback.add( self.groups.message(address, value).prefix(self.controls_prefix + '/'))
        for name, effect in self.effects.items():
            if not address.startswith(name):
                continue
            sub_address = address[len(name) + 1:]
            osc_prefix = self.controls_prefix + '/' + name 
            for control in effect.controls:
                feedback.add(
                    control.message(sub_address, value).prefix(osc_prefix))
            feedback.add(
                self.effects_selectors[name].message(sub_address, value).prefix(osc_prefix))
        return feedback

    def serialize_controls(self):
        osc_messages = self.groups.serialize().prefix(self.controls_prefix + '/')
        for name, effect in self.effects.items():
            osc_prefix = self.controls_prefix + '/' + name
            osc_messages.add(
                self.effects_selectors[name].serialize().prefix(osc_prefix))
            for control in effect.controls:
                osc_messages.add(control.serialize().prefix(osc_prefix + '/'))
        return osc_messages
    
    def update_units(self, data):
        for name, selector in self.effects_selectors.items():
            units = self.groups.get_units(selector.groups)
            if len(units) == 0:
                continue
            if selector.read_tapped():
                self.effects[name].tap(units)
            if units:
                self.effects[name].loop(data, units)

class Selector(Control):
    def __init__(self, groups_count: int, name: str=''):
        self.address = name
        self.groups_count = groups_count
        self.set_all()
        self.tapped = False

    def osc_address_prefixes(self):
        return [self.address]

    def clear_all(self):
        self.values = [0] * groups_count
        self.groups = set()

    def set_all(self):
        self.values = [1] * self.groups_count
        self.groups = set(i for i in range(self.groups_count))
    
    def handle_message(self, address: str, value: float):
        match = re.search('^(all|tap|\d)/?(\d)?', address)
        if not match:
            return Feedback()
        action, group_id = match.groups()
        if action == 'all':
            self.set_all()
        elif action == 'tap':
            if value == 1:
                self.tapped = True
        else:
            group_id = int(group_id)-1
            if value:
                self.groups.add(group_id)
                self.values[group_id] = 1
            else:
                self.groups.discard(group_id)
                self.values[group_id] = 0
        return self.serialize()

    def serialize(self):
        return Feedback({'address': self.address, 'values': self.values})
        
    def read_tapped(self):
        tapped = self.tapped
        self.tapped = False
        return tapped

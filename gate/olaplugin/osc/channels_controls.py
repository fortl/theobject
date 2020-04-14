import olaplugin.osc.effects_controls as effects_controls
from olaplugin.osc.controls import Control
from olaplugin.osc.feedback import Feedback

import time
import statistics
import re

MAX_STROBO_BPM = 2
MIN_STROBO_TAPS = 5

class Groups(effects_controls.Groups):
    """ pads multi-toggle splited into adjoining blocks"""

    def init_values(self):
        for i in range(self.units_count):
            self.values[i%self.groups_count][i] = 1

    def set_value(self, unit: int, target_group: int, value: float):
        for group in range(self.groups_count):
            self.values[group][unit] = 0    
        self.values[target_group][unit] = 1

    def handle_message(self, address: str, value: float):
        super().handle_message(address, value)
        return self.serialize()

class Channels(Control):
    """A set of multiple channel's selectors by group.
    
    [./channel1/all] [./channel2/all] - select that channel for all groups 
     |  multi    |     |  multi    | - multitoggle for selecting channel by group
     | toggle1   |     | toggle2   |
     |./channel1/|     |./channel2/|
    """
    def __init__(self, controls_prefix: str, groups_count: int, 
                default_channel: str, groups: Groups, channels):
        self.channels = channels 
        self.groups_count = groups_count
        self.set_all(default_channel)
        self.controls = list(set(c for channel in channels.values() for c in channel.controls))
        self.controls.append(groups)
        self.groups_controll = groups
        self.controls_prefix = controls_prefix

    def set_all(self, selected_channel):
        self.values = { channel: [0] * self.groups_count for channel in self.channels.keys()}
        self.values[selected_channel] = [1] * self.groups_count
        self.groups = {channel: set() for channel in self.channels.keys()}
        self.groups[selected_channel] = set(i for i in range(self.groups_count))

    def set_group(self, selected_channel: str, group_id: int):
        for groups in self.values.values():
            groups[group_id] = 0
        self.values[selected_channel][group_id] = 1
        for groups in self.groups.values():
            groups.discard(group_id)
        self.groups[selected_channel].add(group_id)
    
    def message(self, address: str, value: float):
        feedback = Feedback()
        if not address.startswith(self.controls_prefix):
            return feedback
        address = address[len(self.controls_prefix) + 1:]
        for control in self.controls:
            feedback.add( control.message(address, value).prefix(self.controls_prefix + '/'))
        match = re.search('^(\w+)/(all|1)/?(\d)?', address)
        if not match:
            return feedback
        channel, select_all, group_id = match.groups()
        if channel not in self.channels:
            return feedback
        if select_all == 'all':
            self.set_all(channel)
        else:
            self.set_group(channel, int(group_id)-1)
        feedback.add(self.serialize().prefix(self.controls_prefix + '/'))
        return feedback

    def serialize(self):
        return Feedback(*[{ 
            'address': channel, 
            'values': self.values[channel] } for channel in self.values.keys()])
    
    def serialize_controls(self):
        osc_messages = self.serialize()
        osc_prefix = self.controls_prefix + '/'
        for control in self.controls:
            osc_messages.add(control.serialize().prefix(osc_prefix))
        return osc_messages

    def get_selected_groups(self, channel: str):
        return self.groups[channel]

    def update_units(self, data):    
        for channel, handler in self.channels.items():
            units = self.groups_controll.get_units(self.groups[channel])
            handler.set_units(data, units)

class StroboSpeed(Control):
    def __init__(self, value, value_address, tap_address):
        self.value = value
        self.interval = MAX_STROBO_BPM*value
        self.value_address = value_address
        self.tap_address = tap_address
        self.tap_times = []
        self.last_tap = time.time()

    def osc_address_prefixes(self):
        return [self.value_address, self.tap_address]
    
    def handle_message(self, address, value):
        if address.startswith(self.value_address):
            self.value = value
            self.interval = MAX_STROBO_BPM*value
            self.tap_times = []
        if address.startswith(self.tap_address) and value == 1:
            self.tap()
        return self.serialize()

    # def tap(self):
    #     self.last_tap = time.time()

    def tap(self):
        """Sets BPM interval by tapping. Have some issues for my tablet(?). 
        Is temporary turned off."""

        current_time = time.time()
        if (current_time - self.last_tap) > MAX_STROBO_BPM:
            self.tap_times = []
        self.last_tap = current_time
        self.tap_times.append(self.last_tap)
        if len(self.tap_times) >= MIN_STROBO_TAPS:
            self.interval = statistics.median(
                [self.tap_times[i+1] - self.tap_times[i] 
                    for i in range(len(self.tap_times)-1)])
            self.value = self.interval/MAX_STROBO_BPM


    def get_value(self):
        return self.value

    def since_last_tap(self):
        return time.time() - self.last_tap

    def serialize(self):
        return Feedback({"address": self.value_address, "values": self.value})
    
class WaveformSwitcher(Control):
    """Two waveform types switcher"""
    def __init__(self, state, address):
        self.state = state
        self.address = address

    def osc_address_prefixes(self):
        return [self.address]
    
    def handle_message(self, address, value):
        row = address[len(self.address) + 1:]
        self.state = int(row[2:])-1
        return self.serialize()

    def serialize(self):
        return Feedback()

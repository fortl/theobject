from collections import OrderedDict

import olaplugin.osc.channels_controls as channels_controls
import olaplugin.osc.effects_controls as effects_controls
from olaplugin.osc.controls import Value
import olaplugin.channels as channels
import olaplugin.effects as effects
import olaplugin.theobject as theobject
from olaplugin.uart_proxy import uart_proxy

""" Interface Declaration """

EFFECT_GROUPS_COUNT = 4
MODE_GROUPS_COUNT = 4
BLOCKS_COUNT = 2
 
master_brightness = Value(1, 'master')
blackout = Value(0, 'blackout')
channels_brightness = Value(1, 'brightness')
artnet_channel = channels.Artnet(theobject.LED_COUNT)
sound_reactive_effect = effects.Sound(theobject.LED_COUNT,
    sensitivity=Value(0.5, 'sensitivity'),
    brightness=Value(1, 'brightness'),
    freq=Value(0, 'freq'))

channels_block = channels_controls.Channels(
    'channels', MODE_GROUPS_COUNT, ['artnet', 'light', 'strobo', 'lfo', 'strips'], 
    channels_controls.Groups(
        units_count = theobject.LED_COUNT, 
        groups_count = MODE_GROUPS_COUNT,
    ), {
        'none': channels.NoneChannel(),
        'artnet': artnet_channel,
        'light': channels.Light(theobject.LED_COUNT, 
            brightness=channels_brightness),
        'strobo': channels.Strobo(theobject.LED_COUNT, 
            brightness=channels_brightness, 
            speed=channels_controls.StroboSpeed(.2, 'stroboSpeed', 'stroboBPM')),
        'lfo': channels.LFO(theobject.LED_COUNT, 
            brightness=channels_brightness, 
            speed=Value(.35, 'lfoSpeed'),
            scale=Value(.2, 'lfoScale'), 
            waveform=channels_controls.WaveformSwitcher(0, 'lfoWaveform')),
        'strips': channels.Strips(theobject.LED_COUNT, 
            brightness=channels_brightness,
            speed=Value(.5, 'stripsSpeed'),
            scale=Value(.75, 'stripsScale'),
            width=Value(.8, 'stripsWidth')),
    })

effects_block = effects_controls.Effects(
    'effects', EFFECT_GROUPS_COUNT,
    effects_controls.Groups(
        units_count = theobject.LED_COUNT, 
        groups_count = EFFECT_GROUPS_COUNT,
    ), {
        'flashSparks': effects.FlashSparks(theobject.LED_COUNT, 
            fade=Value(.5, 'fade'),
            brightness=Value(.8, 'brightness'),
            sparks=Value(1, 'sparks')),
        'flashRandom': effects.FlashRandom(theobject.LED_COUNT,
            fade=Value(.7, 'fade'),
            brightness=Value(.8, 'brightness'),
            units=Value(.4, 'units')),
        'shadow': effects.Shadow(theobject.LED_COUNT,
            fade=Value(.7, 'fade'),
            brightness=Value(1, 'brightness'),
            units=Value(.4, 'units')),
        'sound': sound_reactive_effect,
    })

def button_clicked():
    channel = channels_block.select_next_channel()
    if channel:
        control = channel.get_first_control()
        if not control:
            control = master_brightness
        uart_proxy.set_observe_encoder(lambda inc: control.encoder_inc(inc))

uart_proxy.set_observe_encoder_pushed(lambda inc: master_brightness.encoder_inc(inc))
uart_proxy.set_observe_encoder(lambda inc: master_brightness.encoder_inc(inc))
uart_proxy.set_observe_button(button_clicked)

def handle_message(address, value):
    return channels_block.message(address, value)\
        .add( effects_block.message(address, value))\
        .add( blackout.message(address, value))\
        .add( master_brightness.message(address, value))

def serialize():
    return channels_block.serialize_controls()\
        .add( effects_block.serialize_controls())\
        .add( blackout.serialize())\
        .add( master_brightness.serialize())

def get_units():
    data = [0]*theobject.LED_COUNT
    if blackout.value: 
        return data
    channels_block.update_units(data)
    effects_block.update_units(data)
    data = [int(i * master_brightness.value**2) for i in data]
    return data

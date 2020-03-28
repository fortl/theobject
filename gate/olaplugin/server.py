import asyncio
import concurrent.futures
import time

from ola.ClientWrapper import ClientWrapper
from pythonosc.osc_server import AsyncIOOSCUDPServer
from pythonosc.dispatcher import Dispatcher
from pythonosc.udp_client import SimpleUDPClient

from olaplugin.osc.collection import OSCControlsCollection
from olaplugin.osc.controls.effects_multitoggle import OSCEffectsMultiToggle
from olaplugin.osc.controls.modes_multitoggle import OSCModesMultiToggle
from olaplugin.osc.controls.mode_switchers import OSCModeSwitchers
from olaplugin.osc.controls.effect_switcher import OSCEffectSwitcher
from olaplugin.osc.controls.value import OSCValue
from olaplugin.mode.artnet import ArtnetMode
from olaplugin.mode.none import NoneMode
from olaplugin.mode.light import LightMode
from olaplugin.mode.strobo import StroboMode
from olaplugin.mode.lfo import LFOMode
from olaplugin.mode.strips import StripsMode
from olaplugin.effects.flash import FlashEffect
import olaplugin.theobject as theobject
import olaplugin.net_helper as net_helper

OSC_UPDATE_INTERVAL = 2
OSC_ADDRESS_PREFIX = '/theobject/'
OSC_UPDATE_DEBOUNCE = .2
osc_port = 9000
osc_client_ip = '255.255.255.255'
osc_client_port = 9000
osc_client = SimpleUDPClient(osc_client_ip, osc_client_port, allow_broadcast=True)
osc_ip = '0.0.0.0'
osc_update_timer_handle = None
osc_update_time = time.time()
artnet_universe = 1

EFFECT_GROUPS_COUNT = 4
MODE_GROUPS_COUNT = 4
BLOCKS_COUNT = 2
effect_groups = OSCEffectsMultiToggle(
    units_count = theobject.LED_COUNT, 
    groups_count = EFFECT_GROUPS_COUNT, 
    address = 'effects') 
mode_groups = OSCModesMultiToggle(
    units_count = theobject.LED_COUNT, 
    groups_count = MODE_GROUPS_COUNT, 
    address = 'modes') 
master_brightness = OSCValue(1, 'master', updateable=True)
blackout = OSCValue(0, 'blackout', updateable=True)
mode_swithcher = OSCModeSwitchers(MODE_GROUPS_COUNT, 
    [ 'artnet', 'none', 'light', 'strobo', 'lfo', 'strips' ])
mode_brightness = OSCValue(1, 'mode/brightness')
strobo_speed = OSCValue(1, 'mode/stroboSpeed')
lfo_scale = OSCValue(1, 'mode/lfoScale')
lfo_speed = OSCValue(1, 'mode/lfoSpeed')
strips_scale = OSCValue(1, 'mode/stripsScale')
strips_speed = OSCValue(1, 'mode/stripsSpeed')
strips_width = OSCValue(1, 'mode/stripsWidth')
flash1_switcher = OSCEffectSwitcher(EFFECT_GROUPS_COUNT, 'flash', groups_selector=effect_groups)
controls = OSCControlsCollection().add(
    effect_groups, 
    mode_brightness, strobo_speed,
    lfo_scale, lfo_speed,
    strips_scale, strips_speed, strips_width,
    mode_groups, mode_swithcher,
    flash1_switcher, 
    master_brightness, blackout)

modes = {
    'none': NoneMode(theobject.LED_COUNT),
    'artnet': ArtnetMode(theobject.LED_COUNT),
    'light': LightMode(theobject.LED_COUNT, brightness=mode_brightness),
    'strobo': StroboMode(theobject.LED_COUNT, brightness=mode_brightness, speed=strobo_speed),
    'lfo': LFOMode(theobject.LED_COUNT, brightness=mode_brightness, speed=lfo_speed, scale=lfo_scale),
    'strips': StripsMode(theobject.LED_COUNT, 
        brightness=mode_brightness, speed=strips_speed, scale=strips_scale, width=strips_width),
}
effects = [FlashEffect(theobject.LED_COUNT, controll=flash1_switcher)]

def update_units():
    data = [0]*theobject.LED_COUNT
    if blackout.value: 
        theobject.set_leds(data)
        return
    for mode, handler in modes.items():
        selected_groups = mode_swithcher.get_selected_groups(mode)
        units = mode_groups.get_units(selected_groups)
        handler.set_units(data, units)
    for effect in effects:
        effect.handle(data)
    data = [int(i * master_brightness.value) for i in data]
    theobject.set_leds(data)

async def periodic_units_updates():
    while True:
        update_units()
        await asyncio.sleep(.02)

def artnet_data(data):
    modes['artnet'].set_data(data)

def update_osc_interface_data():
    global osc_update_timer_handle, osc_update_time
    osc_update_time = time.time()
    osc_update_timer_handle = None
    for message in controls.serialize():
        # print(OSC_ADDRESS_PREFIX + message['address'])
        osc_client.send_message(
            OSC_ADDRESS_PREFIX + message['address'], 
            message['values'],
        )

def debounce_update_osc():
    global osc_update_timer_handle, osc_update_time
    if time.time() - osc_update_time < OSC_UPDATE_DEBOUNCE:
        if osc_update_timer_handle:
            osc_update_timer_handle.cancel()
        loop = asyncio.get_event_loop()
        osc_update_timer_handle = loop.call_later(OSC_UPDATE_DEBOUNCE, update_osc_interface_data)
        return
    update_osc_interface_data()

async def periodic_osc_updates():
    while True:
        update_osc_interface_data()
        await asyncio.sleep(OSC_UPDATE_INTERVAL) 

def osc_handler(client_address, address, *args):
    if client_address[0] in net_helper.ip_list:
        return
    if not address.startswith(OSC_ADDRESS_PREFIX):
        return
    address = address[len(OSC_ADDRESS_PREFIX):]
    #print(f"osc {address}: {args}")
    controls.handle_message(address, args[0])
    debounce_update_osc()

def blocking_artnet():
    wrapper = ClientWrapper()
    client = wrapper.Client()
    client.RegisterUniverse(artnet_universe, client.REGISTER, artnet_data)
    wrapper.Run()

async def main_loop():
    loop = asyncio.get_event_loop()
    loop.create_task(periodic_units_updates())
    loop.create_task(periodic_osc_updates())
    dispatcher = Dispatcher()
    dispatcher.set_default_handler(osc_handler, needs_reply_address=True)
    server = AsyncIOOSCUDPServer((osc_ip, osc_port), dispatcher, loop)
    await server.create_serve_endpoint()  # Create datagram endpoint and start serving
    with concurrent.futures.ThreadPoolExecutor() as pool:
        await loop.run_in_executor(pool, blocking_artnet)
        loop.stop()

def start():
    print('OpenSoundControl server port:', osc_port)
    update_osc_interface_data()
    asyncio.run(main_loop())

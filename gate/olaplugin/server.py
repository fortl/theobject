import asyncio
import concurrent.futures
import time

from ola.ClientWrapper import ClientWrapper
from pythonosc.osc_server import AsyncIOOSCUDPServer
from pythonosc.dispatcher import Dispatcher
from pythonosc.udp_client import SimpleUDPClient

import olaplugin.theobject as theobject
import olaplugin.net_helper as net_helper
import olaplugin.interface as interface
from olaplugin.routes import setup_routes
from olaplugin.captive_portal import captive_portal

BASE_DIR = pathlib.Path(__file__).parent
OSC_UPDATE_INTERVAL = 2
OSC_ADDRESS_PREFIX = '/theobject/'
OSC_UPDATE_DEBOUNCE = .2
osc_port = 9000
osc_client_ip = '255.255.255.255'
osc_client_port = 9000
osc_clients = []
for i in net_helper.interfaces: 
    osc_client = SimpleUDPClient(osc_client_ip, osc_client_port, allow_broadcast=True)
    osc_client._sock.setsockopt(socket.SOL_SOCKET, 25, str(i + '\0').encode('utf-8'))
    osc_clients.append(osc_client)
osc_ip = '0.0.0.0'
osc_update_timer_handle = None
osc_update_time = time.time()
artnet_universe = 1

def update_units():
    theobject.set_leds(interface.get_units())

async def periodic_units_updates():
    while True:
        update_units()
        await asyncio.sleep(.02)

def artnet_data(data):
    interface.artnet_channel.set_data(data)

def send_osc_feedback(osc_feedback):
    for osc_client in osc_clients:
        for message in osc_feedback.messages:
            osc_client.send_message(
                OSC_ADDRESS_PREFIX + message['address'], 
                message['values'],
            )

def debounce_messages_osc(osc_feedback):
    global osc_update_timer_handle, osc_update_time
    if time.time() - osc_update_time < OSC_UPDATE_DEBOUNCE:
        if osc_update_timer_handle:
            osc_update_timer_handle.cancel()
        loop = asyncio.get_event_loop()
        osc_update_timer_handle = loop.call_later(OSC_UPDATE_DEBOUNCE, debounce_messages_osc, osc_feedback)
        return
    osc_update_time = time.time()
    osc_update_timer_handle = None
    send_osc_feedback(osc_feedback)

async def periodic_osc_updates():
    while True:
        send_osc_feedback(interface.serialize())
        await asyncio.sleep(OSC_UPDATE_INTERVAL) 

def osc_handler(client_address, address, *args):
    if client_address[0] in net_helper.ip_list:
        return
    if not address.startswith(OSC_ADDRESS_PREFIX):
        return
    address = address[len(OSC_ADDRESS_PREFIX):]
    # print(f"osc {address}: {args}")
    osc_feedback = interface.handle_message(address, args[0])
    if osc_feedback:
        debounce_messages_osc(osc_feedback)

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
    send_osc_feedback(interface.serialize())
    asyncio.run(main_loop())

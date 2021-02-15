import time
import pathlib
import asyncio
import socket
import concurrent.futures
from concurrent.futures import thread
import atexit
from aiohttp import web
import aiohttp_jinja2
import jinja2
import OPi.GPIO as GPIO

from ola.ClientWrapper import ClientWrapper
from pythonosc.osc_server import AsyncIOOSCUDPServer
from pythonosc.dispatcher import Dispatcher
from pythonosc.udp_client import SimpleUDPClient

from olaplugin.uart_proxy import uart_proxy
import olaplugin.sound as sound
import olaplugin.net_helper as net_helper
import olaplugin.interface as interface
from olaplugin.routes import setup_routes
from olaplugin.captive_portal import captive_portal
from olaplugin.config import config

BASE_DIR = pathlib.Path(__file__).parent

class TheObjectServer:
    def __init__(self):
        self.osc_update_timer_handle = None
        self.osc_update_time = time.time()         
        self.osc_clients = []
        self.osc_server_transport = None
        self.tasks = {}
        self.artnet_pool_executor = None

    def reconnect_osc_clients(self):
        self.osc_clients = []
        for i in net_helper.interfaces: 
            osc_client = SimpleUDPClient(
                config['osc']['client']['ip'], config['osc']['client']['port'], 
                allow_broadcast=True)
            osc_client._sock.setsockopt(socket.SOL_SOCKET, 25, str(i + '\0').encode('utf-8'))
            self.osc_clients.append(osc_client)

    def artnet_worker(self):
        wrapper = ClientWrapper()
        client = wrapper.Client()
        client.RegisterUniverse(config['artnet']['universe'], client.REGISTER, 
            lambda: self.artnet_data())
        wrapper.Run()

    def update_units(self):
        uart_proxy.set_leds(interface.get_units())

    async def periodic_units_updates(self):
        while True:
            self.update_units()
            await asyncio.sleep(config['leds']['update_interval'])

    def artnet_data(self, data):
        interface.artnet_channel.set_data(data)

    def handle_sound_data(self, timeline, average):
        interface.sound_reactive_effect.set_data(timeline, average)

    def send_osc_feedback(self, osc_feedback):
        for osc_client in self.osc_clients:
            for message in osc_feedback.messages:
                osc_client.send_message(
                    config['osc']['address_prefix'] + message['address'], 
                    message['values'],
                )

    def debounce_messages_osc(self, osc_feedback):
        if time.time() - self.osc_update_time < config['osc']['update_debounce']:
            if self.osc_update_timer_handle:
                self.osc_update_timer_handle.cancel()
            loop = asyncio.get_event_loop()
            self.osc_update_timer_handle = loop.call_later(
                config['osc']['update_debounce'], 
                lambda: self.debounce_messages_osc(osc_feedback))
            return
        self.osc_update_time = time.time()
        self.osc_update_timer_handle = None
        self.send_osc_feedback(osc_feedback)

    async def periodic_osc_updates(self):
        while True:
            self.send_osc_feedback(interface.serialize())
            await asyncio.sleep(config['osc']['update_interval_seconds']) 

    def osc_handler(self, client_address, address, *args):
        osc_prefix = config['osc']['address_prefix']
        if client_address[0] in net_helper.ip_list:
            return
        if not address.startswith(osc_prefix):
            return
        address = address[len(osc_prefix):]
        # print(f"osc {address}: {args}")
        osc_feedback = interface.handle_message(address, args[0])
        if osc_feedback:
            self.debounce_messages_osc(osc_feedback)

    async def start_osc_service(self):
        loop = asyncio.get_event_loop()
        self.tasks['unit_updates'] = loop.create_task(self.periodic_units_updates())
        self.tasks['osc_updates']  = loop.create_task(self.periodic_osc_updates())
        dispatcher = Dispatcher()
        dispatcher.set_default_handler(
            lambda client, address, *args: self.osc_handler(client, address, *args), 
            needs_reply_address=True)
        updserver = AsyncIOOSCUDPServer(
            (config['osc']['ip'], config['osc']['port']), dispatcher, loop)
        self.osc_server_transport, protocol = await updserver.create_serve_endpoint()

    def start_artnet_service(self):
        loop = asyncio.get_event_loop()
        self.artnet_pool_executor = concurrent.futures.ThreadPoolExecutor()
        self.tasks['artnet'] = loop.run_in_executor(
            self.artnet_pool_executor, lambda: self.artnet_worker())

    async def listen_to_uart(self):
        loop = asyncio.get_event_loop()
        await uart_proxy.connect()
        self.tasks['read_uart_proxy'] = loop.create_task(uart_proxy.read())

    def start_sound_processor(self):
        loop = asyncio.get_event_loop()
        pool = concurrent.futures.ThreadPoolExecutor()
        self.tasks['sound_processor'] = loop.run_in_executor(
            pool, sound.start_analize(lambda timeline, average: self.handle_sound_data(timeline, average)))        

    def enable_uart_proxy(self):
        GPIO.setwarnings(False)
        GPIO.setboard(GPIO.ZEROPLUS)
        GPIO.setmode(GPIO.BOARD)
        pin = config['uart_proxy']['enable_pin']
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.HIGH)

    def disable_uart_proxy(self):
        GPIO.output(config['uart_proxy']['enable_pin'], GPIO.LOW)

    def update_osc_interface(self):
        self.send_osc_feedback(interface.serialize())

    async def start(self, app):
        atexit.unregister(concurrent.futures.thread._python_exit)
        self.enable_uart_proxy()
        self.reconnect_osc_clients()
        self.send_osc_feedback(interface.serialize())
        self.start_artnet_service()
        self.start_sound_processor()
        await asyncio.gather(
            self.listen_to_uart(),
            self.start_osc_service(),
        )

    async def stop(self, app):
        self.disable_uart_proxy()
        self.osc_server_transport.close()
        for task in self.tasks.values():
            task.cancel()
        uart_proxy.close()
        self.artnet_pool_executor.shutdown(wait=False)
 
def run():
    server = TheObjectServer()
    uart_proxy.set_observe_any(lambda: server.update_osc_interface())
    webapp = web.Application(middlewares=[captive_portal])
    setup_routes(webapp, BASE_DIR)
    aiohttp_jinja2.setup(webapp,
        loader=jinja2.FileSystemLoader(str(BASE_DIR  / 'templates')))

    webapp.on_startup.append(server.start)
    webapp.on_shutdown.append(server.stop)
    web.run_app(webapp, port=80)
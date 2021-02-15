import asyncio
import serial_asyncio
import time
import sys
from array import array
import errno

SERIAL_PORT = '/dev/ttyS2'
LED_COUNT = 20
PACKAGE_SIZE = LED_COUNT+2 # cdm + leds + null
PACKAGE_CMD_LEDS_VALUES = 100
THROTTLE_INTERVAL = 0.01

class UARTProxy:
    def __init__(self, url=SERIAL_PORT, baudrate=19200):
        self.url = url
        self.baudrate = baudrate
        self.throttle_time = 0
        self.r = None
        self.w = None
        self.observer_encoder = None
        self.observer_encoder_pushed = None
        self.observer_button = None
        self.observer_any = None

    def set_observe_any(self, observer):
        self.observer_any = observer

    def set_observe_encoder(self, observer_encoder):
        self.observer_encoder = observer_encoder

    def set_observe_encoder_pushed(self, observer_encoder_pushed):
        self.observer_encoder_pushed = observer_encoder_pushed

    def set_observe_button(self, observer_button):
        self.observer_button = observer_button

    async def connect(self):
        self.r, self.w = await serial_asyncio.open_serial_connection(
                                url=self.url, baudrate=self.baudrate)

    def close(self):
        self.w.close()

    def set_leds(self, leds):
        current_time = time.time()
        if (current_time - self.throttle_time < THROTTLE_INTERVAL):
            return
        self.throttle_time = current_time
        self.send_package(leds)

    def send_package(self, leds):
        buf = bytearray([0] * PACKAGE_SIZE)
        buf[0] = PACKAGE_CMD_LEDS_VALUES
        for led in range(0, LED_COUNT):
            led_value = leds[led]
            led_value = led_value + 1 if led_value <= 254 else led_value
            buf[1+led] = led_value
        self.w.write(buf)

    async def read(self):
        while True:
            msg = await self.r.readuntil(b'\0')
            if msg[0] == 65:
                self.handle_update_message(msg)
    
    def handle_update_message(self, msg):
        if msg[2] == 2 and self.observer_button:
            self.observer_button()
        if msg[3] != 64:
            encoder_diff = msg[3]-64
            if msg[1] == 1:
                if self.observer_encoder_pushed:
                    self.observer_encoder_pushed(encoder_diff)  
            else:
                if self.observer_encoder:
                    self.observer_encoder(encoder_diff)
        if self.observer_any:
            self.observer_any()

uart_proxy = UARTProxy()

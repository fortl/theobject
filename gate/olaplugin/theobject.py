import serial
import time
import sys
from array import array

SERIAL_PORT = '/dev/ttyS2'
GROUPS_COUNT = 5
GROUP_SIZE = 4
LED_COUNT = 20
PACKAGE_SIZE = 2 + GROUP_SIZE # (group address + summ) + leds values + null
THROTTLE_INTERVAL = .070

throttle_time = time.time()
leds_serial = serial.Serial(SERIAL_PORT, 19200)

def set_leds(leds):
    global throttle_time

    current_time = time.time()
    if (current_time - throttle_time < THROTTLE_INTERVAL):
        return
    throttle_time = current_time

    for group_id in range(0, GROUPS_COUNT):
        buf = bytearray([0] * PACKAGE_SIZE)
        for led in range(0, GROUP_SIZE):
            led_value = leds[group_id * GROUP_SIZE + led]
            led_value = led_value + 1 if led_value <= 254 else led_value
            buf[1+led] = led_value
            buf[0] ^= led_value
        buf[0] = (buf[0] & 0x0f) ^ (buf[0] >> 4)
        buf[0] |= (group_id << 4) | 0x80
        leds_serial.write(buf)
        leds_serial.flush()

def strobescope():
    value = 0
    while True:
        leds = array('B', [value] * LED_COUNT)
        set_leds(leds)
        if value == 0:
            value = 255
        else:
            value = 0

def blackout():
    set_leds(array('B', [0] * LED_COUNT))

# ledsSerial.close()

import serial
import time
import sys
from array import array
from ola.ClientWrapper import ClientWrapper

SERIAL_PORT = '/dev/ttyS2'
GROUPS_COUNT = 5
GROUP_SIZE = 4
LED_COUNT = 20
PACKAGE_SIZE = 2 + GROUP_SIZE # (group address + summ) + leds values + null
THROTTLE_INTERVAL = .070

throttleTime = time.time()
ledsSerial = serial.Serial(SERIAL_PORT, 19200)

def setLeds(leds):
    for groupId in range(0, GROUPS_COUNT):
        buf = bytearray([0] * PACKAGE_SIZE)
        for led in range(0, GROUP_SIZE):
            ledValue = leds[groupId * GROUP_SIZE + led]
            ledValue = ledValue + 1 if ledValue <= 254 else ledValue
            buf[1+led] = ledValue
            buf[0] ^= ledValue
        buf[0] = (buf[0] & 0x0f) ^ (buf[0] >> 4)
        buf[0] |= (groupId << 4) | 0x80
        ledsSerial.write(buf)
        ledsSerial.flush()

def ArtnetData(data):
    global throttleTime

    currentTime = time.time()
    if (currentTime - throttleTime > THROTTLE_INTERVAL):
        throttleTime = time.time()
        setLeds(data)

def strobescope():
    value = 0
    while True:
        leds = array('B', [value] * LED_COUNT)
        setLeds(leds)
        if value == 0:
            value = 255
        else:
            value = 0

# sys.argv[1]

universe = 1;
wrapper = ClientWrapper()
client = wrapper.Client()
client.RegisterUniverse(universe, client.REGISTER, ArtnetData)
wrapper.Run()

ledsSerial.close()

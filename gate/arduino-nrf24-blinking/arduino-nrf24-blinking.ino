
#include <SPI.h>
#include "RF24.h"

#define CE_PIN 9 
#define CSN_PIN 10

#define LED_COUNT 20
#define LED_GROUPS_COUNT 5
#define GROUPS_ITEMS 4
#define WAVE_SPEED 16

struct package
{
  uint8_t address;
  uint8_t values[GROUPS_ITEMS];
};

uint8_t leds[LED_COUNT];
unsigned long waveUpdate = 0;
RF24 radio(CE_PIN, CSN_PIN);
/**********************************************************/

const uint64_t pipeOut = 0xE8E8F0F0E1LL;
int value = 0;

void setTheObjectLedLine (uint8_t * data) {
  for (uint8_t groupId = 0; groupId < LED_GROUPS_COUNT; groupId++) {
    struct package buffer;
    buffer.address = groupId << 4 | 0x08;
    for (uint8_t i = 0; i < GROUPS_ITEMS; i++) {  
      uint8_t value = data[i + GROUPS_ITEMS * groupId];
      buffer.values[i] = value >= 254 ? 255 : (1 + value);
    }
//    radio.writeFast(&buffer, sizeof(buffer));
    
    radio.write(&buffer, sizeof(struct package));
  }
//  radio.txStandBy();
}

void setup() {  
  radio.begin();
//  radio.setPALevel(RF24_PA_LOW);  
  radio.setAutoAck(false);
  radio.setDataRate(RF24_2MBPS);
  radio.openWritingPipe(pipeOut);
  for (char i = 0; i < LED_COUNT; i++) {
    leds[i] = abs(i - 10)*10;
  }
}

void loop() {
  unsigned long currentMillis = millis();
  if ( currentMillis - waveUpdate > WAVE_SPEED ) {
    unsigned char swapByte = leds[0];
    for (char i = 1; i < LED_COUNT; i++) {
      leds[i-1] = leds[i];
    }
    leds[LED_COUNT-1] = swapByte;
    waveUpdate = currentMillis;
  }
  setTheObjectLedLine(leds);
} 

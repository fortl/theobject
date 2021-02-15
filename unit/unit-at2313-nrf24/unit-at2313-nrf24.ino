#include "RF24.h"

#define CE_PIN 12 
#define CSN_PIN 13
#define LED_PIN 11

#define ADDRESS 0

#define LED_COUNT 20
#define LED_GROUPS_COUNT 5
#define GROUPS_ITEMS 4
#define WAVE_SPEED 16

#define GROUP_SIZE 4
#define GROUP_ID (byte)(ADDRESS/GROUP_SIZE)
#define LOCAL_GROUP_ADDRESS (ADDRESS % GROUP_SIZE)

struct package
{
  uint8_t address;
  uint8_t values[GROUPS_ITEMS];
};

RF24 radio(CE_PIN, CSN_PIN);
const uint64_t pipeIn = 0xE8E8F0F0E1LL;
unsigned long payload = 0;
uint8_t value = 1;

void setup() {
  // Setup and configure rf radio
  analogWrite(LED_PIN, value);
  radio.begin(); // Start up the radio
  radio.setDataRate(RF24_2MBPS);
  radio.setAutoAck(false); // Ensure autoACK is enabled
  radio.openReadingPipe(1, pipeIn); // Read on pipe 1 for device address '1Node'
  radio.startListening(); // Start listening
}

void loop(void){
  unsigned long started_waiting_at = micros(); // Set up a timeout period, get the current microseconds

  while ( !radio.available() ){ // While nothing is received
    if (micros() - started_waiting_at > 1000000 ){ // If waited longer than 1s, fade
      value = int((value*10+1)/11);
      if (value == 0) value = 1;
      analogWrite(LED_PIN, value);
      delay(100);
    }
  }

  struct package buffer; // Grab the response, compare, and send to debugging spew
  radio.read( &buffer, sizeof(struct package) );
  if( ((buffer.address >> 4) & 0x07) == GROUP_ID ) {
    value = buffer.values[LOCAL_GROUP_ADDRESS]-1;
    analogWrite(LED_PIN, value);
  }
}

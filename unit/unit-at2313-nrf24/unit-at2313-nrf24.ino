#include "RF24.h"

#define CE_PIN 12 
#define CSN_PIN 13
#define LED_PIN 11

#define ADDRESS 14

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

void setup() {
  // Setup and configure rf radio
  radio.begin(); // Start up the radio
  radio.setDataRate(RF24_2MBPS);
  radio.setAutoAck(false); // Ensure autoACK is enabled
  radio.openReadingPipe(1, pipeIn); // Read on pipe 1 for device address '1Node'
  radio.startListening(); // Start listening
}

void loop(void){
  unsigned long started_waiting_at = micros(); // Set up a timeout period, get the current microseconds
  boolean timeout = false; // Set up a variable to indicate if a response was received or not

  while ( !radio.available() ){ // While nothing is received
    if (micros() - started_waiting_at > 200000 ){ // If waited longer than 200ms, indicate timeout and exit while loop
      timeout = true;
      break;
    }

  }
  if ( !timeout ){ // Describe the results
    struct package buffer; // Grab the response, compare, and send to debugging spew
    radio.read( &buffer, sizeof(struct package) );
    if( ((buffer.address >> 4) & 0x07) == GROUP_ID ) {
      uint8_t value = buffer.values[LOCAL_GROUP_ADDRESS]-1;
      analogWrite(LED_PIN, value);
    }
  }
}

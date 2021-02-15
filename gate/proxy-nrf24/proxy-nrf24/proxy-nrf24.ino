
#include <SPI.h>
#include "RF24.h"
#include "qdec.h"

#define CE_PIN 8 
#define CSN_PIN 10

#define LED_COUNT 20
#define LED_GROUPS_COUNT 5
#define GROUPS_ITEMS 4

#define PACKAGE_CMD_LEDS_VALUES 100

typedef enum
{
  lfo = 0x00,
  light = 0x01,
} modes;

struct encoder
{
  uint16_t value;
  uint16_t minValue;  
  uint16_t maxValue;
  uint8_t step;
};

struct ledsPackage
{
  uint8_t address;
  uint8_t values[GROUPS_ITEMS];
};

const int ROTARY_PIN_A = 2; // the first pin connected to the rotary encoder
const int ROTARY_PIN_B = 3; // the second pin connected to the rotary encoder
const int ROTARY_BUTTON_PIN = 4; // the button pin connected to the rotary encoder
const int MODE_BUTTON_PIN = 6; 
const int PROXY_MODE_PIN = 7; 
const int BUTTONS_DEBOUNCE_MS = 50;
const int UPDATE_RATE = 10; // ms per update
const float exponentialScaleR = 31.8975139158; // 255*log10(2)/log10(200)
                                               // see https://diarmuid.ie/blog/pwm-exponential-led-fading-on-arduino-or-other-platforms
                                               
::SimpleHacks::QDecoder qdec(ROTARY_PIN_A, ROTARY_PIN_B, true);

// Stores a relative value based on the clockwise / counterclockwise events
volatile encoder master = { 255, 0, 255, 5 };
volatile encoder waveSpeed = { 32, 1, 255, 1 };
const uint16_t generalEncoderZero = 64;
volatile encoder generalEncoder = { generalEncoderZero, 0, generalEncoderZero*2-1, 1 };
volatile encoder *currentEncoder = &master;
// Used in loop() function to track the value of rotaryCount from the
// prior time that loop() executed (to detect changes in the value)
int lastLoopDisplayedRotaryCount = 0;

uint8_t leds[LED_COUNT];
uint8_t wave[LED_COUNT];
unsigned long waveUpdate = 0;
unsigned long ledsUpdate = 0;
unsigned long buttonDebounce = 0;
int buttonState = LOW;
int lastButtonState = LOW;

bool proxyInitiated = false;
uint8_t buffer[LED_COUNT+2];
char bufferIndex = 0;

unsigned long currentMillis;
modes currentMode = light;
RF24 radio(CE_PIN, CSN_PIN);
/**********************************************************/

const uint64_t pipeOut = 0xE8E8F0F0E1LL;
int value = 0;

void IsrForQDEC(void) { // do absolute minimum possible in any ISR ...
  // placing the `using namespace` line into a function limits
  // allows accessing the types and functions of that namespace,
  // but only while in this function.
  using namespace ::SimpleHacks;
  QDECODER_EVENT event = qdec.update();
  if (event & QDECODER_EVENT_CW) {
    if (currentEncoder->value + currentEncoder->step <= currentEncoder->maxValue) 
      currentEncoder->value += currentEncoder->step;
  } else if (event & QDECODER_EVENT_CCW) {
    if (currentEncoder->value - currentEncoder->step >= currentEncoder->minValue) 
      currentEncoder->value -= currentEncoder->step;
  }
  return;
}

void setTheObjectLedLine (uint8_t * data) {
  for (uint8_t groupId = 0; groupId < LED_GROUPS_COUNT; groupId++) {
    struct ledsPackage buffer;
    buffer.address = groupId << 4 | 0x08;
    for (uint8_t i = 0; i < GROUPS_ITEMS; i++) {  
      uint8_t value = data[i + GROUPS_ITEMS * groupId]*master.value/255;
      value = int(value + pow(2, value/exponentialScaleR) - 1)/2;
      buffer.values[i] = value >= 254 ? 255 : (1 + value);
    }
    radio.writeBlocking(&buffer, sizeof(buffer), 1);  // Writes 1 payload to the buffers
  }
}

void setup() {
  pinMode(ROTARY_BUTTON_PIN, INPUT);
  digitalWrite(ROTARY_BUTTON_PIN, HIGH);
  pinMode(MODE_BUTTON_PIN, INPUT);
  digitalWrite(MODE_BUTTON_PIN, HIGH);
  pinMode(PROXY_MODE_PIN, INPUT);
  Serial.begin(19200);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }
  radio.begin();
//  radio.setPALevel(RF24_PA_LOW);
  radio.setAutoAck(false);
  radio.setDataRate(RF24_2MBPS);
  radio.openWritingPipe(pipeOut);
  radio.stopListening();
  qdec.begin();

  // attach an interrupts to each pin, firing on any change in the pin state
  // no more polling for state required!
  attachInterrupt(digitalPinToInterrupt(ROTARY_PIN_A), IsrForQDEC, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ROTARY_PIN_B), IsrForQDEC, CHANGE);
  for (char i = 0; i < LED_COUNT; i++) {
    wave[i] = abs(i - 10)*10;
    leds[i] = 255;
  }
}

void makeAWave() {
  if (currentMillis - waveUpdate > waveSpeed.value) {
    unsigned char swapByte = wave[0];
    for (char i = 1; i < LED_COUNT; i++) {
      wave[i-1] = wave[i];
    }
    wave[LED_COUNT-1] = swapByte;
    waveUpdate = currentMillis;
  }
}

void sendButtonsStatus(const uint16_t encoderDiff, const bool buttonClicked) {
  uint8_t buf[5] = {'A', 
    digitalRead(ROTARY_BUTTON_PIN)?2:1, 
    buttonClicked?2:1, 
    (uint8_t)(encoderDiff & 0xFF),
    0};
  Serial.write(buf, 5);
}

void proxy(const bool buttonClicked) {
  currentEncoder = &generalEncoder;
  if ( generalEncoder.value != generalEncoderZero ) {
    sendButtonsStatus(generalEncoder.value, buttonClicked);
    generalEncoder.value = generalEncoderZero;
  } else if (buttonClicked) {
    sendButtonsStatus(generalEncoderZero, buttonClicked);
  }
  
  while (Serial.available() > 0) {
    uint8_t c = Serial.read(); 
    buffer[bufferIndex++] = c;
    if ((c == '\0') || (bufferIndex == LED_COUNT+2)) {
      if( proxyInitiated
        && (bufferIndex == LED_COUNT+2)
        && (buffer[0] == PACKAGE_CMD_LEDS_VALUES) 
      ) {
        for (char i = 0; i < LED_COUNT; i++) {
          leds[i] = buffer[i+1]-1;
        }
        setTheObjectLedLine(leds);
        analogWrite(5, leds[1]);
      }
      bufferIndex = 0;
    }
  }
}

void interface(const bool buttonClicked) {
  modes lastMode = currentMode;
  if (buttonClicked) {
    currentMode = currentMode == light ? lfo : light;
  }
  
  if (digitalRead(ROTARY_BUTTON_PIN)) {
    currentEncoder = &master;
  }else{
    currentEncoder = &waveSpeed;
  }
  
  if (lastMode != currentMode) {
      // Init mode 
    if (currentMode == light) {
      for (char i = 0; i < LED_COUNT; i++) {
        leds[i] = 255;
      }
    } 
  }
    
  if (currentMode == lfo) {
    makeAWave();
    for (char i = 0; i < LED_COUNT; i++) {
      leds[i] = wave[i];
    }
  }
  
  if (currentMillis - ledsUpdate > UPDATE_RATE) {
    analogWrite(5,int(leds[1]*master.value/255));
    ledsUpdate = currentMillis;
    setTheObjectLedLine(leds);
  }
}

void loop() {
  bool buttonClicked = false;
  currentMillis = millis();

  proxyInitiated = digitalRead(PROXY_MODE_PIN);

  int readingButton = digitalRead(MODE_BUTTON_PIN);
  if (readingButton != lastButtonState) {
    buttonDebounce = currentMillis;
  }
  if ((currentMillis - buttonDebounce) > BUTTONS_DEBOUNCE_MS) {
    if (readingButton != buttonState) {
      buttonState = readingButton;
      if (buttonState == LOW) {
        buttonClicked = true;
      }
    }
  }
  lastButtonState = readingButton;
  
  if (proxyInitiated) {
    proxy(buttonClicked);
  } else {
    interface(buttonClicked);
  }
} 

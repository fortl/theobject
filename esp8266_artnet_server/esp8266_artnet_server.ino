/*
  This sketch receives Art-Net data of one DMX universes over WiFi
  and sends it over the serial interface to a MAX485 module.

  It provides an interface between wireless Art-Net and wired DMX512.

*/

#include <ESP8266WiFi.h>         // https://github.com/esp8266/Arduino
#include <ESP8266WebServer.h>
#include <ESP8266mDNS.h>
#include <WiFiManager.h>         // https://github.com/tzapu/WiFiManager
#include <WiFiClient.h>
#include <ArtnetWifi.h>          // https://github.com/rstephan/ArtnetWifi
#include <FS.h>

#include "setup_ota.h"
#include "send_break.h"

//#define THEOBJECT_SUMM_BYTES 10
#define THEOBJECT_LED_COUNT 20
#define THEOBJECT_LED_GROUPS_COUNT 5
#define THEOBJECT_GROUP_SIZE 4
#define THEOBJECT_PACKAGE_SIZE  1 + THEOBJECT_GROUP_SIZE + 1 // address|summ + LEDS + null
#define ENABLE_THEOBJECT

//#define ENABLE_SERIAL_DEBUG
#ifdef ENABLE_SERIAL_DEBUG
# define SERIAL_DEBUG(x)   { Serial.print(x); }
# define SERIAL_DEBUGLN(x)   { Serial.println(x); }
# define SERIAL_DEBUGLN_ Serial.println();
#else
# define SERIAL_DEBUG(x)   
# define SERIAL_DEBUGLN(x)
# define SERIAL_DEBUGLN_ 
#endif

#define MIN(x,y) (x<y ? x : y)
#define ENABLE_MDNS
#define ENABLE_WEBINTERFACE
#define COMMON_ANODE

Config config;
ESP8266WebServer server(80);
const char* host = "ARTNET";
const char* version = __DATE__ " / " __TIME__;

#define LED_B 16  // GPIO16/D0
#define LED_G 4   // GPIO05/D1
#define LED_R 5   // GPIO04/D2

#define TEST_MODE_PIN 12 // D6
#define WAVE_MODE_PIN 13 // D7
#define POTENTIOMETER A0

// Artnet settings
ArtnetWifi artnet;
unsigned long packetCounter = 0, frameCounter = 0;
float fps = 0;

unsigned char ledsTheObject[THEOBJECT_LED_COUNT];
bool testMode = false;
bool waveMode = false;
unsigned long waveModeUpdate = 0;

// Global universe buffer
struct {
  uint16_t universe;
  uint16_t length;
  uint8_t sequence;
  uint8_t *data;
} global;

// keep track of the timing of the function calls
long tic_loop = 0, tic_fps = 0, tic_packet = 0, tic_web = 0;

/* void setTheObjectLedLine (uint8_t * data) {
  uint8_t buffer[THEOBJECT_LED_COUNT + THEOBJECT_SUMM_BYTES + 1];
  for (uint8_t i = 0; i < THEOBJECT_LED_COUNT; i++) {
    buffer[i] = data[i] >= 254 ? 255 : (1 + data[i]);
  }
  for (uint8_t i = 0; i < THEOBJECT_SUMM_BYTES; i++) {
    uint8_t summ = 0;
    for (uint8_t j = 0; j < (THEOBJECT_LED_COUNT/THEOBJECT_SUMM_BYTES); j++)
      summ ^= buffer[i*(THEOBJECT_LED_COUNT/THEOBJECT_SUMM_BYTES) + j];
    buffer[THEOBJECT_LED_COUNT+i] = summ | 1;
  }
  
  buffer[THEOBJECT_LED_COUNT + THEOBJECT_SUMM_BYTES] = 0;
   
  Serial.write(buffer, THEOBJECT_LED_COUNT + THEOBJECT_SUMM_BYTES + 1);
}*/

void setTheObjectLedLine (uint8_t * data) {
  for (uint8_t groupId = 0; groupId < THEOBJECT_LED_GROUPS_COUNT; groupId++) {
    uint8_t buffer[THEOBJECT_PACKAGE_SIZE];
    uint8_t summ = 0;
    buffer[0] = groupId << 4 | 0x80;
    for (uint8_t i = 0; i < THEOBJECT_GROUP_SIZE; i++) {  
      uint8_t value = data[i + THEOBJECT_GROUP_SIZE * groupId];
      buffer[i+1] = value >= 254 ? 255 : (1 + value);
      summ ^= buffer[i+1];
    }
    buffer[0] |= (summ & 0x0f) ^ (summ >> 4);
    buffer[THEOBJECT_PACKAGE_SIZE - 1] = 0;   
    Serial.write(buffer, THEOBJECT_PACKAGE_SIZE);
  }
}

//this will be called for each UDP packet received
void onDmxPacket(uint16_t universe, uint16_t length, uint8_t sequence, uint8_t * data) {
  // print some feedback
  packetCounter++;
  SERIAL_DEBUG("packetCounter = ");
  SERIAL_DEBUG(packetCounter);
  if ((millis() - tic_fps) > 1000 && frameCounter > 100) {
    // don't estimate the FPS too frequently
    fps = 1000 * frameCounter / (millis() - tic_fps);
    tic_fps = millis();
    frameCounter = 0;
    SERIAL_DEBUG(",  FPS = ");
    SERIAL_DEBUG(fps);
  }
  SERIAL_DEBUGLN_;

  if (universe == config.universe) {
    // copy the data from the UDP packet over to the global universe buffer
    global.universe = universe;
    global.sequence = sequence;
    if (length < 512)
      global.length = length;      

    for (int i = 0; i < global.length; i++)
      global.data[i] = data[i];
  }
} // onDmxpacket


void setup() {
  Serial1.begin(250000, SERIAL_8N2);

#ifdef ENABLE_SERIAL_DEBUG
  Serial.begin(115200);
  while (!Serial) {;}
#endif
  SERIAL_DEBUGLN("setup starting");

#ifdef ENABLE_THEOBJECT
  Serial.begin(19200);
  while (!Serial) {;}
#endif

  pinMode(LED_R, OUTPUT);
  pinMode(LED_G, OUTPUT);
  pinMode(LED_B, OUTPUT);

  pinMode(TEST_MODE_PIN, INPUT_PULLUP);
  pinMode(WAVE_MODE_PIN, INPUT_PULLUP);

  global.universe = 0;
  global.sequence = 0;
  global.length = 512;
  global.data = (uint8_t *)malloc(512);
  for (int i = 0; i < 512; i++)
    global.data[i] = 0;

  SPIFFS.begin();

  initialConfig();

  if (loadConfig()) {
    singleYellow();
    delay(1000);
  }
  else {
    singleRed();
    delay(1000);
  }

  if (WiFi.status() != WL_CONNECTED)
    singleRed();

  WiFiManager wifiManager;
  // wifiManager.resetSettings();
  wifiManager.setDebugOutput(false);
  WiFi.hostname(host);
  wifiManager.setAPStaticIPConfig(IPAddress(192, 168, 1, 1), IPAddress(192, 168, 1, 1), IPAddress(255, 255, 255, 0));
  wifiManager.autoConnect(host);
  SERIAL_DEBUGLN("connected");

  if (WiFi.status() == WL_CONNECTED)
    singleGreen();

#ifdef ENABLE_WEBINTERFACE
  // this serves all URIs that can be resolved to a file on the SPIFFS filesystem
  server.onNotFound(handleNotFound);

  server.on("/", HTTP_GET, []() {
    tic_web = millis();
    handleRedirect("/index");
  });

  server.on("/index", HTTP_GET, []() {
    tic_web = millis();
    handleStaticFile("/index.html");
  });

  server.on("/defaults", HTTP_GET, []() {
    tic_web = millis();
    SERIAL_DEBUGLN("handleDefaults");
    handleStaticFile("/reload_success.html");
    delay(2000);
    singleRed();
    initialConfig();
    saveConfig();
    WiFiManager wifiManager;
    wifiManager.resetSettings();
    WiFi.hostname(host);
    ESP.restart();
  });

  server.on("/reconnect", HTTP_GET, []() {
    tic_web = millis();
    SERIAL_DEBUGLN("handleReconnect");
    handleStaticFile("/reload_success.html");
    delay(2000);
    singleRed();
    WiFiManager wifiManager;
    wifiManager.setAPStaticIPConfig(IPAddress(192, 168, 1, 1), IPAddress(192, 168, 1, 1), IPAddress(255, 255, 255, 0));
    wifiManager.startConfigPortal(host);
    SERIAL_DEBUGLN("connected");
    if (WiFi.status() == WL_CONNECTED)
      singleGreen();
  });

  server.on("/reset", HTTP_GET, []() {
    tic_web = millis();
    SERIAL_DEBUGLN("handleReset");
    handleStaticFile("/reload_success.html");
    delay(2000);
    singleRed();
    ESP.restart();
  });

  server.on("/monitor", HTTP_GET, [] {
    tic_web = millis();
    handleStaticFile("/monitor.html");
  });

  server.on("/hello", HTTP_GET, [] {
    tic_web = millis();
    handleStaticFile("/hello.html");
  });

  server.on("/settings", HTTP_GET, [] {
    tic_web = millis();
    handleStaticFile("/settings.html");
  });

  server.on("/dir", HTTP_GET, [] {
    tic_web = millis();
    handleDirList();
  });

  server.on("/json", HTTP_PUT, [] {
    tic_web = millis();
    handleJSON();
  });

  server.on("/json", HTTP_POST, [] {
    tic_web = millis();
    handleJSON();
  });

  server.on("/json", HTTP_GET, [] {
    tic_web = millis();
    DynamicJsonDocument root(300);
    CONFIG_TO_JSON(universe, "universe");
    CONFIG_TO_JSON(channels, "channels");
    CONFIG_TO_JSON(delay, "delay");
    root["version"] = version;
    root["uptime"]  = long(millis() / 1000);
    root["packets"] = packetCounter;
    root["fps"]     = fps;
    String str;
    serializeJson(root, str);
    server.send(200, "application/json", str);
  });

  server.on("/update", HTTP_GET, [] {
    tic_web = millis();
    handleStaticFile("/update.html");
  });

  server.on("/update", HTTP_POST, handleUpdate1, handleUpdate2);

  // start the web server
  server.begin();
#endif

  // announce the hostname and web server through zeroconf
#ifdef ENABLE_MDNS
  MDNS.begin(host);
  MDNS.addService("http", "tcp", 80);
#endif

  artnet.begin();
  artnet.setArtDmxCallback(onDmxPacket);

  // initialize all timers
  tic_loop   = millis();
  tic_packet = millis();
  tic_fps    = millis();
  tic_web    = 0;

  waveModeUpdate = millis();

  SERIAL_DEBUGLN("setup done");
} // setup

void loop() {
  server.handleClient();

  testMode = (digitalRead(TEST_MODE_PIN) == LOW) ? true : false;
  if (testMode && (digitalRead(WAVE_MODE_PIN) == LOW)) {
    unsigned long currentMillis = millis();
    int waveSpeed = analogRead(POTENTIOMETER)/4;
    if (!waveMode) {
      for (char i = 0; i < THEOBJECT_LED_COUNT; i++) {
        ledsTheObject[i] = abs(i - 10)*10;
      }
      waveMode = true;
    } else if ( currentMillis - waveModeUpdate > waveSpeed ) {
      unsigned char swapByte = ledsTheObject[0];
      for (char i = 1; i < THEOBJECT_LED_COUNT; i++) {
        ledsTheObject[i-1] = ledsTheObject[i];
      }
      ledsTheObject[THEOBJECT_LED_COUNT-1] = swapByte;
      waveModeUpdate = currentMillis;
    }    
  } else {
    if (testMode) {
      int value = (analogRead(POTENTIOMETER)/4);
      if (value > 255) value = 255;
      for (char i = 0; i < THEOBJECT_LED_COUNT; i++) {
        ledsTheObject[i] = (unsigned char)((ledsTheObject[i] * 7 + value)/8);
      }
    }
    waveMode = false;
  }

  if (WiFi.status() != WL_CONNECTED) {
    singleRed();
    delay(10);
  }
  else if ((millis() - tic_web) < 5000) {
    singleBlue();
    delay(25);
  }
  else  {
    singleGreen();
    artnet.read();
  }

  // this section gets executed at a maximum rate of around 40Hz
  if ((millis() - tic_loop) > config.delay) {
    tic_loop = millis();
    frameCounter++;

    sendBreak();

    setTheObjectLedLine(testMode ? ledsTheObject : global.data); 

    Serial1.write(0); // Start-Byte
    // send out the value of the selected channels (up to 512)
    for (int i = 0; i < MIN(global.length, config.channels); i++) {
      Serial1.write(global.data[i]);
    }
  }

  delay(1);
} // loop


#ifdef COMMON_ANODE

void singleRed() {
  digitalWrite(LED_R, LOW);
  digitalWrite(LED_G, HIGH);
  digitalWrite(LED_B, HIGH);
}

void singleGreen() {
  digitalWrite(LED_R, HIGH);
  digitalWrite(LED_G, LOW);
  digitalWrite(LED_B, HIGH);
}

void singleBlue() {
  digitalWrite(LED_R, HIGH);
  digitalWrite(LED_G, HIGH);
  digitalWrite(LED_B, LOW);
}

void singleYellow() {
  digitalWrite(LED_R, LOW);
  digitalWrite(LED_G, LOW);
  digitalWrite(LED_B, HIGH);
}

void allBlack() {
  digitalWrite(LED_R, HIGH);
  digitalWrite(LED_G, HIGH);
  digitalWrite(LED_B, HIGH);
}

#else

void singleRed() {
  digitalWrite(LED_R, HIGH);
  digitalWrite(LED_G, LOW);
  digitalWrite(LED_B, LOW);
}

void singleGreen() {
  digitalWrite(LED_R, LOW);
  digitalWrite(LED_G, HIGH);
  digitalWrite(LED_B, LOW);
}

void singleBlue() {
  digitalWrite(LED_R, LOW);
  digitalWrite(LED_G, LOW);
  digitalWrite(LED_B, HIGH);
}

void singleYellow() {
  digitalWrite(LED_R, HIGH);
  digitalWrite(LED_G, HIGH);
  digitalWrite(LED_B, LOW);
}

void allBlack() {
  digitalWrite(LED_R, LOW);
  digitalWrite(LED_G, LOW);
  digitalWrite(LED_B, LOW);
}

#endif

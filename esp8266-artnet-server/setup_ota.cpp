#include "setup_ota.h"

extern ESP8266WebServer server;
extern Config config;
extern unsigned long packetCounter;

/***************************************************************************/

static String getContentType(const String& path) {
  if (path.endsWith(".html"))       return "text/html";
  else if (path.endsWith(".htm"))   return "text/html";
  else if (path.endsWith(".css"))   return "text/css";
  else if (path.endsWith(".txt"))   return "text/plain";
  else if (path.endsWith(".js"))    return "application/javascript";
  else if (path.endsWith(".png"))   return "image/png";
  else if (path.endsWith(".gif"))   return "image/gif";
  else if (path.endsWith(".jpg"))   return "image/jpeg";
  else if (path.endsWith(".jpeg"))  return "image/jpeg";
  else if (path.endsWith(".ico"))   return "image/x-icon";
  else if (path.endsWith(".svg"))   return "image/svg+xml";
  else if (path.endsWith(".xml"))   return "text/xml";
  else if (path.endsWith(".pdf"))   return "application/pdf";
  else if (path.endsWith(".zip"))   return "application/zip";
  else if (path.endsWith(".gz"))    return "application/x-gzip";
  else if (path.endsWith(".json"))  return "application/json";
  return "application/octet-stream";
}

/***************************************************************************/


bool initialConfig() {
  config.universe = 1;
  config.channels = 512;
  config.delay = 25;
  return true;
}

bool loadConfig() {
  Serial.println("loadConfig");

  File configFile = SPIFFS.open("/config.json", "r");
  if (!configFile) {
    Serial.println("Failed to open config file");
    return false;
  }

  size_t size = configFile.size();
  if (size > 1024) {
    Serial.println("Config file size is too large");
    return false;
  }

  std::unique_ptr<char[]> buf(new char[size]);
  configFile.readBytes(buf.get(), size);
  configFile.close();

  StaticJsonDocument<300> jsonBuffer;
  DynamicJsonDocument root(1024);
  DeserializationError error = deserializeJson(root, buf.get());
  if (error) {
    Serial.println("Failed to parse config file");
    return false;
  }

  JSON_TO_CONFIG(universe, "universe");
  JSON_TO_CONFIG(channels, "channels");
  JSON_TO_CONFIG(delay, "delay");

  return true;
}

bool saveConfig() {
  Serial.println("saveConfig");
  DynamicJsonDocument root(300);

  CONFIG_TO_JSON(universe, "universe");
  CONFIG_TO_JSON(channels, "channels");
  CONFIG_TO_JSON(delay, "delay");

  File configFile = SPIFFS.open("/config.json", "w");
  if (!configFile) {
    Serial.println("Failed to open config file for writing");
    return false;
  }
  else {
    Serial.println("Writing to config file");
    serializeJson(root, configFile);
    configFile.close();
    return true;
  }
}

/***************************************************************************/

void handleUpdate1() {
  server.sendHeader("Connection", "close");
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.send(200, "text/plain", (Update.hasError()) ? "FAIL" : "OK");
  ESP.restart();
}

void handleUpdate2() {
  HTTPUpload& upload = server.upload();
  if (upload.status == UPLOAD_FILE_START) {
    Serial.setDebugOutput(true);
    WiFiUDP::stopAll();
    Serial.printf("Update: %s\n", upload.filename.c_str());
    uint32_t maxSketchSpace = (ESP.getFreeSketchSpace() - 0x1000) & 0xFFFFF000;
    if (!Update.begin(maxSketchSpace)) { //start with max available size
      Update.printError(Serial);
    }
  } else if (upload.status == UPLOAD_FILE_WRITE) {
    if (Update.write(upload.buf, upload.currentSize) != upload.currentSize) {
      Update.printError(Serial);
    }
  } else if (upload.status == UPLOAD_FILE_END) {
    if (Update.end(true)) { //true to set the size to the current progress
      Serial.printf("Update Success: %u\nRebooting...\n", upload.totalSize);
    } else {
      Update.printError(Serial);
    }
    Serial.setDebugOutput(false);
  }
  yield();
}

void handleDirList() {
  Serial.println("handleDirList");
  String str = "";
  Dir dir = SPIFFS.openDir("/");
  while (dir.next()) {
    str += dir.fileName();
    str += " ";
    str += dir.fileSize();
    str += " bytes\r\n";
  }
  server.send(200, "text/plain", str);
}

void handleNotFound() {
  Serial.println("handleNotFound");
  if (SPIFFS.exists(server.uri())) {
    handleStaticFile(server.uri());
  }
  else {
    String message = "File Not Found\n\n";
    message += "URI: ";
    message += server.uri();
    message += "\nMethod: ";
    message += (server.method() == HTTP_GET) ? "GET" : "POST";
    message += "\nArguments: ";
    message += server.args();
    message += "\n";
    for (uint8_t i = 0; i < server.args(); i++) {
      message += " " + server.argName(i) + ": " + server.arg(i) + "\n";
    }
    server.send(404, "text/plain", message);
  }
}

void handleRedirect(String filename) {
  char buf[64];
  filename.toCharArray(buf, 64);
  handleRedirect(filename);
}

void handleRedirect(const char * filename) {
  Serial.println("handleRedirect");
  server.sendHeader("Location", String(filename), true);
  server.send(302, "text/plain", "");
}

bool handleStaticFile(String path) {
  Serial.println("handleStaticFile");
  String contentType = getContentType(path);            // Get the MIME type
  if (SPIFFS.exists(path)) {                            // If the file exists
    File file = SPIFFS.open(path, "r");                 // Open it
    size_t sent = server.streamFile(file, contentType); // And send it to the client
    file.close();                                       // Then close the file again
    return true;
  }
  Serial.println("\tFile Not Found");
  return false;                                         // If the file doesn't exist, return false
}

bool handleStaticFile(const char * path) {
  return handleStaticFile((String)path);
}

void handleJSON() {
  Serial.println("handleJSON");
  String message = "HTTP Request\n\n";
  message += "URI: ";
  message += server.uri();
  message += "\nMethod: ";
  message += (server.method() == HTTP_GET) ? "GET" : "POST";
  message += "\nArguments: ";
  message += server.args();
  message += "\n";
  for (uint8_t i = 0; i < server.args(); i++) {
    message += " " + server.argName(i) + ": " + server.arg(i) + "\n";
  }
  Serial.println(message);

  // this gets called in response to either a PUT or a POST
  if (server.args() == 1 && server.hasArg("plain")) {
    // parse it as JSON object
    DynamicJsonDocument root(300);
    DeserializationError error = deserializeJson(root, server.arg("plain"));
    if (error) {
      handleStaticFile("/reload_failed.html");
      return;
    }
    JSON_TO_CONFIG(universe, "universe");
    JSON_TO_CONFIG(channels, "channels");
    JSON_TO_CONFIG(delay, "delay");
    handleStaticFile("/reload_success.html");
  }
  else {
    // parse it as key1=val1&key2=val2&key3=val3
    KEYVAL_TO_CONFIG(universe, "universe");
    KEYVAL_TO_CONFIG(channels, "channels");
    KEYVAL_TO_CONFIG(delay, "delay");
    handleStaticFile("/reload_success.html");
  }
  saveConfig();
}

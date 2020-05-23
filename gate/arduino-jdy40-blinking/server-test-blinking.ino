void setup() {
  Serial.begin(19200);
  while (!Serial) {}
}

void setLed (char address, char value) {
  uint8_t summ = address;
  uint8_t data;
  Serial.write(address);
  data = '0' + (value>>4);
  summ = summ ^ data;
  Serial.write(data);
  data = '0' + (value&0x0f);
  summ = summ ^ data;
  Serial.write(data);
  Serial.write('0' + ((summ>>4) ^ (summ&0x0f)));
  Serial.write('\n');
  delay(1);
}

void loop() {
  for( uint8_t i = 0; i < 63; i++){
    setLed('1', i*4);
    setLed('2', 255-(i*4));
    delay(50);
  }
  for( uint8_t i = 63; i > 0; i--){
    setLed('1', i*4);
    setLed('2', 255-(i*4));
    delay(50);
  }
}

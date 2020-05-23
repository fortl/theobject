#include <avr/wdt.h>

#define ADDRESS 14

#define LED_PIN 11
#define SET_PIN 7
#define TXD_PIN 1
//#define ENABLE_UART_DEBUG

#define GROUP_SIZE 4
#define BUFFER_SIZE 1+GROUP_SIZE+1 // groupId|summ + leds + null
#define GROUP_ID (byte)(ADDRESS/GROUP_SIZE)
#define LOCAL_GROUP_ADDRESS (ADDRESS % GROUP_SIZE)

uint8_t buffer[BUFFER_SIZE+1]; // command plus terminating null
char bufferIndex = 0;
boolean ready = false;
uint8_t value = 0;
 
void USART_Init( unsigned int baudrate );
unsigned char USART_Receive( void );
void USART_Transmit( unsigned char data );
 
void setup() {
  pinMode(LED_PIN, OUTPUT);
  pinMode(SET_PIN, OUTPUT);
  digitalWrite(SET_PIN, LOW);
#ifndef ENABLE_UART_DEBUG  
  pinMode(TXD_PIN, OUTPUT);
  digitalWrite(TXD_PIN, HIGH);  
#endif 
  TCCR0B = (1 << CS00); 
  USART_Init( 77 ); 
  wdt_enable(WDTO_2S);
}

void loop() {
  wdt_reset();
  uint8_t c = USART_Receive(); 
  buffer[bufferIndex++] = c;
  if ((c == '\0') || (bufferIndex == BUFFER_SIZE)) {
    if( (bufferIndex == BUFFER_SIZE) && (((buffer[0] >> 4) & 0x07) == GROUP_ID) ) {
      value = buffer[LOCAL_GROUP_ADDRESS+1]-1;
#ifdef ENABLE_UART_DEBUG  
      USART_Transmit(value);
#endif 
      uint8_t summ = 0;
      for (uint8_t i = 0; i < GROUP_SIZE; i++)
        summ ^= buffer[1 + i];
      if( ((summ & 0x0f) ^ (summ >> 4)) == (buffer[0] & 0x0f) )
       analogWrite(LED_PIN, value);
    }
    bufferIndex = 0;
  }
}

void USART_Init( unsigned int baudrate ) {
  UBRRH = (unsigned char) (baudrate>>8);                  
  UBRRL = (unsigned char) baudrate;
  UCSRA = (1<<U2X); 
  UCSRB = ( 1 << RXEN );
#ifdef ENABLE_UART_DEBUG  
  UCSRB |= ( 1 << TXEN );
#endif 
  UCSRC = (1<<USBS) | (3<<UCSZ0);
}

unsigned char USART_Receive( void ) {
  while ( !(UCSRA & (1<<RXC)) ) wdt_reset();
  return UDR;
}
 
void USART_Transmit( unsigned char data ) {
  while ( !(UCSRA & (1<<UDRE)) ) wdt_reset(); 
  UDR = data;         
}

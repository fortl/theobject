#include <avr/wdt.h>

#define ADDRESS 15

#define LED 11
//#define ENABLE_UART_DEBUG

#define TOTAL_COUNT 20
#define SUMM_BYTES 10
#define SUMM_BYTE_NUMBER (byte)(ADDRESS*SUMM_BYTES/TOTAL_COUNT)
#define SUMM_START_BYTE (SUMM_BYTE_NUMBER*TOTAL_COUNT/SUMM_BYTES)
#define BUFFER_SIZE (TOTAL_COUNT+SUMM_BYTES+2)

uint8_t buffer[BUFFER_SIZE+1]; // command plus terminating null
char bufferIndex = 0;
boolean ready = false;
uint8_t value = 0;
 
void USART_Init( unsigned int baudrate );
unsigned char USART_Receive( void );
void USART_Transmit( unsigned char data );
 
void setup() {
  pinMode(LED, OUTPUT);
  USART_Init( 77 ); 
  wdt_enable(WDTO_1S);
}

void loop() {
  wdt_reset();
  uint8_t c = USART_Receive(); 
  buffer[bufferIndex++] = c;
  if ((c == '\0') || (bufferIndex == BUFFER_SIZE)) {
    if( (buffer[ADDRESS] > 0) && (bufferIndex > ADDRESS)) {
      value = buffer[ADDRESS]-1;
#ifdef ENABLE_UART_DEBUG  
      USART_Transmit(buffer[ADDRESS]);
#endif 
      uint8_t summ = 0;
      for (uint8_t i = 0; i < (TOTAL_COUNT/SUMM_BYTES); i++)
        summ ^= buffer[SUMM_START_BYTE + i];
      if( (summ|1) == buffer[TOTAL_COUNT+SUMM_BYTE_NUMBER] )
       analogWrite(LED, value);
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
  while ( !(UCSRA & (1<<RXC)) );  
  return UDR;
}
 
void USART_Transmit( unsigned char data ) {
  while ( !(UCSRA & (1<<UDRE)) ); 
  UDR = data;         
}

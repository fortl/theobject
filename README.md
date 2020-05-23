<h1>What's This?</h1>

<p>TheObject is a light controller which consist of 20 small autonomous LED units. It's driving by ArtNet protocol and easly connects to VJs software.</p>

<h1>Let's take a look!</h1>
<p>Check my Youtube video -></p>
<div>
  <a href="https://youtu.be/Y-tGPEiGnRM"><img src="https://img.youtube.com/vi/Y-tGPEiGnRM/0.jpg" alt="Radio LED controller"></a>
</div>
<p>Here is <a href="https://www.youtube.com/watch?v=z9Q8UoAGk6M">one more example.</a></p>
<p>For more images and details you can check out <a href="https://hackaday.io/project/170265-radio-led-controller">the projects page on hackaday.io</a></p> 

<h1>How does it work?</h1>
<img src="https://raw.githubusercontent.com/fortl/theobject/master/images/theobject-main-scheme.png"/>
<p>The gate receives ArtNet bytes flow, pack it into small wireless packages and broadcasts to the units by NRF24 protocol. They receive data packages from the gate, check it, pick the LED value (address is hardcoded for a single unit). Then the unit's microcontroller manage the LED brightnes by PWM and constant current driver.</p>

<h2>Interface</h2>
<p>Interface made with <a href="https://hexler.net/products/touchosc">TouchOSC</a>.</p>
<img width="400" src="https://raw.githubusercontent.com/fortl/theobject/master/interface/interface.png"/>

<h2>What's inside?</h2>
<h3>Unit</h3>
<p>The main goal was to make the controller cheap as possible. That's why I choose ATTiny + NFR24 + OrangePiZero stack.</p>
<p>Before NRF24 I tried chinese JDY-40 modules. It's CC2541-based family of modules, the datasheet promised a lot of performance, but it lies, don't believe it.</p>
<p>I also made my firts gate with ESP8266 chip and <a href='https://robertoostenveld.nl/art-net-to-dmx512-with-esp8266/'>Robert Oostenveld's ArtNet to DMX server</a>. The solution was very cheap and easy. Unfortunately, ESP8266 too slow for something more. The code is available, just connect JDY-40 to UART1 of your ESP8266 and follow Robert's instructions. I'm focused on board-computer solution.</p>

<h3>Gate</h3>
<p>The Gate is OrangePi Zero (or any linux computer). 
<p>It drives leds, and listens to Artnet, interface UDP data.
Artnet integration is OLA server with a plugin. <a href="https://www.openlighting.org/">Open Lighting Project</a> is a flexible solution to manage show's lights&effects.</p>

<h1>Components</h1>
<ul>
  <li>NRF24l01-SMD - 20pcs (+1 for the gate)</li>
  <li>AMC1117 3.3v drivers - 20pcs</li>
  <li>ATTiny2313 - 20pcs</li>
  <li>AMC7135 LED drivers - 20pcs</li>
  <li>3.3v LEDs - 20pcs</li>
  <li>18650 lithium batteries - 20pcs</li>
  <li>18650 holders - 20pcs</li>
  <li>TP4056 lithium charger module - 20pcs</li>
  <li><a href="https://raw.githubusercontent.com/fortl/theobject/master/layouts/unit-nrf24-layout.png">unit module PCB</a> - 20pcs (I ordered at JLCPCB)</li>
  <li>Charger connectors - 20pcs</li>
  <li>Power buttons - 20pcs</li>
  <li>Square aluminium pipe - 40x40x2000mm - cut into 20pcs</li>
  <li>Plastic chair caps - 40pcs</li>
  <li>25A 5V charger - 1pc</li>
  <li>Wires</li>  
</ul>
It costed me about 120$ for 20 units + 15$ ESP8266 gate(with a case and batteries) or 15$ OrangePi Zero server (no batteries, USB powered) 


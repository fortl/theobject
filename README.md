<h1>What's This?</h1>

<p>TheObject is a light controller which consist of 20 small autonomous LED units. It's driving by ArtNet protocol and easly connects to VJs software.</p>

<h1>Let's take a look!</h1>
<p>Check my Youtube video -></p>
<div>
  <a href="https://www.youtube.com/watch?v=r2PG3HvHW_Q"><img src="https://img.youtube.com/vi/r2PG3HvHW_Q/0.jpg" alt="Radio LED controller"></a>
</div>
<p>Here is <a href="https://www.youtube.com/watch?v=z9Q8UoAGk6M">one more example.</a></p>
<p>For more images and details you can check out <a href="https://hackaday.io/project/170265-radio-led-controller">the projects page on hackaday.io</a></p> 

<h1>How it works?</h1>
<img src="https://raw.githubusercontent.com/fortl/theobject/master/images/theobject-main-scheme.png"/>
<p>The gate receives ArtNet bytes flow, pack it into small wireless packages and broadcasts to the units. All the units are driven by internal proprietary radio channel. They receive data packages from the gate, check it, pick the LED value (address is hardcoded for a single unit). Then the unit's microcontroller manage the LED brightnes by PWM and constant current driver.</p>

<h2>What's inside?</h2>
<h3>Unit</h3>
<p>The main goal was to make the controller cheap as possible. That's why I choose AVR ATTiny2313 + JDY-40</p>
<p>JDY-* is a CC2541-based family of modules, and JDY-40 is a transparent UART-wireless trasmitter. It doesn't support broadcasting officially, but I check this mode and it works well for my goals with some limitations.</p>

<img src="https://raw.githubusercontent.com/fortl/theobject/master/images/theobject-single-unit.png"/>
<h3>Gate</h3>
<p>I've created 2 gate implementations.</p> 
<p>The first one was based on ESP8266 chip and <a href='https://robertoostenveld.nl/art-net-to-dmx512-with-esp8266/'>Robert Oostenveld's ArtNet to DMX server</a>. I actually repeated Robert's project, connected a JDY-40 to UART and add code to translate DMX packages to my internal units protocol. My code is available in git. The solution was very cheap and easy. Unfortunately, ESP8266 too slow UART IO. That's enough for some cases, but I focused to fix the lags.</p>
<p>So the second solution I've made uses OrangePi Zero (or any linux computer) as a gate. Thanx to <a href="https://www.openlighting.org/">Open Lighting Project</a> and it fabulous <a href="https://www.openlighting.org/ola/developer-documentation/python-api/">Python API</a> At the moment the only gate's code is ola-plugin. 
<p>With the OrangePi gate I achived 15fps in real cases, which is good enough for my purposes</p>

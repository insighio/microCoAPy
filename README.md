# microCoAPy (Work In progress!)
A mini implementation of CoAP (Constrained Application Protocol) into MicroPython

It is a port of an Arduino C++ library [CoAP-simple-library](https://github.com/hirotakaster/CoAP-simple-library) into MicroPython. 

Its main difference compared to the established Python implementations [aiocoap](https://github.com/chrysn/aiocoap) and [CoAPthon](https://github.com/Tanganelli/CoAPthon) is its size and complexity since this library will be used on microcontrollers that support MicroPython such as: Pycom devices, ESP32, ESP8266. 

The first goal of this implementation will be to provide basic functionality to send and receive data. DTLS or any special features of CoAP as defined in the RFC's, will be examined and implented in the future. 

Current device for testing: [Pycom GPy](https://pycom.io/product/gpy/)

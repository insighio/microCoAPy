# microCoAPy
A mini implementation of CoAP (Constrained Application Protocol) into MicroPython

It is a port of an Arduino C++ library [CoAP-simple-library](https://github.com/hirotakaster/CoAP-simple-library) into MicroPython.

Its main difference compared to the established Python implementations [aiocoap](https://github.com/chrysn/aiocoap) and [CoAPthon](https://github.com/Tanganelli/CoAPthon) is its size and complexity since this library will be used on microcontrollers that support MicroPython such as: Pycom devices, ESP32, ESP8266.

The first goal of this implementation is to provide basic functionality to send and receive data. DTLS and/or any special features of CoAP as defined in the RFC's, will be examined and implented in the future.

# Supported operations

## CoAP client
* PUT
* POST
* GET

## Example of usage

Here is an example using the CoAP client functionality to send requests and receive responses.

```python
import microcoapy.microcoapy as microcoapy
# your code to connect to the network
#...
def receivedMessageCallback(packet, sender):
        print('Message received:', packet, ', from: ', sender)
        print('Mesage payload: ', packet.payload.decode('unicode_escape'))

client = microcoapy.Coap()
client.resposeCallback = receivedMessageCallback
client.start()

_SERVER_IP="192.168.1.2"
_SERVER_PORT=5683
bytesTransferred = client.get(_SERVER_IP, _SERVER_PORT, "current/measure")
print("[GET] Sent bytes: ", bytesTransferred)

client.poll(2000)

client.stop()
```

Lets examine the above code and explain its purpose.

```python
def receivedMessageCallback(packet, sender):
        print('Message received:', packet, ', from: ', sender)
        print('Mesage payload: ', packet.payload.decode('unicode_escape'))

client = microcoapy.Coap()
client.resposeCallback = receivedMessageCallback
```
During this step, the CoAP object get initialized. A callback handler is also created to get notifications from the server regarding our requests. __It is not used for incoming requests.__

```python
client.start()
```

The call to the _start_ function is where the UDP socket gets created. By default it gets bind to the defalut CoAP port 5683. If a custom port is needed, pass it as argument to the _start_ function.

```python
bytesTransferred = client.get(_SERVER_IP, _SERVER_PORT, "current/measure")
print("[GET] Sent bytes: ", bytesTransferred)
```

Having the socket ready, it is time to send our request. In this case we send a simple GET request to the specific address (ex. 192.168.1.2:5683). The _get_ function returns the number of bytes that has been able to send. So in case of error, 0 will be returned.  

```python
client.poll(2000)
```

Since a GET request has been posted, most likely it would be nice to receive and process the server response. For this reason we call _poll_ function that will try to read incoming messages for 2000 milliseconds. Upon timeout the execution will continue to the next command.

If a packet gets received during that period of type that is an _ACK_ to our request or a report (ex. _404_), the callback that has been registered at the  beginning will be called. 


## CoAP server
* Starts a server and calls custom callbacks upon receiving an incoming request. The respose needs to be defined by the user of the library.

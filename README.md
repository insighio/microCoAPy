# microCoAPy

A mini implementation of CoAP (Constrained Application Protocol) into MicroPython

The main difference compared to the established Python implementations [aiocoap](https://github.com/chrysn/aiocoap) and [CoAPthon](https://github.com/Tanganelli/CoAPthon) is its size and complexity since this library will be used on microcontrollers that support MicroPython such as: Pycom devices, ESP32, ESP8266.

The first goal of this implementation is to provide basic functionality to send and receive data. DTLS and/or any special features of CoAP as defined in the RFC's, will be examined and implemented in the future.

# Table of contents

- [Tested boards](#tested-boards)
- [Documentation](https://github.com/insighio/microCoAPy/wiki)
- [Installation](#installation)
- [Supported operations](#supported-operations)
  - [CoAP client](#coap-client)
    - [Example of usage](#example-of-usage)
      - [Code explained](#code-explained)
  - [CoAP server](#coap-server)
    - [Example of usage](#example-of-usage-1)
      - [Code explained](#code-explained-1)
  - [Custom sockets](#custom-sockets)
  - [Pycom custom socket based on AT commands](#pycom-custom-socket-based-on-at-commands)
- [Beta features under implementation or evaluation](#beta-features-under-implementation-or-evaluation)
  - [Discard incoming retransmission](#discard-incoming-retransmission)
  - [Activate debug messages](#activate-debug-messages)
- [Future work](#future-work)
- [Issues and contributions](#issues-and-contributions)

# Tested boards

- Pycom: all Pycom boards
- ESP32
- ESP8266

# Installation

## Using `mip`

For network connected devices, call:

```
import mip
mip.install("github:insighio/microCoAPy")
```

## File Transfer

Download and transfer files in the board through [ampy](https://pypi.org/project/adafruit-ampy/).

# Supported operations

## CoAP client

- PUT
- POST
- GET

### Example of usage

Here is an example using the CoAP client functionality to send requests and receive responses. (this example is part of [examples/pycom_wifi_coap_client.py](https://github.com/insighiot/microCoAPy/blob/master/examples/pycom_wifi_coap_client.py))

```python
import microcoapy
# your code to connect to the network
#...
def receivedMessageCallback(packet, sender):
        print('Message received:', packet.toString(), ', from: ', sender)
        print('Message payload: ', packet.payload.decode('unicode_escape'))

client = microcoapy.Coap()
client.responseCallback = receivedMessageCallback
client.start()

_SERVER_IP="192.168.1.2"
_SERVER_PORT=5683
bytesTransferred = client.get(_SERVER_IP, _SERVER_PORT, "current/measure")
print("[GET] Sent bytes: ", bytesTransferred)

client.poll(2000)

client.stop()
```

#### Code explained

Lets examine the above code and explain its purpose.

```python
def receivedMessageCallback(packet, sender):
        print('Message received:', packet.toString(), ', from: ', sender)
        print('Message payload: ', packet.payload.decode('unicode_escape'))

client = microcoapy.Coap()
client.responseCallback = receivedMessageCallback
```

During this step, the CoAP object get initialized. A callback handler is also created to get notifications from the server regarding our requests. **It is not used for incoming requests.**

When instantiating new Coap object, a custom port can be optionally configured: _client = microcoapy.Coap(5683)_.

```python
client.start()
```

The call to the [_start_](https://github.com/insighio/microCoAPy/wiki#startport) function is where the UDP socket gets created. By default it gets bind to the default CoAP port 5683. If a custom port is required, pass it as argument to the [_start_](https://github.com/insighio/microCoAPy/wiki#startport) function.

```python
bytesTransferred = client.get(_SERVER_IP, _SERVER_PORT, "current/measure")
print("[GET] Sent bytes: ", bytesTransferred)
```

Having the socket ready, it is time to send our request. In this case we send a simple GET request to the specific address (ex. 192.168.1.2:5683). The [_get_](https://github.com/insighio/microCoAPy/wiki#getip-port-url) function returns the number of bytes that have been sent. So in case of error, 0 will be returned.

```python
client.poll(2000)
```

Since a GET request has been posted, most likely it would be nice to receive and process the server response. For this reason we call [_poll_](https://github.com/insighio/microCoAPy/wiki#polltimeoutms-pollperiodms) function that will try to read incoming messages for 2000 milliseconds. Upon timeout the execution will continue to the next command.

If a packet gets received during that period of type that is an _ACK_ to our request or a report (ex. _404_), the callback that has been registered at the beginning will be called.

```python
client.stop()
```

Finally, stop is called to gracefully close the socket. It is preferable to have a corresponding call of [_stop_](https://github.com/insighio/microCoAPy/wiki#stop) to each call of [_start_](https://github.com/insighio/microCoAPy/wiki#startport) function because in special cases such as when using mobile modems, the modem might stuck when running out of available sockets.

To send POST or PUT message replace the call of _get_ function with:

```python
bytesTransferred = client.put(_SERVER_IP, _SERVER_PORT, "led/turnOn", "test",
                                 None, microcoapy.COAP_CONTENT_FORMAT.COAP_TEXT_PLAIN)
```

or

```python
bytesTransferred = client.post(_SERVER_IP, _SERVER_PORT, "led/turnOn", "test",
                                 None, microcoapy.COAP_CONTENT_FORMAT.COAP_TEXT_PLAIN)
```

For details on the arguments please advice the [documentation](https://github.com/insighio/microCoAPy/wiki).

## CoAP server

Starts a server and calls custom callbacks upon receiving an incoming request. The response needs to be defined by the user of the library.

### Example of usage

Here is an example using the CoAP server functionality to receive requests and respond back. (this example is part of [examples/pycom_wifi_coap_server.py](https://github.com/insighiot/microCoAPy/blob/master/examples/pycom_wifi_coap_server.py))

```python
import microcoapy
# your code to connect to the network
#...
client = microcoapy.Coap()

def measureCurrent(packet, senderIp, senderPort):
    print('Measure-current request received: ', packet.toString(), ', from: ', senderIp, ":", senderPort)
    client.sendResponse(senderIp, senderPort, packet.messageid,
                      "222", microcoapy.COAP_RESPONSE_CODE.COAP_CONTENT,
                      microcoapy.COAP_CONTENT_FORMAT.COAP_NONE, packet.token)

client.addIncomingRequestCallback('current/measure', measureCurrent)

client.start()

# wait for incoming request for 60 seconds
timeoutMs = 60000
start_time = time.ticks_ms()
while time.ticks_diff(time.ticks_ms(), start_time) < timeoutMs:
    client.poll(60000)

client.stop()
```

#### Code explained

Lets examine the above code and explain its purpose. For details on [_start_](https://github.com/insighio/microCoAPy/wiki#startport) and [_stop_](https://github.com/insighio/microCoAPy/wiki#stop) functions advice the previous paragraph of the client example.

```python
def measureCurrent(packet, senderIp, senderPort):
    print('Measure-current request received: ', packet.toString(), ', from: ', senderIp, ":", senderPort)
    client.sendResponse(senderIp, senderPort, packet.messageid,
                      "222", microcoapy.COAP_RESPONSE_CODE.COAP_CONTENT,
                      microcoapy.COAP_CONTENT_FORMAT.COAP_NONE, packet.token)

client.addIncomingRequestCallback('current/measure', measureCurrent)
```

This is the main step to prepare the CoAP instance to behave as a server: receive and handle requests. First we create a function _measureCurrent_ that takes as arguments the incoming packet, the sender IP and Port. This function will be used as a callback and will be triggered every time a specific URI path is provided in the incoming request.

This URL is defined upon registering the callback to the CoAP instance by calling [_addIncomingRequestCallback_](https://github.com/insighio/microCoAPy/wiki#addincomingrequestcallbackrequesturl-callback) function. After this call, if a CoAP GET/PUT/POST packet is received with URI path: coap://<IP>/current/measure , the callback will be triggered.

By default, the server does not send any response. This is a responsibility of the user to send (if needed) the appropriate response.

In this example, we reply with a response message packet (which has the same message id as the incoming request packet) whose payload is the actual value of the reading that has just been executed (in the example it is a hard-coded value of 222).

```python
timeoutMs = 60000
start_time = time.ticks_ms()
while time.ticks_diff(time.ticks_ms(), start_time) < timeoutMs:
    client.poll(60000)
```

Finally, since the functions [_loop_](https://github.com/insighio/microCoAPy/wiki#loopblocking) and [_poll_](https://github.com/insighio/microCoAPy/wiki#polltimeoutms-pollperiodms) **can handle a since packet per run**, we wrap its call to a while loop and wait for incoming messages.

## Custom sockets

By using default functions **microcoapy.Coap().start()** and **microcoapy.Coap().stop()** the Coap library handles the creation of a UDP socket from **usocket module** at the default port 5683 (if no other is defined when Coap object gets instantiated).

If this socket type is not the appropriate for your project, custom socket instances can be used instead.

Lets consider the case of supporting an external GSM modem connected via Serial on the board and that there is no direct support of this modem from default modules like **network.LTE**. In this case there is no guarranty that a typical UDP socket from usocket module will be functional. Thus, a custom socket instance needs to be created.

The custom socket needs to implement the functions:

- sendto(self, bytes, address) : returns the number of bytes transmitted
- recvfrom(self, bufsize): returns a byte array
- setblocking(self, flag)

Example:

```python
## Custom socket implementation
class CustomSocket:
    def __init__(self):
        print("CustomSocket: init")

    def sendto(self, bytes, address):
        print("CustomSocket: Sending bytes to: " + str(address))
        return len(bytes)

    def recvfrom(self, bufsize):
        print("CustomSocket: receiving max bytes: " + bufsize)
        return b"test data"

    def setblocking(self, flag):
        print(".", end="")
```

After creating the custom socket, it is utilized by the Coap instance after calling [microcoapy.Coap.setCustomSocket(customSocket)](https://github.com/insighio/microCoAPy/wiki#setcustomsocketcustom_socket).

Example:

```python
client = microcoapy.Coap()
# setup callback for incoming response to a request
client.responseCallback = receivedMessageCallback

# Initialize custom socket
customSocket = CustomSocket()

# Use custom socket to all operations of CoAP
client.setCustomSocket(customSocket)
```

## Pycom custom socket based on AT commands

Since most of the implementations of NBIoT networks are based on IPv6, it was essential to move to a custom implementation of UDP socket, as Pycom do not yet support natively IPv6 sockets. Thus, in [examples/pycom/nbiot/pycom_at_socket.py](https://github.com/insighio/microCoAPy/blob/master/examples/pycom/nbiot/pycom_at_socket.py) you can find a complete implementation of a sample socket that directly uses Sequans AT commands.

NOTE: The socket to work without limitations needs one of the following Pycom firmwares:

- [Pygate Firmware Release v1.20.2.rc11](https://github.com/pycom/pycom-micropython-sigfox/releases/tag/v1.20.2.rc11_pygate) (or newer)
- [Firmware Release v1.20.2.r1](https://github.com/pycom/pycom-micropython-sigfox/releases/tag/v1.20.2.r1) (or newer)

# Beta features under implementation or evaluation

## Discard incoming retransmission

If a received message is the same as the previously message received, it can be discarded. In that case, the poll function will not return at the time of retrieval and will continue to listen for futher incomming messages. Finally the defined responseCallback will not be called.

By default this simplistic feature is disabled. To enable:

```python
client = microcoapy.Coap()
client.discardRetransmissions = True
```

## Activate debug messages

By default, debug prints in microcoapy are enabled. Though, the user can deactivate the prints per Coap instance:

```python
client = microcoapy.Coap()
client.debug = False
```

# Future work

- Since this library is quite fresh, the next period will be full of testing.
- enhancments on funtionality as needed

# Issues and contributions

It would be our pleasure to receive comments, bug reports and/or contributions. To do this use the Issues and Pull requests of GitHub.

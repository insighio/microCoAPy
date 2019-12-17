import network
import machine
import microcoapy.microcoapy as microcoapy
import usocket as socket

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

_MY_SSID = 'myssid'
_MY_PASS = 'mypass'
_SERVER_IP = '192.168.1.2'
_SERVER_PORT = 5683  # default CoAP port
_COAP_URL = 'to/a/path'


def connectToWiFi():
    nets = wlan.scan()
    for net in nets:
        ssid = net[0].decode("utf-8")
        if ssid == _MY_SSID:
            print('Network found!')
            wlan.connect(ssid, _MY_PASS)
            while not wlan.isconnected():
                machine.idle()  # save power while waiting
            print('WLAN connection succeeded!')
            break

    return wlan.isconnected()


def sendPostRequest(client):
    # About to post message...
    bytesTransferred = client.post(_SERVER_IP, _SERVER_PORT, _COAP_URL, "test",
                                   None, microcoapy.COAP_CONTENT_TYPE.COAP_TEXT_PLAIN)
    print("Sent bytes: ", bytesTransferred)

    # wait for respose to our request for 2 seconds
    client.poll(2000)


def sendPutRequest(client):
    # About to post message...
    bytesTransferred = client.put(_SERVER_IP, _SERVER_PORT, "led/turnOn", "test",
                                   "authorization=1234567",
                                   microcoapy.COAP_CONTENT_TYPE.COAP_TEXT_PLAIN)
    print("[PUT] Sent bytes: ", bytesTransferred)

    # wait for respose to our request for 2 seconds
    client.poll(2000)


def sendGetRequest(client):
    # About to post message...
    bytesTransferred = client.get(_SERVER_IP, _SERVER_PORT, "current/measure")
    print("[GET] Sent bytes: ", bytesTransferred)

    # wait for respose to our request for 2 seconds
    client.poll(2000)


def receivedMessageCallback(packet, sender):
        print('Message received:', packet, ', from: ', sender)
        if(hasattr(packet, 'p')):
            print('Mesage payload: ', packet.p)


################################################################################
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
################################################################################

connectToWiFi()

client = microcoapy.Coap()
# setup callback for incoming respose to a request
client.resposeCallback = receivedMessageCallback

# Initialize custom socket
customSocket = CustomSocket()

# Use custom socket to all operations of CoAP
client.setCustomSocket(customSocket)

sendPostRequest(client)
sendPutRequest(client)
sendGetRequest(client)

from network import WLAN
import machine
import microcoapy

wlan = WLAN(mode=WLAN.STA)

_MY_SSID = 'myssid'
_MY_PASS = 'mypass'
_SERVER_IP = '192.168.1.2'
_SERVER_PORT = 5683  # default CoAP port
_COAP_URL = 'to/a/path'


def connectToWiFi():
    nets = wlan.scan()
    for net in nets:
        if net.ssid == _MY_SSID:
            print('Network found!')
            wlan.connect(net.ssid, auth=(net.sec, _MY_PASS), timeout=5000)
            while not wlan.isconnected():
                machine.idle()  # save power while waiting
            print('WLAN connection succeeded!')
            break

    return wlan.isconnected()


def sendPostRequest(client):
    # About to post message...
    bytesTransferred = client.post(_SERVER_IP, _SERVER_PORT, _COAP_URL, "test",
                                   None, microcoapy.COAP_CONTENT_FORMAT.COAP_TEXT_PLAIN)
    print("[POST] Sent bytes: ", bytesTransferred)

    # wait for respose to our request for 2 seconds
    client.poll(2000)


def sendPutRequest(client):
    # About to post message...
    bytesTransferred = client.put(_SERVER_IP, _SERVER_PORT, "led/turnOn", "test",
                                   None, microcoapy.COAP_CONTENT_FORMAT.COAP_TEXT_PLAIN)
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


connectToWiFi()

client = microcoapy.Coap()
# setup callback for incoming respose to a request
client.resposeCallback = receivedMessageCallback

# Starting CoAP...
client.start()

sendPostRequest(client)
sendPutRequest(client)
sendGetRequest(client)

# stop CoAP
client.stop()

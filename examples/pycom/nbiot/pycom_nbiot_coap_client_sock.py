from network import LTE
import machine
import utime
import binascii
import microcoapy

_NBIOT_MAX_CONNECTION_TIMEOUT_MSEC=30000
_NBIOT_APN="iot"

_SERVER_IP="2001:4860:4860::8888"
_SERVER_PORT=5683
_COAP_POST_URL="path/to/post/service"

print("Initializing LTE...")
lte = LTE()
lte.init()

def connectNBIoT(timeout):
    print("Connecting LTE...")
    if(not lte.isattached() or not lte.isconnected()):
        lte.send_at_cmd('AT+CFUN=0')
        lte.send_at_cmd('AT+CMEE=2')
        lte.send_at_cmd('AT+CGDCONT=1,"IPV6","' + _NBIOT_APN + '"')
        lte.send_at_cmd('AT+CFUN?')

        start_time_activation = utime.ticks_ms()

        lte.send_at_cmd('AT+CFUN=1')
        while not lte.isattached() and (utime.ticks_ms()-start_time_activation < timeout):
            print(".", end="")
            machine.idle()

        con_start_time_activation = utime.ticks_ms()
        lte.connect()
        while not lte.isconnected() and (utime.ticks_ms()-con_start_time_activation < timeout):
            print(",", end="")
            machine.idle()
        print("")

    return lte.isattached() and lte.isconnected()

def disconnectNBIoT():
    LTE().detach()


def sendPostRequest(client):
    # About to post message...
    messageId = client.post(_SERVER_IP, _SERVER_PORT, _COAP_POST_URL, '[{"bn":"09876543","n":"batt","u":"V","v":13}]',
                                   "authorization=123456789", microcoapy.COAP_CONTENT_FORMAT.COAP_APPLICATION_JSON)
    print("[POST] Message Id: ", messageId)

    # wait for response to our request for 2 seconds
    client.poll(10000)


def receivedMessageCallback(packet, sender):
    print('Message received:', packet.toString(), ', from: ', sender)



connected = connectNBIoT(_NBIOT_MAX_CONNECTION_TIMEOUT_MSEC)
print("LTE ok: " + str(connected))

if(connected):
    client = microcoapy.Coap()
    # setup callback for incoming response to a request
    client.start()

    sendPostRequest(client)

disconnectNBIoT()

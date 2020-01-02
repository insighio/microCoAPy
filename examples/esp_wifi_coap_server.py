import network
import machine
import microcoapy
import utime as time

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

_MY_SSID = 'monroe2G'
_MY_PASS = 'movement'
_SERVER_PORT = 5683  # default CoAP port


def connectToWiFi():
    print('Starting attempt to connect to to WiFi...')
    nets = wlan.scan()
    for net in nets:
        ssid = net[0].decode("utf-8")
        if ssid == _MY_SSID:
            print('Network found!')
            wlan.connect(ssid, _MY_PASS)
            while not wlan.isconnected():
                machine.idle()  # save power while waiting

            connectionResults = wlan.ifconfig()
            print('WLAN connection succeeded with IP: ', connectionResults[0])
            break

    return wlan.isconnected()

connectToWiFi()

client = microcoapy.Coap()

def turnOnLed(packet, senderIp, senderPort):
    print('Turn-on-led request received:', packet, ', from: ', senderIp, ":", senderPort)
    client.sendResponse(senderIp, senderPort, packet.messageid,
                      None, microcoapy.COAP_RESPONSE_CODE.COAP_CONTENT,
                      microcoapy.COAP_CONTENT_FORMAT.COAP_NONE, "Ok")


def measureCurrent(packet, senderIp, senderPort):
    print('Measure-current request received:', packet, ', from: ', senderIp, ":", senderPort)
    client.sendResponse(senderIp, senderPort, packet.messageid,
                      None, microcoapy.COAP_RESPONSE_CODE.COAP_SERVICE_UNAVALIABLE,
                      microcoapy.COAP_CONTENT_FORMAT.COAP_NONE, None)


# setup callback for incoming respose to a request
client.addIncomingRequestCallback('led/turnOn', turnOnLed)
client.addIncomingRequestCallback('current/measure', measureCurrent)

# Starting CoAP...
client.start()

# wait for incoming request for 60 seconds
timeoutMs = 60000
start_time = time.ticks_ms()
while time.ticks_diff(time.ticks_ms(), start_time) < timeoutMs:
    client.poll(60000)

# stop CoAP
client.stop()

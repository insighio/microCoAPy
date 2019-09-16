from network import WLAN
import machine
import microcoapy.microcoapy as microcoapy

wlan = WLAN(mode=WLAN.STA)

_MY_SSID = 'myssid'
_MY_PASS = 'mypass'
_SERVER_IP = '192.168.1.2'
_SERVER_PORT = 5683  # default CoAP port
_COAP_URL = 'to/a/path'

nets = wlan.scan()
for net in nets:
    if net.ssid == _MY_SSID:
        print('Network found!')
        wlan.connect(net.ssid, auth=(net.sec, _MY_PASS), timeout=5000)
        while not wlan.isconnected():
            machine.idle()  # save power while waiting
        print('WLAN connection succeeded!')
        break

if not wlan.isconnected():
    print("no network found")
else:
    client = microcoapy.Coap()
    try:
        print('Starting CoAP client...')
        client.start()
        print('OK')
    except Exception:
        print('Failed')

    message = "test"

    print("About to post message: ")
    bytesTransferred = client.post(_SERVER_IP,
                                   _SERVER_PORT,
                                   _COAP_URL,
                                   message,
                                   None,
                                   microcoapy.COAP_CONTENT_TYPE.COAP_TEXT_PLAIN)
    print("Sent bytes: ", bytesTransferred)
    client.stop()

import microcoapy.coap_macros as macros
from microcoapy.coap_option import CoapOption

class CoapPacket:
    def __init__(self):
        self.type = macros.COAP_TYPE.COAP_CON  # uint8_t
        self.method = macros.COAP_METHOD.COAP_GET  # uint8_t
        self.token = bytearray()
        self.payload = bytearray()
        self.messageid = 0
        self.content_format = macros.COAP_CONTENT_FORMAT.COAP_NONE
        self.query = bytearray()  # uint8_t*
        self.options = []

    def addOption(self, number, opt_payload):
        if(len(self.options) >= macros._MAX_OPTION_NUM):
            return
        self.options.append(CoapOption(number, opt_payload))

    def setUriHost(self, address):
        self.addOption(macros.COAP_OPTION_NUMBER.COAP_URI_HOST, address)

    def setUriPath(self, url):
        for subPath in url.split('/'):
            self.addOption(macros.COAP_OPTION_NUMBER.COAP_URI_PATH, subPath)

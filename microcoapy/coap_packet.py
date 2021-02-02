from . import coap_macros as macros
from .coap_option import CoapOption

class CoapPacket:
    def __init__(self):
        self.version = macros.COAP_VERSION.COAP_VERSION_UNSUPPORTED
        self.type = macros.COAP_TYPE.COAP_CON  # uint8_t
        self.method = macros.COAP_METHOD.COAP_GET  # uint8_t
        self.token = bytearray()
        self.payload = bytearray()
        self.messageid = 0
        self.content_format = macros.COAP_CONTENT_FORMAT.COAP_NONE
        self.query = bytearray()  # uint8_t*
        self.options = []

    # def __eq__(self, other):
    #     return self.toString() == other.toString()
        # (self.version == other.version and self.type == other.type and\
        #     self.method == other.method and self.token == other.token and\
        #     self.payload == other.payload and self.messageid == other.messageid and\
        #     self.content_format == other.content_format and self.query == other.query and\
        #     self.options == other.options)

    def addOption(self, number, opt_payload):
        if(len(self.options) >= macros._MAX_OPTION_NUM):
            return
        self.options.append(CoapOption(number, opt_payload))

    def setUriHost(self, address):
        self.addOption(macros.COAP_OPTION_NUMBER.COAP_URI_HOST, address)

    def setUriPath(self, url):
        for subPath in url.split('/'):
            self.addOption(macros.COAP_OPTION_NUMBER.COAP_URI_PATH, subPath)

    def toString(self):
        class_, detail = macros.CoapResponseCode.decode(self.method)
        return "type: {}, method: {}.{:02d}, messageid: {}, payload: {}".format(macros.coapTypeToString(self.type), class_, detail, self.messageid, self.payload)

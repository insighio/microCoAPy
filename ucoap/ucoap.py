import usocket as socket
import ustruct as struct
import random
from ubinascii import hexlify

# Macros
_COAP_HEADER_SIZE = 4
_COAP_OPTION_HEADER_SIZE = 1
_COAP_PAYLOAD_MARKER = 0xFF
_MAX_OPTION_NUM = 10
_BUF_MAX_SIZE = 1024
_COAP_DEFAULT_PORT = 5683


def CoapResponseCode(class_, detail):
    """no idea"""
    return ((class_ << 5) | (detail))


def CoapOptionDelta(v):
    """To be used as n=CoapOptionDelta(v)."""
    if v < 13:
        return (0xFF & v)
    elif v <= 0xFF + 13:
        return 13
    else:
        return 14


def enum(**enums):
    return type('Enum', (), enums)


COAP_TYPE = enum(
    COAP_CON=0,
    COAP_NONCON=1,
    COAP_ACK=2,
    COAP_RESET=3
)

COAP_METHOD = enum(
    COAP_GET=1,
    COAP_POST=2,
    COAP_PUT=3,
    COAP_DELETE=4
)

COAP_RESPONSE_CODE = enum(
    COAP_CREATED=CoapResponseCode(2, 1),
    COAP_DELETED=CoapResponseCode(2, 2),
    COAP_VALID=CoapResponseCode(2, 3),
    COAP_CHANGED=CoapResponseCode(2, 4),
    COAP_CONTENT=CoapResponseCode(2, 5),
    COAP_BAD_REQUEST=CoapResponseCode(4, 0),
    COAP_UNAUTHORIZED=CoapResponseCode(4, 1),
    COAP_BAD_OPTION=CoapResponseCode(4, 2),
    COAP_FORBIDDEN=CoapResponseCode(4, 3),
    COAP_NOT_FOUNT=CoapResponseCode(4, 4),
    COAP_METHOD_NOT_ALLOWD=CoapResponseCode(4, 5),
    COAP_NOT_ACCEPTABLE=CoapResponseCode(4, 6),
    COAP_PRECONDITION_FAILED=CoapResponseCode(4, 12),
    COAP_REQUEST_ENTITY_TOO_LARGE=CoapResponseCode(4, 13),
    COAP_UNSUPPORTED_CONTENT_FORMAT=CoapResponseCode(4, 15),
    COAP_INTERNAL_SERVER_ERROR=CoapResponseCode(5, 0),
    COAP_NOT_IMPLEMENTED=CoapResponseCode(5, 1),
    COAP_BAD_GATEWAY=CoapResponseCode(5, 2),
    COAP_SERVICE_UNAVALIABLE=CoapResponseCode(5, 3),
    COAP_GATEWAY_TIMEOUT=CoapResponseCode(5, 4),
    COAP_PROXYING_NOT_SUPPORTED=CoapResponseCode(5, 5)
)

COAP_OPTION_NUMBER = enum(
    COAP_IF_MATCH=1,
    COAP_URI_HOST=3,
    COAP_E_TAG=4,
    COAP_IF_NONE_MATCH=5,
    COAP_URI_PORT=7,
    COAP_LOCATION_PATH=8,
    COAP_URI_PATH=11,
    COAP_CONTENT_FORMAT=12,
    COAP_MAX_AGE=14,
    COAP_URI_QUERY=15,
    COAP_ACCEPT=17,
    COAP_LOCATION_QUERY=20,
    COAP_PROXY_URI=35,
    COAP_PROXY_SCHEME=39
)

COAP_CONTENT_TYPE = enum(
    COAP_NONE=-1,
    COAP_TEXT_PLAIN=0,
    COAP_APPLICATION_LINK_FORMAT=40,
    COAP_APPLICATION_XML=41,
    COAP_APPLICATION_OCTET_STREAM=42,
    COAP_APPLICATION_EXI=47,
    COAP_APPLICATION_JSON=50,
    COAP_APPLICATION_CBOR=60
)


class CoapOption:
    def __init__(self, number=-1, buffer=None):
        self.number = number
        # self.length = -1 -> will be replaced by len(self.buffer)
        self.buffer = buffer


class CoapPacket:
    def __init__(self):
        type = COAP_TYPE.COAP_CON  # uint8_t
        code = COAP_METHOD.COAP_GET  # uint8_t
        token = bytearray()
        payload = bytearray()
        messageid = 0
        contentType = COAP_CONTENT_TYPE.COAP_NONE
        query = bytearray()  # uint8_t*
        options = []

    def addOption(self, number, opt_payload):
        if(len(self.options) >= _MAX_OPTION_NUM):
            return
        self.options.append(CoapOption(number, opt_payload))

    def setUriHost(self, address):
        self.addOption(COAP_RESPONSE_CODE.COAP_URI_HOST, address)

    def setUriPath(self, url):
        for subPath in url.split('/'):
            self.addOption(COAP_RESPONSE_CODE.COAP_URI_PATH, subPath)


# probably unessasary
class CoapUri:
    def __init__(self):
        self.callbacks = {}

    def addCallBack(self, callback, url):
        # if it already exists, update the callback of the URL
        # if it does not exists, add new tuple
        self.callbacks[url] = callback

    def find(self, url):
        return self.callbacks[url]


class Coap:
    def __init__(self):
        self.sock = None
        self.callbacks = {}
        self.resposeCallback = None
        self.port = 0

    def start(self, port=_COAP_DEFAULT_PORT):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        server_address = ('localhost', port)
        self.sock.bind(server_address)

    def stop(self):
        if self.sock is not None:
            self.sock.close()

    def sendPacket(self, ip, port, coapPacket):
        # the packet must be less than the MTU
        runningDelta = 0
        packetSize = 0

        # make coap packet base header
        buffer = bytearray()
        buffer.append(0x01 << 6)
        buffer[0] |= (coapPacket.type & 0x03) << 4
        # max: 8 bytes of tokens, if token length is greater, it is ignored
        tokenLength = 0
        if (coapPacket.token is not None) and (len(coapPacket.token) <= 0x0F):
            tokenLength = len(coapPacket.token)

        buffer[0] |= (tokenLength & 0x0F)
        buffer.append(coapPacket.code)
        buffer.append(coapPacket.messageid >> 8)
        buffer.append(coapPacket.messageid & 0xFF)
        packetSize += _COAP_HEADER_SIZE

        if tokenLength > 0:
            buffer.extend(coapPacket.token)
            packetSize += tokenLength

        # make option header
        for opt in coapPacket.options:
            if ((opt.buffer is None) or (len(opt.buffer) == 0)) or (packetSize + 5 + len(opt.buffer) >= _BUF_MAX_SIZE):
                return 0

            optBufferLen = len(opt.buffer)
            optdelta = opt.number - runningDelta
            delta = CoapOptionDelta(optdelta)
            len = CoapOptionDelta(optBufferLen)

            buffer.append(0xFF & (delta << 4 | len))
            if (delta == 13):
                buffer.append(optdelta - 13)
                packetSize += 1
            elif (delta == 14):
                buffer.append((optdelta - 269) >> 8)
                buffer.append(0xFF & (optdelta - 269))
                packetSize += 2

            if (len == 13):
                buffer.append(optBufferLen - 13)
                packetSize += 1
            elif (len == 14):
                buffer.append(optBufferLen >> 8)
                buffer.append(0xFF & (optBufferLen - 269))
                packetSize += 2

            buffer.extend(opt.buffer)
            packetSize += optBufferLen + 1  # why +1?
            runningDelta = opt.number

        # make payload
        if (coapPacket.payload is not None) and (len(coapPacket.payload)):
            if (packetSize + 1 + len(coapPacket.payload)) >= _BUF_MAX_SIZE:
                return 0
            buffer.append(0xFF)
            buffer.extend(coapPacket.payload)
            packetSize += 1 + len(coapPacket.payload)

        print('Senging Packet: ', hex(len(buffer)), "> ", hexlify(buffer, ":"))
        status = 0
        try:
            status = self.sock.sendto(buffer, (ip, port))
            print('Packet sent. Status: ', status)
        except Exception as e:
            status = 0
            print('Exception while sending packet...', e)

        return status

    def send(self, ip, port, url, type, method, token, payload, content_type, queryOption):
        packet = CoapPacket()
        packet.type = type
        packet.code = method
        packet.token = token
        packet.payload = payload
        packet.contentType = content_type
        packet.query = queryOption

        return self.sendEx(ip, port, url, packet)

    def sendEx(self, ip, port, url, packet):
        packet.optionnum = 0
        # messageId field: 16bit -> 0-65535
        packet.messageid = random.randint(0, 65535)
        packet.setUriHost(ip)
        packet.setUriPath(url)

        if packet.contentType != COAP_CONTENT_TYPE.COAP_NONE:
            optionBuffer = bytearray(2)
            struct.pack_into("!H", optionBuffer, 0, packet.contentType)
            struct.pack_into("!H", optionBuffer, 1, packet.contentType)
            optionBuffer[0] = (optionBuffer[0] & 0xFF00) >> 8
            optionBuffer[1] = (optionBuffer[1] & 0x00FF)
            packet.addOption(COAP_OPTION_NUMBER.COAP_CONTENT_FORMAT, optionBuffer)

        if (packet.query is not None) and (len(packet.query) > 0):
            packet.addOption(COAP_OPTION_NUMBER.COAP_URI_QUERY, packet.query)

        return self.sendPacket(ip, port, packet)

    def post(self, ip, port, url, payload=bytearray(), queryOption=None, contentType=COAP_CONTENT_TYPE.COAP_NONE):
        return self.send(ip, port, url, COAP_TYPE.COAP_CON, COAP_METHOD.COAP_POST, None, payload, contentType, queryOption)

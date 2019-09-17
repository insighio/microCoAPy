import usocket as socket
import uos
from ubinascii import hexlify
import utime as time
import errno

# Macros
_COAP_HEADER_SIZE = 4
_COAP_OPTION_HEADER_SIZE = 1
_COAP_PAYLOAD_MARKER = 0xFF
_MAX_OPTION_NUM = 10
_BUF_MAX_SIZE = 1024
_COAP_DEFAULT_PORT = 5683


def CoapResponseCode(class_, detail):
    """ """
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
        byteBuf = bytearray()
        if buffer is not None:
            byteBuf.extend(buffer)
        self.buffer = byteBuf

    def __str__(self):
        return "Opt(number:{0}, buffer:{1})".format(self.number, self.buffer)


class CoapPacket:
    def __init__(self):
        self.type = COAP_TYPE.COAP_CON  # uint8_t
        self.code = COAP_METHOD.COAP_GET  # uint8_t
        self.token = bytearray()
        self.payload = bytearray()
        self.messageid = 0
        self.contentType = COAP_CONTENT_TYPE.COAP_NONE
        self.query = bytearray()  # uint8_t*
        self.options = []

    def addOption(self, number, opt_payload):
        if(len(self.options) >= _MAX_OPTION_NUM):
            return
        self.options.append(CoapOption(number, opt_payload))

    def setUriHost(self, address):
        self.addOption(COAP_OPTION_NUMBER.COAP_URI_HOST, address)

    def setUriPath(self, url):
        for subPath in url.split('/'):
            self.addOption(COAP_OPTION_NUMBER.COAP_URI_PATH, subPath)

    def __str__(self):
        tmpStr = "\n\ttype: {0}\n\tcode: {1}\n\ttoken: {2}\n\tpayload: {3}\n\tmessageid: {4}\n\tcontentType: {5}\n\tquery: {6}".format(
            self.type, self.code, self.token, self.payload, self.messageid, self.contentType, self.query
            )
        tmpStr += '\n\toptions: ['
        for opt in self.options:
            tmpStr += str(opt)
        tmpStr += ']'
        return tmpStr


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
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', port))

    def stop(self):
        if self.sock is not None:
            self.sock.close()
            self.sock = None

    def sendPacket(self, ip, port, coapPacket):
        # the packet must be less than the MTU
        runningDelta = 0
        packetSize = 0

        if coapPacket.contentType != COAP_CONTENT_TYPE.COAP_NONE:
            optionBuffer = bytearray(2)
            optionBuffer[0] = (coapPacket.contentType & 0xFF00) >> 8
            optionBuffer[1] = (coapPacket.contentType & 0x00FF)
            coapPacket.addOption(COAP_OPTION_NUMBER.COAP_CONTENT_FORMAT, optionBuffer)

        if (coapPacket.query is not None) and (len(coapPacket.query) > 0):
            coapPacket.addOption(COAP_OPTION_NUMBER.COAP_URI_QUERY, coapPacket.query)

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
            if (opt is None) or (opt.buffer is None) or (len(opt.buffer) == 0):
                continue

            optBufferLen = len(opt.buffer)

            if (packetSize + 5 + optBufferLen) >= _BUF_MAX_SIZE:
                return 0

            optdelta = opt.number - runningDelta
            delta = CoapOptionDelta(optdelta)
            length = CoapOptionDelta(optBufferLen)

            buffer.append(0xFF & (delta << 4 | length))
            if (delta == 13):
                buffer.append(optdelta - 13)
                packetSize += 1
            elif (delta == 14):
                buffer.append((optdelta - 269) >> 8)
                buffer.append(0xFF & (optdelta - 269))
                packetSize += 2

            if (length == 13):
                buffer.append(optBufferLen - 13)
                packetSize += 1
            elif (length == 14):
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
            sockaddr = socket.getaddrinfo(ip, port)[0][-1]
            status = self.sock.sendto(buffer, sockaddr)
            if status > 0:
                status = coapPacket.messageid
            print('Packet sent. MessageId: ', status)
        except Exception as e:
            status = 0
            print('Exception while sending packet...')
            import sys
            sys.print_exception(e)

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
        # urandom to generate 2 bytes
        randBytes = uos.urandom(2)
        packet.messageid = (randBytes[0] << 8) | randBytes[1]
        packet.setUriHost(ip)
        packet.setUriPath(url)

        return self.sendPacket(ip, port, packet)

    # to be tested
    def sendResponse(self, ip, port, messageid, payload, code, contentType, token):
        packet = CoapPacket()

        packet.type = COAP_TYPE.COAP_ACK
        packet.code = code
        packet.token = token
        packet.payload = payload
        packet.optionnum = 0
        packet.messageid = messageid
        packet.contentType = contentType

        return self.sendPacket(ip, port, packet)

    def parseOption(self, packet, runningDelta, buffer, i):
        option = CoapOption()
        headlen = 1

        errorMessage = (False, runningDelta, i)

        if (buffer is None):
            return errorMessage

        buflen = len(buffer) - i

        if (buflen < headlen):
            return errorMessage

        delta = (buffer[i] & 0xF0) >> 4
        length = buffer[i] & 0x0F

        if delta == 13:
            headlen += 1
            if (buflen < headlen):
                return errorMessage
            delta = buffer[i+1] + 13
            i += 1
        elif delta == 14:
            headlen += 2
            if (buflen < headlen):
                return errorMessage
            delta = ((buffer[i+1] << 8) | buffer[i+2]) + 269
            i += 2
        elif delta == 15:
            return errorMessage

        if length == 13:
            headlen += 1
            if (buflen < headlen):
                return errorMessage
            length = buffer[i+1] + 13
            i += 1
        elif length == 14:
            headlen += 2
            if (buflen < headlen):
                return errorMessage
            length = ((buffer[i+1] << 8) | buffer[i+2]) + 269
            i += 2
        elif length == 15:
            return errorMessage

        endOfOptionIndex = (i + 1 + length)

        if endOfOptionIndex > len(buffer):
            return errorMessage

        option.number = delta + runningDelta
        option.buffer = buffer[i+1:length]
        packet.options.append(option)

        return (True, runningDelta + delta, endOfOptionIndex)

    # to be tested
    def get(self, ip, port, url):
        return self.send(ip, port, url, COAP_TYPE.COAP_CON, COAP_METHOD.COAP_GET, None, None, COAP_CONTENT_TYPE.COAP_NONE, None)

    # to be tested
    def put(self, ip, port, url, payload=bytearray(), queryOption=None, contentType=COAP_CONTENT_TYPE.COAP_NONE):
        return self.send(ip, port, url, COAP_TYPE.COAP_CON, COAP_METHOD.COAP_PUT, None, payload, contentType, queryOption)

    def post(self, ip, port, url, payload=bytearray(), queryOption=None, contentType=COAP_CONTENT_TYPE.COAP_NONE):
        return self.send(ip, port, url, COAP_TYPE.COAP_CON, COAP_METHOD.COAP_POST, None, payload, contentType, queryOption)

    def handleIncomingRequest(self, requestPacket, sourceIp, sourcePort):
#             String url = "";
#             // call endpoint url function
#             for (int i = 0; i < packet.optionnum; i++) {
#                 if (packet.options[i].number == COAP_URI_PATH && packet.options[i].length > 0) {
#                     char urlname[packet.options[i].length + 1];
#                     memcpy(urlname, packet.options[i].buffer, packet.options[i].length);
#                     urlname[packet.options[i].length] = '\0';
#                     if(url.length() > 0)
#                       url += "/";
#                     url += urlname;
#                 }
#             }
#
#             if (!uri.find(url)) {
#                 sendResponse(_udp->remoteIP(), _udp->remotePort(), packet.messageid, NULL, 0,
#                         COAP_NOT_FOUNT, COAP_NONE, NULL, 0);
#             } else {
#                 uri.find(url)(packet, _udp->remoteIP(), _udp->remotePort());
#             }
#         }
#
#         /* this type check did not use.
#         if (packet.type == COAP_CON) {
#             // send response
#              sendResponse(_udp->remoteIP(), _udp->remotePort(), packet.messageid);
#         }
#          */
        return False

    def readBytesFromSocket(self, numOfBytes):
        try:
            return self.sock.recvfrom(numOfBytes)
        except Exception as e:
            return (None, None)

    def loop(self):
        hasReceivedPacket = False
        if self.sock is None:
            return False

        (buffer, remoteAddress) = self.readBytesFromSocket(_BUF_MAX_SIZE)
        self.sock.setblocking(True)

        while (buffer is not None) and (len(buffer) > 0):
            bufferLen = len(buffer)
            if (bufferLen < _COAP_HEADER_SIZE) or (((buffer[0] & 0xC0) >> 6) != 1):
                (tempBuffer, tempRemoteAddress) = self.readBytesFromSocket(_BUF_MAX_SIZE - bufferLen)
                if tempBuffer is not None:
                    buffer.extend(tempBuffer)
                continue

            packet = CoapPacket()
            packet.type = (buffer[0] & 0x30) >> 4
            packet.tokenLength = buffer[0] & 0x0F
            packet.code = buffer[1]
            packet.messageid = 0xFF00 & (buffer[2] << 8)
            packet.messageid |= 0x00FF & buffer[3]

            if (packet.tokenLength == 0):
                packet.token = None
            elif (packet.tokenLength <= 8):
                packet.token = buffer[4:packet.tokenLength]
            else:
                (tempBuffer, tempRemoteAddress) = self.readBytesFromSocket(_BUF_MAX_SIZE - bufferLen)
                if tempBuffer is not None:
                    buffer.extend(tempBuffer)
                continue

            if(_COAP_HEADER_SIZE + packet.tokenLength < bufferLen):
                delta = 0
                bufferIndex = _COAP_HEADER_SIZE + packet.tokenLength
                while (len(packet.options) < _MAX_OPTION_NUM) and\
                      (bufferIndex < bufferLen) and\
                      (buffer[bufferIndex] != 0xFF):
                    (status, delta, bufferIndex) = self.parseOption(packet, delta, buffer, bufferIndex)
                    if status is False:
                        return hasReceivedPacket
                packet.optionnum = len(packet.options)

                if ((bufferIndex + 1) < bufferLen) and (buffer[bufferIndex] == 0xFF):
                    packet.payload = buffer[bufferIndex+1:]  # does this works?
                else:
                    packet.payload = None

            hasReceivedPacket = True

            if packet.type == COAP_TYPE.COAP_ACK:
                if self.resposeCallback is not None:
                    self.resposeCallback(packet, remoteAddress)
            else:
                self.handleIncomingRequest(packet, remoteAddress)

            # deactivated for now - read only one packet per call
            # next packet
            # (buffer, remoteAddress) = self.sock.recvfrom(_BUF_MAX_SIZE)
            return hasReceivedPacket
        return hasReceivedPacket

    def poll(self, timeoutMs=-1):
        self.sock.setblocking(False)
        start_time = time.ticks_ms()
        while not self.loop() and (time.ticks_diff(time.ticks_ms(), start_time)):
            self.sock.setblocking(False)
            time.sleep_ms(10)

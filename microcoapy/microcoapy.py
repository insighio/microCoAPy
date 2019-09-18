import usocket as socket
import uos
import utime as time

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
    COAP_NOT_FOUND=CoapResponseCode(4, 4),
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

    def addIncomingRequestCallback(self, requestUrl, callback):
        self.callbacks[requestUrl] = callback

    def writePacketHeaderInfo(self, buffer, packet):
        # make coap packet base header
        buffer.append(0x01 << 6)
        buffer[0] |= (packet.type & 0x03) << 4
        # max: 8 bytes of tokens, if token length is greater, it is ignored
        tokenLength = 0
        if (packet.token is not None) and (len(packet.token) <= 0x0F):
            tokenLength = len(packet.token)

        buffer[0] |= (tokenLength & 0x0F)
        buffer.append(packet.code)
        buffer.append(packet.messageid >> 8)
        buffer.append(packet.messageid & 0xFF)

        if tokenLength > 0:
            buffer.extend(packet.token)

    def writePacketOptions(self, buffer, packet):
        runningDelta = 0
        # make option header
        for opt in packet.options:
            if (opt is None) or (opt.buffer is None) or (len(opt.buffer) == 0):
                continue

            optBufferLen = len(opt.buffer)

            if (len(buffer) + 5 + optBufferLen) >= _BUF_MAX_SIZE:
                return 0

            optdelta = opt.number - runningDelta
            delta = CoapOptionDelta(optdelta)
            length = CoapOptionDelta(optBufferLen)

            buffer.append(0xFF & (delta << 4 | length))
            if (delta == 13):
                buffer.append(optdelta - 13)
            elif (delta == 14):
                buffer.append((optdelta - 269) >> 8)
                buffer.append(0xFF & (optdelta - 269))

            if (length == 13):
                buffer.append(optBufferLen - 13)
            elif (length == 14):
                buffer.append(optBufferLen >> 8)
                buffer.append(0xFF & (optBufferLen - 269))

            buffer.extend(opt.buffer)
            runningDelta = opt.number

    def writePacketPayload(self, buffer, packet):
        # make payload
        if (packet.payload is not None) and (len(packet.payload)):
            if (len(buffer) + 1 + len(packet.payload)) >= _BUF_MAX_SIZE:
                return 0
            buffer.append(0xFF)
            buffer.extend(packet.payload)

    def sendPacket(self, ip, port, coapPacket):
        if coapPacket.contentType != COAP_CONTENT_TYPE.COAP_NONE:
            optionBuffer = bytearray(2)
            optionBuffer[0] = (coapPacket.contentType & 0xFF00) >> 8
            optionBuffer[1] = (coapPacket.contentType & 0x00FF)
            coapPacket.addOption(COAP_OPTION_NUMBER.COAP_CONTENT_FORMAT, optionBuffer)

        if (coapPacket.query is not None) and (len(coapPacket.query) > 0):
            coapPacket.addOption(COAP_OPTION_NUMBER.COAP_URI_QUERY, coapPacket.query)

        buffer = bytearray()
        self.writePacketHeaderInfo(buffer, coapPacket)

        self.writePacketOptions(buffer, coapPacket)

        self.writePacketPayload(buffer, coapPacket)

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

        if delta == 15 or length == 15:
            return errorMessage

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

        endOfOptionIndex = (i + 1 + length)

        if endOfOptionIndex > len(buffer):
            return errorMessage

        option.number = delta + runningDelta
        option.buffer = buffer[i+1:i+1+length]
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
        url = ""
        for opt in requestPacket.options:
            if (opt.number == COAP_OPTION_NUMBER.COAP_URI_PATH) and (len(opt.buffer) > 0):
                if url != "":
                    url += "/"
                url += opt.buffer.decode('unicode_escape')

        urlCallback = None
        if url != "":
            urlCallback = self.callbacks.get(url)

        if urlCallback is None:
            print('Callback for url [', url, "] not found")
            self.sendResponse(sourceIp, sourcePort, requestPacket.messageid,
                              None, COAP_RESPONSE_CODE.COAP_NOT_FOUND,
                              COAP_CONTENT_TYPE.COAP_NONE, None)
        else:
            print("redirecting packet to handlers...")
            urlCallback(requestPacket, sourceIp, sourcePort)

    def readBytesFromSocket(self, numOfBytes):
        try:
            return self.sock.recvfrom(numOfBytes)
        except Exception:
            return (None, None)

    def parsePacketHeaderInfo(self, buffer, packet):
        packet.type = (buffer[0] & 0x30) >> 4
        packet.tokenLength = buffer[0] & 0x0F
        packet.code = buffer[1]
        packet.messageid = 0xFF00 & (buffer[2] << 8)
        packet.messageid |= 0x00FF & buffer[3]

    def parsePacketToken(self, buffer, packet):
        if (packet.tokenLength == 0):
            packet.token = None
        elif (packet.tokenLength <= 8):
            packet.token = buffer[4:4+packet.tokenLength]
        else:
            (tempBuffer, tempRemoteAddress) = self.readBytesFromSocket(_BUF_MAX_SIZE - bufferLen)
            if tempBuffer is not None:
                buffer.extend(tempBuffer)
            return False
        return True

    def parsePacketOptionsAndPayload(self, buffer, packet):
        bufferLen = len(buffer)
        if (_COAP_HEADER_SIZE + packet.tokenLength) < bufferLen:
            delta = 0
            bufferIndex = _COAP_HEADER_SIZE + packet.tokenLength
            while (len(packet.options) < _MAX_OPTION_NUM) and\
                  (bufferIndex < bufferLen) and\
                  (buffer[bufferIndex] != 0xFF):
                (status, delta, bufferIndex) = self.parseOption(packet, delta, buffer, bufferIndex)
                if status is False:
                    return False

            if ((bufferIndex + 1) < bufferLen) and (buffer[bufferIndex] == 0xFF):
                packet.payload = buffer[bufferIndex+1:]  # does this works?
            else:
                packet.payload = None
        return True

    def loop(self, blocking=True):
        if self.sock is None:
            return False

        self.sock.setblocking(blocking)
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

            self.parsePacketHeaderInfo(buffer, packet)

            if not self.parsePacketToken(buffer, packet):
                continue

            if not self.parsePacketOptionsAndPayload(buffer, packet):
                return False

            if packet.type == COAP_TYPE.COAP_ACK or\
               packet.code == COAP_RESPONSE_CODE.COAP_NOT_FOUND:
                if self.resposeCallback is not None:
                    self.resposeCallback(packet, remoteAddress)
            else:
                self.handleIncomingRequest(packet, remoteAddress[0], remoteAddress[1])
            return True

        return False

    def poll(self, timeoutMs=-1, pollPeriodMs=500):
        start_time = time.ticks_ms()
        while not self.loop(False) and (time.ticks_diff(time.ticks_ms(), start_time) < timeoutMs):
            time.sleep_ms(pollPeriodMs)

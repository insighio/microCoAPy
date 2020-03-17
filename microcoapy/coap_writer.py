from microcoapy.coap_macros import _BUF_MAX_SIZE
from microcoapy.coap_macros import COAP_VERSION

def CoapOptionDelta(v):
    if v < 13:
        return (0xFF & v)
    elif v <= 0xFF + 13:
        return 13
    else:
        return 14

def writePacketHeaderInfo(buffer, packet):
    # make coap packet base header
    buffer.append(COAP_VERSION.COAP_VERSION_1 << 6)
    buffer[0] |= (packet.type & 0x03) << 4
    # max: 8 bytes of tokens, if token length is greater, it is ignored
    tokenLength = 0
    if (packet.token is not None) and (len(packet.token) <= 0x0F):
        tokenLength = len(packet.token)

    buffer[0] |= (tokenLength & 0x0F)
    buffer.append(packet.method)
    buffer.append(packet.messageid >> 8)
    buffer.append(packet.messageid & 0xFF)

    if tokenLength > 0:
        buffer.extend(packet.token)

def writePacketOptions(buffer, packet):
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

def writePacketPayload(buffer, packet):
    # make payload
    if (packet.payload is not None) and (len(packet.payload)):
        if (len(buffer) + 1 + len(packet.payload)) >= _BUF_MAX_SIZE:
            return 0
        buffer.append(0xFF)
        buffer.extend(packet.payload)

import microcoapy.coap_macros as macros
from microcoapy.coap_option import CoapOption

def parseOption(packet, runningDelta, buffer, i):
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

def parsePacketHeaderInfo(buffer, packet):
    packet.version = (buffer[0] & 0xC0) >> 6
    packet.type = (buffer[0] & 0x30) >> 4
    packet.tokenLength = buffer[0] & 0x0F
    packet.method = buffer[1]
    packet.messageid = 0xFF00 & (buffer[2] << 8)
    packet.messageid |= 0x00FF & buffer[3]

def parsePacketOptionsAndPayload(buffer, packet):
    bufferLen = len(buffer)
    if (macros._COAP_HEADER_SIZE + packet.tokenLength) < bufferLen:
        delta = 0
        bufferIndex = macros._COAP_HEADER_SIZE + packet.tokenLength
        while (len(packet.options) < macros._MAX_OPTION_NUM) and\
              (bufferIndex < bufferLen) and\
              (buffer[bufferIndex] != 0xFF):
            (status, delta, bufferIndex) = parseOption(packet, delta, buffer, bufferIndex)
            if status is False:
                return False

        if ((bufferIndex + 1) < bufferLen) and (buffer[bufferIndex] == 0xFF):
            packet.payload = buffer[bufferIndex+1:]  # does this works?
        else:
            packet.payload = None
    return True

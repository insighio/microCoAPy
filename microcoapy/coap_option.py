class CoapOption:
    def __init__(self, number=-1, buffer=None):
        self.number = number
        byteBuf = bytearray()
        if buffer is not None:
            byteBuf.extend(buffer)
        self.buffer = byteBuf

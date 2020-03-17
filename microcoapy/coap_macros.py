# Macros
_COAP_HEADER_SIZE = 4
_COAP_OPTION_HEADER_SIZE = 1
_COAP_PAYLOAD_MARKER = 0xFF
_MAX_OPTION_NUM = 10
_BUF_MAX_SIZE = 1024
_COAP_DEFAULT_PORT = 5683

def enum(**enums):
    return type('Enum', (), enums)


class CoapResponseCode:
    """ """
    @staticmethod
    def encode(class_, detail):
        """ """
        return ((class_ << 5) | (detail))

    @staticmethod
    def decode(value):
        class_ = (0xE0 & value) >> 5
        detail = 0x1F & value
        return (class_, detail)

COAP_VERSION = enum(
    COAP_VERSION_UNSUPPORTED = 0,
    COAP_VERSION_1 = 1
)

COAP_TYPE = enum(
    COAP_CON=0,
    COAP_NONCON=1,
    COAP_ACK=2,
    COAP_RESET=3
)

COAP_METHOD = enum(
    COAP_EMPTY_MESSAGE=0,
    COAP_GET=1,
    COAP_POST=2,
    COAP_PUT=3,
    COAP_DELETE=4
)

COAP_RESPONSE_CODE = enum(
    COAP_CREATED=CoapResponseCode.encode(2, 1),
    COAP_DELETED=CoapResponseCode.encode(2, 2),
    COAP_VALID=CoapResponseCode.encode(2, 3),
    COAP_CHANGED=CoapResponseCode.encode(2, 4),
    COAP_CONTENT=CoapResponseCode.encode(2, 5),
    COAP_BAD_REQUEST=CoapResponseCode.encode(4, 0),
    COAP_UNAUTHORIZED=CoapResponseCode.encode(4, 1),
    COAP_BAD_OPTION=CoapResponseCode.encode(4, 2),
    COAP_FORBIDDEN=CoapResponseCode.encode(4, 3),
    COAP_NOT_FOUND=CoapResponseCode.encode(4, 4),
    COAP_METHOD_NOT_ALLOWD=CoapResponseCode.encode(4, 5),
    COAP_NOT_ACCEPTABLE=CoapResponseCode.encode(4, 6),
    COAP_PRECONDITION_FAILED=CoapResponseCode.encode(4, 12),
    COAP_REQUEST_ENTITY_TOO_LARGE=CoapResponseCode.encode(4, 13),
    COAP_UNSUPPORTED_CONTENT_FORMAT=CoapResponseCode.encode(4, 15),
    COAP_INTERNAL_SERVER_ERROR=CoapResponseCode.encode(5, 0),
    COAP_NOT_IMPLEMENTED=CoapResponseCode.encode(5, 1),
    COAP_BAD_GATEWAY=CoapResponseCode.encode(5, 2),
    COAP_SERVICE_UNAVALIABLE=CoapResponseCode.encode(5, 3),
    COAP_GATEWAY_TIMEOUT=CoapResponseCode.encode(5, 4),
    COAP_PROXYING_NOT_SUPPORTED=CoapResponseCode.encode(5, 5)
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

COAP_CONTENT_FORMAT = enum(
    COAP_NONE=-1,
    COAP_TEXT_PLAIN=0,
    COAP_APPLICATION_LINK_FORMAT=40,
    COAP_APPLICATION_XML=41,
    COAP_APPLICATION_OCTET_STREAM=42,
    COAP_APPLICATION_EXI=47,
    COAP_APPLICATION_JSON=50,
    COAP_APPLICATION_CBOR=60
)

coapTypeToStringMap={
        COAP_TYPE.COAP_CON:    'CON',
        COAP_TYPE.COAP_NONCON: 'NONCON',
        COAP_TYPE.COAP_ACK:    'ACK',
        COAP_TYPE.COAP_RESET:  'RESET'
    }

def coapTypeToString(type):
    return coapTypeToStringMap.get(type, "INVALID")

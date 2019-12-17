# Macros
_COAP_HEADER_SIZE = 4
_COAP_OPTION_HEADER_SIZE = 1
_COAP_PAYLOAD_MARKER = 0xFF
_MAX_OPTION_NUM = 10
_BUF_MAX_SIZE = 1024
_COAP_DEFAULT_PORT = 5683

def enum(**enums):
    return type('Enum', (), enums)


def CoapResponseCode(class_, detail):
    """ """
    return ((class_ << 5) | (detail))


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

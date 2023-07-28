from enum import Enum

BTSNOOP_HEADER_SIZE = 16
BTSNOOP_PACKET_HEADER_SIZE = 24


class BtSnoopPacketDataType(Enum):
    ORIGINAL_LENGTH = 0
    INCLUDED_LENGTH = 1
    PACKET_FLAGS = 2
    CUMULATIVE_DROPS = 3
    TIMESTAMP_MICROSECONDS = 4
    PACKET_DATA = 5


btSnoopPacketDataFields = {
    BtSnoopPacketDataType.ORIGINAL_LENGTH: {
        'size': 4,
        'offset': 0
    },
    BtSnoopPacketDataType.INCLUDED_LENGTH: {
        'size': 4,
        'offset': 4
    },
    BtSnoopPacketDataType.PACKET_FLAGS: {
        'size': 4,
        'offset': 8
    },
    BtSnoopPacketDataType.CUMULATIVE_DROPS: {
        'size': 4,
        'offset': 12
    },
    BtSnoopPacketDataType.TIMESTAMP_MICROSECONDS: {
        'size': 8,
        'offset': 16
    },
    BtSnoopPacketDataType.PACKET_DATA: {
        'offset': 24
    }
}


def get_n_byte_int(data: bytes, index: int, n: int) -> int:
    value: int = 0
    for i in range(n):
        value += data[index + i] << (8 * (n - i - 1))
    return value


def get_int(data: bytes, packet_index: int, field_type: BtSnoopPacketDataType) -> int:
    if field_type not in btSnoopPacketDataFields.keys():
        raise Exception("Type not defined")
    type_properties = btSnoopPacketDataFields.get(field_type)
    if 'size' not in type_properties.keys():
        raise Exception("Type does not have a fixed size.")
    if 'offset' not in type_properties.keys():
        raise Exception("Type does not have a fixed offset.")
    return get_n_byte_int(data, packet_index + type_properties.get('offset'), type_properties.get('size'))


def get_bytes(data: bytes, packet_index: int, field_type: BtSnoopPacketDataType, size: int | None = None) -> bytes:
    if field_type not in btSnoopPacketDataFields.keys():
        raise Exception("Type not defined")
    type_properties = btSnoopPacketDataFields.get(field_type)
    if 'size' not in type_properties.keys() and size is None:
        raise Exception("Type does not have a fixed size.")
    if 'offset' not in type_properties.keys():
        raise Exception("Type does not have a fixed offset.")
    if size is None:
        size: int = type_properties.get('size')
    return data[packet_index + type_properties.get('offset'): packet_index + type_properties.get('offset') + size]


def get_field_size(field_type: BtSnoopPacketDataType) -> int:
    if field_type not in btSnoopPacketDataFields.keys():
        raise Exception("Type not defined")
    type_properties = btSnoopPacketDataFields.get(field_type)
    if 'size' not in type_properties.keys():
        raise Exception("Type does not have a fixed size.")
    return type_properties.get('size')


def get_field_offset(field_type: BtSnoopPacketDataType) -> int:
    if field_type not in btSnoopPacketDataFields.keys():
        raise Exception("Type not defined")
    type_properties = btSnoopPacketDataFields.get(field_type)
    return type_properties.get('offset')


def get_packet_record(data: bytes, packet_index: int) -> bytes:
    included_length: int = get_int(data, packet_index, BtSnoopPacketDataType.INCLUDED_LENGTH)
    return data[packet_index:packet_index + BTSNOOP_PACKET_HEADER_SIZE + included_length]


def get_packet_header(data: bytes, packet_index: int) -> bytes:
    return data[packet_index:packet_index + BTSNOOP_PACKET_HEADER_SIZE]

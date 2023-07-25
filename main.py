#! /usr/bin/env python

import sys


def get_4_byte_int(data, index):
    return (data[index] << 24) + (data[index + 1] << 16) + (data[index + 2] << 8) + data[index + 3]


def dump(b):
    print(''.join('{:02x}'.format(x) for x in b))


def fix_contents(in_contents):
    packet_idx = 8 + 4 + 4
    contents = in_contents[:packet_idx]
    previous_packet = None
    previous_len = 0
    packet_counter = 0
    time_signature = in_contents[packet_idx + 16:packet_idx + 24]
    while packet_idx < len(in_contents):
        broken = False
        original_length = get_4_byte_int(in_contents, packet_idx)
        included_length = get_4_byte_int(in_contents, packet_idx + 4)
        if original_length < included_length:
            print(f"\033[01m\033[31mBroken packet ({packet_counter}): \033[0mOriginal packet length is smaller than included packet length")
            broken = True
        if included_length + packet_idx + 24 > len(in_contents):
            print(f"\033[01m\033[31mBroken packet ({packet_counter}): \033[0mIncluded packet length is greater than file size.")
            broken = True
        if not broken:
            if previous_packet is not None:
                contents += previous_packet
            previous_packet = in_contents[packet_idx:packet_idx + included_length + 24]
            previous_len = included_length
            time_signature = in_contents[packet_idx + 16:packet_idx + 24]
            packet_idx += included_length + 24
        else:
            time_signature_bytes = 7                        # Try to match 7 bytes from the timestamp first
            print("\033[01m\033[36mBroken header: \033[0m", end="")
            dump(in_contents[packet_idx:packet_idx + 24])
            match = False
            match_idx = None

            while not match and time_signature_bytes > 1:
                (match, match_idx) = match_time_signature(in_contents, packet_idx - previous_len, min(packet_idx, len(in_contents) - len(time_signature)), time_signature[:time_signature_bytes])
                if not match:
                    (match, match_idx) = match_time_signature(in_contents, packet_idx, len(in_contents) - len(time_signature), time_signature[:time_signature_bytes])
                    if not match:
                        time_signature_bytes -= 1
                    else:
                        if previous_packet is not None:
                            contents += previous_packet  # Append previous packet as it seems to be okay.
                            previous_packet = None

            if not match:
                print("\033[31mBroken packet is non-recoverable.\033[0m")
                sys.exit(2)
            else:
                print(f"\033[32mPresumed packet found with {time_signature_bytes} bytes matching the last time signature.\033[0m")
                packet_idx = match_idx - 16
                previous_packet = None
        packet_counter += 1
    return contents


def match_time_signature(data, start, end, time_signature):
    match = False
    match_idx = None
    for i in range(start, end):
        match_idx = i
        match = True
        for j in range(len(time_signature)):
            if time_signature[j] != data[i + j]:
                match = False
                break
        if match:
            break
    return match, match_idx


def repair_file():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <filename>")
        sys.exit(1)

    in_file = open(sys.argv[1], 'rb')
    in_contents = in_file.read()
    out_contents = fix_contents(in_contents)
    out_file = open(f'{sys.argv[1]}.fixed', 'wb')
    out_file.write(out_contents)
    in_file.close()
    out_file.close()


if __name__ == '__main__':
    repair_file()

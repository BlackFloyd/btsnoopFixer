#! /usr/bin/env python

import sys
import argparse


def get_4_byte_int(data, index) -> int:
    return (data[index] << 24) + (data[index + 1] << 16) + (data[index + 2] << 8) + data[index + 3]


def get_8_byte_int(data, index) -> int:
    return (get_4_byte_int(data, index) << 32) + get_4_byte_int(data, index + 4)


def dump(b):
    print(''.join('{:02x}'.format(x) for x in b))


def fix_contents(in_contents, args) -> bytes:
    packet_idx = 8 + 4 + 4
    contents = in_contents[:packet_idx]
    previous_packet = None
    previous_len = 0
    previous_cumulative_drops = 0
    previous_time = 0
    packet_counter = 0
    time_signature = in_contents[packet_idx + 16:packet_idx + 24]
    while packet_idx < len(in_contents):
        broken = False
        original_length = get_4_byte_int(in_contents, packet_idx)
        included_length = get_4_byte_int(in_contents, packet_idx + 4)
        cumulative_drops = get_4_byte_int(in_contents, 12)
        time = get_8_byte_int(in_contents, packet_idx + 16)

        if included_length + packet_idx + 24 > len(in_contents):
            print(f"\033[01m\033[31mBroken packet ({packet_counter}): \033[0mIncluded packet length is greater than file size.")
            broken = True
        if args.length and original_length < included_length:
            print(f"\033[01m\033[31mBroken packet ({packet_counter}): \033[0mOriginal packet length is smaller than included packet length.")
            broken = True
        if args.drop and cumulative_drops < previous_cumulative_drops:
            print(f"\033[01m\033[31mBroken packet ({packet_counter}): \033[0mCumulative drops decreased.")
            broken = True
        if args.time and time < previous_time:
            print(f"\033[01m\033[31mBroken packet ({packet_counter}): \033[0mTime went backwards.")
            broken = True

        if not broken:
            if previous_packet is not None:
                contents += previous_packet
            previous_packet = in_contents[packet_idx:packet_idx + included_length + 24]
            previous_len = included_length
            time_signature = in_contents[packet_idx + 16:packet_idx + 24]
            packet_idx += included_length + 24
            previous_cumulative_drops = cumulative_drops
            previous_time = time
        else:
            time_signature_bytes = 7
            print("\033[01m\033[36mBroken header: \033[0m", end="")
            dump(in_contents[packet_idx:packet_idx + 24])
            match = False
            match_idx = None

            while not match and time_signature_bytes > 1:
                # Backwards seek
                (match, match_idx) = match_time_signature(in_contents, packet_idx - previous_len, min(packet_idx, len(in_contents) - len(time_signature)), time_signature[:time_signature_bytes])
                if not match:
                    # Forwards seek
                    (match, match_idx) = match_time_signature(in_contents, packet_idx, len(in_contents) - len(time_signature), time_signature[:time_signature_bytes])
                    if not match:
                        # None of the seeks yielded a result. Trying to match less bytes of the timestamp
                        time_signature_bytes -= 1
                    else:
                        if previous_packet is not None:
                            # Forwards seek succeeded - previous packet was okay
                            contents += previous_packet
                            previous_packet = None

            if not match:
                print("\033[31mBroken packet is non-recoverable.\033[0m")
                sys.exit(2)
            else:
                print(f"\033[32mPresumed packet found with {time_signature_bytes} bytes matching the last time signature.\033[0m")
                packet_idx = match_idx - 16
                previous_packet = None
        packet_counter += 1
    if previous_packet is not None:
        contents += previous_packet
    return contents


def match_time_signature(data, start, end, time_signature) -> (bool, int):
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


def parse_args():
    parser = argparse.ArgumentParser(description="Fix broken BT Snoop files ")
    parser.add_argument('broken_file', help="Path of the broken BT Snoop log", type=argparse.FileType('rb'))
    parser.add_argument('destination_file', help="Path to write the fixed file to", type=argparse.FileType('wb'))
    parser.add_argument('-l', '--length', help="Check length sanity", action="store_true")
    parser.add_argument('-d', '--drop', help="Check drop sanity", action="store_true")
    parser.add_argument('-t', '--time', help="Check time sanity", action="store_true")
    return parser.parse_args()


def repair_file():
    args = parse_args()

    in_contents = args.broken_file.read()
    out_contents = fix_contents(in_contents, args)
    args.destination_file.write(out_contents)

    print(f"\033[32mRecovery completed. The new file should be fine.\033[0m")


if __name__ == '__main__':
    repair_file()

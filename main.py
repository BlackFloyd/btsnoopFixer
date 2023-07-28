#! /usr/bin/env python

import sys
import argparse
from BTSnoop import *

FORWARD_TIME_THRESHOLD_MICROSECONDS = 1000 * 1000 * 60 * 60 * 24 * 365  # About one year


def dump(b: bytes):
    print(''.join('{:02x}'.format(x) for x in b))


def fix_contents(in_contents: bytes, args) -> bytes:
    packet_idx: int = BTSNOOP_HEADER_SIZE
    contents: bytes = in_contents[:BTSNOOP_HEADER_SIZE]
    previous_packet: bytes | None = None
    previous_len: int = 0
    previous_cumulative_drops: int = 0
    previous_time: int | None = None
    packet_counter: int = 0
    time_signature: bytes = get_bytes(in_contents, BTSNOOP_HEADER_SIZE, BtSnoopPacketDataType.TIMESTAMP_MICROSECONDS)
    while packet_idx < len(in_contents):
        broken: bool = False
        original_length: int = get_int(in_contents, packet_idx, BtSnoopPacketDataType.ORIGINAL_LENGTH)
        included_length: int = get_int(in_contents, packet_idx, BtSnoopPacketDataType.INCLUDED_LENGTH)
        cumulative_drops: int = get_int(in_contents, packet_idx, BtSnoopPacketDataType.CUMULATIVE_DROPS)
        time: int = get_int(in_contents, packet_idx, BtSnoopPacketDataType.TIMESTAMP_MICROSECONDS)

        if included_length + packet_idx + 24 > len(in_contents):
            print(f"\033[01m\033[31mBroken packet ({packet_counter}): \033[0mIncluded packet length is greater than file size.")
            broken = True
        if args.length and original_length < included_length:
            print(f"\033[01m\033[31mBroken packet ({packet_counter}): \033[0mOriginal packet length is smaller than included packet length.")
            broken = True
        if args.drop and cumulative_drops < previous_cumulative_drops:
            print(f"\033[01m\033[31mBroken packet ({packet_counter}): \033[0mCumulative drops decreased.")
            broken = True
        if args.time and previous_time is not None and time < previous_time:
            print(f"\033[01m\033[31mBroken packet ({packet_counter}): \033[0mTime went backwards.")
            broken = True
        if args.forward_time and previous_time is not None and time - previous_time > FORWARD_TIME_THRESHOLD_MICROSECONDS:
            print(f"\033[01m\033[31mBroken packet ({packet_counter}): \033[0mTime progressed more than a year.")
            broken = True

        if not broken:
            if previous_packet is not None:
                contents += previous_packet
            previous_packet = get_packet_record(in_contents, packet_idx)
            previous_len = included_length
            time_signature = get_bytes(in_contents, BTSNOOP_HEADER_SIZE, BtSnoopPacketDataType.TIMESTAMP_MICROSECONDS)
            packet_idx += included_length + BTSNOOP_PACKET_HEADER_SIZE
            previous_cumulative_drops = cumulative_drops
            previous_time = time
        else:
            time_signature_bytes: int = get_field_size(BtSnoopPacketDataType.TIMESTAMP_MICROSECONDS) - 1
            print("\033[01m\033[36mBroken header: \033[0m", end="")
            dump(get_packet_header(in_contents, packet_idx))
            match: bool = False
            match_idx: int | None = None

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
                print("\033[31mBroken packet is non-recoverable. The resulting file will end before this packet.\033[0m")
                return contents
            else:
                print(f"\033[32mPresumed packet found with {time_signature_bytes} bytes matching the last time signature.\033[0m")
                packet_idx = match_idx - 16
                previous_packet = None
        packet_counter += 1
    if previous_packet is not None:
        contents += previous_packet
    return contents


def match_time_signature(data: bytes, start: int, end: int, time_signature: bytes) -> (bool, int):
    match: bool = False
    match_idx: int | None = None
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
    parser: argparse.ArgumentParser = argparse.ArgumentParser(description="Fix broken BT Snoop files ")
    parser.add_argument('broken_file', help="Path of the broken BT Snoop log", type=argparse.FileType('rb'))
    parser.add_argument('destination_file', help="Path to write the fixed file to", type=argparse.FileType('wb'))
    parser.add_argument('-l', '--length', help="Check Length Sanity", action="store_true")
    parser.add_argument('-d', '--drop', help="Check Drop Sanity", action="store_true")
    parser.add_argument('-t', '--time', help="Check Time Sanity", action="store_true")
    parser.add_argument('-f', '--forward-time', help="Forward Time Sanity", action="store_true")
    return parser.parse_args()


def repair_file():
    args = parse_args()

    in_contents: bytes = args.broken_file.read()
    out_contents: bytes = fix_contents(in_contents, args)
    args.destination_file.write(out_contents)

    print(f"\033[32mRecovery completed. The new file should be fine.\033[0m")


if __name__ == '__main__':
    repair_file()

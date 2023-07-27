# BT Snoop Fixer

A simple tool that tries to fix broken BT Snoop logs files.

## Why?!

I recently encountered some broken BT Snoop files that I absolutely needed for debugging.
Fixing them manually was certainly possible, but tedious and way more time-consuming than writing a small tool.
I'm just putting this out there in case it helps somebody ;)

## Usage

Actually nothing fancy:

```commandline
$ python main.py <broken_btsnoop.log>
```

## How it works

### The error this fixes

BT Snoop files are pretty simple. They consist of a file header followed by the packets records.
Those records themselves consist of a header and the actual packet data.
Because this data can vary in length, this length is being saved to the header of the packet record.
If everything goes well (which it usually does), a program can navigate this file by using this recorded length.
If, however, something goes horribly wrong (like in my case), the file might be missing some data (or vice-versa).
In that case the packet records won't line up anymore and whatever software is trying to read the file will just fail.

### How to detect it

There are a few ways to detect those errors. This program currently uses two of them.
Both of rely on checking the packet lengths provided by the files.
If the file reports a packet that would exceed the file itself, that's an obvious error.
Furthermore, this tool checks if the packet data included in the record is larger than the original packet data.
This would also indicate an error.
My goal is to also check the timestamps for sanity, but this should be optional as it might break as soon as a clock skew is corrected.

### What to do about it?

If this tool encounters an error it will first assume the previous packet to be broken.
It will then check for the last known good timestamp it has read and try to find a similar timestamp within the previous packet.
If it doesn't find one, it will assume the previous packet to be good and seek forward, again looking for such a timestamp.
As soon as it finds another timestamp, it will discard any data that is known to be bad and realign the packet records.

This method relies on assumptions and - well - guessing. But it seems to work pretty well in my environment and there's no harm in trying,

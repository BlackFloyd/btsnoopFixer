# BT Snoop Fixer

A simple tool that tries to fix broken BT Snoop log files.

## Why?!

I recently encountered some broken BT Snoop files that I absolutely needed for debugging.
Fixing them manually was certainly possible, but tedious and way more time-consuming than writing a small tool.
I'm just putting this out there in case it helps somebody ;)

## Usage

Actually nothing fancy:

```commandline
$ python main.py <broken_btsnoop.log> <fixed_file.log>
```

Furthermore, there are error detection methods available:

```commandline
-l, --length        Check Length Sanity
-d, --drop          Check Drop Sanity
-t, --time          Check Time Sanity
-f, --forward-time  Forward Time Sanity
```

These options are unsafe in rare cases, but they may yield better results whenever this tool misses errors.
See below for a detailed description.

## How It Works

### The Error This Fixes

BT Snoop files are pretty simple. They consist of a file header followed by the packet records.
Those records themselves consist of a header and the actual packet data.
Because this data can vary in length, this length is being saved to the header of the packet record.
If everything goes well (which it usually does), a program can navigate this file by using this recorded length.
If, however, something goes horribly wrong (like in my case), the file might be missing some data (or vice-versa).
In that case the packet records won't line up anymore and whatever software is trying to read the file will just fail.

### How To Detect It

There are a few ways to detect those errors. By default, only file breaking packet lengths will be detected and fixed.
In most cases none of the checks should yield any false positives, but as they might still do it, all but the Exceeding Size check are disabled by default.

#### Exceeding Size Check

This check is always enabled as it is required to produce a readable file.
Whenever a packet record would - according to its header - exceed the file, an error is detected.
The check is performed by comparing the Included Length Field with the file size.

#### Size Sanity

The Size Sanity Check will report an error whenever the Included Length is reported to be bigger than the Original Length.
This shouldn't really happen this way round, so this option is pretty safe to enable.

#### Drop Sanity

Drop Sanity will check for the Cumulative Drops reported by the packet record.
This number should only increase throughout the file.
This detection may theoretically be triggered by an overflow.
Usually this shouldn't happen so it should be relatively safe to enable. 

#### Time Sanity

Time Sanity compares the current packet record's timestamp to that of the last one.
If the timestamp decreased, this check will report an error.
This may however be triggered if the sniffing host updated its clock, so it has some potential for false positives.

#### Forward Time Sanity

Forward Time Sanity also compares two timestamps,
but this time it will report an error if more than one year elapsed between two packet records.
This obviously may flag valid packet records as invalid, but it adds a great layer of protection against sneaky errors.

### What To Do About It?

If this tool encounters an error it will first assume the previous packet to be broken.
It will then check for the last known good timestamp it has read and try to find a similar timestamp within the previous packet.
If it doesn't find one, it will assume the previous packet to be good and seek forward, again looking for such a timestamp.
As soon as it finds another timestamp, it will discard any data that is known to be bad and realign the packet records.

This method relies on assumptions and - well - guessing. But it seems to work pretty well in my environment and there's no harm in trying.

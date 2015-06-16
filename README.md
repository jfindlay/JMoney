# JMoney CDDA ripper

JMoney uses cdparanoia to rip CDDA tracks and retrieves disc and track info
from freedb.  A directory is created for each disc.  The disc directory and
tracks are named according to the freedb lookup of the disc ID.  If more than
one freedb record matches the disc ID, the user must select the preferred
record for disc and track names.  If there are no freedb records for the disc
ID, then the disc ID is used for the disc directory name and cdparanoia default
names are used for the track names.  All records retrieved from freedb are
stored as yaml in a file in the disc directory.

A separate script yet to be written will convert each track to flac format.

## Example
```console
# insert a disc into the drive
$ rip.py --help | less
$ time rip.py --device /dev/sr0 --library-dir ${HOME}/Music --read-speed 8
```

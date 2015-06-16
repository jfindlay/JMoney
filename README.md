# JMoney CDDA ripper

JMoney uses cdparanoia to rip CDDA track files and retrieves disc and track
info from freedb.  A directory is created for each disc.  The disc directory
and track files are named according to the freedb lookup of the disc ID.  If
more than one freedb record matches the disc ID, the user must select the
preferred record for disc and track names.  If there are no freedb records for
the disc ID, then the disc ID is used for the disc directory name and
cdparanoia default names are used for the track file names.  All records
retrieved from freedb are stored as yaml in a file in the disc directory.

JMoney can also encode ripped tracks into flac format.  This can be done as a
second step in the ripping process, for a single disc directory or for the
entire library.

## Examples
```console
# insert a disc into the drive
$ ./jmoney --help | less
$ time ./jmoney --device /dev/sr0 --library-dir ${HOME}/Music --read-speed 8 rip
$ time ./jmoney --no-verify-encoding encode
```
```console
# rip and encode a single disc
$ time ./jmoney rip encode
# encode all wav files in the library
$ time ./jmoney encode
```

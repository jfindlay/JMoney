# JMoney optical disc ripper

## CDDA

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

## DVD/BluRay

In video mode, JMoney uses makemkvcon to rip DVD/BluRay discs.  You will need
to provide makemkvcon with your own product key, if necessary.

## Examples

```console
# Install
$ git clone https://github.com/jfindlay/jmoney.git ; cd jmoney
$ ./jmoney --help
```
```console
# Rip a CDDA
$ time ./jmoney --type audio --device /dev/sr0 --library-dir ${HOME}/Music --read-speed 8
```
```console
# Rip a DVD/BluRay
$ time ./jmoney --type video --video-dir ${HOME}/Videos/Napoleon_Dynamite
```

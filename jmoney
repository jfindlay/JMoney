#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os
import sys
import six
import yaml
from pprint import pprint
from time import sleep
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, FileType
from subprocess import call

import DiscID, CDDB
try:
    import discogs_client
    HAS_DISCOGS=True
except ImportError:
    HAS_DISCOGS=False


exit_codes = {'disc_drive': 11,
              'freedb_query': 21,
              'disc_dir': 31,
              'rip_disc': 41}


def encode_dict(d, encoding='UTF-8'):
    '''
    encode top level key and value strings in `d` in `encoding`
    '''
    codings = ['iso-8859-1']  # list of codings to try
    transcoded_d = {}
    for k,v in d.items():
        for coding in codings:
            try:
                if isinstance(k, six.string_types):
                    k = k.decode(coding).encode(encoding)
                if isinstance(v, six.string_types):
                    v = v.decode(coding).encode(encoding)
            except UnicodeDecodeError:
                pass
            transcoded_d[k] = v
    return transcoded_d


class CDDrive(object):
    '''
    interaction with CD drive
    '''
    def __init__(self, opts):
        '''
        setup options
        '''
        self.opts = opts

    def close(self):
        '''
        close disc drive drawer
        '''
        if call(['eject', '-t']) != 0:
            print('\nFailed to close disc drive drawer')
            sys.exit(exit_codes['disc_drive'])

    def open(self):
        '''
        open disc drive drawer
        '''
        if call(['eject']) != 0:
            print('\nFailed to open disc drive')
            sys.exit(exit_codes['disc_drive'])


class FreeDB(object):
    '''
    interaction with freedb
    '''
    def __init__(self, opts):
        '''
        setup parameters, options
        '''
        self.opts = opts
        self.client_name, self.client_version = opts['agent'].split('/')
        self.disc_id = DiscID.disc_id(DiscID.open(opts['device']))
        self.db_record = [{'disc_id': self.disc_id}]

        self.get_disc_info()
        self.get_track_info()
        self.get_preferred()

    def get_disc_info(self):
        '''
        retrieve disc info
        '''
        status, results = CDDB.query(self.disc_id,
                                     server_url=self.opts['freedb_mirror'],
                                     client_name=self.client_name,
                                     client_version=self.client_version)

        if not str(status).startswith('2'):
            print('Failed to query freedb mirror "{0}" for disc info on disc_id "{1}": '
                  'HTTP code {2}'.format(self.opts['freedb_mirror'], self.disc_id[0], status))
            sys.exit(exit_codes['freedb_query'])

        # a single result will not be enclosed in a list by the CDDB lib
        results = [results] if isinstance(results, dict) else results

        self.results = [encode_dict(result) for result in results]

    def get_track_info(self):
        '''
        retrieve track info for each result
        '''
        for num, result in enumerate(self.results):
            print('\n===== Result {0:>02} =====\n'.format(num + 1))
            pprint(result) ; print('')
            sleep(1)  # throttle query rate
            status, track_info = CDDB.read(result['category'],
                                           result['disc_id'],
                                           server_url=self.opts['freedb_mirror'],
                                           client_name=self.client_name,
                                           client_version=self.client_version)

            if not str(status).startswith('2'):
                print('Failed to query freedb mirror {0} for track info: '
                      'HTTP code {1}'.format(self.opts['freedb_mirror'], status))
                sys.exit(exit_codes['freedb_query'])

            track_info = encode_dict(track_info)
            self.db_record.append({'disc_info': result, 'track_info': track_info})

            for track in range(self.disc_id[1]):
                print('Track {0:>02d}: {1}'.format(track + 1, track_info['TTITLE{0}'.format(track)]))
        print('\n=====================\n')

    def get_preferred(self):
        '''
        get preferred info set
        '''
        if len(self.results) > 1:
            valid_selection = False
            while valid_selection == False:
                try:
                    select_range = '[1-{0}]'.format(len(self.results))
                    selected_result_num = int(input('Select a preferred result {0}: '.format(select_range)))
                except Exception:
                    selected_result_num = None
                if selected_result_num in range(1, len(self.results) + 1):
                    valid_selection = True
                    selected_result = self.results[selected_result_num - 1]
                    self.db_record[selected_result_num]['preferred'] = True
                else:
                    print('Invalid selection')
        elif len(self.results) == 1:
            selected_result = self.results[0]
            self.db_record[1]['preferred'] = True
        else:
            print('\nNo freedb results found for disc')

        if len(self.results):
            print('\nSelected result: {0}\n'.format(selected_result['title']))


class Discogs(object):
    '''
    interaction with discogs
    '''
    def __init__(self, opts):
        '''
        setup options
        '''
        if not HAS_DISCOGS:
            print('discogs client library is unavailable')
        else:
            self.opts = opts
            self.d = discogs_client.Client(self.opts['agent'],
                                           user_token=self.opts['token'])

    def query(self, search):
        '''
        query discogs database
        '''
        if not HAS_DISCOGS:
            print('discogs client library is unavailable')
        else:
            results = self.d.search('Stockholm By Night', type='release')
            artist = results[0].artists[0]
            releases = d.search('Bit Shifter', type='artist')[0].releases[1].versions[0].labels[0].releases
            for release in releases:
                print(release)


class CDParanoia(object):
    '''
    interaction with cdparanoia
    '''
    def __init__(self, opts, db_record):
        '''
        setup options and disc information
        '''
        self.opts = opts
        self.db_record = db_record

        self.setup_dir()
        self.rip_tracks()
        self.rename_tracks()
        self.save_db_record()

    def setup_dir(self):
        '''
        setup disc directory
        '''
        disc_dir = ''
        self.preferred = 0
        for number, entry in enumerate(self.db_record):
            if 'preferred' in entry:
                self.preferred = number
                disc_dir = entry['disc_info']['title'].replace('/', '::')
        if not disc_dir:
            disc_dir = self.db_record[0]['disc_id'][0]

        self.dest_dir = os.path.join(self.opts['library_dir'], disc_dir)
        if os.path.exists(self.dest_dir):
            if self.opts['force']:
                for track in os.listdir(self.dest_dir):
                    os.remove(track)
                os.rmdir(self.dest_dir)
            else:
                print('Destination directory, "{0}", exists'.format(self.dest_dir))
                sys.exit(exit_codes['disc_dir'])
        else:
            os.makedirs(self.dest_dir)

    def rip_tracks(self):
        '''
        rip all tracks from the disc
        '''
        cmd = ['cdparanoia', '--log-debug=/dev/null',
                             '--log-summary=/dev/null',
                             '--output-wav',
                             '--batch',
                             '--force-read-speed={0}'.format(self.opts['read_speed']),
                             '--never-skip']
        if call(cmd, cwd=self.dest_dir) != 0:
            print('\nFailed to rip disc')
            sys.exit(exit_codes['rip_disc'])

    def rename_tracks(self):
        '''
        rename ripped tracks
        '''
        # not all discs have a TOC track it seems
        TOC_source = os.path.join(self.dest_dir, 'track00.cdda.wav')
        if os.path.exists(TOC_source):
            TOC_dest = os.path.join(self.dest_dir, '00 - disc TOC.wav')
            os.rename(TOC_source, TOC_dest)

        if self.preferred:
            for track_number in range(self.db_record[0]['disc_id'][1]):
                old_name = 'track{0:02}.cdda.wav'.format(track_number + 1)
                track_name = self.db_record[self.preferred]['track_info']['TTITLE{0}'.format(track_number)]
                new_name = '{0:02} - {1}.wav'.format(track_number + 1, track_name)
                os.rename(os.path.join(self.dest_dir, old_name), os.path.join(self.dest_dir, new_name))

    def save_db_record(self):
        '''
        save database record in disc directory
        '''
        if len(self.db_record) == 1:
            print('\nNo CDDA database records were found for {0}; '
                  'you will need to name the disc directory, {1}, and tracks manually'
                  ''.format(self.db_record[0]['disc_id'][0], self.dest_dir))

        with open(os.path.join(self.dest_dir, '00 - disc info.yaml'), 'wb') as disc_record:
            disc_record.write(yaml.dump(self.db_record))


class FLAC(object):
    '''
    flac interaction
    '''
    def __init__(self, opts, disc_dir=None):
        '''
        setup opts
        '''
        self.opts = opts
        if disc_dir:
            self.rip_dir = disc_dir

    def encode(self):
        '''
        encode all `*.wav` files in the disc directory
        '''
        def encode_disc(cmd, disc_dir):
            '''
            encode all the tracks from a disc
            '''
            for track_name in os.listdir(disc_dir):
                if track_name.endswith('.wav'):
                    call(cmd, cwd=disc_dir)

        cmd = ['flac', '--keep-foreign-metadata']
        if self.opts['verify_encoding']:
            cmd.append('--verify')
        if not self.opts['keep_wav']:
            cmd.append('--delete-input-file')

        if hasattr(self, 'rip_dir'):
            encode_disc(cmd, self.rip_dir)
        elif self.opts['disc_dir']:
            encode_disc(cmd, self.disc_dir)
        else:
            for disc_dir in self.opts['library_dir']:
                encode_disc(cmd, disc_dir)


def get_opts():
    '''
    setup program options
    '''
    script_dir = os.path.split(__file__)[0]
    agent_file = os.path.join(script_dir, 'agent')
    token_file = os.path.join(script_dir, 'token')

    library_dir = os.path.join(os.environ['HOME'], 'Music')

    def parse_args():
        '''
        process invocation arguments
        '''
        desc = 'rip CDDA discs and flac encode and tag the tracks with info from a CDDA database'
        parser = ArgumentParser(description=desc, formatter_class=ArgumentDefaultsHelpFormatter)
        parser.add_argument('action',
                            nargs='*',
                            help='`rip`: rip CDDA tracks, `encode`: encode tracks in flac format; '
                                 'if both arguments are given, the disc is ripped '
                                 'and the tracks are encoded sequentially as a single operation, '
                                 'otherwise if only `rip` is given, only ripping occurs, or '
                                 'if only `encode` is specified, all unencoded tracks in the library dir are encoded')
        parser.add_argument('-d', '--device',
                            type=str,
                            default='/dev/sr0',
                            help='CD drive device name')
        parser.add_argument('-a', '--agent-file',
                            type=FileType('rb'),
                            default=agent_file,
                            help='file containing HTTP client agent name and version conforming to RFC 1945 §3.7')
        parser.add_argument('-t', '--token-file',
                            type=FileType('rb'),
                            default=token_file,
                            help='file containing discogs API token')
        parser.add_argument('-m', '--freedb-mirror',
                            type=str,
                            default='http://freedb.freedb.org/~cddb/cddb.cgi',
                            help='freedb mirror URL')
        parser.add_argument('-l', '--library-dir',
                            type=str,
                            default=library_dir,
                            help='base directory of music library')
        parser.add_argument('-s', '--read-speed',
                            type=str,
                            default=8,
                            help='disc drive read speed')
        parser.add_argument('-f', '--force',
                            action='store_true',
                            help='overwrite existing disc directory if it exists')
        parser.add_argument('-v', '--verify-encoding',
                            action='store_false',
                            help='verify that flac encoded files match their source wav files')
        parser.add_argument('-k', '--keep-wav',
                            action='store_true',
                            help='do not delete wave files after successful flac encoding')
        parser.add_argument('-e', '--encode-dir',
                            type=str,
                            help='encode the tracks in a specific disc dir')

        return vars(parser.parse_args())

    opts = parse_args()

    opts['agent'] = opts['agent_file'].read().strip() ; del opts['agent_file']
    opts['token'] = opts['token_file'].read().strip() ; del opts['token_file']
    opts['action'] = set(opts['action'])

    return opts


def main():
    '''
    rip CDDA discs and flac encode and tag the tracks with info from a CDDA
    database
    '''
    opts = get_opts()

    if 'rip' in opts['action']:
        cd_drive = CDDrive(opts)
        cd_drive.close()

        freedb = FreeDB(opts)
        cdparanoia = CDParanoia(opts, freedb.db_record)

    if {'rip', 'encode'} == opts['action']:
        flac = FLAC(opts, cdparanoia.dest_dir)
    elif 'encode' in opts['action']:
        flac = FLAC(opts)

    if 'rip' in opts['action']:
        cd_drive.open()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

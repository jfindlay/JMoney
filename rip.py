#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
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


def setup(opts):
    '''
    load disc drive
    '''
    if call(['eject', '-t']) != 0:
        print('\nFailed to close disc drive')
        sys.exit(1)


def freedb(opts):
    '''
    query freedb
    '''
    client_name, client_version = opts['agent'].split('/')

    # get disc info
    disc_id = DiscID.disc_id(DiscID.open(opts['device']))
    status, results = CDDB.query(disc_id,
                                 server_url=opts['freedb_mirror'],
                                 client_name=client_name,
                                 client_version=client_version)
    db_record = [{'disc_id': disc_id}]

    if not str(status).startswith('2'):
        print('Failed to query freedb mirror {0} for disc info: HTTP code {1}'.format(opts['freedb_mirror'], status))
        sys.exit(2)

    if isinstance(results, dict):  # only one result found
        results = [results]

    # get track info
    for num, result in enumerate(results):
        print('\n===== Result {0:>02} =====\n'.format(num + 1))
        pprint(result) ; print('')
        sleep(1)  # throttle query rate
        status, track_info = CDDB.read(result['category'],
                                       result['disc_id'],
                                       server_url=opts['freedb_mirror'],
                                       client_name=client_name,
                                       client_version=client_version)
        db_record.append({'disc_info': result, 'track_info': track_info})
        if not str(status).startswith('2'):
            print('Failed to query freedb mirror {0} for track info: HTTP code {1}'.format(opts['freedb_mirror'], status))
            sys.exit(2)

        for track in range(disc_id[1]):
            print('Track {0:>02d}: {1}'.format(track + 1, track_info['TTITLE{0}'.format(track)]))
    print('\n=====================\n')

    # get preferred info set
    if len(results) > 1:
        valid_selection = False
        while valid_selection == False:
            try:
                select_range = '[1-{0}]'.format(len(results))
                selected_result_num = int(input('Select a preferred result {0}: '.format(select_range)))
            except Exception:
                selected_result_num = None
            if selected_result_num in range(1, len(results) + 1):
                valid_selection = True
                selected_result = results[selected_result_num - 1]
                db_record[selected_result_num]['preferred'] = True
            else:
                print('Invalid selection')
    elif len(results) == 1:
        selected_result = results[0]
        db_record[1]['preferred'] = True
    else:
        print('\nNo freedb results found for disc')

    if len(results):
        print('\nSelected result: {0}\n'.format(selected_result['title']))

    return db_record


def discogs(opts):
    '''
    query discogs
    '''
    if not HAS_DISCOGS:
        print('discogs client library is unavailable')
        return

    d = discogs_client.Client(opts['agent'], user_token=opts['token'])
    results = d.search('Stockholm By Night', type='release')
    artist = results[0].artists[0]
    releases = d.search('Bit Shifter', type='artist')[0].releases[1].versions[0].labels[0].releases
    for release in releases:
        print(release)


def rip(opts, db_record):
    '''
    use cdparanoia to rip disc and rename ripped track files
    '''
    # setup directory
    disc_dir = ''
    preferred = 0
    for number, entry in enumerate(db_record):
        if 'preferred' in entry:
            preferred = number
            disc_dir = entry['disc_info']['title'].replace('/', '::')
    if not disc_dir:
        disc_dir = db_record[0]['disc_id'][0]

    dest_dir = os.path.join(opts['library_dir'], disc_dir)
    if os.path.exists(dest_dir):
        print('Destination directory exists')
        sys.exit(3)
    else:
        os.makedirs(dest_dir)

    # rip tracks
    cmd = ['cdparanoia', '--log-debug=/dev/null',
                         '--log-summary=/dev/null',
                         '--output-wav',
                         '--batch',
                         '--force-read-speed={0}'.format(opts['read_speed']),
                         '--never-skip']
    if call(cmd, cwd=dest_dir) != 0:
        print('\nFailed to rip disc')
        sys.exit(4)

    # rename ripped tracks
    os.rename(os.path.join(dest_dir, 'track00.cdda.wav'), os.path.join(dest_dir, '00 - CDDA TOC.wav'))
    if preferred:
        for track_number in range(db_record[0]['disc_id'][1]):
            old_name = 'track{0:02}.cdda.wav'.format(track_number + 1)
            track_name = db_record[preferred]['track_info']['TTITLE{0}'.format(track_number)]
            new_name = '{0:02} - '.format(track_number + 1) + track_name + '.wav'
            os.rename(os.path.join(dest_dir, old_name), os.path.join(dest_dir, new_name))

    # save database record for disc
    with open(os.path.join(dest_dir, '00 - disc info.yaml'), 'wb') as disc_record:
        disc_record.write(yaml.dump(db_record))

    return dest_dir


def finish(opts, db_record, dest_dir):
    '''
    unload disc drive and warn if no CDDA database results were found
    '''
    if len(db_record) == 1:
        print('\nNo CDDA database records were found for {0}; '
              'you must rename the disc directory, {1}, and tracks manually'
              ''.format(db_record[0]['disc_id'][0], dest_dir))
    if call(['eject']) != 0:
        print('\nFailed to open disc drive')
        sys.exit(1)


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
        arg_parser = ArgumentParser(description=desc, formatter_class=ArgumentDefaultsHelpFormatter)
        arg_parser.add_argument('-d', '--device',
                                type=str,
                                default='/dev/sr0',
                                help='CD drive device name')
        arg_parser.add_argument('-a', '--agent-file',
                                type=FileType('rb'),
                                default=agent_file,
                                help='file containing HTTP client agent name and version conforming to RFC 1945 §3.7')
        arg_parser.add_argument('-t', '--token-file',
                                type=FileType('rb'),
                                default=token_file,
                                help='file containing discogs API token')
        arg_parser.add_argument('-m', '--freedb-mirror',
                                type=str,
                                default='http://freedb.freedb.org/~cddb/cddb.cgi',
                                help='freedb mirror URL')
        arg_parser.add_argument('-l', '--library-dir',
                                type=str,
                                default=library_dir,
                                help='base directory of music library')
        arg_parser.add_argument('-s', '--read-speed',
                                type=str,
                                default=8,
                                help='disc drive read speed')

        return vars(arg_parser.parse_args())

    opts = parse_args()

    opts['agent'] = opts['agent_file'].read().strip() ; del opts['agent_file']
    opts['token'] = opts['token_file'].read().strip() ; del opts['token_file']

    return opts


def main():
    '''
    rip CDDA discs and flac encode and tag the tracks with info from a CDDA database
    '''
    opts = get_opts()

    setup(opts)

    db_record = freedb(opts)
    dest_dir = rip(opts, db_record)

    finish(opts, db_record, dest_dir)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

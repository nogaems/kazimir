#!/usr/bin/env python3
'''
This utility extracts layout information from *.h files and returns it as an internal python structure
for futher using in the drawing util.
Header file example: https://github.com/gordon-quad/qmk_firmware/blob/master/keyboards/lets_split/keymaps/i2c-yoba-key64-goldcrest/chords.h
This is *NOT* a common solution and only adopted for the only header file above (at least for now).

'''

import sys
import urllib.request
import imp
import re
import copy
import pprint
import argparse


class Chord:
    def __init__(self, value, layout):
        self.value = value
        self.layout = layout
        self.keys = self.bits_to_list(value, layout)

    def bits_to_list(self, value, layout):
        if len(value) < 3:
            print('Incorrect value')
            return None
        value = value[2:]
        if rcount(layout) == 0 or len(value) != rcount(layout):
            print('Incorrect layout configuration')
            return None
        value = list(value)[::-1]
        # Gvido for fuck's sake go kill yourself
        result = copy.deepcopy(layout)
        for i in range(len(result)):
            for j in range(len(result[0])):
                if result[i][j] is not None:
                    result[i][j] = value[result[i][j]]
        return result

    @property
    def pretty(self):
        pass

    def __hash__(self):
        if self.value is None:
            return 0
        return int(self.value, base=2)

    def __eq__(self, other):
        return True if self.__hash__() == other.__hash__() else False

    def __str__(self):
        return repr(self.keys)

    def __repr__(self):
        return self.__str__()

    def __gt__(self, other):
        return True if self.value.count('1') > other.value.count('1') else False

    def __lt__(self, other):
        return not self.__gt__(other)


def safe_fetch(url):
    try:
        with urllib.request.urlopen(url) as response:
            return response.read()
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as e:
        print(e)
        return None


def get_header_text(path):
    '''
    This feature could be very handy if you want to use header files from different git revisions.
    '''
    if path.startswith("http"):
        return safe_fetch(path)
    else:
        return open(path).read()


def issecure(code):
    '''
    Checks whether a code secure from dangerous evaluations during import or not.
    This check is based on the idea that to make any dangerous thing like
    `os.system('rm -rf /')` call you have to import `os` module in your code.
    Almost every potentically dangerous action in python requires importing,
    at least I cannot invent any opposite example.
    I'd like you proof me wrong.
    '''
    return True if code.find('import') == -1 else False


def load_config(path):
    if not issecure(open(path).read()):
        print('Insecure conguration file')
        return None
    try:
        config = imp.load_source('config', path)
        return config
    except Exception as e:
        print("{}: {}".format(e.__class__.__name__, e))


def rcount(l):
    '''
    Recursively count nested elements in a list including only non-None values
    '''
    if not l:
        return 0
    else:
        return rcount(l[1:]) + len([v for v in l[0] if v is not None])


def parse(text, config):
    chord_to_id = {}
    id_to_name = {}
    result = []
    desc = []
    base = r'[\[\]\w]*\s*\w*\s*=\s*\{\s*([\[\]=\s\w,]*)\s*\}\;'
    for key, values in config.mapping.items():
        desc.append(key)
        regex = str(key) + base
        chords = re.findall(regex, text)
        if len(chords) == 0:
            print("The header file syntax and/or its structure is incompatible with this parser. Please, contact the maintainer.")
            return None
        regex = '\[(\w+)\] = (\d+)'
        chords = re.findall(regex, chords[0])
        for chord, id in chords:
            chord = Chord(chord, config.mapping[key]['layout'])
            for c, i in chord_to_id.items():
                if i == id and c > chord:
                    chord = c
            chord_to_id[chord] = id
        if not isinstance(values['chords'], list):
            values['chords'] = [values['chords']]
        for value in values['chords']:
            desc.append(value)
            regex = str(value) + base
            names = re.findall(regex, text)
            regex = '\[(\w+)\] = (\w+)'
            names = re.findall(regex, names[0])
            for id, name in names:
                if id not in id_to_name:
                    id_to_name[id] = [name[6:]]
                else:
                    id_to_name[id] = id_to_name[id] + \
                        [name[6:]]  # To cut "CHORD_"
        for chord in chord_to_id.keys():
            if chord_to_id[chord] in id_to_name:
                result.append(
                    {', '.join(id_to_name[chord_to_id[chord]]): chord})
    result = 'data = {}\ndesc = \'{}\'\noutput = \'\''.format(
        result,
        ''.join([desc[0], ' -> ', ', '.join(desc[1:])])
    )
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('header',
                        help='path or URL to the *.h file')
    parser.add_argument('config',
                        help='path to the configuration file')
    parser.add_argument('-o', '--out',
                        help='specify an output file, if not set - print the result to the stdout',
                        action='store', default=False)
    args = parser.parse_args()
    if not args.out:
        output = sys.stdout
    else:
        output = open(args.out, 'w')
    result = parse(get_header_text(args.header), load_config(args.config))

    print(result, file=output)

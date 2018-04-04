#!/usr/bin/env python3
# coding: utf-8

import imp
import itertools
import math
import os
import argparse
from PIL import Image, ImageDraw, ImageFont


class SecureError(Exception):
    ...


class IntegrityError(Exception):
    ...


class Artist:
    layout = None
    font = None
    # There's the default configuration
    config = {
        'bg': (255, 255, 255, 255),
        'cols': 8,  # Amount of columns of chords
        'font': './fonts/TerminusTTF-4.40.1.ttf',
        'font_color': (0, 0, 0, 255),
        'font_size': 16,
        'cell_size': 32,  # The size of a side of the square in pixels
        'cell_bg': (102, 102, 102, 255),
        'cell_fg': (241, 194, 50, 255)
    }
    spacing = round(config['cell_size'] * 0.1)  # 10% of any cell size

    def __init__(self, name, config='config.py'):
        self.load_layout(name)
        self.normalize_optionals()
        self.load_config()
        self.load_font()

    def safe_load(self, path):
        code = open(path).read()
        if not self.issecure(code):
            raise SecureError(
                'The code you\'re going to load is not secure and contains potencially dangerous parts')
        return imp.load_source('', path)

    def load_layout(self, path):
        layout = self.safe_load(path)
        correct, reason = self.iscorrect(layout)
        if not correct:
            raise IntegrityError(
                'The file contents don\'t match the specification: {}'.format(reason))
        self.layout = layout

    def load_config(self, path=None):
        if not path:
            if hasattr(self.layout, 'config'):
                config = self.layout.config
            else:
                return
        else:
            config = self.safe_load(path).config
        for option in self.config.keys():
            if option in config:
                self.config[option] = config[option]

    def load_font(self):
        self.font = ImageFont.truetype(
            font=self.config['font'],
            size=self.config['font_size']
        )

    # TODO: configuration validation

    @staticmethod
    def issecure(code):
        return not any([code.find(expr) != -1 for expr in
                        ['import', 'eval', 'exec', 'compile']])

    def iscorrect(self, code):
        '''
        Checks the only required fields. Returns a tuple with a result and a reason.
        If the result is True, the reason is None.
        Since I don't have macro in python this code will contain a lot of boilerplate.
        I'm considering any suggestions how to improve this function.
        '''

        if not hasattr(code, 'data'):
            return (False, "Required 'data' field is missing")
        if not isinstance(code.data, list):
            return (False, "'data' value should be 'list', not '{}'".format(
                code.data.__class__.__name__
            ))
        if len(code.data) == 0:
            return (False, "'data' value should be non-empty")
        for entry in code.data:
            if not isinstance(entry, dict):
                return (False, "'data' entries should be 'dict', not '{}'".format(
                    entry.__class__.__name__
                ))
            desc = list(entry.keys())
            if len(desc) != 1:
                return (False, "There's should be only one diagram per entry")
            if not isinstance(desc[0], str):
                return (False, "Diagram description key should be 'str', not '{}'".format(
                    desc[0].__class__.__name__
                ))
            layout = list(entry.values())[0]
            if not isinstance(layout, list):
                return (False, "Diagram layout should be 'list', not '{}'".format(
                    layout.__class__.__name__
                ))
            chain = list(itertools.chain.from_iterable(layout))
            if any([not isinstance(el, (type(None), int, str))
                    for el in chain]) or \
               not all(map(
                   lambda e: e.replace('.', '', 1).isdigit(),
                   filter(lambda e: isinstance(e, str), chain))):
                return (False, "All elements of the layout should be None or reducible to 'int'")
        return (True, None)

    def normalize_optionals(self):
        if not self.layout:
            return False
        for entry in ('desc', 'output'):
            if not hasattr(self.layout, entry):
                setattr(self.layout, entry, '')
            obj = getattr(self.layout, entry)
            if not isinstance(obj, str):
                setattr(self.layout, entry, str(obj))

    def draw_chord(self, chord, width, height):
        name = list(chord.keys())[0]
        value = list(chord.values())[0]
        cols = len(value[0])
        rows = len(value)
        name_w, name_h = self.font.getsize(name)
        img = Image.new('RGBA', (width, height), self.config['bg'])
        draw = ImageDraw.Draw(img)
        draw.text((width / 2 - name_w / 2, self.spacing), name,
                  font=self.font, fill=self.config['font_color'])
        cursor = [width / 2 - (cols / 2) * self.config['cell_size'] - self.spacing * (cols - 1),
                  self.spacing * 2 + name_h]
        for row in value:
            for cell in row:
                if cell is None:
                    continue
                draw.rectangle(
                    [cursor[0],
                     cursor[1],
                     cursor[0] + self.config['cell_size'],
                     cursor[1] + self.config['cell_size']],
                    fill=self.config['cell_bg'],
                    outline=(0, 0, 0, 255)
                )
                if int(cell) == 1:
                    draw.ellipse(
                        [cursor[0] + self.spacing / 2,
                         cursor[1] + self.spacing / 2,
                         cursor[0] + self.config['cell_size'] -
                         self.spacing / 2,
                         cursor[1] + self.config['cell_size'] -
                         self.spacing / 2],
                        fill=self.config['cell_fg'],
                        outline=(0, 0, 0, 255)
                    )
                cursor[0] += self.spacing + self.config['cell_size']
            cursor[0] = width / 2 - \
                (cols / 2) * self.config['cell_size'] - \
                self.spacing * (cols - 1)
            cursor[1] += self.spacing + self.config['cell_size']
        return img

    def draw(self):
        max_len_name = max([list(c.keys())[0] for c in self.layout.data],
                           key=lambda x: len(x))
        name_w, name_h = self.font.getsize(max_len_name)
        chords = []
        cols = len(list(self.layout.data[0].values())[0][0])
        rows = len(list(self.layout.data[0].values())[0])
        width = cols * self.config['cell_size'] + self.spacing * (cols + 1)
        width = width if width >= name_w else name_w + self.spacing * 2
        height = rows * self.config['cell_size'] + \
            self.spacing * (rows + 1) + name_h + self.spacing
        for chord in self.layout.data:
            chords.append(self.draw_chord(chord, width, height))
        desc_w, desc_h = self.font.getsize(self.layout.desc)
        result_w = self.config['cols'] * width if \
            len(chords) >= self.config['cols'] else len(chords) * width
        result_h = math.ceil(len(chords) / self.config['cols']) * height + \
            self.spacing * 2 + \
            desc_h
        result = Image.new('RGBA', (result_w, result_h), self.config['bg'])
        draw = ImageDraw.Draw(result)
        draw.text((result_w / 2 - desc_w / 2, self.spacing),
                  self.layout.desc,
                  fill=self.config['font_color'],
                  font=self.font
                  )
        counter = 0
        cursor = [0, desc_h + self.spacing * 2]
        for chord in chords:
            counter += 1
            result.paste(chord, tuple(cursor))
            if counter // self.config['cols'] != 1:
                cursor[0] += width
            else:
                cursor[0] = 0
                cursor[1] += height
                counter = 0

        return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('file',
                        help='path to the layout file')
    parser.add_argument('-o', '--out',
                        help='specify an output file',
                        action='store', default=False)
    args = parser.parse_args()
    if args.out:
        output = args.out
    else:
        output = args.file + '.png'
    try:
        a = Artist(args.file)
        a.draw().save(output)

    except Exception as e:
        print("An error has occured\n{}: {}".format(e.__class__.__name__, e))

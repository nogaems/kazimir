#!/usr/bin/env python3
# coding: utf-8

import imp
import itertools
import os


class SecureError(Exception):
    ...


class IntegrityError(Exception):
    ...


class Artist:
    layout = None

    def __init__(self, name):
        self.load_layout(name)
        self.normalize_optionals()

    def load_layout(self, path):
        code = open(path).read()
        if not self.issecure(code):
            raise SecureError(
                'The code you\'re going to load is not secure and contains potencially dangerous parts')
        layout = imp.load_source('layout', path)
        secure, reason = self.iscorrect(layout)
        if not secure:
            raise IntegrityError(
                'The file contents don\'t match the specification: {}'.format(reason))
        self.layout = layout

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


if __name__ == '__main__':
    try:
        a = Artist('example.py')
    except Exception as e:
        print("An error has occured\n{}: {}".format(e.__class__.__name__, e))
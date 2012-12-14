#!/usr/bin/env python
# encoding: utf-8
from __future__ import print_function
"""
genkey
"""


import string

KEYCHARS_INT = string.digits
KEYCHARS_HEX = string.hexdigits

KEYCHARS = (
    'abcdefghjkmnpqrstuvwxyz'
    '23456789'
    'ABCDEFGHJKMNPQRSTUVWXY')

KEYCHARS_LEN = len(KEYCHARS)

import logging
log = logging.getLogger('encode')

KEYCHAR_LOOKUP = {char:i for i,char in enumerate(KEYCHARS)}

def print_keychars(keychars,printf=print):
    row1 = []
    row2 = []
    for i,c in enumerate(keychars):
        row2.append(c)
        row1.append(not (i % 10) and str((i / 10)) or ' ')

    printf('KEYCHARS:')
    printf(' '.join(row1))
    printf(' '.join(row2))


def encode(x, base=KEYCHARS_LEN):
    def _int2base(x, base):
        while x:
            yield KEYCHARS[x % base]
            x /= base

    return (''.join(_int2base(x, base)))[::-1]


def decode(x, base=KEYCHARS_LEN):
    #values = [
    #    (KEYCHAR_LOOKUP[c]*(base**n))
    #        for n,c in enumerate(x[::-1])]
    _sum = 0
    for n, digit in enumerate(x[::-1]):
        base10_value = KEYCHAR_LOOKUP[digit]
        place_value = (base**n)
        digit_value = base10_value * place_value
        _sum += digit_value
        log.debug('%d\t%r\t%r\t%r\t%r\t%r' %
                (n, digit, base10_value, place_value, digit_value, _sum))

    return _sum
    #print('values: %r' % values)
    #value = sum(values)
    #return value
    # sum
    # shift to base16
    # decode('hex')


def str_to_int(inptstr):
    print('inptstr: %r' % inptstr)
    hexinpt = inptstr.encode('hex')
    print('hexinpt: %r' % hexinpt)
    intinpt = int(hexinpt, 16)
    print('intinpt: %r' % intinpt)
    return intinpt


import unittest
import logging
class TestEncoding(unittest.TestCase):
    log = logging.getLogger('TestEncoding')
    # assert ('%x' % int(inptstr.encode('hex'),16)).decode('hex') == inptstr
    def test_routine(self):
        inptstr = 'test'

        self.log.debug('inptstr: %r' % inptstr)
        hexinpt = inptstr.encode('hex')
        self.log.debug('hexinpt: %r' % hexinpt)

        intinpt = int(hexinpt, 16)
        self.log.debug('intinpt: %r' % intinpt)

        encoded = encode(intinpt)
        self.log.debug('encoded: %r' % encoded)

        decoded = decode(encoded)
        self.log.debug('decoded: %r' % decoded)

        #assert encoded == str(decoded) # base 10

        decodedhex = '%x' % decoded
        self.log.debug('dechex:  %r' % decodedhex)

        assert hexinpt == decodedhex

        outputstr = decodedhex.decode('hex')
        self.log.debug('outputstr: %r' % outputstr)

        assert outputstr == inptstr

    def test_int(self):
        INPUT=1
        encoded = encode(INPUT)
        self.log.debug('encoded: %r' % encoded)
        decoded = decode(encoded)
        assert INPUT == decoded

    def test_uuid4(self):
        import uuid
        id = uuid.uuid4()
        self.log.debug('<-id: %r' % id)


        encoded = encode(id.int)
        self.log.info('->encoded: %r' % encoded)

        encodedint = decode(encoded)
        self.log.debug('->id: %r' % encodedint)

        output_uuid = uuid.UUID(int=encodedint)
        self.log.debug('-->: %r' % output_uuid)

        assert id == output_uuid

    def test_uuid1(self):
        import uuid
        id = uuid.uuid1()

        encoded = encode(id.int)
        self.log.debug('->encoded: %r' % encoded)

        decoded = decode(encoded)
        self.log.debug('->: %r' % decoded)

        output_uuid = uuid.UUID(int=decoded)

    def test_slug(self):
        import uuid
        @property
        def toslug(self):
            return encode(self.int)

        @classmethod
        def fromslug(cls, slug):
            return cls(int=decode(slug))

        uuid.UUID.slug = toslug
        uuid.UUID.fromslug = fromslug


        id = uuid.uuid4()
        self.log.debug(id)
        self.log.debug(id.slug)

        idfromslug = uuid.UUID.fromslug(id.slug)
        self.log.debug(idfromslug)


def genkey():
    """
    mainfunc
    """
    pass



def main():
    import optparse
    import logging

    prs = optparse.OptionParser(usage="./%prog : args")

    prs.add_option('-v', '--verbose',
                    dest='verbose',
                    action='store_true',)
    prs.add_option('-q', '--quiet',
                    dest='quiet',
                    action='store_true',)
    prs.add_option('-t', '--test',
                    dest='run_tests',
                    action='store_true',)

    (opts, args) = prs.parse_args()

    if not opts.quiet:
        logging.basicConfig()

        if opts.verbose:
            logging.getLogger().setLevel(logging.DEBUG)

    if opts.run_tests:
        import sys
        sys.argv = [sys.argv[0]] + args
        import unittest
        retval=unittest.main()
        # exit(retval)

    genkey()

if __name__ == "__main__":
    main()

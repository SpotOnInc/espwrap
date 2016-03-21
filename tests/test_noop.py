#!/usr/bin/env python

from __future__ import print_function, division, unicode_literals

import sys

from espwrap.adaptors.noop import NoopMassEmail

if sys.version_info < (3,):
    range = xrange


def test_instantiatable():
    assert NoopMassEmail()


def test_can_add_single_recipient():
    me = NoopMassEmail()

    me.add_recipient(
        name='Tester Dude', email='test+tester@something.com',
        merge_vars={'EXAMPLE': 'A TEST REPLACEMENT'}
    )

    recips = me.get_recipients()

    assert len(recips) == 1

    assert recips[0].get('merge_vars') is not None


def test_can_add_list_recipients():
    me = NoopMassEmail()

    me.add_recipients([
        {
            'email': 'test+tester@something.com',
            'name': 'Some test dude',
        },
        {
            'email': 'test1+tester1@something.com',
            'name': 'Some test dude',
        },
    ])

    recips = me.get_recipients()

    assert len(recips) == 2


def test_recipients_get_default_empty_merge_vars():
    me = NoopMassEmail()

    me.add_recipients([
        {
            'email': 'test+tester@something.com',
            'name': 'Some test dude',
        },
        {
            'email': 'test1+tester1@something.com',
            'name': 'Some test dude',
        },
    ])

    recips = [x for x in me.get_recipients() if x.get('merge_vars') == {}]

    assert len(recips) == 2


def test_can_lazily_add_recipients():
    def generate_recipients(count=10):
        for x in range(count):
            yield {
                'name': 'Test Recip {}'.format(x),
                'email': 'test+{}@something.com'.format(x),
            }

    gen_count = 20

    me = NoopMassEmail()

    me.add_recipients(generate_recipients(gen_count))

    recips = me.get_raw_recipients()

    assert hasattr(recips, '__iter__') and not hasattr(recips, '__len__')

    recips_list = me.get_recipients()

    assert len(recips_list) == gen_count
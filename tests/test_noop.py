#!/usr/bin/env python

from __future__ import print_function, division, unicode_literals

import sys

import pytest

from espwrap.base import MIMETYPE_HTML, MIMETYPE_TEXT
from espwrap.adaptors.noop import NoopMassEmail

if sys.version_info < (3,):
    range = xrange


def test_instantiatable():
    assert NoopMassEmail()


def test_add_recipient():
    me = NoopMassEmail()

    me.add_recipient(
        name='Tester Dude', email='test+tester@something.com',
        merge_vars={'EXAMPLE': 'A TEST REPLACEMENT'}
    )

    recips = me.get_recipients()

    assert len(recips) == 1

    assert recips[0].get('merge_vars') is not None


def test_add_recipients():
    '''
    Test that a list of recipients can be added in bulk, assigning a default
    empty dict of merge vars when not provided
    '''

    me = NoopMassEmail()

    me.add_recipients([
        {
            'email': 'test+tester@something.com',
            'name': 'Some test dude',
            'merge_vars': {'SOMETHING': 'test'},
        },
        {
            'email': 'test1+tester1@something.com',
            'name': 'Some test dude',
        },
    ])

    recips = me.get_recipients()

    assert len(recips) == 2

    recips = [x for x in me.get_recipients() if x.get('merge_vars') == {}]

    assert len(recips) == 1


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


def test_no_tags_by_default():
    me = NoopMassEmail()

    assert len(me.get_tags()) == 0


def test_add_tags():
    me = NoopMassEmail()

    me.add_tags('test', 'mode')

    assert len(me.get_tags()) == 2


def test_clear_tags():
    me = NoopMassEmail()

    me.add_tags('test', 'mode')

    assert len(me.get_tags()) == 2

    me.clear_tags()

    assert len(me.get_tags()) == 0


def test_set_body_and_get_body():
    me = NoopMassEmail()
    msg = '<h1>Hello!</h1>'

    me.set_body(msg)

    assert me.get_body().get(MIMETYPE_HTML) == msg
    assert me.get_body(mimetype=MIMETYPE_HTML) == msg

    with pytest.raises(AttributeError) as e:
        me.get_body(mimetype=MIMETYPE_TEXT)

    assert 'mimetype' in str(e.value)


def test_set_body_with_mimetype():
    '''
    Test that setting a body will set the default (HTML), but this mimetype
    can be overridden with an argument (for, ie. plain text)
    '''
    me = NoopMassEmail()
    msg_text = 'Tester Test'
    msg_html = '<h1>Tester Test HTML</h1>'

    me.set_body(msg_html)
    me.set_body(msg_text, mimetype=MIMETYPE_TEXT)

    assert me.get_body(mimetype=MIMETYPE_HTML) == msg_html
    assert me.get_body(mimetype=MIMETYPE_TEXT) == msg_text

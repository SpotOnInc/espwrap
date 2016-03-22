#!/usr/bin/env python

from __future__ import print_function, division, unicode_literals, absolute_import

import sys

import pytest

from espwrap.adaptors.sendgrid import SendGridMassEmail

if sys.version_info < (3,):
    range = xrange

API_KEY = 'unit_test'


def test_delimiters():
    me = SendGridMassEmail(API_KEY)
    start = '*|'
    end = '|*'

    me.set_variable_delimiters(start, end)

    delimiters = me.get_variable_delimiters(True)

    assert delimiters.get('start') == start
    assert delimiters.get('end') == end

    assert me.get_variable_delimiters() == (start, end)


def test_add_tags():
    me = SendGridMassEmail(API_KEY)

    with pytest.raises(Exception) as err:
        me.add_tags(*['something'] * 11)

    assert 'Too many tags' in str(err)

    me.add_tags(*['something'] * 9)

    with pytest.raises(Exception) as err:
        me.add_tags(*['something'] * 2)

    assert 'limit' in str(err)

    me.add_tags('tenth')

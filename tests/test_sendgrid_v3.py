#!/usr/bin/env python

from __future__ import print_function, division, unicode_literals, absolute_import

import json
import sys

import pytest

from espwrap.base import MIMETYPE_TEXT
from espwrap.adaptors.sendgrid_v3 import SendGridMassEmail
from espwrap.adaptors.sendgrid_common import breakdown_recipients

if sys.version_info < (3,):
    range = xrange

API_KEY = 'unit_test'


def test_breakdown_recipients():
    me = SendGridMassEmail(API_KEY)

    # This function will split straight up duplicates
    me.add_recipient(name='Test', email='test@test.com')
    me.add_recipient(name='Test', email='test@test.com')

    # This function will split aliases we've already seen
    # the base of
    me.add_recipient(name='Test', email='test+1@test.com')

    broken = breakdown_recipients(me.get_recipients())

    # So it should send as three separate batches
    assert len(broken) == 3


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

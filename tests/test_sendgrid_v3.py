#!/usr/bin/env python

from __future__ import print_function, division, unicode_literals, absolute_import

import json
import sys

import pytest

from espwrap.base import MIMETYPE_TEXT, batch
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

def test_message_construction():
    me = SendGridMassEmail(API_KEY)

    template_name = 'test template'
    ip_pool = 'testPool'
    company_name = 'UnitTest Spam Corp the Second'
    tags = ['unit', 'test', 'for', 'the', 'win']
    webhook_data = {
        'm_id': '56f2c1341a89ddc8c04d5407',
        'env': 'local',
        'p_id': '56f2c1571a89ddc8c04d540a',
    }

    me.set_reply_to_addr('custsupport@spam.com')
    me.set_from_addr('donotreply@spam.com')

    me.add_recipients([
        {
            'name': 'Josh',
            'email': 'spam@spam.com',
            'merge_vars': {
                'CUSTOMER_NAME': 'Josh',
            },
        },
        {
            'name': 'Jim',
            'email': 'spam2@spam.com',
            'merge_vars': {
                'CUSTOMER_NAME': 'Jim',
                'SOMETHING_UNIQUE': 'tester',
            },
        },
    ])

    me.add_global_merge_vars(COMPANY_NAME=company_name)

    me.set_variable_delimiters('*|', '|*')

    me.set_ip_pool(ip_pool)

    me.set_template_name(template_name)

    me.enable_click_tracking()
    me.enable_open_tracking()

    me.set_webhook_data(webhook_data)

    me.add_tags(*tags)

    me.set_subject('test subject')

    delims = me.get_variable_delimiters()

    grouped_recipients = batch(list(me.recipients), me.partition)

    for grp in grouped_recipients:
        to_send = breakdown_recipients(grp)

        message = me.message_constructor(to_send)
        message_dict = message.get()

        print (message_dict)

        assert set(message_dict['categories']) == set(tags)
        assert message_dict['tracking_settings']['open_tracking']['enable'] == True
        assert message_dict['tracking_settings']['click_tracking']['enable'] == True

        print(message_dict['personalizations'])

        assert message_dict['personalizations'][0]['to'][0]['name'] == 'Jim'
        assert message_dict['personalizations'][0]['to'][0]['email'] == 'spam2@spam.com'
        assert message_dict['personalizations'][1]['to'][0]['name'] == 'Josh'
        assert message_dict['personalizations'][1]['to'][0]['email'] == 'spam@spam.com'

        company_name_key = delims[0] + 'COMPANY_NAME' + delims[1]
        assert message_dict['personalizations'][0]['substitutions'][company_name_key] == 'UnitTest Spam Corp the Second'
        assert message_dict['personalizations'][1]['substitutions'][company_name_key] == 'UnitTest Spam Corp the Second'

        customer_name_key = delims[0] + 'CUSTOMER_NAME' + delims[1]
        assert message_dict['personalizations'][0]['substitutions'][customer_name_key] == 'Jim'
        assert message_dict['personalizations'][1]['substitutions'][customer_name_key] == 'Josh'

        something_unique_key = delims[0] + 'SOMETHING_UNIQUE' + delims[1]
        assert message_dict['personalizations'][0]['substitutions'][something_unique_key] == 'tester'
        assert something_unique_key not in message_dict['personalizations'][1]['substitutions'].keys()

        assert message_dict['ip_pool_name'] == ip_pool

        assert message_dict['custom_args']['template_name'] == template_name

#!/usr/bin/env python

from __future__ import absolute_import, division, print_function, unicode_literals

import json
import sys

import pytest

from espwrap.adaptors.sendgrid import SendGridMassEmail
from espwrap.adaptors.sendgrid_common import breakdown_recipients

if sys.version_info < (3,):
    range = xrange

API_KEY = "unit_test"


def test_breakdown_recipients():
    me = SendGridMassEmail(API_KEY)

    # This function will split straight up duplicates
    me.add_recipient(name="Test", email="test@test.com")
    me.add_recipient(name="Test", email="test@test.com")

    # This function will split aliases we've already seen
    # the base of
    me.add_recipient(name="Test", email="test+1@test.com")

    broken = breakdown_recipients(me.get_recipients())

    # So it should send as three separate batches
    assert len(broken) == 3


def test_delimiters():
    me = SendGridMassEmail(API_KEY)
    start = "*|"
    end = "|*"

    me.set_variable_delimiters(start, end)

    delimiters = me.get_variable_delimiters(True)

    assert delimiters.get("start") == start
    assert delimiters.get("end") == end

    assert me.get_variable_delimiters() == (start, end)


def test_add_tags():
    me = SendGridMassEmail(API_KEY)

    with pytest.raises(Exception) as err:
        me.add_tags(*[str(tag) for tag in range(11)])

    assert "Too many tags" in str(err)

    me.add_tags(*[str(tag) for tag in range(9)])

    with pytest.raises(Exception) as err:
        me.add_tags(*["foo", "bar"])

    assert "limit" in str(err)

    me.add_tags("tenth")


def test_prepare_payload():
    me = SendGridMassEmail(API_KEY)

    template_name = "test template"
    ip_pool = "testPool"
    company_name = "UnitTest Spam Corp the Second"
    tags = ["unit", "test", "for", "the", "win"]
    webhook_data = {
        "m_id": "56f2c1341a89ddc8c04d5407",
        "env": "local",
        "p_id": "56f2c1571a89ddc8c04d540a",
    }

    me.set_reply_to_addr("custsupport@spam.com")
    me.set_from_addr("donotreply@spam.com")

    me.add_recipients(
        [
            {
                "name": "Josh",
                "email": "spam@spam.com",
                "merge_vars": {
                    "CUSTOMER_NAME": "Josh",
                },
            },
            {
                "name": "Jim",
                "email": "spam2@spam.com",
                "merge_vars": {
                    "CUSTOMER_NAME": "Jim",
                    "SOMETHING_UNIQUE": "tester",
                },
            },
        ]
    )

    me.add_global_merge_vars(COMPANY_NAME=company_name)

    me.set_variable_delimiters("*|", "|*")
    me.set_ip_pool(ip_pool)
    me.set_template_name(template_name)

    me.enable_click_tracking()
    me.enable_open_tracking()

    me.set_webhook_data(webhook_data)

    me.add_tags(*tags)

    payload_str = me._prepare_payload().json_string()
    payload = json.loads(payload_str)

    assert payload.get("filters", {}).get("clicktrack", {}).get("settings", {}).get("enable") == 1
    assert payload.get("filters", {}).get("opentrack", {}).get("settings", {}).get("enable") == 1

    assert '"Josh" <spam@spam.com>' in payload.get("to")
    assert '"Jim" <spam2@spam.com>' in payload.get("to")

    assert payload.get("section") is not None
    assert len(payload.get("section").keys()) == 1
    assert payload.get("section").get(":COMPANY_NAME") == company_name

    assert payload.get("sub") is not None
    assert len(payload.get("sub", {}).get("*|CUSTOMER_NAME|*")) == 2
    assert len(payload.get("sub", {}).get("*|COMPANY_NAME|*")) == 2

    sub_unique = payload.get("sub", {}).get("*|SOMETHING_UNIQUE|*")

    assert len(sub_unique) == 2
    assert sub_unique[0] is None
    assert sub_unique[1] == "tester"

    cat_set = set(payload.get("category"))

    assert len(cat_set) == 5
    assert len(cat_set.intersection(tags)) == 5

    assert payload.get("ip_pool") == ip_pool
    assert payload.get("unique_args") == webhook_data

    assert payload.get("filters", {}).get("templates", {}).get("settings", {}).get("enabled") == 1
    assert payload.get("filters", {}).get("templates", {}).get("settings", {}).get("template_id") == template_name

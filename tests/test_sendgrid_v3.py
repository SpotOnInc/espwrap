# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import sys

try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch

import pytest
from python_http_client.exceptions import (  # this is a dependency of sendgrid-python
    BadRequestsError,
)

from espwrap.adaptors.sendgrid_common import breakdown_recipients
from espwrap.adaptors.sendgrid_v3 import _HTTP_EXC_MSG, SendGridMassEmail
from espwrap.base import batch

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


def test_message_construction():
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
            {
                "name": "姓",
                "email": "test@test.com",
                "merge_vars": {"CUSTOMER_NAME": "姓", "SOMETHING_UNIQUE": "独特"},
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

    me.set_subject("test subject")

    delims = me.get_variable_delimiters()

    me.add_cc("testcc@spam.com")
    me.add_bcc("testbcc@spam.com")

    grouped_recipients = batch(list(me.recipients), me.partition)

    for grp in grouped_recipients:
        # Note: The order of recipients in this test case is reversed from what's listed above
        to_send = breakdown_recipients(grp)

        message = me.message_constructor(to_send)
        message_dict = message.get()

        print(message_dict)

        assert set(message_dict["categories"]) == set(tags)
        assert message_dict["tracking_settings"]["open_tracking"]["enable"] is True
        assert message_dict["tracking_settings"]["click_tracking"]["enable"] is True

        print(message_dict["personalizations"])

        assert message_dict["personalizations"][0]["to"][0]["name"] == "姓"
        assert message_dict["personalizations"][0]["to"][0]["email"] == "test@test.com"
        assert message_dict["personalizations"][1]["to"][0]["name"] == "Jim"
        assert message_dict["personalizations"][1]["to"][0]["email"] == "spam2@spam.com"
        assert message_dict["personalizations"][2]["to"][0]["name"] == "Josh"
        assert message_dict["personalizations"][2]["to"][0]["email"] == "spam@spam.com"

        assert message_dict["personalizations"][0]["cc"][0]["email"] == "testcc@spam.com"
        assert message_dict["personalizations"][1]["cc"][0]["email"] == "testcc@spam.com"
        assert message_dict["personalizations"][2]["cc"][0]["email"] == "testcc@spam.com"
        assert message_dict["personalizations"][0]["bcc"][0]["email"] == "testbcc@spam.com"
        assert message_dict["personalizations"][1]["bcc"][0]["email"] == "testbcc@spam.com"
        assert message_dict["personalizations"][2]["bcc"][0]["email"] == "testbcc@spam.com"
        
        company_name_key = delims[0] + "COMPANY_NAME" + delims[1]
        assert message_dict["personalizations"][0]["substitutions"][company_name_key] == "UnitTest Spam Corp the Second"
        assert message_dict["personalizations"][1]["substitutions"][company_name_key] == "UnitTest Spam Corp the Second"

        customer_name_key = delims[0] + "CUSTOMER_NAME" + delims[1]
        #        assert message_dict['personalizations'][0]['substitutions'][customer_name_key] == '姓'
        assert message_dict["personalizations"][1]["substitutions"][customer_name_key] == "Jim"
        assert message_dict["personalizations"][2]["substitutions"][customer_name_key] == "Josh"

        something_unique_key = delims[0] + "SOMETHING_UNIQUE" + delims[1]
        #        assert message_dict['personalizations'][0]['substitutions'][something_unique_key] == '独特'
        assert something_unique_key not in message_dict["personalizations"][2]["substitutions"].keys()

        assert message_dict["ip_pool_name"] == ip_pool

        assert message_dict["custom_args"]["template_name"] == template_name


def test_send_error_400(caplog):
    """
    Test the handling of HTTP 400 Bad Request responses. The Sendgrid V3 API will return data
    along with a 400 response that has details on why it was rejected.  Make sure this data
    makes it back to the caller, pretty pretty please.
    """
    subject = "subject"
    resp_status_code = 400
    resp_reason = "main reason for error"
    resp_body = "the body of the response"

    me = SendGridMassEmail(API_KEY)

    me.subject = subject
    me.from_addr = "noreply@mailinator.com"
    me.add_recipient(email="recip@mailinator.com")

    with patch("sendgrid.SendGridAPIClient.send") as mock_send:
        error = Mock()
        error.code = resp_status_code
        error.reason = resp_reason
        error.read = lambda: resp_body

        mock_send.side_effect = BadRequestsError(error)

        me.send()

        assert mock_send.called, "It should have made it to the send method in the sendgrid lib."
        assert len(caplog.record_tuples) == 1, "There should a log message in the exception block."
        severity = caplog.record_tuples[0][1]
        msg = caplog.record_tuples[0][2]
        assert severity == 40, "The log should be an Error level log."
        assert msg == _HTTP_EXC_MSG % (
            subject,
            resp_status_code,
            resp_reason,
            resp_body,
        ), "The log message should contain details from the response."

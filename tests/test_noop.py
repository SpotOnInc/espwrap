#!/usr/bin/env python

from __future__ import absolute_import, division, print_function, unicode_literals

import sys

import pytest

from espwrap.adaptors.noop import NoopMassEmail
from espwrap.base import MIMETYPE_HTML, MIMETYPE_TEXT, batch

if sys.version_info < (3,):
    range = xrange


def generate_recipients(count=10):
    for x in range(count):
        yield {
            "name": "Test Recip {}".format(x),
            "email": "test+{}@something.com".format(x),
        }


def test_batch():
    tester = ["lol"] * 500

    res = list(batch(tester, 5))

    assert len(res) == 100

    lengths = [len(x) for x in res]

    assert max(lengths) == 5


def test_instantiatable():
    assert NoopMassEmail()


def test_add_recipient():
    me = NoopMassEmail()

    me.add_recipient(
        name="Tester Dude",
        email="test+tester@something.com",
        merge_vars={"EXAMPLE": "A TEST REPLACEMENT"},
    )

    recips = me.get_recipients()

    assert len(recips) == 1

    assert recips[0].get("merge_vars") is not None


def test_add_recipients():
    """
    Test that a list of recipients can be added in bulk, assigning a default
    empty dict of merge vars when not provided
    """

    me = NoopMassEmail()

    me.add_recipients(
        [
            {
                "email": "test+tester@something.com",
                "name": "Some test dude",
                "merge_vars": {"SOMETHING": "test"},
            },
            {
                "email": "test1+tester1@something.com",
                "name": "Some test dude",
            },
        ]
    )

    recips = me.get_recipients()

    assert len(recips) == 2

    recips = [x for x in me.get_recipients() if x.get("merge_vars") == {}]

    assert len(recips) == 1


def test_can_lazily_add_recipients_and_solidify():
    gen_count = 20

    me = NoopMassEmail()

    me.add_recipients(generate_recipients(gen_count))

    recips = me.get_raw_recipients()

    assert hasattr(recips, "__iter__") and not hasattr(recips, "__len__")

    recips_list = me.solidify_recipients()

    assert len(recips_list) == gen_count


def test_no_global_merge_vars_by_default():
    me = NoopMassEmail()

    assert not me.get_global_merge_vars()


def test_add_global_merge_vars():
    me = NoopMassEmail()

    me.add_global_merge_vars(FIRST="server", SECOND_ONE_IS_BEST="client")

    assert len(me.get_global_merge_vars().items()) == 2
    assert "FIRST" in me.get_global_merge_vars().keys()
    assert "SECOND_ONE_IS_BEST" in me.get_global_merge_vars().keys()


def test_clear_global_merge_vars():
    me = NoopMassEmail()

    me.add_global_merge_vars(FIRST="server", SECOND="client")

    me.clear_global_merge_vars()

    assert not me.get_global_merge_vars()


def test_no_tags_by_default():
    me = NoopMassEmail()

    assert len(me.get_tags()) == 0


def test_add_tags():
    me = NoopMassEmail()

    # Make sure dupes are eliminated
    me.add_tags("test", "mode", "test")
    assert len(me.get_tags()) == 2


def test_clear_tags():
    me = NoopMassEmail()

    me.add_tags("test", "mode")

    assert len(me.get_tags()) == 2

    me.clear_tags()

    assert len(me.get_tags()) == 0


def test_set_body_and_get_body():
    me = NoopMassEmail()
    msg = "<h1>Hello!</h1>"

    me.set_body(msg)

    assert me.get_body().get(MIMETYPE_HTML) == msg
    assert me.get_body(mimetype=MIMETYPE_HTML) == msg

    with pytest.raises(AttributeError) as e:
        me.get_body(mimetype=MIMETYPE_TEXT)

    assert "mimetype" in str(e.value)


def test_set_body_with_mimetype():
    """
    Test that setting a body will set the default (HTML), but this mimetype
    can be overridden with an argument (for, ie. plain text)
    """
    me = NoopMassEmail()
    msg_text = "Tester Test"
    msg_html = "<h1>Tester Test HTML</h1>"

    me.set_body(msg_html)
    me.set_body(msg_text, mimetype=MIMETYPE_TEXT)

    assert me.get_body(mimetype=MIMETYPE_HTML) == msg_html
    assert me.get_body(mimetype=MIMETYPE_TEXT) == msg_text


def test_from_addr():
    me = NoopMassEmail()
    addr = "spam@spam.com"

    me.set_from_addr(addr)

    assert me.get_from_addr() == addr


def test_reply_to_addr():
    me = NoopMassEmail()
    addr = "spam@spam.com"

    me.set_reply_to_addr(addr)

    assert me.get_reply_to_addr() == addr


def test_subject():
    me = NoopMassEmail()
    sub = "Testing"

    me.set_subject(sub)

    assert me.get_subject() == sub


def test_validate():
    me = NoopMassEmail()

    with pytest.raises(Exception) as e:
        me.validate()

    assert "address and subject" in str(e)

    me.set_subject("something")
    me.set_from_addr("spam@spam.com")

    me.validate()


def test_webhook_data():
    me = NoopMassEmail()
    sub = "Testing"

    me.set_webhook_data(sub)

    assert me.get_webhook_data() == sub


def test_click_tracking():
    me = NoopMassEmail()

    assert not me.get_click_tracking_status()

    me.enable_click_tracking()

    assert me.get_click_tracking_status() is True

    me.disable_click_tracking()

    assert me.get_click_tracking_status() is False


def test_open_tracking():
    me = NoopMassEmail()

    assert not me.get_open_tracking_status()

    me.enable_open_tracking()

    assert me.get_open_tracking_status() is True

    me.disable_open_tracking()

    assert me.get_open_tracking_status() is False


def test_importance():
    me = NoopMassEmail()

    me.set_importance(True)
    assert me.get_importance() is True

    me.set_importance(False)
    assert me.get_importance() is False


def test_ip_pool():
    me = NoopMassEmail()
    pool = "abc_group"

    me.set_ip_pool(pool)

    assert me.get_ip_pool() == pool


def test_template_name():
    me = NoopMassEmail()
    template_name = "test template"

    me.set_template_name(template_name)

    assert me.get_template_name() == template_name


def test_send():
    me = NoopMassEmail()

    with pytest.raises(NotImplementedError):
        me.send()


def test_delimiters():
    """
    By default, we assume the ESP cannot hot-swap variable delimiters the way
    SendGrid can, so we raise NotImplementedError and call it a day.
    """

    me = NoopMassEmail()

    with pytest.raises(NotImplementedError):
        me.set_variable_delimiters(start="*|", end="|*")

    with pytest.raises(NotImplementedError):
        me.get_variable_delimiters()

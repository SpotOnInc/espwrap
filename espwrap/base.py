from __future__ import print_function, division, unicode_literals

import abc
import collections
import itertools
import sys


if sys.version_info < (3,):
    range = xrange


class MassEmail(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def _prepare_payload(self):
        raise NotImplementedError(
            'Payloads must be generated on a per-ESP basis'
        )

    @abc.abstractmethod
    def send(self):
        raise Exception('Send method must be defined on a per-ESP basis')

    def __init__(self, subject='', from_addr='', text='', html='',
                 send_partition=500, reply_to_addr='', webhook_data=None,
                 track_clicks=False, track_opens=False):
        self.recipients = []
        self.global_merge_vars = {}
        self.tags = []
        self.webhook_data = webhook_data

        self.subject = subject
        self.from_addr = from_addr
        self.reply_to_addr = None

        self.partition = send_partition

        self.track_clicks = track_clicks
        self.track_opens = track_opens

        self.important = False

        self.body = {
            'text/plain': text,
            'text/html': html,
        }

    def add_recipient(self, email, name='', merge_vars=None):
        # was given a dict containing everything, rather than a spread
        if isinstance(email, collections.Mapping):
            recip = email
        else:
            recip = {
                'name': name,
                'email': email,
                'merge_vars': merge_vars or {},
            }

        # tuple for performance
        self.recipients = itertools.chain(self.recipients, (recip,))

    def add_recipients(self, recipients):
        for recip in recipients:
            self.add_recipient(recip)

    def clear_recipients(self):
        self.recipients = []

    def add_global_merge_vars(self, **kwargs):
        for key, val in kwargs.items():
            self.global_merge_vars[key] = val

    def clear_global_merge_vars(self):
        self.global_merge_vars = {}

    def add_tags(self, *tags):
        self.tags += tags

    def clear_tags(self):
        self.tags = []

    def set_body(self, content, mimetype='text/html'):
        self.body[mimetype] = content

    def set_from_addr(self, from_addr):
        self.from_addr = from_addr

    def set_reply_to_addr(self, reply_to_addr):
        self.reply_to_addr = reply_to_addr

    def set_subject(self, subject):
        self.subject = subject

    def set_webhook_data(self, data):
        self.webhook_data = data

    def enable_click_tracking(self):
        self.track_clicks = True

    def disable_click_tracking(self):
        self.track_clicks = False

    def enable_open_tracking(self):
        self.track_opens = True

    def disable_open_tracking(self):
        self.track_opens = False

    def set_importance(self, important):
        self.important = bool(important)

    def validate(self):
        if not self.subject or not self.from_addr:
            raise Exception('from address and subject are required!')

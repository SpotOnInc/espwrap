from __future__ import print_function, division, unicode_literals

import abc
import collections
import itertools
import sys


if sys.version_info < (3,):
    range = xrange


def batch(iterable, count=1):
    '''
    Split an iterable into a list of iterables having a length <= `count`
    '''

    total = len(iterable)

    for ndx in range(0, total, count):
        yield iterable[ndx:min(ndx + count, total)]


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
                 ip_pool=None, track_clicks=False, track_opens=False):
        self.recipients = []
        self.global_merge_vars = {}
        self.tags = []
        self.webhook_data = webhook_data
        self.ip_pool = ip_pool

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

            if recip.get('merge_vars') is None:
                recip['merge_vars'] = {}
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

    def solidify_recipients(self):
        '''
        Since recipients can be chained iterables of any form, but must
        eventually become lists that are passed to some upstream API, we want
        a consistent place to do that step. Thus, this will listify the internal
        iterable of recipients.
        '''

        self.recipients = list(self.recipients)

        return self.recipients

    def get_recipients(self):
        '''
        Safely returns the internal recipients listing, casting to an actual list.

        This will implicitly listify the recipients, see #solidify_recipients()
        for details
        '''

        return self.solidify_recipients()

    def get_raw_recipients(self):
        '''
        Returns the internal recipients listing in whatever, potentially unsafe,
        form it might be in (likely some itertools chain).
        '''

        return self.recipients

    def add_global_merge_vars(self, **kwargs):
        for key, val in kwargs.items():
            self.global_merge_vars[key] = val

    def clear_global_merge_vars(self):
        self.global_merge_vars = {}

    def get_global_merge_vars(self):
        return self.global_merge_vars

    def get_tags(self):
        return self.tags

    def clear_tags(self):
        self.tags = []

    def add_tags(self, *tags):
        self.tags += tags

    def set_body(self, content, mimetype='text/html'):
        self.body[mimetype] = content

    def get_body(self, mimetype):
        if mimetype:
            spec = self.body.get(mimetype)
            if spec:
                return spec

            raise Exception('Specified mimetype has not been set in body')

        return self.body

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

    def set_ip_pool(self, value):
        self.ip_pool = value

    def validate(self):
        if not self.subject or not self.from_addr:
            raise Exception('from address and subject are required!')

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
                 send_partition=500, reply_to_addr='', track_clicks=False,
                 track_opens=False
                 ):
        self.clear_recipients()
        self.clear_global_merge_vars()
        self.clear_tags()

        self.subject = subject
        self.from_addr = from_addr
        self.reply_to_addr = None

        self.partition = send_partition

        self.track_clicks = track_clicks
        self.track_opens = track_opens

        self.body = {
            'text/plain': text,
            'text/html': html,
        }

    def add_recipient(self, email, name='', merge_vars={}):
        # was given a dict containing everything, rather than a spread
        if isinstance(email, collections.Mapping):
            recip = email
        else:
            recip = {
                'name': name,
                'email': email,
                'merge_vars': merge_vars,
            }

        # tuple for performance
        self.recipients = itertools.chain(self.recipients, (recip,))

        return self

    def add_recipients(self, recipients):
        for recip in recipients:
            self.add_recipient(recip)

        return self

    def clear_recipients(self):
        self.recipients = list()

        return self

    def add_global_merge_var(self, key, value, overwrite=False):
        if not overwrite and self.global_merge_vars.get(key):
            raise Exception(
                'Global merge var {} has already been set'.format(key)
            )

        self.global_merge_vars[key] = value

        return self

    def add_global_merge_vars(self, mvars):
        for var in mvars:
            self.add_global_merge_var(**var)

        return self

    def clear_global_merge_vars(self):
        self.global_merge_vars = {}

        return self

    def add_tag(self, tag):
        self.tags.append(tag)

        return self

    def add_tags(self, tags):
        self.tags += tags

        return self

    def clear_tags(self):
        self.tags = list()

        return self

    def set_body(self, content, mimetype='text/html'):
        self.body[mimetype] = content

        return self

    def set_from_addr(self, from_addr):
        # TODO verify that this is a valid email string
        self.from_addr = from_addr

        return self

    def set_reply_to_addr(self, reply_to_addr):
        # TODO verify that this is a valid email string
        self.reply_to_addr = reply_to_addr

        return self

    def set_subject(self, subject):
        self.subject = subject

        return self

    def enable_click_tracking(self):
        self.track_clicks = True

        return self

    def disable_click_tracking(self):
        self.track_clicks = False

        return self

    def enable_open_tracking(self):
        self.track_opens = True

        return self

    def disable_open_tracking(self):
        self.track_opens = False

        return self

    def validate(self):
        if not self.subject or not self.from_addr:
            raise Exception('from address and subject are required!')

        return self

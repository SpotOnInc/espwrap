from __future__ import print_function, division, unicode_literals, absolute_import

import sys

import sendgrid
from smtpapi import SMTPAPIHeader

from espwrap.base import MassEmail, batch


if sys.version_info < (3,):
    range = xrange


class SendGridMassEmail(MassEmail):
    def __init__(self, api_key, *args, **kwargs):
        super(SendGridMassEmail, self).__init__(*args, **kwargs)

        self.client = sendgrid.SendGridClient(api_key)
        self.delimiters = ('-', '-')

    def set_variable_delimiters(self, start='-', end='-'):
        self.delimiters = (start, end)

    def add_tag(self, tag):
        if len(self.tags) >= 10:
            raise Exception('Cannot add new tag {}, SendGrid limits to 10 per email'.format(tag))

        return super(SendGridMassEmail, self).add_tag(tag)

    def add_tags(self, *tags):
        if len(tags) > 10:
            raise Exception('Too many tags, SendGrid limits to 10 per email')

        return super(SendGridMassEmail, self).add_tags(*tags)

    def _prepare_payload(self, recipients=None):
        def namestr(rec):
            if not rec.get('name'):
                return rec.get('email')

            return '{} <{}>'.format(rec['name'], rec['email'])

        if not recipients:
            recipients = list(self.recipients)

        num_rec = len(recipients)

        payload = SMTPAPIHeader()

        merge_vars = {}

        for key, val in self.global_merge_vars.items():
            keystr = ':{}'.format(key)

            new_key = '{1}{0}{2}'.format(key, *self.delimiters)

            merge_vars[new_key] = [keystr] * num_rec

            payload.add_section(keystr, val)

        for index, recip in enumerate(recipients):
            payload.add_to(recip if isinstance(recip, str) else namestr(recip))

            for rkey, rvalue in recip.get('merge_vars', {}).items():
                new_key = '{1}{0}{2}'.format(rkey, *self.delimiters)

                if not merge_vars.get(new_key):
                    merge_vars[new_key] = [None] * num_rec

                merge_vars[new_key][index] = rvalue

        if self.webhook_data:
            payload.set_unique_args(self.webhook_data)

        if self.ip_pool:
            payload.set_ip_pool(self.ip_pool)

        payload.set_substitutions(merge_vars)

        payload.add_filter('clicktrack', 'enable', self.track_clicks and 1 or 0)
        payload.add_filter('opentrack', 'enable', self.track_opens and 1 or 0)

        payload.set_categories(self.tags)

        return payload

    def send(self):
        self.validate()

        grouped_recipients = batch(list(self.recipients), self.partition)

        for grp in grouped_recipients:
            msg = sendgrid.Mail(smtpapi=self._prepare_payload(grp))

            msg.set_from(self.from_addr)
            msg.set_subject(self.subject)

            if self.reply_to_addr:
                msg.set_replyto(self.reply_to_addr)

            if self.body['text/plain']:
                msg.set_text(self.body['text/plain'])

            if self.body['text/html']:
                msg.set_html(self.body['text/html'])

            if self.important:
                msg.set_headers(Priority='Urgent', Importance='high')

            self.client.send(msg)

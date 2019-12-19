from __future__ import print_function, division, unicode_literals, absolute_import

import re
import sys

import sendgrid
from smtpapi import SMTPAPIHeader

from espwrap.base import MassEmail, batch, MIMETYPE_HTML, MIMETYPE_TEXT
from espwrap.adaptors.sendgrid_common import breakdown_recipients

if sys.version_info < (3,):
    range = xrange


class SendGridMassEmail(MassEmail):
    def __init__(self, api_key, *args, **kwargs):
        super(SendGridMassEmail, self).__init__(*args, **kwargs)

        try:
            self.client = sendgrid.SendGridAPIClient(api_key)
        except:
            try:
                self.client = sendgrid.SendGridClient(api_key)
            except AttributeError as e:
                raise Exception(
                    '{}.\nSendgrid client attribute is SendGridAPIClient in newer versions. \
Also tried older client name, SendGridClient. Both failed.'.format(e))
        
        self.delimiters = ('-', '-')

    def set_variable_delimiters(self, start='-', end='-'):
        self.delimiters = (start, end)

    def get_variable_delimiters(self, as_dict=False):
        if as_dict:
            return {
                'start': self.delimiters[0],
                'end': self.delimiters[1],
            }

        return self.delimiters

    def add_tags(self, *tags):
        if len(tags) > 10:
            raise Exception('Too many tags, SendGrid limits to 10 per email')

        if len(tags) + len(self.tags) > 10:
            raise Exception('Requested tags would have raised total to above Sendgrid limit of 10')

        return super(SendGridMassEmail, self).add_tags(*tags)

    def _prepare_payload(self, recipients=None):
        def namestr(rec):
            if not rec.get('name'):
                return rec.get('email')

            return '"{}" <{}>'.format(rec['name'].replace('"', ''), rec['email'].replace(',', ''))

        if not recipients:
            recipients = self.solidify_recipients()

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

        if self.template_name:
            payload.add_filter('templates', 'enabled', 1)
            payload.add_filter('templates', 'template_id', self.template_name)

        payload.set_substitutions(merge_vars)

        payload.add_filter('clicktrack', 'enable', self.track_clicks and 1 or 0)
        payload.add_filter('opentrack', 'enable', self.track_opens and 1 or 0)

        payload.set_categories(self.tags)

        return payload

    def send(self):
        self.validate()

        grouped_recipients = batch(list(self.recipients), self.partition)

        for grp in grouped_recipients:
            to_send = breakdown_recipients(grp)

            for subgrp in to_send:
                msg = sendgrid.Mail(smtpapi=self._prepare_payload(subgrp))

                msg.set_from(self.from_addr)
                msg.set_subject(self.subject)

                if self.reply_to_addr:
                    msg.set_replyto(self.reply_to_addr)

                if self.body[MIMETYPE_TEXT]:
                    msg.set_text(self.body[MIMETYPE_TEXT])

                if self.body[MIMETYPE_HTML]:
                    msg.set_html(self.body[MIMETYPE_HTML])

                if self.important:
                    msg.set_headers({'Priority': 'Urgent', 'Importance': 'high'})

                if self.attachments:
                    for file_name, file_path_or_string in self.attachments.iteritems():
                        msg.add_attachment(file_name, file_path_or_string)

                if self.send_at:
                    msg.smtpapi.set_send_at(self.send_at)

                for email in self.cc_list:
                    msg.add_cc(email)

                for email in self.bcc_list:
                    msg.add_bcc(email)

                self.client.send(msg)

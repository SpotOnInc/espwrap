from __future__ import print_function, division, unicode_literals, absolute_import

import base64
import json
import logging
import os
import sys

from python_http_client import exceptions
import sendgrid
from sendgrid.helpers.mail import (
    Mail, From, To, Cc, Bcc, Subject, Substitution,
    CustomArg, SendAt, Content, MimeType, Attachment, FileName,
    FileContent, ReplyTo, Category, IpPoolName,
    TrackingSettings, ClickTracking,
    OpenTracking, OpenTrackingSubstitutionTag,
    Section)

from espwrap.base import MassEmail, batch, MIMETYPE_HTML, MIMETYPE_TEXT
from espwrap.adaptors.sendgrid_common import breakdown_recipients

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class SendGridMassEmail(MassEmail):
    def __init__(self, api_key, *args, **kwargs):
        super(SendGridMassEmail, self).__init__(*args, **kwargs)

        self.client = sendgrid.SendGridAPIClient(api_key)

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

    def message_constructor(self, to_send):
        message = Mail()
        to_emails = []

        # Content (Text)
        if self.body[MIMETYPE_TEXT]:
            content = Content(
                MimeType.text,
                self.body[MIMETYPE_TEXT]
            )
            message.content = content

        # Content (Html)
        if self.body[MIMETYPE_HTML]:
            content = Content(
                MimeType.html,
                self.body[MIMETYPE_HTML]
            )
            message.content = content

        message.subject = Subject(self.subject)

        # Category
        if self.tags:
            for tag in self.tags:
                message.category = Category(tag)

        # Reply
        if self.reply_to_addr:
            message.reply_to = ReplyTo(self.reply_to_addr)

        # Send At
        if self.send_at:
            message.send_at = SendAt(self.send_at)

        # IP Pool
        if self.ip_pool:
            message.ip_pool_name = IpPoolName(self.ip_pool)

        # CC
        if self.cc_list:
            list_cc = [Cc(email) for email in self.cc_list]
            message.cc = list_cc

        # BCC
        if self.bcc_list:
            list_bcc = [Bcc(email) for email in self.cc_list]
            message.bcc = list_bcc

        # Attachment
        if self.attachments:
            for file_name, file_path_or_string in self.attachments.iteritems():
                attachment = Attachment()
                encoded = base64.b64encode(str(file_path_or_string))
                attachment.file_content = FileContent(encoded)
                attachment.file_name = FileName(file_name)
            message.attachment = attachment

        # Webhook Data
        if self.webhook_data:
            for key, val in self.webhook_data.items():
                message.custom_arg = CustomArg(key, val)

        # Metadata
        if hasattr(self, 'metadata'):
            for key, val in self.metadata.items():
                message.custom_arg = CustomArg(key, val)

        # Template Name
        if self.template_name:
            message.custom_arg = CustomArg('template_name', self.template_name)

        # Tracking
        tracking_settings = TrackingSettings()
        # Opens
        if self.track_opens:
            tracking_settings.open_tracking = OpenTracking(
                self.track_opens,
                OpenTrackingSubstitutionTag("open_tracking")
            )
        # Clicks
        if self.track_clicks:
            tracking_settings.click_tracking = ClickTracking(
                self.track_clicks,
                self.track_clicks
            )
        message.tracking_settings = tracking_settings
        message.from_email = From(self.from_addr)

        for subgrps in to_send:
            for subgrp in subgrps:
                substitutions = subgrp['merge_vars']
                substitutions = {'{1}{0}{2}'.format(x, *self.delimiters): str(substitutions[x]) for x in substitutions}
                to_emails.append(To(subgrp['email'], subgrp['name'], substitutions=substitutions))

        message.add_to(to_emails, is_multiple=True)

        # Global Subs
        for key, val in self.global_merge_vars.items():
            new_key = '{1}{0}{2}'.format(key, *self.delimiters)
            message.substitution = Substitution(new_key, str(val))

        return message


    def send(self):

        responses=[]

        self.validate()

        grouped_recipients = batch(list(self.recipients), self.partition)

        #DEBUG
        print (self.recipients)

        for grp in grouped_recipients:
            to_send = breakdown_recipients(grp)

            message = self.message_constructor(to_send)

            #message data as dict for examination/validation below
            message_dict = message.get()

            #do not send if custom args >10 KB (sendgrid rule)
            if 'custom_args' in message_dict:
                message_custom_args = len(json.dumps(message_dict['custom_args']))
                custom_args_size = sys.getsizeof(message_custom_args)
                custom_args_kb = 0.001 * float(custom_args_size)
                if custom_args_kb > 10:
                    raise Exception('attempted to send {} KB custom_args, not to exceed 10 KB.'.format(custom_args_kb))

            #do not send if number of recipients >1000 (sendgrid rule)
            num_recips = len(message_dict['personalizations'])
            if num_recips > 1000:
                raise Exception('attempted to send to {} email addresses, not to exceed 1000 addresses.'.format(num_recips))

            """
            send message and append response from this grp to list of returned responses for all grouped_recipients
            """
            try:
                logger.debug(message)
                response = self.client.send(message)
                responses.append(response)
            except Exception:
                logger.exception('')

        #return list of all responses for each grp in grouped_recipients
        return responses

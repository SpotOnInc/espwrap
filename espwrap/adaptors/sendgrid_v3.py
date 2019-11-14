from __future__ import print_function, division, unicode_literals, absolute_import

import base64
import json
import logging
import os
import sys

import sendgrid
from sendgrid.helpers.mail import (
    Mail, From, To, Cc, Bcc, Subject, Substitution,
    CustomArg, SendAt, Content, MimeType, Attachment, FileName,
    FileContent, ReplyTo, Category, IpPoolName,
    TrackingSettings, ClickTracking,
    OpenTracking, OpenTrackingSubstitutionTag,
    Section)

from python_http_client import exceptions

from espwrap.base import MassEmail, batch, MIMETYPE_HTML, MIMETYPE_TEXT

from espwrap.adaptors.sendgrid_common import breakdown_recipients

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
#handler = logging.StreamHandler(sys.stdout)
#handler.setLevel(logging.INFO)
#formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#handler.setFormatter(formatter)
#logger.addHandler(handler)


class SendGridMassEmail(MassEmail):
    def __init__(self, api_key, *args, **kwargs):
        
        super(SendGridMassEmail, self).__init__(*args, **kwargs)

        self.client = sendgrid.SendGridAPIClient(api_key)

        self.delimiters = ('-', '-')

        self.verbose = True #False

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


    def send(self):
        self.validate()
        
        grouped_recipients = batch(list(self.recipients), self.partition)
        
        #DEBUG
        logger.info("grouped_recipients >>>>>>>>>>")
        logger.info(grouped_recipients)

        for grp in grouped_recipients:
            
            #DEBUG
            logger.info("grp >>>>>>>>>>")
            logger.info(grp)

            to_send = breakdown_recipients(grp)

            #DEBUG
            logger.info("to_send >>>>>>>>>>")
            logger.info(to_send)

            message = Mail()

            for subgrp in to_send:

                #DEBUG
                logger.info("subgrp >>>>>>>>>>>>")
                logger.info(subgrp)

                #Reply
                if self.reply_to_addr:
                    message.reply_to = ReplyTo(self.reply_to_addr)

                #Send At
                if self.send_at:
                    message.send_at = SendAt(self.send_at)

                #Category
                if self.tags:
                    message.Category = Category(self.tags)

                #IP Pool
                if self.ip_pool:
                    message.ip_pool_name = IpPoolName(self.ip_pool)

                #CC
                if self.cc_list:
                    list_cc = []
                    for email in self.cc_list:
                        list_cc.append(Cc(email))
                    message.cc = list_cc

                #BCC
                if self.bcc_list:
                    list_bcc = []
                    for email in self.bcc_list:
                        list_bcc.append(Bcc(email))
                    message.bcc = list_bcc

                #Content (Text)
                if self.body[MIMETYPE_TEXT]:
                    content = Content(
                        MimeType.text,
                        self.body[MIMETYPE_TEXT]
                    )
                    message.content = content

                #Content (Html)
                if self.body[MIMETYPE_HTML]:
                    content = Content(
                        MimeType.html,
                        self.body[MIMETYPE_HTML]
                    )
                    message.content = content

                #Attachment
                if self.attachments:
                    for file_name, file_path_or_string in self.attachments.iteritems():
                        attachment = Attachment()
                        encoded = base64.b64encode(str(file_path_or_string))
                        attachment.file_content = FileContent(encoded)
                        attachment.file_name = FileName(file_name)
                    message.attachment = attachment

                #Webhook Data
                if self.webhook_data:
                    for key, val in self.webhook_data.items():
                        message.custom_arg = CustomArg(key, val)
                if self.template_name:
                    message.custom_arg = CustomArg('template_name', self.template_name)

                #Tracking
                tracking_settings = TrackingSettings()            
                #Opens
                if self.track_opens:
                    tracking_settings.open_tracking = OpenTracking(
                        self.track_opens,
                        OpenTrackingSubstitutionTag("open_tracking")
                    )
                #Clicks
                if self.track_clicks:
                    tracking_settings.click_tracking = ClickTracking(
                        self.track_clicks,
                        self.track_clicks
                    )
                message.tracking_settings = tracking_settings                
                
                for p, recip in enumerate(subgrp):

                    #DEBUG
                    logger.info("p >>>>>>")
                    logger.info(p)
                    logger.info("recip >>>>>>>>")
                    logger.info(recip)

                    
                    message.from_email = From(self.from_addr)
                    message.to = To(recip['email'], p=p)
                    message.subject = Subject(self.subject)

                    #Global Subs
                    for key, val in self.global_merge_vars.items():
                        new_key = '{1}{0}{2}'.format(key, *self.delimiters)
                        message.substitution =  Substitution(new_key, val, p=p)
                    
                    #Substitutions
                    for key, val in recip['merge_vars'].items():
                        new_key = '{1}{0}{2}'.format(key, *self.delimiters)
                        message.substitution = Substitution(new_key, val, p=p)


                #DEBUG
                logger.info("message1 >>>>>>")
                logger.info(message)

            try:
                response = self.client.send(message)
                if self.verbose:
                    print(response.status_code)
                    print(response.body)
                    print(response.headers)
            except exceptions.BadRequestsError as e:
                raise

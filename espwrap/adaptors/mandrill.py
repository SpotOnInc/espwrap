from __future__ import print_function, division, unicode_literals, absolute_import

import sys

import mandrill

from espwrap.base import MassEmail, batch, MIMETYPE_HTML, MIMETYPE_TEXT


if sys.version_info < (3,):
    range = xrange


class MandrillMassEmail(MassEmail):
    def __init__(self, api_key, *args, **kwargs):
        super(MandrillMassEmail, self).__init__(*args, **kwargs)

        self.client = mandrill.Mandrill(api_key)

    def _prepare_payload(self, recipients=None):
        def namestr(rec):
            if not rec.get('name'):
                return rec.get('email')

            return '{} <{}>'.format(rec['name'], rec['email'])

        if not recipients:
            recipients = list(self.recipients)

        payload = {
            'from_email': self.from_addr,
            'html': self.body.get(MIMETYPE_HTML),
            'text': self.body.get(MIMETYPE_TEXT),
            'subject': self.subject,
            'to': [],
            'preserve_recipients': False,
            'merge': True,
            'merge_language': 'mailchimp',
            'global_merge_vars': [{
                'name': key,
                'content': value,
            } for key, value in self.global_merge_vars.items()],
            'merge_vars': [],
            'important': self.important,
        }

        for index, recip in enumerate(recipients):
            payload['to'].append({
                'type': 'to',
                'name': recip.get('name', recip['email']),
                'email': recip['email'],
            })

            payload['merge_vars'].append({
                'rcpt': recip['email'],
                'vars': [{
                    'name': key,
                    'content': value,
                } for key, value in recip.get('merge_vars', {}).items()],
            })

        payload['track_clicks'] = self.track_clicks
        payload['track_opens'] = self.track_opens
        payload['tags'] = self.tags

        if self.webhook_data:
            payload['metadata'] = self.webhook_data

        return payload

    def send(self):
        self.validate()

        kwargs = {
            'async': True
        }

        if self.ip_pool:
            kwargs['ip_pool'] = self.ip_pool

        if self.template_name:
            mandrill_send = self.client.messages.send_template
            kwargs['template_name'] = self.template_name
        else:
            mandrill_send = self.client.messages.send

        grouped_recipients = batch(list(self.recipients), self.partition)

        for grp in grouped_recipients:
            mandrill_send(message=self._prepare_payload(grp), **kwargs)

from __future__ import print_function, division, unicode_literals, absolute_import

import sys

from espwrap.base import MassEmail


if sys.version_info < (3,):
    range = xrange


class NoopMassEmail(MassEmail):
    def __init__(self, api_key, *args, **kwargs):
        super(NoopMassEmail, self).__init__(*args, **kwargs)

    def send(self):
        pass

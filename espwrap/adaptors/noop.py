from __future__ import print_function, division, unicode_literals, absolute_import

import sys

from espwrap.base import MassEmail


if sys.version_info < (3,):
    range = xrange


class NoopMassEmail(MassEmail):
    def send(self):
        pass

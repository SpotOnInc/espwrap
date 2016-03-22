from __future__ import absolute_import

from espwrap.base import MassEmail


class NoopMassEmail(MassEmail):
    def send(self):
        raise NotImplementedError()

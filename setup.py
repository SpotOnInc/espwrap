from __future__ import print_function, division, unicode_literals

from setuptools import setup

setup(
    name='espwrap',
    version='1.0.0',
    description='A light wrapper around email service providers',
    url='https://github.com/SpotOnInc/espwrap',
    license='MIT',
    author='SpotOn',
    packages=[str('espwrap')],
    platforms='any',
    extras_require={
        'mandrill': ['mandrill>=1.0.57'],
        'sendgrid': [
            'smtpapi>=0.3.1',
            'sendgrid>=2.2.1',
        ],
    }
)

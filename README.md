# ESPwrap

[![Travis-CI Build Status](https://api.travis-ci.org/SpotOnInc/espwrap.svg)](https://travis-ci.org/SpotOnInc/espwrap)

A light wrapper around email service providers. Allows (semi-)seamless movement between supported ESP backends.

## Example Usage
```python
from espwrap.adaptors.mandrill import MandrillMassEmail

email = MandrillMassEmail(api_key='< YOUR MANDRILL KEY HERE >')

email.set_from_addr('donotreply@spam.com')

email.set_subject('Mandrill Test (via ESPwrap)')

email.add_recipient(name='Josh', email='SOME@EMAIL.HERE', merge_vars={'CUSTOMER_NAME': 'Josh'})
email.add_recipient(name='Jim', email='SOME@OTHEREMAIL.HERE', merge_vars={'CUSTOMER_NAME': 'Jim'})

email.add_global_merge_vars(SENDING_COMPANY='SpotOn')

email.set_body('Testing Test to *|CUSTOMER_NAME|* from *|SENDING_COMPANY|*', mimetype='text/plain')
email.set_body('<h2>TESTING TEST TO *|CUSTOMER_NAME|* FROM *|SENDING_COMPANY|*</h2>')

email.send()
```

## Currently Supported ESP Backends
Full/partial support is relative to the overall ESPwrap feature set. "Full" support does *not* indicate that ESPwrap supports all functionality of the ESP, but rather that all "common denominator" functionality which ESPwrap provides, is available in that ESP's subclass.

- Mandrill (Partial as of 22 March 2016)
    * Webhooks unsupported
    * IP Pools unsupported
- SendGrid (Full as of 21 March 2016)

Don't see your ESP in the list? It's easy to write an adaptor! Perhaps check out the Mandrill adaptor and write your own based on it. Pull requests are always welcome!


## ESPwrap is open-source!
```
The MIT License (MIT)

Copyright (c) 2016 SpotOn

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```


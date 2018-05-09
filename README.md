# ESPwrap

[![Travis-CI Build Status](https://api.travis-ci.org/SpotOnInc/espwrap.svg)](https://travis-ci.org/SpotOnInc/espwrap)

A light wrapper around email service providers. Allows (semi-)seamless movement
between supported ESP backends.

Supported on, and [tested against](https://travis-ci.org/SpotOnInc/espwrap),
the following versions of Python (or see `.travis.yml`):

- 2.7
- 3.4
- 3.5
- 3.6

We also test against nightly, but may prioritize bugs found on this version of
Python lower than others.

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
Full/partial support is relative to the overall ESPwrap feature set. "Full"
support does *not* indicate that ESPwrap supports all functionality of the ESP,
but rather that all "common denominator" functionality which ESPwrap provides,
is available in that ESP's subclass.

- SendGrid (Full)
- Mandrill (Full)

Don't see your ESP in the list? It's easy to write an adaptor! Perhaps check
out the Mandrill adaptor and write your own based on it. Pull requests are
always welcome!


## API
### `add_recipient(email, name='', merge_vars={})`
Support: Mandrill, SendGrid

> Adds a recipient to the send list. Recipients will be hidden from each other,
> which is currently a hard-coded fact of life.

> `email` may be a string (optionally joined by the `name` and `merge_vars`
> named arguments), or may be a dictionary containing `email` and optionally
> `name` and `merge_vars` keys.

> If `merge_vars` are not provided, they will be set to an empty object.

```python
me = NoopMassEmail()

me.add_recipient('test@spam.com', name='Spammer')
me.add_recipient({
    'name': 'Spammer 2',
    'email': 'hunter2@spam.com',
    'merge_vars': {
        'SOME_VAR': 42,
    },
})
```


### `add_recipients(recipients=[])`
Support: Mandrill, SendGrid

> Will lazily append the iterable `recipients` to the internal list of
> recipients. Should be an iterable of dictionaries.

> If a lazy structure is passed here, the values will not be parsed until an
> eventual call to `solidify_recipients` or `get_recipients`.

> See `add_recipient` for the format of these dictionaries.


### `clear_recipients()`
Support: Mandrill, SendGrid

> Resets the internal recipients list to an empty list.


### `solidify_recipients()`
Support: Mandrill, SendGrid

> This is largely an internal function that should never need to be called by a
> consumer. This will evaluate any lazy recipient entries in the internal
> listing and coerce the internal recipient listing to a true `list` type.

> Returns the new list.


### `get_recipients()`
Support: Mandrill, SendGrid

> Returns the internal recipients listing after being fully evaluated by
> `solidify_recipients()`


### `get_raw_recipients()`
Support: Mandrill, SendGrid

> Returns the raw internal structure of the recipients listing. This will
> almost always be either a `list` or an `itertools.chain` object.

> Should not be needed by any consumers, largely used for unit testing.


### `add_global_merge_vars(**kwargs)`
Support: Mandrill, SendGrid

> Sets each named parameter in the internal listing of global merge variables.
> These variables will be set in each outgoing email unless overridden in a
> recipient-level merge variable according to ESP-specific rules.

> In Mandrill, this is simply done through the `global_merge_vars` payload
> entry.

> In SendGrid, to save payload size, global merge vars become
> [Sections](https://sendgrid.com/docs/API_Reference/SMTP_API/section_tags.html)
> which are referenced in the eventual Substitutions array.

```python
me = NoopMassEmail()

me.add_global_merge_vars(COMPANY_NAME='SpotOn', COPYRIGHT='2016')
```


### `clear_global_merge_vars()`
Support: Mandrill, SendGrid

> Clears the internal listing of global merge variables (sets it to an empty
> dictionary).


### `get_global_merge_vars()`
Support: Mandrill, SendGrid

> Useful for sanity checks, returns the current listing of global merge
> variables as a dictionary.

```python
me = NoopMassEmail()

me.add_global_merge_vars(COMPANY_NAME='SpotOn', COPYRIGHT='2016')

me.get_global_merge_vars()
# => { 'COMPANY_NAME': 'SpotOn', 'COPYRIGHT': '2016' }
```


### `add_tags(tag1, tag2, ...)`
Support: Mandrill, SendGrid

> Add a tag to the email. These are used in varying ways, check with your ESP
> for details on how many they'll keep track of.

> SendGrid limitation: only 10 tags may be added to an email.

```python
me = NoopMassEmail()

tags = ['something', 'and', 'something', 'else']

me.add_tags(*tags)

me.add_tags('OneMoreForGoodMeasure')
```


### `get_tags()`
Support: Mandrill, SendGrid

> Return the list of tags currently assigned to the email.


### `clear_tags()`
Support: Mandrill, SendGrid

> Reset the internal tags collection to an empty `list`


### `set_body(content, mimetype='text/html')`
Support: Mandrill, SendGrid

> Sets the body content of the email, segregated by mimetype, defaulting to
> HTML. Presently, only plain text and HTML emails are supported. You may wish
> to use the `MIMETYPE_PLAIN` and `MIMETYPE_HTML` constants defined in
> `espwrap.base` here.

```python
me = NoopMassEmail()
msg_text = 'Tester Test'
msg_html = '<h1>Tester Test HTML</h1>'

me.set_body(msg_html)
me.set_body(msg_text, mimetype=MIMETYPE_TEXT)
```


### `get_body(mimetype=None)`
Support: Mandrill, SendGrid

> Returns the current body content, either as a dictionary (keyed on mimetype),
> or as a string if a valid `mimetype` is passed. If an unset `mimetype`
> is passed, an `AttributeError` will be raised.


### `set_from_addr(from_addr)` and `get_from_addr()`
Support: Mandrill, SendGrid

> Sets or gets the email address the email will be from. **REQUIRED** before
> emails can be sent through Mandrill or SendGrid adaptors.


### `set_reply_to_addr(reply_to_addr)` and `get_reply_to_addr()`
Support: Mandrill, SendGrid

> Sets or gets a reply-to address for the email. Optional, and will default to
> `None` and not be set in the outgoing email.


### `set_subject(subject)` and `get_subject()`
Support: Mandrill, SendGrid

> Sets or gets the subject for the email. **REQUIRED** before
> emails can be sent through Mandrill or SendGrid adaptors.


### `set_webhook_data(data)` and `get_webhook_data()`
Support: Mandrill, SendGrid

> Sets or gets unique webhook-related data for the email. ESPs will handle this
> in their own unique ways internally, please see their documentation for what
> format this should be in.


### `enable_click_tracking()`, `disable_click_tracking()`, and `get_click_tracking_status()`
Support: Mandrill, SendGrid

> Enables, disables, or reports status of click tracking for the email.


### `enable_open_tracking()`, `disable_open_tracking()`, and `get_open_tracking_status()`
Support: Mandrill, SendGrid

> Enables, disables, or reports status of open tracking for the email.


### `set_importance(important)` and `get_importance()`
Support: Mandrill, SendGrid

> Sets/gets (through a cast boolean) whether an email should have standard
> SMTP priority headers. Not all email servers or clients can handle this info,
> in which cases it may be silently ignored.


### `set_ip_pool(value)` and `get_ip_pool()`
Support: Mandrill, SendGrid

> Sets/gets the IP Pool identifier the email should use.


### `set_template_name(value)` and `get_template_name()`
Support: Mandrill, SendGrid

> Sets/gets the ESP-hosted template name to use with this message.
> Falsy values indicate no ESP template.


### `validate()`
Support: Mandrill, SendGrid

> Ensure that both a subject and from address have been set on the email.
> Called internally to sanity-check emails before producing payloads or sending.
> Will raise an `Exception` if these criteria are not met.


### `set_variable_delimiters(start='-', end='-')`
Support: SendGrid

> Define the delimiters to use for merge variables. Defaults to SendGrid's
> default hyphens, but can easily be swapped out with, ex. Mandrill-style
> delimiters.


### `get_variable_delimiters(as_dict=False)`
Support: SendGrid

> Returns the currently set variable delimiters, either as a tuple (the default),
> or as a dictionary keyed on `start` and `end`.


### `add_attachment(file_name, file_obj_or_path)`
Support: SendGrid

> Adds an attachment. The file_obj_or_path is either a path or a
> file object returned by open.


### `add_bcc(email)`
Support: SendGrid

> Adds blind carbon copy.


### `add_cc(email)`
Support: SendGrid

> Adds carbon copy.

### `set_send_at(email)`
Support: SendGrid

> Schedules email up to 72 hours in advance.

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


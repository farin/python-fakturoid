# fakturoid.cz Python API

The Python interface to online accounting service [Fakturoid](http://fakturoid.cz/).

This library is developed and maintained by Roman Krejcik ([farin@farin.cz](mailto:farin@farin.cz)).
It is unoficial and no support from Fakturoid team can be claimed.

## Installation

Install from PyPI

    pip install fakturoid

or alternatively install development version directly from github

    pip install -e git+git://github.com/farin/python-fakturoid#egg=fakturoid


Supported Python versions are 2.6+ and 3.x. Dependencies are [requests](https://pypi.python.org/pypi/requests),
[python-dateutil](https://pypi.python.org/pypi/python-dateutil/2.1)

## Quickstart

Create context:
```python
from fakturoid import Fakturoid

fa = Fakturoid('yoursubdomain', '38dc73...', 'YourApp (yourname@example.com)')
```

Print 25 regular invoices in year 2013:
```python
from datetime import date

for invoice in fa.invoices(proforma=False, since=date(2013,1,1))[:25]:
    print(invoice.number, invoice.total)
```

Delete subject with id 27:
```python
subject = fa.subject(27)
fa.delete(subject)
```

And finally create new invoice:
```python
from fakturoid import Invoice, InvoiceLine

invoice = Invoice(
    subject_id=28,
    number='2013-0108',
    due=10,
    issued_on=date(2012, 3, 30),
    taxable_fulfillment_due=date(2012, 3, 30),
    lines=[
        # use Decimal or string for floating values
        InvoiceLine(name='Hard work', unit_name='h', unit_price=40000, vat_rate=20),
        InvoiceLine(name='Soft material', quantity=12, unit_name='ks', unit_price="4.60", vat_rate=20),
    ]
)
fa.save(invoice)

print(invoice.due_on)
```

## API

<code>Fakturoid.<b>account()</b></code>

Returns `Account` instance. Account is readonly and can't be updated by API.

<code>Fakturoid.<b>subject(id)</b></code>

Returns `Subject` instance.

<code>Fakturoid.<b>subjects(since=None)</b></code>

Loads all subjects. If since (`date` or `datetime`) paramter is passed, retuns only subjects created since given date.

<code>Fakturoid.<b>invoce(id)</b></code>

Returns `Invoice` instance.

<code>Fakturoid.<b>invoices(proforma=None, subject_id=None, since=None, number=None, status=None)</b></code>

Use `proforma=False`/`True` parameter to load regular or proforma invoices only.

Returns list of invoices. Invoices are lazily loaded according to slicing.
```python
fa.invoices(status='paid')[:100]   # loads 100 paid invoices
fa.invoices()[-1]   # loads first issued invoice (invoices are ordered from latest to first)
```

<code>Fakturoid.<b>generator(id)</b></code>

Returns `Generator` instance.

<code>Fakturoid.<b>generators(recurring=None, subject_id=None, since=None)</b></code>

Use `recurring=False`/`True` parameter to load recurring or simple templates only.

<code>Fakturoid.<b>save(model)</b></code>

Create or modify `Subject`, `Invoice` or `Generator`.

Fakturoid JSON API doesn't support modifying invoice lines. Only base invoice attributes
can be updated and `lines` property is ignored during save.

<code>Fakturoid.<b>delete(model)</b></code><br>
<code>Fakturoid.<b>delete(model_type, id)</b></code>

Delete `Subject`, `Invoice` or `Generator`.

```python
subj = fa.subject(1234)
fa.delete(subj)            # delete subject

fa.delete(Subject, 1234)   # or alternativelly delete is possible without object loading
```

### Models

All models fields are named same as  [Fakturoid API](http://docs.fakturoid.apiary.io/).

Values are mapped to corresponding `int`, `decimal.Decimal`, `datetime.date` and `datetime.datetime` types.

<code>Fakturoid.<b>Account</b></code>

[http://docs.fakturoid.apiary.io/#account](http://docs.fakturoid.apiary.io/#account)

<code>Fakturoid.<b>Subject</b></code>

[http://docs.fakturoid.apiary.io/#subjects](http://docs.fakturoid.apiary.io/#subjects)

<code>Fakturoid.<b>Invoice</b></code><br>
<code>Fakturoid.<b>InvoiceLine</b></code>

[http://docs.fakturoid.apiary.io/#invoices](http://docs.fakturoid.apiary.io/#invoices)

<code>Fakturoid.<b>Generator</b></code>

[http://docs.fakturoid.apiary.io/#generators](http://docs.fakturoid.apiary.io/#generators)

Use `InvoiceLine` for generator lines

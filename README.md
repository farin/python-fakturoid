# fakturoid.cz Python API

The Python interface to online accounting service [Fakturoid](http://fakturoid.cz/).

This library is developed and maintained by Roman Krejcik ([farin@farin.cz](mailto:farin@farin.cz)).
It is unoficial and no support from Fakturoid team can be claimed.

**Full API is not implmented yet. python-fakturoid is under active development and must be consider unstable yet.**

## Installation

    python setup.py install

Supported Python versions are 2.6+ and 3.x. Dependencies are [requests](https://pypi.python.org/pypi/requests),
[python-dateutil](https://pypi.python.org/pypi/python-dateutil/2.1)

## Quickstart

Create context:

    from fakturoid import Fakturoid

    fa = Fakturoid('yoursubdomain', '653638dc733afce75130303fe6e6010f63768af0', 'YourApp (yourname@example.com)')

Print 25 regular invoices in year 2013:

    from datetime import date

    for invoice in fa.invoices(proforma=False, since=date(2013,1,1))[:25]:
        print(invoice.number, invoice.total)

Delete subject with id 27:

    subject = fa.subject(27)
    fa.delete(subject)

And finally create new invoice:

    from fakturoid import Invoice, InvoiceLine

    invoice = Invoice(
        subject_id=28,
        number='2013-0108',
        due=10,
        issued_on=date(2012, 3, 30),
        taxable_fulfillment_due=date(2012, 3, 30),
        lines=[
            InvoiceLine(name='Hard work', unit_name='h', unit_price=40000, vat_rate=20),
            InvoiceLine(name='Soft material', quantity=12, unit_name='ks', unit_price="4.60", vat_rate=20),
        ]
    )
    fa.save(invoice)
    print(invoice.due_on)


## API

All models fields are named same as  [Fakturoid API](https://github.com/fakturoid/api).

Values are mapped to corresponding `int`, `decimal.Decimal`, `datetime.date` and `datetime.datetime` types.

### Account

[API/account.md](https://github.com/fakturoid/api/blob/master/sections/account.md)

####Fakturoid.account()

Returns account model.

### Subjects

[API/subject.md](https://github.com/fakturoid/api/blob/master/sections/subject.md)

####Fakturoid.subject(id)

Returns subject model by id

####Fakturoid.subjects(since=None)

Returns all subjects.

### Invoices

####Fakturoid.invoice(id)

Returns invoice model by id [API/invoice.md](https://github.com/fakturoid/api/blob/master/sections/invoice.md)

####Fakturoid.invoices(proforma=None, subject_id=None, since=None, number=None, status=None)

Use `proforma=False`/`True` parameter to load regular or proforma invoices only.

Returns list of invoices. Invoices are lazily loaded according to slicing.
Be careful with negative indexes. JSON API dosen't provide invoice count so
all invoice pages must be iterate in such case.

    fa.invoices()[99]   # loads 100th invoice,
                        # read one invoice page

    fa.invoices()[-1]   # loads first issued invoice (invoices are ordered from latest to first)
                        # must read all invoice pages

### Data updates

####Fakturoid.save(model)

Create or modify subject or invoice.

Note: Original fakturoid API doesn't support updating invoice lines!

####Fakturoid.delete(model)

Delete subject or invoice.














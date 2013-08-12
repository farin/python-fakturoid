from __future__ import unicode_literals

import sys

from decimal import Decimal
from dateutil.parser import parse

__all__ = ['Account', 'Subject', 'InvoiceLine', 'Invoice', 'Generator']

if sys.version_info[0] >= 3: # Python 3
    basestring = str


class UnicodeMixin(object):
  """Mixin class to handle defining the proper __str__/__unicode__
  methods in Python 2 or 3."""
  if sys.version_info[0] >= 3: # Python 3
      def __str__(self):
          return self.__unicode__()
  else:  # Python 2
      def __str__(self):
          return self.__unicode__().encode('utf8')


class Model(UnicodeMixin):
    """Base class for all Fakturoid model objects"""
    id = None

    def __init__(self, **fields):
        self.update(fields)

    def __repr__(self):
        return "<{0}:{1}>".format(self.__class__.__name__, self.id)

    def update(self, fields):
        for field, value in fields.items():
            if value and isinstance(value, basestring):
                if field.endswith('_at'):
                    fields[field] = parse(value)
                elif field.endswith('_on') or field.endswith('_due') or field.endswith('_date'):
                    fields[field] = parse(value).date()
                elif field in self.Meta.decimal:
                    fields[field] = Decimal(value)
        self.__dict__.update(fields)

    def is_field_writable(self, field, value):
        # if hasattr(self.Meta, 'writable'):
        #    return field in self.Meta.writable
        if hasattr(self.Meta, 'readonly'):
            return field not in self.Meta.readonly
        return True

    def serialize_field_value(self, value):
        if isinstance(value, Model):
            return value.get_fields()
        if isinstance(value, list):
            nv = []
            for item in value:
                nv.append(self.serialize_field_value(item))
            return nv
        if isinstance(value, Decimal):
            return str(value)
        if hasattr(value, 'isoformat'):
            return value.isoformat()
        return value

    def get_fields(self):
        data = {}
        for field, value in self.__dict__.items():
            if self.is_field_writable(field, value):
                data[field] = self.serialize_field_value(value)
        return data


class Account(Model):
    """See https://github.com/fakturoid/api/blob/master/sections/account.md for complete field reference."""
    name = None

    class Meta:
        decimal = []

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return "<{0}:{1}>".format(self.__class__.__name__, self.name)


class Subject(Model):
    """See https://github.com/fakturoid/api/blob/master/sections/subject.md for complete field reference."""
    name = None

    class Meta:
        readonly = ['id', 'html_url', 'url', 'updated_at']
        decimal = []

    def __unicode__(self):
        return self.name


class InvoiceLine(Model):
    quantity = None

    class Meta:
        readonly = []
        decimal = ['quantity', 'unit_price']

    def __init__(self, **kwargs):
        self.quantity = Decimal(1)
        super(InvoiceLine, self).__init__(**kwargs)

    def __unicode__(self):
        if self.unit_name:
            return "{0} {1} {2}".format(self.quantity, self.unit_name, self.name)
        else:
            if self.quantity == 1:
                return self.name
            else:
                return "{0} {1}".format(self.quantity, self.name)


class AbstractInvoice(Model):
    lines = []

    def update(self, fields):
        if 'lines' in fields:
            self.lines = []
            for line in fields.pop('lines'):
                if not isinstance(line, InvoiceLine):
                    line = InvoiceLine(**line)
                self.lines.append(line)
        super(AbstractInvoice, self).update(fields)

    def is_field_writable(self, field, value):
        if field == 'lines' and self.id:
            #HACK API is not able to modify existing invoice/generators lines (it currently performs only append)
            return False
        if field.startswith('your_'):
            return False
        return super(AbstractInvoice, self).is_field_writable(field, value)


class Invoice(AbstractInvoice):
    """See https://github.com/fakturoid/api/blob/master/sections/invoice.md for complete field reference."""
    number = None

    class Meta:
        readonly = ['id', 'html_url', 'url', 'updated_at', 'proforma', 'due_on', 'subtotal', 'total'
            'native_subtotal', 'native_total', 'remaining_amount', 'remaining_native_amount',
            'reminder_sent_at', 'sent_at', 'subject_url']
        decimal = ['exchange_rate', 'subtotal', 'total',
            'native_subtotal', 'native_total', 'remaining_amount', 'remaining_native_amount']

    def __unicode__(self):
        return self.number


class Generator(AbstractInvoice):
    """See https://github.com/fakturoid/api/blob/master/sections/generator.md for complete field reference."""
    name = None

    class Meta:
        readonly = ['id', 'html_url', 'url', 'updated_at', 'subtotal', 'total'
            'native_subtotal', 'native_total', 'subject_url']
        decimal = ['exchange_rate', 'subtotal', 'total', 'native_subtotal', 'native_total']

    def __unicode__(self):
        return self.name
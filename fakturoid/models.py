from __future__ import unicode_literals

from decimal import Decimal
from dateutil.parser import parse

from fakturoid import six

__all__ = ['Account', 'Subject', 'InvoiceLine', 'Invoice', 'Generator', 'Message']


class Model(six.UnicodeMixin):
    """Base class for all Fakturoid model objects"""
    id = None

    def __init__(self, **fields):
        self.update(fields)

    def __repr__(self):
        return "<{0}:{1}>".format(self.__class__.__name__, self.id)

    def update(self, fields):
        for field, value in fields.items():
            if value and isinstance(value, six.string_types):
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

    def serialize_field_value(self, field, value):
        if isinstance(value, Model):
            return value.get_fields()
        if isinstance(value, list):
            nv = []
            for i, item in enumerate(value):
                nv.append(self.serialize_field_value('{0}.{1}'.format(field, i), item))
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
                data[field] = self.serialize_field_value(field, value)
        return data


class Account(Model):
    """See http://docs.fakturoid.apiary.io/ for complete field reference."""
    name = None

    class Meta:
        decimal = []

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return "<{0}:{1}>".format(self.__class__.__name__, self.name)


class Subject(Model):
    """See http://docs.fakturoid.apiary.io/ for complete field reference."""
    name = None

    class Meta:
        readonly = ['id', 'avatar_url', 'html_url', 'url', 'updated_at']
        decimal = []

    def __unicode__(self):
        return self.name


class InvoiceLine(Model):
    quantity = None

    class Meta:
        readonly = []  # no id here, to correct update
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
    _loaded_lines = []  # keep loaded data to be able delete removed lines

    def update(self, fields):
        if 'lines' in fields:
            self.lines = []
            self._loaded_lines = []
            for line in fields.pop('lines'):
                if not isinstance(line, InvoiceLine):
                    if 'id' in line:
                        self._loaded_lines.append(line)
                    line = InvoiceLine(**line)
                self.lines.append(line)
        super(AbstractInvoice, self).update(fields)

    def serialize_field_value(self, field, value):
        result = super(AbstractInvoice, self).serialize_field_value(field, value)
        if field == 'lines':
            ids = map(lambda l: l.get('id'), result)
            for remote in self._loaded_lines:
                if remote['id'] not in ids:
                    remote['_destroy'] = True
                    result.append(remote)
        return result

    def is_field_writable(self, field, value):
        if field.startswith('your_') or field.startswith('client_'):
            return False
        return super(AbstractInvoice, self).is_field_writable(field, value)


class Invoice(AbstractInvoice):
    """See http://docs.fakturoid.apiary.io/ for complete field reference."""
    number = None

    class Meta:
        readonly = [
            'id', 'token', 'status', 'due_on',
            'sent_at', 'paid_at', 'reminder_sent_at', 'accepted_at', 'canceled_at',
            'subtotal', 'native_subtotal', 'total', 'native_total',
            'remaining_amount', 'remaining_native_amount',
            'html_url', 'public_html_url', 'url', 'updated_at',
            'subject_url'
        ]
        decimal = [
            'exchange_rate', 'subtotal', 'total',
            'native_subtotal', 'native_total', 'remaining_amount',
            'remaining_native_amount'
        ]

    def __unicode__(self):
        return self.number


class Generator(AbstractInvoice):
    """See http://docs.fakturoid.apiary.io/ for complete field reference."""
    name = None

    class Meta:
        readonly = [
            'id', 'subtotal', 'native_subtotal', 'total', 'native_total',
            'html_url', 'url', 'subject_url', 'updated_at'
        ]
        decimal = ['exchange_rate', 'subtotal', 'total', 'native_subtotal', 'native_total']

    def __unicode__(self):
        return self.name


class Message(Model):
    """See http://docs.fakturoid.apiary.io/#reference/messages for complete field reference."""
    subject = None

    class Meta:
        decimal = []

    def __unicode__(self):
        return self.subject

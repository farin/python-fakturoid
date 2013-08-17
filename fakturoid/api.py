import json
from datetime import date, datetime

import requests

from fakturoid.models import Account, Subject, Invoice, Generator
from fakturoid.paging import PagedResource

__all__ = ['Fakturoid']


class Fakturoid(object):
    subdomain = None
    api_key = None
    user_agent = 'python-fakturoid (https://github.com/farin/python-fakturoid)'

    _sections = None

    def __init__(self, subdomain=None, api_key=None, user_agent=None):
        self.subdomain = subdomain
        self.api_key = api_key
        self.user_agent = user_agent or self.user_agent

        self._sections = {
            Account: AccountApi(self),
            Subject: SubjectsApi(self),
            Invoice: InvoicesApi(self),
            Generator: GeneratorsApi(self),
        }

    def account(self):
        return self._sections[Account].load()

    def subject(self, id):
        return self._sections[Subject].load(id)

    def subjects(self, *args, **kwargs):
        return self._sections[Subject].find(*args, **kwargs)

    def invoice(self, id):
        return self._sections[Invoice].load(id)

    def invoices(self, *args, **kwargs):
        return self._sections[Invoice].find(*args, **kwargs)

    def generator(self, id):
        return self._sections[Generator].load(id)

    def generators(self, *args, **kwargs):
        return self._sections[Generator].find(*args, **kwargs)

    def save(self, obj):
        section = self._sections.get(type(obj))
        if not section or not hasattr(section, 'save'):
            raise TypeError('save is not supported for {0}'.format(type(obj).__name__))
        section.save(obj)

    def delete(self, obj):
        section = self._sections.get(type(obj))
        if not section or not hasattr(section, 'delete'):
            raise TypeError('delete is not supported for {0}'.format(type(obj).__name__))
        section.delete(obj)

    def _make_request(self, method, success_status, endpoint, **kwargs):
        url = "https://{0}.fakturoid.cz/api/v1/{1}.json".format(self.subdomain, endpoint)
        headers = {'User-Agent': self.user_agent}
        headers.update(kwargs.pop('headers', {}))
        r = getattr(requests, method)(url, auth=('', self.api_key), headers=headers, **kwargs)
        try:
            json_result = r.json()
        except:
            json_result = None

        if r.status_code == success_status:
            return json_result

        if json_result and "errors" in json_result:
            raise ValueError(json_result["errors"])

        r.raise_for_status()

    def _get(self, endpoint, params=None):
        return self._make_request('get', 200, endpoint, params=params)

    def _post(self, endpoint, data):
        return self._make_request('post', 201, endpoint, headers={'Content-Type': 'application/json'}, data=json.dumps(data))

    def _put(self, endpoint, data):
        return self._make_request('put', 200, endpoint,  headers={'Content-Type': 'application/json'}, data=json.dumps(data))

    def _delete(self, endpoint):
        return self._make_request('delete', 204, endpoint)


class Section(object):
    api = None

    def __init__(self, api):
        self.api = api

    def __str__(self):
        return str(self.get)

    def extract_id(self, model_type, value):
        if isinstance(value, int):
            return value
        if not isinstance(value, model_type):
            raise TypeError("int or {0} expected".format(model_type.__name__.lower()))
        if not getattr(value, 'id', None):
            raise ValueError("object wit unassigned id")
        return value.id

    def unpack(self, model_type, endpoint, **kwargs):
        result = self.api._get(endpoint, **kwargs)
        if isinstance(result, list):
            objects = []
            for fields in result:
                objects.append(model_type(**fields))
            return objects
        else:
            return model_type(**result)


class CrudSection(Section):
    model_type = None
    endpoint = None

    def load(self, id):
        if not isinstance(id, int):
            raise TypeError('id must be int')
        return self.unpack(self.model_type, '{0}/{1}'.format(self.endpoint, id))

    def find(self, params={}, endpoint=None):
        return self.unpack(self.model_type, endpoint or self.endpoint, params=params)

    def save(self, model):
        if model.id:
            result = self.api._put('{0}/{1}'.format(self.endpoint, model.id), model.get_fields())
        else:
            result = self.api._post(self.endpoint, model.get_fields())
        model.update(result)

    def delete(self, model):
        id = self.extract_id(self.model_type, model)
        self.api._delete('{0}/{1}'.format(self.endpoint, id))


class AccountApi(Section):
    """API resource https://github.com/fakturoid/api/blob/master/sections/account.md"""

    def load(self):
        return self.unpack(Account, 'account')


class SubjectsApi(CrudSection):
    """API resource https://github.com/fakturoid/api/blob/master/sections/subject.md"""
    model_type = Subject
    endpoint = 'subjects'

    def find(self, since=None):
        params = {}
        if since:
            if not isinstance(since, (datetime, date)):
                raise TypeError("'since' parameter must be date or datetime")
            params['since'] = since.isoformat()
        return super(SubjectsApi, self).find(params)


class InvoicesApi(CrudSection):
    """API https://github.com/fakturoid/api/blob/master/sections/invoice.md

    If number argument is givent returs single Invoice object (or None), otherwise iterable list of invoices are returned.
    """
    model_type = Invoice
    endpoint = 'invoices'

    STATUSES = ['open', 'sent', 'overdue', 'paid', 'cancelled']

    def find(self, proforma=None, subject_id=None, since=None, number=None, status=None):
        params = {}
        if subject_id:
            if not isinstance(subject_id, int):
                raise TypeError("'subject_id' parameter must be int")
            params['subject_id'] = subject_id
        if since:
            if not isinstance(since, (datetime, date)):
                raise TypeError("'since' parameter must be date or datetime")
            params['since'] = since.isoformat()
        if number:
            params['number'] = number
        if status:
            if status not in self.STATUSES:
                raise ValueError('invalid invoice status, expected one of {0}'.format(', '.join(self.STATUSES)))
            params['status'] = status

        if proforma is None:
            endpoint = self.endpoint
        elif proforma:
            endpoint = '{0}/proforma'.format(self.endpoint)
        else:
            endpoint = '{0}/regular'.format(self.endpoint)

        return InvoiceList(self, endpoint, params)


class InvoiceList(PagedResource):

    def __init__(self, section_api, endpoint, params=None):
        self.section_api = section_api
        self.endpoint = endpoint
        self.params = params or {}

    def load_page(self, n):
        params = {'page': n + 1}
        params.update(self.params)
        return list(self.section_api.unpack(Invoice, self.endpoint, params=params))


class GeneratorsApi(CrudSection):
    model_type = Generator
    endpoint = 'generators'

    def find(self, recurring=None, subject_id=None, since=None):
        params = {}
        if subject_id:
            if not isinstance(subject_id, int):
                raise TypeError("'subject_id' parameter must be int")
            params['subject_id'] = subject_id
        if since:
            if not isinstance(since, (datetime, date)):
                raise TypeError("'since' parameter must be date or datetime")
            params['since'] = since.isoformat()

        if recurring is None:
            endpoint = self.endpoint
        elif recurring:
            endpoint = '{0}/recurring'.format(self.endpoint)
        else:
            endpoint = '{0}/template'.format(self.endpoint)

        return super(GeneratorsApi, self).find(params, endpoint)

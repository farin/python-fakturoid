import re
import json
from datetime import date, datetime

import requests

from fakturoid.models import Model, Account, Subject, Invoice, Generator
from fakturoid.paging import ModelList

__all__ = ['Fakturoid']

link_header_pattern = re.compile('page=(\d+)>; rel="last"')


class Fakturoid(object):
    """Fakturoid API v2 - http://docs.fakturoid.apiary.io/"""
    slug = None
    api_key = None
    user_agent = 'python-fakturoid (https://github.com/farin/python-fakturoid)'

    _models_api = None

    def __init__(self, slug, email, api_key, user_agent=None):
        self.slug = slug
        self.api_key = api_key
        self.email = email
        self.user_agent = user_agent or self.user_agent

        self._models_api = {
            Account: AccountApi(self),
            Subject: SubjectsApi(self),
            Invoice: InvoicesApi(self),
            Generator: GeneratorsApi(self),
        }

    def account(self):
        return self._models_api[Account].load()

    def subject(self, id):
        return self._models_api[Subject].load(id)

    def subjects(self, *args, **kwargs):
        return self._models_api[Subject].find(*args, **kwargs)

    def invoice(self, id):
        return self._models_api[Invoice].load(id)

    def invoices(self, *args, **kwargs):
        return self._models_api[Invoice].find(*args, **kwargs)

    def generator(self, id):
        return self._models_api[Generator].load(id)

    def generators(self, *args, **kwargs):
        return self._models_api[Generator].find(*args, **kwargs)

    def save(self, obj):
        mapi = self._models_api.get(type(obj))
        if not mapi or not hasattr(mapi, 'save'):
            raise TypeError('save is not supported for {0}'.format(type(obj).__name__))
        mapi.save(obj)

    def delete(self, *args):
        """Call with model object or model type and id.

        s = fa.subject(1234)
        fa.delete(s)

        fa.delete(Subject, 1234)
        """
        if len(args) == 1:
            model_type, obj = type(args[0]), args[0]
        elif len(args) == 2:
            model_type, obj = args
        else:
            raise ValueError('invalid number of arguments. Use delete(model) or delete(model_type, id)')

        if not isinstance(model_type, type) or not issubclass(model_type, Model):
            raise TypeError('{0} is not Fakturoid model or type'.format(model_type))

        mapi = self._models_api.get(model_type)
        if not mapi or not hasattr(mapi, 'delete'):
            raise TypeError('delete is not supported for {0}'.format(model_type.__name__))
        mapi.delete(obj)

    def _extract_page_link(self, header):
        m = link_header_pattern.search(header)
        if m:
            return int(m.group(1))
        return None

    def _make_request(self, method, success_status, endpoint, **kwargs):
        url = "https://app.fakturoid.cz/api/v2/accounts/{0}/{1}.json".format(self.slug, endpoint)
        headers = {'User-Agent': self.user_agent}
        headers.update(kwargs.pop('headers', {}))
        r = getattr(requests, method)(url, auth=(self.email, self.api_key), headers=headers, **kwargs)
        try:
            json_result = r.json()
        except:
            json_result = None

        if r.status_code == success_status:
            response = {'json': json_result}
            if 'link' in r.headers:
                page_count = self._extract_page_link(r.headers['link'])
                if page_count:
                    response['page_count'] = page_count
            return response

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


class ModelApi(object):
    api = None
    model_type = None
    endpoint = None

    def __init__(self, api):
        self.api = api

    def extract_id(self, value):
        if isinstance(value, int):
            return value
        if not isinstance(value, self.model_type):
            raise TypeError("int or {0} expected".format(self.model_type.__name__.lower()))
        if not getattr(value, 'id', None):
            raise ValueError("object wit unassigned id")
        return value.id

    def unpack(self, response):
        raw = response['json']
        if isinstance(raw, list):
            objects = []
            for fields in raw:
                objects.append(self.model_type(**fields))
            return objects
        else:
            return self.model_type(**raw)


class CrudModelApi(ModelApi):
    def load(self, id):
        if not isinstance(id, int):
            raise TypeError('id must be int')
        response = self.api._get('{0}/{1}'.format(self.endpoint, id))
        return self.unpack(response)

    def find(self, params={}, endpoint=None):
        response = self.api._get(endpoint or self.endpoint, params=params)
        return self.unpack(response)

    def save(self, model):
        if model.id:
            result = self.api._put('{0}/{1}'.format(self.endpoint, model.id), model.get_fields())
        else:
            result = self.api._post(self.endpoint, model.get_fields())
        model.update(result['json'])

    def delete(self, model):
        id = self.extract_id(self.model_type, model)
        self.api._delete('{0}/{1}'.format(self.endpoint, id))


class AccountApi(ModelApi):
    model_type = Account
    endpoint = 'account'

    def load(self):
        response = self.api._get(self.endpoint)
        return self.unpack(response)


class SubjectsApi(CrudModelApi):
    model_type = Subject
    endpoint = 'subjects'

    def find(self, since=None):
        params = {}
        if since:
            if not isinstance(since, (datetime, date)):
                raise TypeError("'since' parameter must be date or datetime")
            params['since'] = since.isoformat()
        return super(SubjectsApi, self).find(params)


class InvoicesApi(CrudModelApi):
    """If number argument is givent returms single Invoice object (or None), otherwise iterable list of invoices are returned.
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

        return ModelList(Invoice, self, endpoint, params)


class GeneratorsApi(CrudModelApi):
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

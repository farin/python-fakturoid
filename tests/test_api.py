from __future__ import absolute_import

import unittest
import datetime
from mock import patch

from fakturoid import Fakturoid

from tests.mock import response, FakeResponse


class FakturoidTestCase(unittest.TestCase):

    def setUp(self):
        self.fa = Fakturoid('myslug', '9ACA7', 'Test App')


class AccountTestCase(FakturoidTestCase):

    @patch('requests.get', return_value=response('account.json'))
    def test_load(self, mock):
        account = self.fa.account()

        self.assertEquals('https://app.fakturoid.cz/api/v2/accounts/myslug/account.json', mock.call_args[0][0])
        self.assertEquals("Alexandr Hejsek", account.name)
        self.assertEquals("testdph@test.cz", account.email)


class SubjectTestCase(FakturoidTestCase):

    @patch('requests.get', return_value=response('subject_28.json'))
    def test_load(self, mock):
        subject = self.fa.subject(28)

        self.assertEquals('https://app.fakturoid.cz/api/v2/accounts/myslug/subjects/28.json', mock.call_args[0][0])
        self.assertEquals(28, subject.id)
        self.assertEquals('47123737', subject.registration_no)
        self.assertEquals('2012-06-02T09:34:47+02:00', subject.updated_at.isoformat())

    @patch('requests.get', return_value=response('subjects.json'))
    def test_find(self, mock):
        subjects = self.fa.subjects()

        self.assertEquals('https://app.fakturoid.cz/api/v2/accounts/myslug/subjects.json', mock.call_args[0][0])
        self.assertEquals(2, len(subjects))
        self.assertEquals('Apple Czech s.r.o.', subjects[0].name)


class InvoiceTestCase(FakturoidTestCase):

    @patch('requests.get', return_value=response('invoice_9.json'))
    def test_load(self, mock):
        invoice = self.fa.invoice(9)

        self.assertEquals('https://app.fakturoid.cz/api/v2/accounts/myslug/invoices/9.json', mock.call_args[0][0])
        self.assertEquals('2012-0004', invoice.number)

    @patch('requests.post', return_value=FakeResponse(''))
    def test_load(self, mock):
        invoice = self.fa.fire_invoice_event(9, 'pay')

        mock.assert_called_once_with('https://app.fakturoid.cz/api/v2/accounts/myslug/invoices/9/fire.json',
                                     auth=('9ACA7', 'Test App'),
                                     data='{}',
                                     headers={'User-Agent': 'python-fakturoid (https://github.com/farin/python-fakturoid)', 'Content-Type': 'application/json'},
                                     params={'event': 'pay'})


    @patch('requests.get', return_value=response('invoices.json'))
    def test_find(self, mock):
        invoice = self.fa.invoices()[:10]

        self.assertEquals('https://app.fakturoid.cz/api/v2/accounts/myslug/invoices.json', mock.call_args[0][0])
        #TODO paging test


class GeneratorTestCase(FakturoidTestCase):

    @patch('requests.get', return_value=response('generator_4.json'))
    def test_load(self, mock):
        g = self.fa.generator(4)

        self.assertEquals('https://app.fakturoid.cz/api/v2/accounts/myslug/generators/4.json', mock.call_args[0][0])
        self.assertEquals('Podpora', g.name)

    @patch('requests.get', return_value=response('generators.json'))
    def test_find(self, mock):
        generators = self.fa.generators()

        self.assertEquals('https://app.fakturoid.cz/api/v2/accounts/myslug/generators.json', mock.call_args[0][0])
        self.assertEquals(2, len(generators))


if __name__ == '__main__':
    unittest.main()

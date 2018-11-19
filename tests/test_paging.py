from __future__ import absolute_import

import unittest
from mock import patch

from fakturoid.paging import PagedResource


class PageResourceTestCase(unittest.TestCase):

    def setUp(self):
        self.pg = PagedResource()
        self.pg.page_size = 5
        self.pg.page_count = 3
        self.pg.pages.update({
            0: 'abcde',
            1: 'fghij',
            2: 'k'
        })

    def test_len(self):
        self.assertEqual(11, len(self.pg))

    def test_getitem(self):
        self.assertEqual('a', self.pg[0])
        self.assertEqual('k', self.pg[10])
        self.assertEqual('j', self.pg[-2])
        with self.assertRaises(IndexError):
            self.pg[11]
        with self.assertRaises(IndexError):
            self.pg[-100]

    def test_getitem_slice(self):
        self.assertEqual('abcdef', ''.join(self.pg[0:6]))
        self.assertEqual('abcdef', ''.join(self.pg[:6]))
        self.assertEqual('abcdefghijk', ''.join(self.pg[:]))
        self.assertEqual('efghijk', ''.join(self.pg[-7:]))
        self.assertEqual('ceg', ''.join(self.pg[2:8:2]))

    @patch.object(PagedResource, 'load_page', return_value=['x', 'y', 'z'])
    def test_loadpage(self, load_page):
        unloaded = PagedResource(page_size=3)
        unloaded.page_size = 5
        self.assertEqual('z', unloaded[2])
        load_page.assert_called_once_with(0)

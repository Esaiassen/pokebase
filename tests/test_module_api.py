# -*- coding: utf-8 -*-

import shelve
import unittest
from unittest.mock import patch

from hypothesis import given
from hypothesis.strategies import text, sampled_from, integers, none, assume, dictionaries
from requests.exceptions import HTTPError

from pokebase import api
from pokebase.common import ENDPOINTS, cache_uri_build
from pokebase import cache
from pokebase.cache import set_cache, save


class TestFunction__call_api(unittest.TestCase):

    # _call_api(endpoint, resource_id)

    def setUp(self):
        set_cache('testing')

    @given(endpoint=sampled_from(ENDPOINTS),
           resource_id=(integers(min_value=1)))
    @patch('pokebase.api.requests.get')
    def testExpectedParams(self, mock_get, endpoint, resource_id):

        mock_get.return_value.json.return_value = {'id': resource_id}

        self.assertEqual(api._call_api(endpoint, resource_id)['id'],
                         resource_id)
    
    @given(endpoint=text(),
           resource_id=(integers(min_value=1)))
    def testInvalidEndpoint(self, endpoint, resource_id):
        with self.assertRaises(ValueError):
            api._call_api(endpoint, resource_id)

    @given(endpoint=sampled_from(ENDPOINTS),
           resource_id=none())
    @patch('pokebase.api.requests.get')
    def testNoneID(self, mock_get, endpoint, resource_id):
        
        mock_get.return_value.json.return_value = {'count': 100, 'results': ['some', 'reults']}

        self.assertIsNotNone(api._call_api(endpoint, resource_id).get('count'))

    @given(endpoint=sampled_from(ENDPOINTS),
           resource_id=(integers(min_value=1)))
    @patch('pokebase.api.requests.get')
    def testError(self, mock_get, endpoint, resource_id):
        mock_get.return_value.raise_for_status.side_effect = HTTPError()

        with self.assertRaises(HTTPError):
            api._call_api(endpoint, resource_id)


class TestFunction_get_data(unittest.TestCase):

    # get_data(endpoint, resource_id)

    def setUp(self):
        set_cache('testing')

    @given(data=dictionaries(text(), text()),
           endpoint=sampled_from(ENDPOINTS),
           resource_id=integers(min_value=1))
    def testExpectedParamsGettingCached(self, data, endpoint, resource_id):
        assume(data != dict())
        # save some data to the cache
        save(data, endpoint, resource_id)
        self.assertEqual(data, api.get_data(endpoint, resource_id))

    @given(data=dictionaries(text(), text()),
           endpoint=sampled_from(ENDPOINTS),
           resource_id=integers(min_value=1))
    @patch('pokebase.api.requests.get')
    def testExpectedParamsGettingNoncached(self, mock_get, data, endpoint, resource_id):
        
        mock_get.return_value.json.return_value = data

        # assert that the data is not in the cache
        with shelve.open(cache.API_CACHE) as cache_file:
            key = cache_uri_build(endpoint, resource_id)
            if key in cache_file.keys():
                del cache_file[key]

        self.assertEqual(data, api.get_data(endpoint, resource_id))

    @given(endpoint=text(),
           resource_id=integers(min_value=1))
    def testBadParam_endpoint(self, endpoint, resource_id):
        with self.assertRaises(ValueError):
            api.get_data(endpoint, resource_id)

    @given(endpoint=sampled_from(ENDPOINTS),
           resource_id=text())
    def testBadParam_resource_id(self, endpoint, resource_id):
        with self.assertRaises(ValueError):
            api.get_data(endpoint, resource_id)

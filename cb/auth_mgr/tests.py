import time
from unittest import mock

from django.test import TestCase

from .authentication import authenticate


# This method will be used by the mock to replace requests.post
def mocked_requests_post(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data={}, status_code=5):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    for i in range(1, 20):
        if args[0] == f'http://sleep_{i}/':
            time.sleep(i)
            return MockResponse({'id': i, 'username': f'test_{i}'}, 200)

    return MockResponse({}, 200)


class RemoteAuthticationTestCase(TestCase):
    def setUp(self):
        pass

    # We patch 'requests.get' with our own method. The mock object is passed in to our test case method.
    @mock.patch('cb.auth_mgr.authentication.requests.post', side_effect=mocked_requests_post)
    def test_fetch(self, mock_get):
        settings = {
            'HOSTS_URL': (
                'http://sleep_1/',
                'http://sleep_2/',
                'http://sleep_15/',
            ),
            'TIMEOUT': 10  # in seconds
        }

        data = authenticate(auth_settings=settings)
        self.assertDictEqual(data, {'id': 1, 'username': 'test_1'})

        # It will return {} because of timeout
        settings = {
            'HOSTS_URL': (
                'http://sleep_15/',
            ),
            'TIMEOUT': 10  # in seconds
        }

        data = authenticate(auth_settings=settings)
        self.assertEqual(data, {})

        # return user 2
        settings = {
            'HOSTS_URL': (
                'http://sleep_2/',
                'http://sleep_5/',
                'http://sleep_15/',
            ),
            'TIMEOUT': 10  # in seconds
        }

        data = authenticate(auth_settings=settings)
        self.assertDictEqual(data, {'id': 2, 'username': 'test_2'})

        # return user 2
        settings = {
            'HOSTS_URL': (
                'http://sleep_2/',
                'http://sleep_x/',
            ),
            'TIMEOUT': 10  # in seconds
        }

        data = authenticate(auth_settings=settings)
        self.assertDictEqual(data, {'id': 2, 'username': 'test_2'})

        # no user return
        settings = {
            'HOSTS_URL': (
                'http://sleep_x/',
            ),
            'TIMEOUT': 10  # in seconds
        }

        data = authenticate(auth_settings=settings)
        self.assertEqual(data, {})

        # no user return
        settings = {
            'HOSTS_URL': (
            ),
            'TIMEOUT': 10  # in seconds
        }

        data = authenticate(auth_settings=settings)
        self.assertEqual(data, {})

from datetime import datetime, timedelta
import os
import sqlite3
import sys
import unittest
import xml.etree.ElementTree as ET


HOME = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

if HOME not in sys.path:
    sys.path.append(HOME)

import env

from cb.util.network import RequestEtag
from module import log

log.set_log_config(os.path.join(os.environ["CONF"], "log.backend.conf"))
# ensure the log filename no matter this program is executed by user or
# cb.process.launcher
script_name = os.path.splitext(os.path.basename(__file__))[0]
os.environ.setdefault('COLLECTIVE_NAME', script_name)


class RequestEtagTester(unittest.TestCase):
    def setUp(self):
        self.url = 'https://code.jquery.com/jquery-2.2.4.min.js'
        self.db_file = os.path.join(HOME, ".test_etag.db")
        if os.path.exists(self.db_file):
            os.remove(self.db_file)

    def get_etag(self, url):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.execute(
            "SELECT url, etag FROM etag WHERE url='{url}'".format(
                url=url
            )
        )

        records = cursor.fetchall()
        if len(records):
            return records[0][1]
        else:
            return None

    def test_no_db_file(self):
        kwargs = {
            'headers': {
                'Connection': 'keep-alive',
            },
            'params': {}
        }
        with RequestEtag(self.url, db_file=self.db_file, **kwargs) as response:
            self.assertEqual(response.status_code, 200)
            etag = response.headers.get("ETag")
        self.assertEqual(etag, self.get_etag(self.url))

    def test_update(self):
        with RequestEtag(self.url, db_file=self.db_file) as response:
            self.assertEqual(response.status_code, 200)

        with RequestEtag(self.url, db_file=self.db_file) as response:
            self.assertEqual(response.status_code, 304)

    def test_force_update(self):
        with RequestEtag(self.url, db_file=self.db_file) as response:
            self.assertEqual(response.status_code, 200)

        with RequestEtag(
                self.url, force_update=True, db_file=self.db_file) as response:
            self.assertEqual(response.status_code, 200)

    def test_404(self):
        with RequestEtag(self.url+".123", db_file=self.db_file) as response:
            self.assertEqual(response.status_code, 404)

    def test_params(self):
        # test with ncdr
        url = 'https://alerts.ncdr.nat.gov.tw/api/datastore'

        params = {
            'apikey': os.environ.get('NCDR_KEY'),
            'format': 'json',
        }
        with RequestEtag(url, db_file=self.db_file, params=params) as response:
            self.assertEqual(response.status_code, 200)
            result = response.json()['result']

        if len(result) == 0:
            return

        cap_id = result[0].get('capid')
        url = 'https://alerts.ncdr.nat.gov.tw/api/dump/datastore'
        params = {
            'apikey': os.environ.get('NCDR_KEY'),
            'format': 'xml',
            'capid': cap_id,
        }
        ns = {
            'cap': 'urn:oasis:names:tc:emergency:cap:1.2'
        }
        with RequestEtag(url, db_file=self.db_file, params=params) as response:
            self.assertEqual(response.status_code, 200)
            root = ET.fromstring(response.text)
            self.assertEqual(root.find('cap:identifier', ns).text, cap_id)

        with RequestEtag(url, db_file=self.db_file, params=params) as response:
            self.assertEqual(response.status_code, 200)
            root = ET.fromstring(response.text)
            self.assertEqual(root.find('cap:identifier', ns).text, cap_id)

    def test_exception(self):
        try:
            with RequestEtag(self.url, db_file=self.db_file) as response:
                self.assertEqual(response.status_code, 200)
                raise FileExistsError
        except:
            pass

        self.assertEqual(self.get_etag(self.url), None)


if __name__ == "__main__":
    unittest.main()

import os
import sys
import sqlite3

import requests

from module import log

PWD = os.path.dirname(os.path.abspath(__file__))


class RequestEtag:
    """
    request with etag
    """
    DB_FILE = os.path.join(PWD, ".etag.db")

    def __init__(self, url, force_update=False, db_file=None, **kwargs):
        self.url = url
        self.force_update = force_update
        if db_file is None:
            self.db_file = self.DB_FILE
        else:
            self.db_file = db_file
        self.kwargs = kwargs

        self.status_code = None
        self.db_etag = None
        try:
            self.conn = sqlite3.connect(self.db_file)
            self.cursor = self.conn.cursor()
            cursor = self.conn.execute(
                "SELECT url, etag FROM etag WHERE url='{url}'".format(
                    url=url
                )
            )
            records = cursor.fetchall()
            if len(records):
                self.db_etag = records[0][1]
        except sqlite3.OperationalError as e:
            log.warning("sqlite3 : ", e.args)
            self.create_table()

    def create_table(self):
        try:
            log.diag("creat table for etag")
            self.conn.execute(
                "CREATE TABLE IF NOT EXISTS etag("
                "  url TEXT PRIMARY KEY NOT NULL,"
                "  etag TEXT)"
            )
        except:
            log.exception()

    def __enter__(self):
        headers = self.kwargs.get('headers', {})
        if self.db_etag and not self.force_update:
            headers.update({'If-None-Match': self.db_etag})
            self.kwargs.update({'headers': headers})

        response = requests.get(self.url, **self.kwargs)
        self.response_etag = response.headers.get("ETag")
        self.status_code = response.status_code

        if self.response_etag is None:
            log.diag('no ETag for ', self.url)

        return response

    def __exit__(self, type, value, traceback):
        if type is None:
            # No exception
            if self.status_code == 200:
                if self.db_etag:
                    sql = (
                        "UPDATE etag set etag='{etag}' "
                        "WHERE url='{url}'"
                    ).format(url=self.url, etag=self.response_etag)
                else:
                    sql = (
                        "INSERT INTO etag(url, etag) "
                        "VALUES('{url}', '{etag}')"
                    ).format(url=self.url, etag=self.response_etag)
                try:
                    self.conn.execute(sql)
                    self.conn.commit()
                except sqlite3.OperationalError as e:
                    log.warning("sqlite3 : ", e.args)
                except:
                    log.exception()

            return

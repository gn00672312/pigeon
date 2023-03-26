import datetime
import unittest

from module.util.dateutil import DateFactory


class DateUtilTestCase(unittest.TestCase):
    def setUp(self):
        self.factory = DateFactory()

    def test_parse_dtime(self):
        dtime = '2021/01/02'

        dt, _ = self.factory.parse_dtime(dtime)

        self.assertEqual(datetime.datetime(2021, 1, 2), dt)

    def test_month_range(self):
        dt = DateFactory.now()

        month_start, month_end, _ = self.factory.month_range(dt)
        print(month_start, month_end)


if __name__ == '__main__':
    unittest.main()

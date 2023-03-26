import unittest

from module.util.geocoding import latlon2citytown


class GeoToolTestCase(unittest.TestCase):
    def test_get_town(self):
        lat = 25.020938053669536
        lng = 121.52772705070676

        expect_city = '台北市'
        expect_town = '中正區'
        target_city, target_town, target_area = latlon2citytown(lat, lng)

        self.assertEqual(expect_city, target_city)
        self.assertEqual(expect_town, target_town)
        self.assertEqual(expect_city+expect_town, target_area)

    def test_get_town_case2(self):
        lat = 23.02344795745138
        lng = 120.2200815291144

        expect_city = '台南市'
        expect_town = '永康區'
        target_city, target_town, target_area = latlon2citytown(lat, lng)

        self.assertEqual(expect_city, target_city)
        self.assertEqual(expect_town, target_town)
        self.assertEqual(expect_city + expect_town, target_area)


if __name__ == '__main__':
    unittest.main()

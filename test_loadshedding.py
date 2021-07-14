"""Unit Tests to validate the core logic of `loadshedding.py`
"""

import unittest
import datetime

import pandas as pd

from loadshedding import check_shedding


class TestCheckShedding(unittest.TestCase):
    def setUp(self):
        configuration_system = {
            'API_URL':
                'http://loadshedding.eskom.co.za/LoadShedding/GetStatus',
            'LOGSTAGE': 'stagelog.txt',
            'LOG': 'log.log',
            'MIN_OFFSET': 4,
            'MAX_OFFSET': 17,
            'NOTIFICATION_TIMEOUT': 0
        }
        configuration_user = {
            'AREA': '8B',
            'SCHEDULE_CSV': 'schedules/load_shedding_city_power.csv',
            'CMD': 'sudo /usr/sbin/s2disk',
            'GTK_NOTIFICATION': False
        }
        sched = pd.read_csv(configuration_user['SCHEDULE_CSV'], sep=';')

        self.configuration_system = configuration_system
        self.configuration_user = configuration_user
        self.schedule = sched

    def check_case(self, test):
        """Check a specific test case tuple for correctness

        Args:
            test (tuple): # Tuple of (AREA, TIMESTAMP (ISO FORMAT), STAGE,
                EXPECTED LOADSHEDDING STATUS)
        """
        self.configuration_user['AREA'] = test[0]
        datetime_test = datetime.datetime.fromisoformat(test[1])
        stage = test[2]
        expected_status = test[3]

        status = check_shedding(stage, self.schedule, self.configuration_user,
                                self.configuration_system, datetime_test)

        self.assertIs(status, expected_status, test)

    def test_stage_0_false(self):
        """Randomly test that stage 0 always returns false (not shedding)
        """
        import random

        # Modified from https://stackoverflow.com/a/553448
        def random_date(start, end):
            """
            This function will return a random datetime between two datetime
            objects.
            """
            delta = end - start
            int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
            random_second = random.randrange(int_delta)
            return start + datetime.timedelta(seconds=random_second)

        n_tests = 1024
        date_start = datetime.datetime(2020, 1, 1, 0, 0, 0)
        date_end = datetime.datetime(2050, 12, 31, 23, 59, 59)

        for i in range(n_tests):
            datetime_test = random_date(date_start, date_end)

            with self.subTest(i=i, date=str(datetime_test.date)):
                shedding = check_shedding(
                    0, self.schedule, self.configuration_user,
                    self.configuration_system, datetime_test)
                self.assertFalse(shedding)

    def test_select(self):
        """Tests a few handcrafted test cases, nothing too difficult
        """
        tests = (
            # On-Off at between stage 1 and 2
            ('8B', '2021-07-13 11:28:30', 1, False),
            ('8B', '2021-07-13 11:28:30', 2, True),
            # On-Off Before loadshedding starts (shedding starts at 06:00,
            # 2A does not appear earlier that day)
            ('2A', '2025-07-06 05:55:59', 1, False),
            ('2A', '2025-07-06 05:55:59', 4, False),
            ('2A', '2025-07-06 05:55:59', 5, True),
            ('2A', '2025-07-06 05:55:59', 8, True),
            ('2A', '2025-07-06 07:55:59', 8, True),
            # Off before loadshedding stops
            ('6A', '2024-01-27 22:00:30', 7, True),
            ('6A', '2024-01-27 22:15:30', 7, True),
            ('6A', '2024-01-27 22:20:30', 7, True),
            ('6A', '2024-01-27 22:21:30', 7, True),
            ('6A', '2024-01-27 22:22:30', 7, True),
            ('6A', '2024-01-27 22:23:30', 7, True),
            ('6A', '2024-01-27 22:24:30', 7, True),
            ('6A', '2024-01-27 22:25:30', 7, True),
            ('6A', '2024-01-27 22:26:30', 7, True),  # Might expect 'False'
            ('6A', '2024-01-27 22:26:59', 7, True),  # based on 4min Window
            ('6A', '2024-01-27 22:27:00', 7, False),
            ('6A', '2024-01-27 22:27:01', 7, False),
            ('6A', '2024-01-27 22:27:30', 7, False),
            ('6A', '2024-01-27 22:28:30', 7, False),
            ('6A', '2024-01-27 22:29:30', 7, False),
            ('6A', '2024-01-27 22:30:30', 7, False),
            ('6A', '2024-01-27 22:45:30', 7, False),
            # On before starts (shedding starts at 04:00 for this case)
            ('4A', '2027-12-08 03:30:14', 5, False),
            ('4A', '2027-12-08 03:40:14', 5, False),
            ('4A', '2027-12-08 03:41:14', 5, False),
            ('4A', '2027-12-08 03:42:14', 5, False),
            ('4A', '2027-12-08 03:43:14', 5, True),
            ('4A', '2027-12-08 03:44:14', 5, True),
            ('4A', '2027-12-08 03:45:14', 5, True),
            ('4A', '2027-12-08 03:55:14', 5, True),
            ('4A', '2027-12-08 04:00:00', 5, True),
            ('4A', '2027-12-08 04:05:14', 5, True),
        )

        for test in tests:
            self.check_case(test)

    def test_midnight_tomorrow(self):
        """Tests that shedding will be correctly inferred when loadshedding
        starts within a few minutes the next
        day
        """
        tests = (
            ('7A', '2021-07-01 23:35:30', 1, False),
            ('7A', '2021-07-01 23:50:36', 1, True),

            ('4B', '2021-07-13 23:35:30', 4, False),
            ('4B', '2021-07-13 23:58:30', 3, False),
            ('4B', '2021-07-13 23:58:30', 4, True),
        )

        for test in tests:
            self.check_case(test)

    def test_early_morning_yesterday(self):
        """Tests that shedding will be inferred if the schedules from the
        previous day is still active
        """
        tests = (
            ('6B', '2021-07-06 00:02:33', 1, True),
            ('6B', '2021-07-06 00:29:12', 1, False),
        )

        for test in tests:
            self.check_case(test)

    def test_midnight_month(self):
        """[summary]
        """
        tests = (
            # 30 November for shedding on 01 December
            ('1A', '2021-11-30 23:35:30', 5, False),
            ('1A', '2021-11-30 23:50:36', 5, True),

            # 28 Feb 2021 shedding for 01 March
            ('1B', '2021-02-28 23:35:30', 5, False),
            ('1B', '2021-02-28 23:50:36', 5, True),
        )

        for test in tests:
            self.check_case(test)


if __name__ == '__main__':
    unittest.main()

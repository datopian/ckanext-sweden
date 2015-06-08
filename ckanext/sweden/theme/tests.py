import datetime

from nose import tools as nosetools

try:
    import ckan.tests.helpers as helpers
except ImportError:
    # CKAN 2.3
    import ckan.new_tests.helpers as helpers

from ckanext.sweden.theme import helpers as swe_helpers


class TestWeeklyTotalsHelpers(helpers.FunctionalTestBase):

    l = [
        ('01', datetime.datetime(2015, 1, 1)),
        ('02', datetime.datetime(2015, 1, 4)),
        ('02', datetime.datetime(2015, 1, 21)),
        ('02', datetime.datetime(2015, 2, 9)),
        ('02', datetime.datetime(2015, 2, 11)),
        ('02', datetime.datetime(2015, 2, 11)),
        ('02', datetime.datetime(2015, 2, 14)),
    ]

    def test_weekly_totals_basic(self):
        '''
        A list of (datetime, id) tuples is correctly grouped into weekly
        batches with correct weekly totals.
        '''

        weekly_totals = swe_helpers._weekly_totals(self.l)

        nosetools.assert_equal(len(weekly_totals), 3)

        # 2 in w/c 29 dec 2014
        nosetools.assert_equal(weekly_totals[0][0],
                               datetime.date(2014, 12, 29))
        nosetools.assert_equal(weekly_totals[0][1], 2)

        # 1 in w/c 19 jan 2015
        nosetools.assert_equal(weekly_totals[1][0], datetime.date(2015, 1, 19))
        nosetools.assert_equal(weekly_totals[1][1], 1)

        # 4 in w/c 9 feb 2015
        nosetools.assert_equal(weekly_totals[2][0], datetime.date(2015, 2, 9))
        nosetools.assert_equal(weekly_totals[2][1], 4)

    def test_weekly_totals_cumulative(self):
        '''
        A list of (datetime, id) tuples is correctly grouped into weekly
        batches with correct cumulative weekly totals.
        '''
        weekly_totals = swe_helpers._weekly_totals(self.l, cumulative=True)

        nosetools.assert_equal(len(weekly_totals), 3)

        # 2 in w/c 29 dec 2014
        nosetools.assert_equal(weekly_totals[0][0],
                               datetime.date(2014, 12, 29))
        nosetools.assert_equal(weekly_totals[0][1], 2)

        # 1 in w/c 19 jan 2015
        nosetools.assert_equal(weekly_totals[1][0], datetime.date(2015, 1, 19))
        nosetools.assert_equal(weekly_totals[1][1], 3)

        # 4 in w/c 9 feb 2015
        nosetools.assert_equal(weekly_totals[2][0], datetime.date(2015, 2, 9))
        nosetools.assert_equal(weekly_totals[2][1], 7)

    def test_weekly_totals_timestamp(self):
        '''
        A list of (datetime, id) tuples is correctly grouped into weekly
        batches with correct translated datetime --> timestamp values.
        '''
        weekly_totals = swe_helpers._weekly_totals(self.l, timestamp=True)

        nosetools.assert_equal(len(weekly_totals), 3)

        # 2 in w/c 29 dec 2014
        nosetools.assert_equal(weekly_totals[0][0], 1419811200000)
        nosetools.assert_equal(weekly_totals[0][1], 2)

        # 1 in w/c 19 jan 2015
        nosetools.assert_equal(weekly_totals[1][0], 1421625600000)
        nosetools.assert_equal(weekly_totals[1][1], 3)

        # 4 in w/c 9 feb 2015
        nosetools.assert_equal(weekly_totals[2][0], 1423440000000)
        nosetools.assert_equal(weekly_totals[2][1], 7)

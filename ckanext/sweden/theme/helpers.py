from itertools import groupby
import datetime
import calendar
from sqlalchemy import Table, select, func

import ckan.model as model


def table(name):
    return Table(name, model.meta.metadata, autoload=True)


def get_new_datasets():
    '''
    Returns list of new pkgs and date when they were created,
    in format: [(id, datetime), ...]
    '''
    # Can't filter by time in select because 'min' function has to
    # be 'for all time' else you get first revision in the time period.
    package_revision = table('package_revision')
    revision = table('revision')
    s = select([package_revision.c.id, func.min(revision.c.timestamp)],
               from_obj=[package_revision.join(revision)]).\
        group_by(package_revision.c.id).\
        order_by(func.min(revision.c.timestamp))
    res = model.Session.execute(s).fetchall()  # [(id, datetime), ...]
    res_pickleable = []
    for pkg_id, created_datetime in res:
        res_pickleable.append((pkg_id, created_datetime))
    return res_pickleable


def get_package_revisions():
    '''
    Returns list of revisions and date of them, in format: [(id, date), ...]
    '''
    package_revision = table('package_revision')
    revision = table('revision')
    s = select([package_revision.c.id, revision.c.timestamp],
               from_obj=[package_revision.join(revision)]).\
        order_by(revision.c.timestamp)
    res = model.Session.execute(s).fetchall()  # [(id, datetime), ...]
    return res


def get_weekly_new_dataset_totals(timestamp=True):
    '''For each week, return the cumulative total of datasets.'''
    new_datasets = get_new_datasets()

    return _weekly_totals(new_datasets, timestamp=timestamp, cumulative=True)


def get_weekly_dataset_activity(timestamp=True):
    '''For each week, get the number datasets with some sort of activity.'''
    pkg_revisions = get_package_revisions()

    return _weekly_totals(pkg_revisions, timestamp=timestamp)


def get_weekly_dataset_activity_new(timestamp=True):
    '''For each week, get the number of new datasets.'''
    new_datasets = get_new_datasets()

    return _weekly_totals(new_datasets, timestamp=timestamp)


def _weekly_totals(id_date_list, cumulative=False, timestamp=False):
    '''
    For a list of (id, datetime) tuples, count the number of ids in each
    weekly batch (starting Monday). If cumulative is True, add previous counts
    to the total for each subsequent timestamp (e.g. to determine growth).

    Return a list of tuples in the form (date, id count). If `timestamp` is
    True, the date is a timestamp in milliseconds, otherwise date is a
    datetime.

    e.g.: [(1429488000000, 8), (1430092800000, 10), (1430697600000, 13)]
    '''

    # transform each datetime to its week start and convert to timestamp
    ids_week_start = [(pkg_id, _transform_to_week_start(date_time))
                      for pkg_id, date_time in id_date_list]

    if timestamp:
        ids_week_start = [(pkg_id, _datetime_to_timestamp(date_time))
                          for pkgs, date_time in ids_week_start]

    # group ids by new date (weekly batches)
    week_totals = []
    total_datasets = 0
    for week, group in groupby(ids_week_start, lambda x: x[1]):
        if cumulative:
            total_datasets += len(list(group))
        else:
            total_datasets = len(list(group))
        week_totals.append((week, total_datasets))

    return week_totals


def _datetime_to_timestamp(dt):
    '''Convert given datetime object to a timestamp in milliseconds'''
    return calendar.timegm(dt.timetuple()) * 1000


def _iso_year_start(iso_year):
    "The gregorian calendar date of the first day of the given ISO year"
    fourth_jan = datetime.date(iso_year, 1, 4)
    delta = datetime.timedelta(fourth_jan.isoweekday()-1)
    return fourth_jan - delta


def _transform_to_week_start(dt):
    '''Rewind the given datetime to the start of the week in which it
    resides (Monday).'''
    iso_year, iso_week, _ = dt.isocalendar()
    year_start = _iso_year_start(iso_year)
    return year_start + datetime.timedelta(weeks=iso_week-1)

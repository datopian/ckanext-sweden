import random
from itertools import groupby
import datetime
import calendar
from sqlalchemy import Table, select, func, and_

from ckan.plugins import toolkit
import ckan.model as model


def table(name):
    return Table(name, model.meta.metadata, autoload=True)


def get_new_datasets(pkg_ids=None):
    '''
    Return a list of new pkgs and date when they were created,
    in format: [(id, datetime), ...]

    If pkg_ids list is passed, limit query to just those packages.
    '''
    # Can't filter by time in select because 'min' function has to
    # be 'for all time' else you get first revision in the time period.
    package_revision = table('package_revision')
    revision = table('revision')
    s = select([package_revision.c.id, func.min(revision.c.timestamp)],
               from_obj=[package_revision.join(revision)])
    if pkg_ids:
        s = s.where(and_(package_revision.c.id.in_(pkg_ids),
                         package_revision.c.type == 'dataset'))
    else:
        s = s.where(package_revision.c.type == 'dataset')
    s = s.group_by(package_revision.c.id).\
        order_by(func.min(revision.c.timestamp))
    res = model.Session.execute(s).fetchall()  # [(id, datetime), ...]
    res_pickleable = []
    for pkg_id, created_datetime in res:
        res_pickleable.append((pkg_id, created_datetime))
    return res_pickleable


def get_package_revisions():
    '''
    Return a list of revision id and datetime, in format: [(id, date), ...]
    '''
    package_revision = table('package_revision')
    revision = table('revision')
    s = select([package_revision.c.id, revision.c.timestamp],
               from_obj=[package_revision.join(revision)]).\
        order_by(revision.c.timestamp)
    s = s.where(package_revision.c.type == 'dataset')
    res = model.Session.execute(s).fetchall()  # [(id, datetime), ...]
    return res


def get_weekly_new_dataset_totals(timestamp=True, zero_week=True):
    '''For each week, return the cumulative total number of datasets.'''
    new_datasets = get_new_datasets()

    return _weekly_totals(new_datasets, timestamp=timestamp, cumulative=True,
                          zero_week=zero_week)


def get_weekly_dataset_activity(timestamp=True, zero_week=True):
    '''For each week, get the number datasets with some sort of activity.'''
    pkg_revisions = get_package_revisions()

    return _weekly_totals(pkg_revisions, timestamp=timestamp,
                          zero_week=zero_week)


def get_weekly_dataset_activity_new(timestamp=True, zero_week=True):
    '''For each week, get the number of new datasets.'''
    new_datasets = get_new_datasets()

    return _weekly_totals(new_datasets, timestamp=timestamp,
                          zero_week=zero_week)


def get_weekly_new_dataset_totals_for_eurovoc_label(eurovoc_label,
                                                    timestamp=True,
                                                    zero_week=True):
    '''
    For a given eurovoc category label, return the cumulative total number of
    weekly new datasets.
    '''
    # get package ids for packages with the relevant eurovoc category.
    pkgs = toolkit.get_action('package_search')(
        data_dict={'fq':
                   u'+eurovoc_category_label:"{0}"'.format(eurovoc_label)}
    )
    pkg_ids = [pkg['id'] for pkg in pkgs['results']]

    # get a list of (package_revision id, datetime) for the passed package ids
    new_datasets_for_pkg_ids = get_new_datasets(pkg_ids=pkg_ids)

    return _weekly_totals(new_datasets_for_pkg_ids, timestamp=timestamp,
                          cumulative=True,
                          zero_week=zero_week)


def get_random_active_eurovoc_label():
    '''
    Return a eurovoc category label randomly picked from a list of eurovoc
    categories (that have at least one dataset, otherwise the chart will have
    nothing to show).
    '''
    # get active eurovoc category labels from package search
    search_results = toolkit.get_action('package_search')(
        data_dict={'facet.field': ['eurovoc_category_label']}
    )
    facets = search_results.get('facets')
    facet_labels = [key for key in facets['eurovoc_category_label'].keys()]

    try:
        return random.choice(facet_labels)
    except IndexError:
        return None


def _weekly_totals(id_date_list, cumulative=False, timestamp=False,
                   zero_week=True):
    '''
    For a list of (id, datetime) tuples, count the number of ids in each
    weekly batch (starting Monday).

    If cumulative is True, add previous counts to the total for each
    subsequent timestamp (e.g. to determine growth).

    If zero_week is True, prepend a (timestamp, 0) pair to the start of the
    list, where the timestamp is a week before the earliest date.

    Return a list of tuples in the form (date, id count). If `timestamp` is
    True, the date is a timestamp in milliseconds, otherwise date is a
    datetime.

    e.g.: [(1429488000000, 8), (1430092800000, 10), (1430697600000, 13)]
    '''

    if zero_week:
        first_date = id_date_list[0][1]
        previous_week = first_date - datetime.timedelta(weeks=1)
        previous_week_start = _transform_to_week_start(previous_week)
        if timestamp:
            previous_week_start = _datetime_to_timestamp(previous_week_start)

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

    if zero_week:
        week_totals.insert(0, (previous_week_start, 0))

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

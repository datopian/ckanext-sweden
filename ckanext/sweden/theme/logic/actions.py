import ckan.plugins.toolkit as toolkit

from ckanext.sweden.theme import helpers


@toolkit.side_effect_free
def total_datasets_by_week(context, data_dict):
    '''
    Return a list of [datetime, count] pairs where the datetime is the start
    of a week (Monday), and the count is the total number of datasets in that
    week. `datetime` is a timestamp in millisecs.
    '''
    toolkit.check_access('sweden_stats_show', context, data_dict)

    return helpers.get_weekly_new_dataset_totals(zero_week=False)


@toolkit.side_effect_free
def weekly_dataset_activity(context, data_dict):
    '''
    Return a list of [datetime, count] pairs where the datetime is the start
    of a week (Monday), and the count is the number of updated datasets in
    that week. `datetime` is a timestamp in millisecs.
    '''
    toolkit.check_access('sweden_stats_show', context, data_dict)

    return helpers.get_weekly_dataset_activity(zero_week=False)


@toolkit.side_effect_free
def weekly_dataset_activity_new(context, data_dict):
    '''
    Return a list of [datetime, count] pairs where the datetime is the start
    of a week (Monday), and the count is the number of new datasets added in
    that week. `datetime` is a timestamp in millisecs.
    '''
    toolkit.check_access('sweden_stats_show', context, data_dict)

    return helpers.get_weekly_dataset_activity_new(zero_week=False)

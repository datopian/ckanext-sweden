import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit


def blog_admin(context, data_dict=None):
    # Get the user name of the logged-in user.
    user_name = context.get('user')

    # Get a list of the members of the 'blogadmins' group.
    try:
        members = toolkit.get_action('member_list')(
            data_dict={'id': 'blogadmins', 'object_type': 'user'})
    except toolkit.ObjectNotFound:
        # The blogadmins group doesn't exist.
        return {'success': False,
                'msg': "The blogadmins groups doesn't exist, so only sysadmins "
                       "are authorized to administrate the blog."}

    # 'members' is a list of (user_id, object_type, capacity) tuples, we're
    # only interested in the user_ids.
    member_ids = [member_tuple[0] for member_tuple in members]

    # We have the logged-in user's user name, get their user id.
    convert_user_name_or_id_to_id = toolkit.get_converter(
        'convert_user_name_or_id_to_id')
    try:
        user_id = convert_user_name_or_id_to_id(user_name, context)
    except toolkit.Invalid:
        # The user doesn't exist (e.g. they're not logged-in).
        return {'success': False,
                'msg': 'You must be logged-in as a member of the blogadmins '
                       'group to administrate the blog.'}

    # Finally, we can test whether the user is a member of the blogadmins group.
    if username and user_id in member_ids:
        return {'success': True}
    else:
        return {'success': False,
                'msg': 'Only blogadmins are allowed to administrate the blog'}

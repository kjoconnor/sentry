"""
sentry.web.frontend.explore
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Contains views for the "Explore" section of Sentry.

:copyright: (c) 2010-2013 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import division

from sentyr.models import FilterKey, FilterValue, Group
from sentry.web.decorators import has_access
from sentry.web.helpers import render_to_response


@has_access
def tag_list(request, team, project):
    tag_name_qs = FilterKey.objects.filter(
        project=project).values_list('key', flat=True)

    tag_value_qs = FilterValue.objects.filter(
        project=project).order_by('-times_seen')

    # O(N) db access
    tag_list = []
    for tag_name in tag_name_qs:
        tag_list.append((tag_name, [
            (value, times_seen)
            for (value, times_seen)
            in tag_value_qs.filter(key=tag_name)[:5]
        ]))

    return render_to_response('sentry/explore/tag_list.html', {
        'SECTION': 'explore',
        'tag_list': tag_list,
    }, request)


@has_access
def tag_value_list(request, team, project, key):
    tag_values_qs = FilterValue.objects.filter(
        project=project).order_by('-times_seen')

    return render_to_response('sentry/explore/tag_value_list.html', {
        'title': key.replace('_', ' ').title(),
        'tag_name': key,
        'tag_values': tag_values_qs,
        'SECTION': 'explore',
    }, request)


@has_access
def tag_details(request, team, project, key, value):
    tag = FilterValue.objects.get(
        project=project, key=key, value=value)

    event_list = Group.objects.filter(
        grouptag__key=key,
        grouptag__value=value,
    ).order_by('-score')

    return render_to_response('sentry/explore/tag_value_details.html', {
        'team': team,
        'tag': tag,
        'event_list': event_list,
        'SECTION': 'users',
    }, request)

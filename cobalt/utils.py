from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def cobalt_paginator(request, events_list, items_per_page=30):
    """ common pagination function

    Args:
        request(HTTPRequest): standard request object
        events_list(list): list of things to paginate
        items_per_page(int): number of items on a page

    Returns: list
    """

    page = request.GET.get("page", 1)

    paginator = Paginator(events_list, items_per_page)
    try:
        events = paginator.page(page)
    except PageNotAnInteger:
        events = paginator.page(1)
    except EmptyPage:
        events = paginator.page(paginator.num_pages)

    return events

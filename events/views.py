from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Congress
from .forms import CongressForm
from rbac.core import rbac_user_allowed_for_model, rbac_user_has_role
from rbac.views import rbac_forbidden
from django.contrib import messages


@login_required()
def home(request):
    congresses = Congress.objects.all()
    return render(request, "events/home.html", {"congresses": congresses})


@login_required()
def view_congress(request, congress_id):
    """ basic view of an event.

    Args:
        request(HTTPRequest): standard user request
        congress_id(int): congress to view

    Returns:
        page(HTTPResponse): page with details about the event
    """

    congress = get_object_or_404(Congress, pk=congress_id)

    return render(request, "events/congress.html", {"congress": congress})


@login_required()
def preview_congress(request, congress_id):
    """ basic preview of an event. Doesn't use base.html

    Args:
        request(HTTPRequest): standard user request
        congress_id(int): congress to view

    Returns:
        page(HTTPResponse): page with details about the event
    """

    congress = get_object_or_404(Congress, pk=congress_id)

    return render(
        request, "events/congress.html", {"congress": congress, "preview": True}
    )


@login_required()
def create_congress(request):
    """ create a new congress

    Args:
        request(HTTPRequest): standard user request

    Returns:
        page(HTTPResponse): page to create congress
    """
    # get orgs that this user can manage congresses for
    valid_orgs = rbac_user_allowed_for_model(
        user=request.user, app="events", model="org", action="manage"
    )

    if request.method == "POST":
        form = CongressForm(request.POST, valid_orgs=valid_orgs)
        if form.is_valid():
            role = "events.org.%s.manage" % form.cleaned_data["org"].id
            if not rbac_user_has_role(request.user, role):
                return rbac_forbidden(request, role)

            congress = form.save(commit=False)
            congress.author = request.user
            congress.save()

            messages.success(
                request, "Congress created", extra_tags="cobalt-message-success"
            )
            return redirect("events:edit_congress", congress_id=congress.id)
    else:
        form = CongressForm(valid_orgs=valid_orgs)

    return render(
        request,
        "events/edit_congress.html",
        {"form": form, "title": "Create New Congress"},
    )


@login_required()
def edit_congress(request, congress_id):
    """ edit a new congress

    Args:
        request(HTTPRequest): standard user request
        congress_id(int): congress to view

    Returns:
        page(HTTPResponse): page to create congress
    """

    # get orgs that this user can manage congresses for
    valid_orgs = rbac_user_allowed_for_model(
        user=request.user, app="events", model="org", action="manage"
    )

    congress = get_object_or_404(Congress, pk=congress_id)
    print(congress.venue_location)

    role = "events.org.%s.manage" % congress.org.id
    if not rbac_user_has_role(request.user, role):
        return rbac_forbidden(request, role)

    if request.method == "POST":

        # we only process save or publish through here

        form = CongressForm(request.POST, instance=congress, valid_orgs=valid_orgs)
        if form.is_valid():

            print(form.cleaned_data["venue_location"])

            role = "events.org.%s.manage" % form.cleaned_data["org"].id
            if not rbac_user_has_role(request.user, role):
                return rbac_forbidden(request, role)

            congress = form.save(commit=False)
            congress.last_updated_by = request.user
            congress.last_updated = timezone.localtime()

            if "Publish" in request.POST:
                congress.status = "Published"
                messages.success(
                    request, "Congress published", extra_tags="cobalt-message-success",
                )

            congress.save()
            messages.success(
                request, "Congress saved", extra_tags="cobalt-message-success"
            )
        else:
            messages.warning(
                request,
                "There are errors on this form",
                extra_tags="cobalt-message-warning",
            )

    else:
        form = CongressForm(instance=congress, valid_orgs=valid_orgs)

    return render(
        request,
        "events/edit_congress.html",
        {"form": form, "title": "Edit Congress", "congress": congress},
    )


@login_required()
def delete_congress(request, congress_id):
    """ delete a congress

    Args:
        request(HTTPRequest): standard user request
        congress_id(int): congress to delete

    Returns:
        page(HTTPResponse): redirects to events
    """

    congress = get_object_or_404(Congress, pk=congress_id)

    role = "events.org.%s.manage" % congress.org.id
    if not rbac_user_has_role(request.user, role):
        return rbac_forbidden(request, role)

    congress.delete()
    messages.success(request, "Congress deleted", extra_tags="cobalt-message-success")
    return redirect("events:events")

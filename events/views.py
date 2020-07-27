from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Congress
from .forms import CongressForm
from rbac.core import rbac_user_allowed_for_model, rbac_user_has_role
from rbac.views import rbac_forbidden
from django.contrib import messages


@login_required()
def home(request):
    return render(request, "events/home.html")


@login_required()
def view_congress(request, congress_id):
    """ basic view of an event.

    Args:
        request(HTTPRequest): standard user request
        event_id(int): event to view

    Returns:
        page(HTTPResponse): page with details about the event
    """

    congress = get_object_or_404(Congress, pk=congress_id)

    return render(request, "events/congress.html", {"congress": congress})


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
    else:
        form = CongressForm(valid_orgs=valid_orgs)

    return render(request, "events/edit_congress.html", {"form": form})

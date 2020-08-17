from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Congress, CongressMaster
from .forms import CongressForm, NewCongressForm
from rbac.core import (
    rbac_user_allowed_for_model,
    rbac_user_has_role,
    rbac_get_users_with_role,
)
from rbac.views import rbac_forbidden
from organisations.models import Organisation
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
    everything, valid_orgs = rbac_user_allowed_for_model(
        user=request.user, app="events", model="org", action="edit"
    )

    if everything:
        valid_orgs = Organisation.objects.all().values_list("pk")

    # get CongressMasters that this user can manage
    congress_masters = CongressMaster.objects.filter(org__in=valid_orgs).values_list(
        "pk"
    )
    congress_masters = [cm[0] for cm in congress_masters]  # strip tuple noise

    if request.method == "POST":
        form = CongressForm(
            request.POST, valid_orgs=valid_orgs, congress_masters=congress_masters
        )
        if form.is_valid():
            role = "events.org.%s.edit" % form.cleaned_data["org"].id
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
            messages.error(
                request,
                "There are errors on this form",
                extra_tags="cobalt-message-error",
            )
    else:
        form = CongressForm(valid_orgs=valid_orgs, congress_masters=congress_masters)

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
    everything, valid_orgs = rbac_user_allowed_for_model(
        user=request.user, app="events", model="org", action="edit"
    )

    if everything:
        valid_orgs = Organisation.objects.all().values_list("pk")

    # get CongressMasters that this user can manage
    congress_masters = CongressMaster.objects.filter(org__in=valid_orgs).values_list(
        "pk"
    )
    congress_masters = [cm[0] for cm in congress_masters]  # strip tuple noise

    congress = get_object_or_404(Congress, pk=congress_id)

    role = "events.org.%s.edit" % congress.org.id
    if not rbac_user_has_role(request.user, role):
        return rbac_forbidden(request, role)

    conveners = rbac_get_users_with_role("events.org.%s.edit" % congress.org.id)

    if request.method == "POST":

        # we only process save or publish through here

        form = CongressForm(
            request.POST,
            instance=congress,
            valid_orgs=valid_orgs,
            congress_masters=congress_masters,
        )
        if form.is_valid():

            print(form.cleaned_data["venue_location"])

            role = "events.org.%s.edit" % form.cleaned_data["org"].id
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
            messages.error(
                request,
                "There are errors on this form",
                extra_tags="cobalt-message-error",
            )

    else:
        form = CongressForm(
            instance=congress, valid_orgs=valid_orgs, congress_masters=congress_masters
        )

    return render(
        request,
        "events/edit_congress.html",
        {
            "form": form,
            "title": "Edit Congress",
            "congress": congress,
            "conveners": conveners,
        },
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

    role = "events.org.%s.edit" % congress.org.id
    if not rbac_user_has_role(request.user, role):
        return rbac_forbidden(request, role)

    congress.delete()
    messages.success(request, "Congress deleted", extra_tags="cobalt-message-success")
    return redirect("events:events")


@login_required()
def get_conveners_ajax(request, org_id):
    """ returns a list of conveners as html for an organisation """

    conveners = rbac_get_users_with_role("events.org.%s.edit" % org_id)

    ret = "<ul>"
    for con in conveners:
        ret += "<li>%s" % con
    ret += (
        "</ul><p>These can be changed from the <a href='/organisations/edit/%s' target='_blank'>Organisation Administration Page</p>"
        % org_id
    )

    data_dict = {"data": ret}
    return JsonResponse(data=data_dict, safe=False)


@login_required()
def get_congress_master_ajax(request, org_id):
    """ returns a list of congress_masters as html for an organisation """

    # org = get_object_or_404(Organisation, pk=org_id)
    #
    # qs = CongressMaster.objects.filter()
    #
    # ret = "<ul>"
    # for con in conveners:
    #     ret += "<li>%s" % con
    # ret += (
    #     "</ul><p>These can be changed from the <a href='/organisations/edit/%s' target='_blank'>Organisation Administration Page</p>"
    #     % org_id
    # )
    #
    # data_dict = {"data": ret}
    # return JsonResponse(data=data_dict, safe=False)


@login_required()
def create_congress_wizard(request, step=1, congress_id=None):
    """ create a new congress using wizard """

    # handle stepper on screen
    step_list = {}
    for i in range(1, 8):
        step_list[i] = "btn-default"
    step_list[step] = "btn-primary"

    # Step 1 - Create
    if step == 1:

        if request.method == "POST":
            if "scratch" in request.POST:
                congress = Congress()
                congress.save()
                return redirect(
                    "events:create_congress_wizard", step=2, congress_id=congress.id
                )
            if "copy" in request.POST:
                print("copy")
        else:
            # valid orgs
            everything, valid_orgs = rbac_user_allowed_for_model(
                user=request.user, app="events", model="org", action="edit"
            )
            if everything:
                valid_orgs = Organisation.objects.all().values_list("pk")

            form = NewCongressForm(valid_orgs=valid_orgs)
            return render(
                request,
                "events/congress_wizard_1.html",
                {"form": form, "step_list": step_list},
            )

    if step == 2:
        print("Step 2")

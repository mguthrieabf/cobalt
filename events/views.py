from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Congress, CongressMaster, Event, Session
from .forms import CongressForm, NewCongressForm, EventForm, SessionForm
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
    return render(request, "events/soon.html", {"congresses": congresses})
    #return render(request, "events/home.html", {"congresses": congresses})


@login_required()
def view_congress(request, congress_id, fullscreen=False):
    """ basic view of an event.

    Args:
        request(HTTPRequest): standard user request
        congress_id(int): congress to view
        fullscreen(boolean): if true shows just the page, not the standard surrounds

    Returns:
        page(HTTPResponse): page with details about the event
    """

    congress = get_object_or_404(Congress, pk=congress_id)

# We need to build a table for the program from events that has
# rowspans for the number of days. This is too complex for the
# template so we build it here.
#
# basic structure:
#
# <tr><td>Simple Pairs Event<td>Monday<td>12/09/2025 10am<td>Links</tr>
#
# <tr><td rowspan=2>Long Teams Event<td>Monday <td>13/09/2025 10am<td rowspan=2>Links</tr>
# <tr> !Nothing!                    <td>Tuesday<td>14/09/2025 10am !Nothing! </tr>

# get all events for this congress so we can build the program table
    events = congress.event_set.all()

# program_list will be passed to the template, each entry is a <tr> element
    program_list=[]

# every day of an event gets its own row so we use rowspan for event name and links
    for event in events:
        program = {}

# get all sessions for this event plus days and number of rows (# of days)
        sessions = event.session_set.all()
        days = sessions.distinct("session_date")
        rows = days.count()

# day td
        first_row_for_event = True
        for day in days:
            if first_row_for_event:
                program['event'] = f"<td rowspan='{rows}'><span class='title'>{event.event_name}</span></td>"
                program['links'] = f"<td rowspan='{rows}'>Links go here</td>"
                first_row_for_event = False
            program['day'] = "<td>%s</td>" % day.session_date.strftime("%A")

# handle multiple times on same day
# time needs a bit of manipulation as %-I not supported (maybe just Windows?)
            session_start_hour = day.session_start.strftime("%I")
            session_start_hour = "%d" % int(session_start_hour)
            session_minutes = day.session_start.strftime("%M")
            if session_minutes == "00":
                time_str = "%s - %s%s" % (day.session_date.strftime("%d-%m-%Y"), session_start_hour, day.session_start.strftime("%p"))
            else:
                time_str = "%s - %s:%s" % (day.session_date.strftime("%d-%m-%Y"), session_start_hour, day.session_start.strftime("%M%p"))

            times = Session.objects.filter(event__pk=day.event.id, session_date=day.session_date).order_by("session_start")

            print(day.id)
            print(day.event)
            print(times)

            for time in times[1:]:
                session_start_hour = time.session_start.strftime("%I")
                session_start_hour = "%d" % int(session_start_hour)
                session_minutes = time.session_start.strftime("%M")
                if session_minutes == "00":
                    time_str = "%s & %s%s" % (time_str, session_start_hour, time.session_start.strftime("%p"))
                else:
                    time_str = "%s & %s:%s" % (time_str, session_start_hour, time.session_start.strftime("%M%p"))

                #    time_str = "%s & %s:%s" % (time_str, session_start_hour, day.session_start.strftime("%M%p"))
            program['time'] = "<td>%s</td>" % time_str.lower() # AM -> pm
            program_list.append(program)
            program = {}

    return render(
        request,
        "events/congress.html",
        {"congress": congress, "fullscreen": fullscreen, "program_list": program_list},
    )


# @login_required()
# def create_congress(request):
#     """ create a new congress
#
#     Args:
#         request(HTTPRequest): standard user request
#
#     Returns:
#         page(HTTPResponse): page to create congress
#     """
#     # get orgs that this user can manage congresses for
#     everything, valid_orgs = rbac_user_allowed_for_model(
#         user=request.user, app="events", model="org", action="edit"
#     )
#
#     if everything:
#         valid_orgs = Organisation.objects.all().values_list("pk")
#
#     # get CongressMasters that this user can manage
#     congress_masters = CongressMaster.objects.filter(org__in=valid_orgs).values_list(
#         "pk"
#     )
#     congress_masters = [cm[0] for cm in congress_masters]  # strip tuple noise
#
#     if request.method == "POST":
#         form = CongressForm(
#             request.POST, valid_orgs=valid_orgs, congress_masters=congress_masters
#         )
#         if form.is_valid():
#             role = "events.org.%s.edit" % form.cleaned_data["org"].id
#             if not rbac_user_has_role(request.user, role):
#                 return rbac_forbidden(request, role)
#
#             congress = form.save(commit=False)
#             congress.author = request.user
#             congress.save()
#
#             messages.success(
#                 request, "Congress created", extra_tags="cobalt-message-success"
#             )
#             return redirect("events:edit_congress", congress_id=congress.id)
#         else:
#             messages.error(
#                 request,
#                 "There are errors on this form",
#                 extra_tags="cobalt-message-error",
#             )
#     else:
#         form = CongressForm(valid_orgs=valid_orgs, congress_masters=congress_masters)
#
#     return render(
#         request,
#         "events/edit_congress.html",
#         {"form": form, "title": "Create New Congress"},
#     )


# @login_required()
# def edit_congress(request, congress_id):
#     """ edit a new congress
#
#     Args:
#         request(HTTPRequest): standard user request
#         congress_id(int): congress to view
#
#     Returns:
#         page(HTTPResponse): page to create congress
#     """
#
#     # get orgs that this user can manage congresses for
#     everything, valid_orgs = rbac_user_allowed_for_model(
#         user=request.user, app="events", model="org", action="edit"
#     )
#
#     if everything:
#         valid_orgs = Organisation.objects.all().values_list("pk")
#
#     # get CongressMasters that this user can manage
#     congress_masters = CongressMaster.objects.filter(org__in=valid_orgs).values_list(
#         "pk"
#     )
#     congress_masters = [cm[0] for cm in congress_masters]  # strip tuple noise
#
#     congress = get_object_or_404(Congress, pk=congress_id)
#
#     role = "events.org.%s.edit" % congress.org.id
#     if not rbac_user_has_role(request.user, role):
#         return rbac_forbidden(request, role)
#
#     conveners = rbac_get_users_with_role("events.org.%s.edit" % congress.org.id)
#
#     if request.method == "POST":
#
#         # we only process save or publish through here
#
#         form = CongressForm(
#             request.POST,
#             instance=congress,
#             valid_orgs=valid_orgs,
#             congress_masters=congress_masters,
#         )
#         if form.is_valid():
#
#             print(form.cleaned_data["venue_location"])
#
#             role = "events.org.%s.edit" % form.cleaned_data["org"].id
#             if not rbac_user_has_role(request.user, role):
#                 return rbac_forbidden(request, role)
#
#             congress = form.save(commit=False)
#             congress.last_updated_by = request.user
#             congress.last_updated = timezone.localtime()
#
#             if "Publish" in request.POST:
#                 congress.status = "Published"
#                 messages.success(
#                     request, "Congress published", extra_tags="cobalt-message-success",
#                 )
#
#             congress.save()
#             messages.success(
#                 request, "Congress saved", extra_tags="cobalt-message-success"
#             )
#         else:
#             messages.error(
#                 request,
#                 "There are errors on this form",
#                 extra_tags="cobalt-message-error",
#             )
#
#     else:
#         form = CongressForm(
#             instance=congress, valid_orgs=valid_orgs, congress_masters=congress_masters
#         )
#
#     return render(
#         request,
#         "events/edit_congress.html",
#         {
#             "form": form,
#             "title": "Edit Congress",
#             "congress": congress,
#             "conveners": conveners,
#         },
#     )


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

    org = get_object_or_404(Organisation, pk=org_id)

    qs = CongressMaster.objects.filter(org=org).distinct("name")

    ret = "<option value=''>-----------"
    for cm in qs:
        ret += f"<option value='{cm.pk}'>{cm.name}</option>"

    data_dict = {"data": ret}
    return JsonResponse(data=data_dict, safe=False)


@login_required()
def get_congress_ajax(request, congress_id):
    """ returns a list of congresses as html for an congress_master """

    master = get_object_or_404(CongressMaster, pk=congress_id)

    qs = Congress.objects.filter(congress_master=master).distinct("name")

    ret = "<option value=''>-----------"
    for cm in qs:
        ret += f"<option value='{cm.id}'>{cm.name}</option>"

    data_dict = {"data": ret}
    return JsonResponse(data=data_dict, safe=False)


@login_required()
def create_congress_wizard(request, step=1, congress_id=None):
    """ create a new congress using a wizard format.

    There are a number of steps. Step 1 creates a congress either from
    scratch or by copying another one. All other steps edit data on the
    congress. The last steps allows the congress to be published.

    """

    # handle stepper on screen
    step_list = {}
    for i in range(1, 8):
        step_list[i] = "btn-default"
    step_list[step] = "btn-primary"

    # Step 1 - Create
    if step == 1:
        return create_congress_wizard_1(request, step_list)

    # all subsequent steps need the congress
    congress = get_object_or_404(Congress, pk=congress_id)

    # check access
    role = "events.org.%s.edit" % congress.congress_master.org.id
    if not rbac_user_has_role(request.user, role):
        return rbac_forbidden(request, role)

    if step == 2:
        return create_congress_wizard_2(request, step_list, congress)
    if step == 3:
        return create_congress_wizard_3(request, step_list, congress)
    if step == 4:
        return create_congress_wizard_4(request, step_list, congress)
    if step == 5:
        return create_congress_wizard_5(request, step_list, congress)
    if step == 6:
        return create_congress_wizard_6(request, step_list, congress)
    if step == 7:
        return create_congress_wizard_7(request, step_list, congress)


def create_congress_wizard_1(request, step_list):
    """ congress wizard step 1 - create """
    if request.method == "POST":

        form = NewCongressForm(request.POST)

        if form.is_valid():

            if "scratch" in request.POST:
                congress_master_id = form.cleaned_data["congress_master"]
                congress_master = get_object_or_404(
                    CongressMaster, pk=congress_master_id
                )

                # check access
                role = "events.org.%s.edit" % congress_master.org.id
                if not rbac_user_has_role(request.user, role):
                    return rbac_forbidden(request, role)

                congress = Congress()
                congress.congress_master = congress_master
                congress.save()
                messages.success(
                    request, "Congress Created", extra_tags="cobalt-message-success"
                )
                return redirect(
                    "events:create_congress_wizard", step=2, congress_id=congress.id
                )
            if "copy" in request.POST:
                congress_id = form.cleaned_data["congress"]
                congress = get_object_or_404(Congress, pk=congress_id)
                congress.pk = None
                congress.save()
                messages.success(
                    request, "Congress Copied", extra_tags="cobalt-message-success"
                )
                return redirect(
                    "events:create_congress_wizard", step=2, congress_id=congress.id
                )

        else:
            print(form.errors)
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


def create_congress_wizard_2(request, step_list, congress):
    """ wizard step 2 - general """

    if request.method == "POST":
        form = CongressForm(request.POST)
        if form.is_valid():
            congress.default_email = form.cleaned_data["default_email"]
            congress.year = form.cleaned_data["year"]
            congress.name = form.cleaned_data["name"]
            congress.date_string = form.cleaned_data["date_string"]
            congress.start_date = form.cleaned_data["start_date"]
            congress.end_date = form.cleaned_data["end_date"]
            congress.general_info = form.cleaned_data["general_info"]
            congress.links = form.cleaned_data["links"]
            congress.people = form.cleaned_data["people"]
            congress.people_array = form.cleaned_data["people_array"]
            congress.additional_info = form.cleaned_data["additional_info"]
            congress.save()
            return redirect(
                "events:create_congress_wizard", step=3, congress_id=congress.id
            )
        else:
            print(form.errors)
    else:
        # datepicker is very fussy about format
        initial = {}
        if congress.start_date:
            initial["start_date"] = congress.start_date.strftime("%d/%m/%Y")
        if congress.entry_close_date:
            initial["end_date"] = congress.end_date.strftime("%d/%m/%Y")
        form = CongressForm(instance=congress, initial=initial)

    form.fields["default_email"].required = True
    form.fields["year"].required = True
    form.fields["name"].required = True
    form.fields["start_date"].required = True
    form.fields["end_date"].required = True
    form.fields["date_string"].required = True
    form.fields["general_info"].required = True
    form.fields["links"].required = True
    form.fields["people"].required = True
    form.fields["people_array"].required = True

    return render(
        request,
        "events/congress_wizard_2.html",
        {"form": form, "step_list": step_list, "congress": congress},
    )


def create_congress_wizard_3(request, step_list, congress):
    """ wizard step 3 - venue """

    if request.method == "POST":
        form = CongressForm(request.POST)
        if form.is_valid():
            congress.venue_name = form.cleaned_data["venue_name"]
            congress.venue_location = form.cleaned_data["venue_location"]
            congress.venue_transport = form.cleaned_data["venue_transport"]
            congress.venue_catering = form.cleaned_data["venue_catering"]
            congress.venue_additional_info = form.cleaned_data["venue_additional_info"]
            congress.venue_additional_info = form.cleaned_data["venue_additional_info"]
            congress.save()
            return redirect(
                "events:create_congress_wizard", step=4, congress_id=congress.id
            )
        else:
            print(form.errors)
    else:
        form = CongressForm(instance=congress)

    form.fields["venue_name"].required = True
    form.fields["venue_location"].required = True
    form.fields["venue_transport"].required = True
    form.fields["venue_catering"].required = True

    return render(
        request,
        "events/congress_wizard_3.html",
        {"form": form, "step_list": step_list, "congress": congress},
    )


def create_congress_wizard_4(request, step_list, congress):
    """ wizard step 3 - sponsor """

    if request.method == "POST":
        form = CongressForm(request.POST)
        if form.is_valid():
            congress.sponsors = form.cleaned_data["sponsors"]
            congress.save()
            return redirect(
                "events:create_congress_wizard", step=5, congress_id=congress.id
            )

        else:
            print(form.errors)
    else:
        form = CongressForm(instance=congress)

    return render(
        request,
        "events/congress_wizard_4.html",
        {"form": form, "step_list": step_list, "congress": congress},
    )


def create_congress_wizard_5(request, step_list, congress):
    """ wizard step 5 - options """

    if request.method == "POST":
        form = CongressForm(request.POST)
        if form.is_valid():
            congress.payment_method_system_dollars = form.cleaned_data[
                "payment_method_system_dollars"
            ]
            congress.payment_method_bank_transfer = form.cleaned_data[
                "payment_method_bank_transfer"
            ]
            congress.payment_method_cash = form.cleaned_data["payment_method_cash"]
            congress.payment_method_cheques = form.cleaned_data[
                "payment_method_cheques"
            ]
            congress.entry_open_date = form.cleaned_data["entry_open_date"]
            congress.entry_close_date = form.cleaned_data["entry_close_date"]
            congress.allow_partnership_desk = form.cleaned_data[
                "allow_partnership_desk"
            ]
            congress.save()
            return redirect(
                "events:create_congress_wizard", step=6, congress_id=congress.id
            )
        else:
            print(form.errors)

    else:
        form = CongressForm(instance=congress)

    form.fields["payment_method_system_dollars"].required = True
    form.fields["payment_method_bank_transfer"].required = True
    form.fields["payment_method_cash"].required = True
    form.fields["payment_method_cheques"].required = True
    form.fields["entry_open_date"].required = True
    form.fields["entry_close_date"].required = True
    form.fields["allow_partnership_desk"].required = True

    return render(
        request,
        "events/congress_wizard_5.html",
        {"form": form, "step_list": step_list, "congress": congress},
    )


def create_congress_wizard_6(request, step_list, congress):
    """ wizard step 6 - events """

    if request.method == "POST":
        form = CongressForm(request.POST)
        if form.is_valid():
            congress.payment_method_system_dollars = form.cleaned_data[
                "payment_method_system_dollars"
            ]
            congress.payment_method_bank_transfer = form.cleaned_data[
                "payment_method_bank_transfer"
            ]
            congress.payment_method_cash = form.cleaned_data["payment_method_cash"]
            congress.payment_method_cheques = form.cleaned_data[
                "payment_method_cheques"
            ]
            congress.entry_open_date = form.cleaned_data["entry_open_date"]
            congress.entry_close_date = form.cleaned_data["entry_close_date"]
            congress.allow_partnership_desk = form.cleaned_data[
                "allow_partnership_desk"
            ]
            congress.save()
            return redirect(
                "events:create_congress_wizard", step=7, congress_id=congress.id
            )
        else:
            print(form.errors)

    else:
        form = CongressForm(instance=congress)

    form.fields["payment_method_system_dollars"].required = True
    form.fields["payment_method_bank_transfer"].required = True
    form.fields["payment_method_cash"].required = True
    form.fields["payment_method_cheques"].required = True
    form.fields["entry_open_date"].required = True
    form.fields["entry_close_date"].required = True
    form.fields["allow_partnership_desk"].required = True

    events = Event.objects.filter(congress=congress)

    return render(
        request,
        "events/congress_wizard_6.html",
        {"form": form, "step_list": step_list, "congress": congress, "events": events},
    )


def create_congress_wizard_7(request, step_list, congress):
    """ wizard step 7 - publish """

    if request.method == "POST":
        if "Publish" in request.POST:
            congress.status = "Published"
            congress.save()
            messages.success(
                request, "Congress published", extra_tags="cobalt-message-success",
            )
            return redirect(request, "events:view_congress", congress_id=congress.id)

        if "Delete" in request.POST:
            congress.delete()
            messages.success(
                request, "Congress deleted", extra_tags="cobalt-message-success",
            )
            return redirect(request, "events:events")

    url = "%s/%s/" % (reverse("events:create_congress_wizard"), congress.id)
    errors = []
    warnings = []

    if not congress.name:
        errors.append("<a href='%s%s'>%s</a>" % (url, 2, "Congress name is missing"))
    if not congress.default_email:
        errors.append("<a href='%s%s'>%s</a>" % (url, 2, "Default email is missing"))
    if not congress.additional_info:
        warnings.append("<a href='%s%s'>%s</a>" % (url, 2, "Additional is missing"))
    if not congress.start_date:
        errors.append("<a href='%s%s'>%s</a>" % (url, 2, "Start date is missing"))
    if not congress.end_date:
        errors.append("<a href='%s%s'>%s</a>" % (url, 2, "End date is missing"))
    if not congress.date_string:
        warnings.append("<a href='%s%s'>%s</a>" % (url, 2, "Date string is missing"))
    if not congress.year:
        warnings.append("<a href='%s%s'>%s</a>" % (url, 2, "Year is missing"))
    if not congress.general_info:
        errors.append("<a href='%s%s'>%s</a>" % (url, 2, "General is missing"))
    if not congress.people:
        errors.append("<a href='%s%s'>%s</a>" % (url, 2, "People is missing"))
    if not congress.venue_name:
        warnings.append("<a href='%s%s'>%s</a>" % (url, 3, "Venue name is missing"))
    if not congress.venue_location:
        warnings.append("<a href='%s%s'>%s</a>" % (url, 3, "Venue location is missing"))
    if not congress.venue_transport:
        warnings.append(
            "<a href='%s%s'>%s</a>" % (url, 3, "Venue transport is missing")
        )
    if not congress.venue_catering:
        warnings.append("<a href='%s%s'>%s</a>" % (url, 3, "Venue catering is missing"))
    if not congress.venue_additional_info:
        warnings.append(
            "<a href='%s%s'>%s</a>" % (url, 3, "Venue Additional info is missing")
        )
    if not congress.entry_open_date:
        warnings.append(
            "<a href='%s%s'>%s</a>" % (url, 2, "Entry open date is missing")
        )
    if not congress.entry_close_date:
        warnings.append(
            "<a href='%s%s'>%s</a>" % (url, 2, "Entry close date is missing")
        )

    events = Event.objects.filter(congress=congress).count()
    if events == 0:
        errors.append("<a href='%s%s'>%s</a>" % (url, 6, "This congress has no events defined"))

    return render(
        request,
        "events/congress_wizard_7.html",
        {
            "step_list": step_list,
            "congress": congress,
            "errors": errors,
            "warnings": warnings,
        },
    )


def _update_event(request, form, event, congress, msg):
    """ common shared function to update an event with form data """

    event.congress = congress
    event.event_name = form.cleaned_data["event_name"]
    event.description = form.cleaned_data["description"]
    event.max_entries = form.cleaned_data["max_entries"]
    event.event_type = form.cleaned_data["event_type"]
    event.entry_open_date = form.cleaned_data["entry_open_date"]
    event.entry_close_date = form.cleaned_data["entry_close_date"]
    event.player_format = form.cleaned_data["player_format"]
    event.save()
    messages.success(request, msg, extra_tags="cobalt-message-success")


@login_required
def create_event(request, congress_id):
    """ create an event within a congress """

    congress = get_object_or_404(Congress, pk=congress_id)

    # check access
    role = "events.org.%s.edit" % congress.congress_master.org.id
    if not rbac_user_has_role(request.user, role):
        return rbac_forbidden(request, role)

    if request.method == "POST":

        form = EventForm(request.POST)

        if form.is_valid():
            event = Event()
            _update_event(request, form, event, congress, "Event added")
            return redirect(
                "events:edit_event", event_id=event.id, congress_id=congress_id
            )
        else:
            print(form.errors)

    else:
        form = EventForm()

    return render(
        request, "events/create_event.html", {"form": form, "congress": congress},
    )


@login_required
def edit_event(request, congress_id, event_id):
    """ edit an event within a congress """

    congress = get_object_or_404(Congress, pk=congress_id)

    # check access
    role = "events.org.%s.edit" % congress.congress_master.org.id
    if not rbac_user_has_role(request.user, role):
        return rbac_forbidden(request, role)

    event = get_object_or_404(Event, pk=event_id)
    sessions = Session.objects.filter(event=event).order_by(
        "session_date", "session_start"
    )

    if request.method == "POST":

        form = EventForm(request.POST, instance=event)

        if form.is_valid():
            _update_event(request, form, event, congress, "Event updated")
        else:
            print(form.errors)

    else:
        # datepicker is very fussy about format
        initial = {}
        if event.entry_open_date:
            initial["entry_open_date"] = event.entry_open_date.strftime("%d/%m/%Y")
        if event.entry_close_date:
            initial["entry_close_date"] = event.entry_close_date.strftime("%d/%m/%Y")
        form = EventForm(instance=event, initial=initial)

    return render(
        request,
        "events/edit_event.html",
        {"form": form, "congress": congress, "event": event, "sessions": sessions},
    )


@login_required
def create_session(request, event_id):
    """ create session within an event  """

    event = get_object_or_404(Event, pk=event_id)

    # check access
    role = "events.org.%s.edit" % event.congress.congress_master.org.id
    if not rbac_user_has_role(request.user, role):
        return rbac_forbidden(request, role)

    if request.method == "POST":
        form = SessionForm(request.POST)
        print(request.POST.get("session_date"))
        print(request.POST.get("session_start"))
        if form.is_valid():
            session = Session()
            session.event = event
            session.session_date = form.cleaned_data["session_date"]
            session.session_start = form.cleaned_data["session_start"]
            session.session_end = form.cleaned_data["session_end"]
            session.save()

            messages.success(
                request, "Session Added", extra_tags="cobalt-message-success"
            )
            return redirect(
                "events:edit_event", event_id=event_id, congress_id=event.congress.id
            )
        else:
            print(form.errors)

    else:
        form = SessionForm()

    return render(
        request, "events/create_session.html", {"form": form, "event": event},
    )


@login_required
def edit_session(request, event_id, session_id):
    """ edit session within an event  """

    event = get_object_or_404(Event, pk=event_id)
    session = get_object_or_404(Session, pk=session_id)

    # check access
    role = "events.org.%s.edit" % event.congress.congress_master.org.id
    if not rbac_user_has_role(request.user, role):
        return rbac_forbidden(request, role)

    if request.method == "POST":
        form = SessionForm(request.POST, instance=session)
        if form.is_valid():
            session.session_date = form.cleaned_data["session_date"]
            session.session_start = form.cleaned_data["session_start"]
            session.session_end = form.cleaned_data["session_end"]
            session.save()

            messages.success(
                request, "Session Updated", extra_tags="cobalt-message-success"
            )
            return redirect(
                "events:edit_event", event_id=event_id, congress_id=event.congress.id
            )
        else:
            print(form.errors)

    else:
        # datepicker is very fussy about format
        initial = {}
        if session.session_date:
            initial["session_date"] = session.session_date.strftime("%d/%m/%Y")
        if session.session_start:
            initial["session_start"] = session.session_start.strftime("%I:%M %p")
        if session.session_end:
            initial["session_end"] = session.session_end.strftime("%I:%M %p")

        form = SessionForm(instance=event, initial=initial)

    return render(request, "events/edit_session.html", {"form": form, "event": event},)


@login_required()
def delete_event_ajax(request):
    """ Ajax call to delete an event from a congress """

    if request.method == "GET":
        event_id = request.GET["event_id"]

    event = get_object_or_404(Event, pk=event_id)

    # check access
    role = "events.org.%s.edit" % event.congress.congress_master.org.id
    if not rbac_user_has_role(request.user, role):
        return rbac_forbidden(request, role)

    event.delete()

    response_data = {}
    response_data["message"] = "Success"
    return JsonResponse({"data": response_data})


@login_required()
def delete_session_ajax(request):
    """ Ajax call to delete a session from a congress """

    if request.method == "GET":
        session_id = request.GET["session_id"]

    session = get_object_or_404(Session, pk=session_id)

    # check access
    role = "events.org.%s.edit" % session.event.congress.congress_master.org.id
    if not rbac_user_has_role(request.user, role):
        return rbac_forbidden(request, role)

    session.delete()

    response_data = {}
    response_data["message"] = "Success"
    return JsonResponse({"data": response_data})

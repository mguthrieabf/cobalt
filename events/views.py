import csv
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.forms import formset_factory
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.utils import timezone, dateformat
from django.db.models import Sum, Q
from notifications.views import contact_member
from logs.views import log_event
from .models import (
    Congress,
    Category,
    CongressMaster,
    Event,
    Session,
    EventEntry,
    EventEntryPlayer,
    PAYMENT_TYPES,
    EVENT_PLAYER_FORMAT_SIZE,
    BasketItem,
    PlayerBatchId,
    EventLog,
)
from accounts.models import User, TeamMate
from .forms import (
    CongressForm,
    NewCongressForm,
    EventForm,
    SessionForm,
    EventEntryPlayerForm,
    RefundForm,
)
from rbac.core import (
    rbac_user_allowed_for_model,
    rbac_get_users_with_role,
)
from rbac.views import rbac_user_role_or_error
from payments.core import payment_api, org_balance, update_account, update_organisation
from organisations.models import Organisation
from django.contrib import messages
import uuid
from cobalt.settings import (
    GLOBAL_ORG,
    GLOBAL_CURRENCY_NAME,
    TIME_ZONE,
    GLOBAL_CURRENCY_SYMBOL,
    COBALT_HOSTNAME,
    TBA_PLAYER,
)
from datetime import datetime
import itertools
from utils.utils import cobalt_paginator
from django.utils.timezone import make_aware, now, utc
import pytz
from decimal import Decimal

TZ = pytz.timezone(TIME_ZONE)


@login_required()
def home(request):
    """ main screen to show congresses """

    congresses = Congress.objects.order_by("start_date").filter(
        start_date__gte=datetime.now()
    )

    grouped_by_month = {}
    for congress in congresses:

        # Comment field
        if congress.entry_open_date > make_aware(datetime.now(), TZ):
            congress.msg = "Entries open on " + congress.entry_open_date.strftime(
                "%d %b %Y"
            )
        elif congress.entry_close_date > make_aware(datetime.now(), TZ):
            congress.msg = "Entries close on " + congress.entry_close_date.strftime(
                "%d %b %Y"
            )
        else:
            congress.msg = "Congress entries are closed"

        # check access
        congress.convener = congress.user_is_convener(request.user)

        # Group congresses by date
        month = congress.start_date.strftime("%B %Y")
        if month in grouped_by_month:
            grouped_by_month[month].append(congress)
        else:
            grouped_by_month[month] = [congress]

    # check if user has any admin rights to show link to create congress
    admin = rbac_user_allowed_for_model(request.user, "events", "org", "edit")[1]

    return render(
        request,
        "events/home.html",
        {"grouped_by_month": grouped_by_month, "admin": admin},
    )


@login_required()
def view_congress(request, congress_id, fullscreen=False):
    """ basic view of an event.

    Args:
        request(HTTPRequest): standard user request
        congress_id(int): congress to view
        fullscreen(boolean): if true shows just the page, not the standard surrounds
        Also accepts a GET parameter of msg to display for returning from event entry

    Returns:
        page(HTTPResponse): page with details about the event
    """

    congress = get_object_or_404(Congress, pk=congress_id)

    if request.method == "GET" and "msg" in request.GET:
        msg = request.GET["msg"]
    else:
        msg = None

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
    program_list = []

    # every day of an event gets its own row so we use rowspan for event name and links
    for event in events:
        program = {}

        # see if user has entered already
        program["entry"] = event.already_entered(request.user)

        # get all sessions for this event plus days and number of rows (# of days)
        sessions = event.session_set.all()
        days = sessions.distinct("session_date")
        rows = days.count()

        # day td
        first_row_for_event = True
        for day in days:
            if first_row_for_event:
                program[
                    "event"
                ] = f"<td rowspan='{rows}'><span class='title'>{event.event_name}</span></td>"
                if program["entry"]:
                    program[
                        "links"
                    ] = f"<td rowspan='{rows}'><a href='/events/congress/event/change-entry/{congress.id}/{event.id}'>Edit Entry</a><br><a href='/events/congress/event/view-event-entries/{congress.id}/{event.id}'>View Entries</a></td>"
                else:
                    program[
                        "links"
                    ] = f"<td rowspan='{rows}'><a href='/events/congress/event/enter/{congress.id}/{event.id}'>Enter</a><br><a href='/events/congress/event/view-event-entries/{congress.id}/{event.id}'>View Entries</a></td>"
                first_row_for_event = False
            program["day"] = "<td>%s</td>" % day.session_date.strftime("%A")

            # handle multiple times on same day
            # time needs a bit of manipulation as %-I not supported (maybe just Windows?)
            session_start_hour = day.session_start.strftime("%I")
            session_start_hour = "%d" % int(session_start_hour)
            session_minutes = day.session_start.strftime("%M")
            if session_minutes == "00":
                time_str = "%s - %s%s" % (
                    day.session_date.strftime("%d-%m-%Y"),
                    session_start_hour,
                    day.session_start.strftime("%p"),
                )
            else:
                time_str = "%s - %s:%s" % (
                    day.session_date.strftime("%d-%m-%Y"),
                    session_start_hour,
                    day.session_start.strftime("%M%p"),
                )

            times = Session.objects.filter(
                event__pk=day.event.id, session_date=day.session_date
            ).order_by("session_start")

            for time in times[1:]:
                session_start_hour = time.session_start.strftime("%I")
                session_start_hour = "%d" % int(session_start_hour)
                session_minutes = time.session_start.strftime("%M")
                if session_minutes == "00":
                    time_str = "%s & %s%s" % (
                        time_str,
                        session_start_hour,
                        time.session_start.strftime("%p"),
                    )
                else:
                    time_str = "%s & %s:%s" % (
                        time_str,
                        session_start_hour,
                        time.session_start.strftime("%M%p"),
                    )

            program["time"] = "<td>%s</td>" % time_str.lower()  # AM -> pm

            program_list.append(program)
            program = {}

    return render(
        request,
        "events/congress.html",
        {
            "congress": congress,
            "fullscreen": fullscreen,
            "program_list": program_list,
            "msg": msg,
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

    # check access
    role = "events.org.%s.edit" % congress.org.id
    rbac_user_role_or_error(request, role)

    congress.delete()
    messages.success(request, "Congress deleted", extra_tags="cobalt-message-success")
    return redirect("events:events")


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
    rbac_user_role_or_error(request, role)

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
                rbac_user_role_or_error(request, role)

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
                original_congress = get_object_or_404(Congress, pk=congress_id)
                congress.pk = None
                congress.save()

                # Also copy events and sessions
                print(original_congress.id)
                print(congress.id)
                events = Event.objects.filter(congress=original_congress)
                print(events)
                for event in events:
                    sessions = Session.objects.filter(event=event)
                    event.pk = None
                    event.congress = congress
                    event.save()
                    for session in sessions:
                        session.pk = None
                        session.event = event
                        session.save()

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
            congress.year = form.cleaned_data["year"]
            congress.name = form.cleaned_data["name"]
            congress.date_string = form.cleaned_data["date_string"]
            congress.start_date = form.cleaned_data["start_date"]
            congress.end_date = form.cleaned_data["end_date"]
            congress.general_info = form.cleaned_data["general_info"]
            congress.links = form.cleaned_data["links"]
            congress.people = form.cleaned_data["people"]
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

    form.fields["year"].required = True
    form.fields["name"].required = True
    form.fields["start_date"].required = True
    form.fields["end_date"].required = True
    form.fields["date_string"].required = True
    form.fields["general_info"].required = True
    form.fields["links"].required = True
    form.fields["people"].required = True

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
            congress.allow_early_payment_discount = form.cleaned_data[
                "allow_early_payment_discount"
            ]
            congress.early_payment_discount_date = form.cleaned_data[
                "early_payment_discount_date"
            ]
            congress.allow_youth_payment_discount = form.cleaned_data[
                "allow_youth_payment_discount"
            ]
            congress.youth_payment_discount_date = form.cleaned_data[
                "youth_payment_discount_date"
            ]
            congress.bank_transfer_details = form.cleaned_data["bank_transfer_details"]
            congress.cheque_details = form.cleaned_data["cheque_details"]
            congress.save()
            return redirect(
                "events:create_congress_wizard", step=6, congress_id=congress.id
            )
        else:
            print(form.errors)

    else:
        # sort out dates
        initial = {}
        if congress.entry_open_date:
            initial["entry_open_date"] = congress.entry_open_date.strftime("%d/%m/%Y")
        if congress.entry_close_date:
            initial["entry_close_date"] = congress.entry_close_date.strftime("%d/%m/%Y")
        if congress.early_payment_discount_date:
            initial[
                "early_payment_discount_date"
            ] = congress.early_payment_discount_date.strftime("%d/%m/%Y")
        if congress.youth_payment_discount_date:
            initial[
                "youth_payment_discount_date"
            ] = congress.youth_payment_discount_date.strftime("%d/%m/%Y")
        if congress.senior_date:
            initial["senior_date"] = congress.senior_date.strftime("%d/%m/%Y")
        form = CongressForm(instance=congress, initial=initial)

    form.fields["payment_method_system_dollars"].required = True
    form.fields["payment_method_bank_transfer"].required = True
    form.fields["payment_method_cash"].required = True
    form.fields["payment_method_cheques"].required = True
    form.fields["entry_open_date"].required = True
    form.fields["entry_close_date"].required = True
    form.fields["allow_partnership_desk"].required = True
    form.fields["allow_early_payment_discount"].required = True
    form.fields["bank_transfer_details"].required = True
    form.fields["cheque_details"].required = True

    return render(
        request,
        "events/congress_wizard_5.html",
        {"form": form, "step_list": step_list, "congress": congress},
    )


def create_congress_wizard_6(request, step_list, congress):
    """ wizard step 6 - events """

    events = Event.objects.filter(congress=congress)

    return render(
        request,
        "events/congress_wizard_6.html",
        {"step_list": step_list, "congress": congress, "events": events},
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
            "<a href='%s%s'>%s</a>"
            % (
                url,
                2,
                "Entry open date is missing. Entries will be accepted any time before closing date.",
            )
        )
    if not congress.entry_close_date:
        warnings.append(
            "<a href='%s%s'>%s</a>"
            % (
                url,
                2,
                "Entry close date is missing. Entries will be accepted even after the congress has started.",
            )
        )

    events = Event.objects.filter(congress=congress).count()
    if events == 0:
        errors.append(
            "<a href='%s%s'>%s</a>" % (url, 6, "This congress has no events defined")
        )

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
    event.entry_fee = form.cleaned_data["entry_fee"]
    event.entry_early_payment_discount = form.cleaned_data[
        "entry_early_payment_discount"
    ]
    event.entry_youth_payment_discount = form.cleaned_data[
        "entry_youth_payment_discount"
    ]
    event.save()
    messages.success(request, msg, extra_tags="cobalt-message-success")


@login_required
def create_event(request, congress_id):
    """ create an event within a congress """

    congress = get_object_or_404(Congress, pk=congress_id)

    # check access
    role = "events.org.%s.edit" % congress.congress_master.org.id
    rbac_user_role_or_error(request, role)

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
        request,
        "events/edit_event.html",
        {"form": form, "congress": congress, "page_type": "add"},
    )


@login_required
def edit_event(request, congress_id, event_id):
    """ edit an event within a congress """

    congress = get_object_or_404(Congress, pk=congress_id)

    # check access
    role = "events.org.%s.edit" % congress.congress_master.org.id
    rbac_user_role_or_error(request, role)

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

    categories = Category.objects.filter(event=event)

    return render(
        request,
        "events/edit_event.html",
        {
            "form": form,
            "congress": congress,
            "event": event,
            "sessions": sessions,
            "categories": categories,
            "page_type": "edit",
        },
    )


@login_required
def create_session(request, event_id):
    """ create session within an event  """

    event = get_object_or_404(Event, pk=event_id)

    # check access
    role = "events.org.%s.edit" % event.congress.congress_master.org.id
    rbac_user_role_or_error(request, role)

    if request.method == "POST":
        form = SessionForm(request.POST)
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
    rbac_user_role_or_error(request, role)

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


def enter_event_form(event, congress, request, existing_choices=None):
    """ build the form part of the enter_event view. Its not a Django form,
        we build our own as the validation won't work with a dynamic form
        and we are validating on the client side anyway.

        If this is called by the edit entry option then it will pass in
        existing_choices to pre-fill in the form. If this is a new entry
        then this will be None.

    """

    our_form = []

    # get payment types for this congress
    pay_types = []
    if congress.payment_method_system_dollars:
        pay_types.append(
            ("my-system-dollars", f"My {GLOBAL_ORG} {GLOBAL_CURRENCY_NAME}s")
        )
    if congress.payment_method_bank_transfer:
        pay_types.append(("bank-transfer", "Bank Transfer"))
    if congress.payment_method_cash:
        pay_types.append(("cash", "Cash on the day"))
    if congress.payment_method_cheques:
        pay_types.append(("cheque", "Cheque"))

    # Get team mates for this user - exclude anyone entered already
    all_team_mates = TeamMate.objects.filter(user=request.user)
    team_mates_list = all_team_mates.values_list("team_mate")
    print(team_mates_list)
    entered_team_mates = (
        EventEntryPlayer.objects.filter(event_entry__event=event)
        .filter(player__in=team_mates_list)
        .values_list("player")
    )
    print(entered_team_mates)
    team_mates = all_team_mates.exclude(team_mate__in=entered_team_mates)
    print(team_mates)

    name_list = [(0, "Search..."), (TBA_PLAYER, "TBA")]
    for team_mate in team_mates:
        item = (team_mate.team_mate.id, "%s" % team_mate.team_mate.full_name)
        name_list.append(item)

    # set values for player0 (the user)
    entry_fee, discount, reason, description = event.entry_fee_for(request.user)

    if existing_choices:
        payment_selected = existing_choices["player0"]["payment"]
        if (
            payment_selected == "my-system-dollars"
        ):  # only ABF dollars go in the you column
            entry_fee_you = entry_fee
            entry_fee_pending = ""
        else:
            entry_fee_you = ""
            entry_fee_pending = entry_fee
    else:
        payment_selected = pay_types[0]
        entry_fee_pending = ""
        entry_fee_you = entry_fee

    player0 = {
        "id": request.user.id,
        "payment_choices": pay_types.copy(),
        "payment_selected": payment_selected,
        "name": request.user.full_name,
        "entry_fee_you": "%s" % entry_fee_you,
        "entry_fee_pending": "%s" % entry_fee_pending,
    }

    # add another option for everyone except the current user
    if congress.payment_method_system_dollars:
        pay_types.append(("other-system-dollars", f"Ask them to pay"))

    # set values for other players
    team_size = EVENT_PLAYER_FORMAT_SIZE[event.player_format]
    min_entries = team_size
    if team_size == 6:
        min_entries = 4
    for ref in range(1, team_size):

        # if we are returning then set the passed values
        if existing_choices and "player%s" % ref in existing_choices.keys():
            payment_selected = existing_choices["player%s" % ref]["payment"]
            name_selected = existing_choices["player%s" % ref]["name"]
            entry_fee = existing_choices["player%s" % ref]["entry_fee"]
        else:
            payment_selected = pay_types[0]
            name_selected = None
            entry_fee = None

        # only ABF dollars go in the you column
        if payment_selected == "my-system-dollars":
            entry_fee_you = entry_fee
            entry_fee_pending = ""
        else:
            entry_fee_you = ""
            entry_fee_pending = entry_fee

        if payment_selected == "their-system-dollars":
            augment_payment_types = [
                ("their-system-dollars", f"Their {GLOBAL_ORG} {GLOBAL_CURRENCY_NAME}s")
            ]
        else:
            augment_payment_types = []

        # set value for whether this is a new entry or an edit
        if existing_choices:
            entry_status = "new"
        else:
            entry_status = "old"

        item = {
            "player_no": ref,
            "payment_choices": pay_types + augment_payment_types,
            "payment_selected": payment_selected,
            "name_choices": name_list,
            "name_selected": name_selected,
            "entry_fee_you": entry_fee_you,
            "entry_fee_pending": entry_fee_pending,
            "entry_status": entry_status,
        }

        our_form.append(item)

    # Start time of event
    sessions = Session.objects.filter(event=event).order_by(
        "session_date", "session_start"
    )
    event_start = sessions.first()

    # use reason etc from above to see if discounts apply
    alert_msg = None

    # don't alert about discounts if editing the entry
    if not existing_choices:
        if reason == "Early discount":
            date_field = event.congress.early_payment_discount_date.strftime("%d/%m/%Y")
            alert_msg = [
                "Early Entry Discount",
                "You qualify for an early discount if you enter now. You will save $%.2f on this event. Discount valid until %s."
                % (discount, date_field),
            ]

        if reason == "Youth discount":
            alert_msg = [
                "Youth Discount",
                "You qualify for a youth discount for this event. A saving of $%.2f."
                % discount,
            ]

    # categories
    categories = Category.objects.filter(event=event)

    return render(
        request,
        "events/enter_event.html",
        {
            "player0": player0,
            "our_form": our_form,
            "congress": congress,
            "event": event,
            "categories": categories,
            "sessions": sessions,
            "event_start": event_start,
            "alert_msg": alert_msg,
            "discount": discount,
            "description": description,
            "min_entries": min_entries,
        },
    )


@login_required()
def enter_event(request, congress_id, event_id):
    """ enter an event """

    # Load the event
    event = get_object_or_404(Event, pk=event_id)
    congress = get_object_or_404(Congress, pk=congress_id)

    # Check if already entered
    if event.already_entered(request.user):
        return redirect("events:edit_event_entry", event_id=event.id)

    # Check if entries are open
    if not event.is_open():
        return render(request, "events/event_closed.html", {"event": event})

    # Check if full
    if event.is_full():
        return render(request, "events/event_full.html", {"event": event})

    # check if POST.
    # Note: this works a bit differently to most forms in Cobalt.
    #       We build our own form and use client side code to validate and
    #       modify it.
    #       This will work unless someone has
    #       deliberately bypassed the client side validation in which case we
    #       don't mind failing with an error.

    if request.method == "POST":

        # create event_entry
        event_entry = EventEntry()
        event_entry.event = event
        event_entry.primary_entrant = request.user

        # see if we got a category
        category = request.POST.get("category", None)
        if category:
            event_entry.category = get_object_or_404(Category, pk=category)

        event_entry.save()

        # Log it
        EventLog(
            event=event,
            actor=event_entry.primary_entrant,
            action=f"Event entry {event_entry.id} created",
        ).save()

        # add to basket
        basket_item = BasketItem()
        basket_item.player = request.user
        basket_item.event_entry = event_entry
        basket_item.save()

        # Get players from form
        players = {0: request.user}
        player_payments = {0: request.POST.get("player0_payment")}

        for p_id in range(1, 6):
            p_string = f"player{p_id}"
            ppay_string = f"player{p_id}_payment"
            if p_string in request.POST:
                p_string_value = request.POST.get(p_string)
                if p_string_value != "":
                    players[p_id] = get_object_or_404(User, pk=int(p_string_value))
                    player_payments[p_id] = request.POST.get(ppay_string)

        # validate
        if (event.player_format == "Pairs" and len(players) != 2) or (
            event.player_format == "Teams" and len(players) < 4
        ):
            print("invalid number of entries")
            return

        # create player entries
        for p_id in range(len(players)):

            event_entry_player = EventEntryPlayer()
            event_entry_player.event_entry = event_entry
            event_entry_player.player = players[p_id]
            event_entry_player.payment_type = player_payments[p_id]
            entry_fee, discount, reason, description = event.entry_fee_for(
                event_entry_player.player
            )
            if p_id < 4:
                event_entry_player.entry_fee = entry_fee
                event_entry_player.reason = reason
            else:
                event_entry_player.entry_fee = 0
                event_entry_player.reason = "Team > 4"
                event_entry_player.payment_status = "Paid"
            event_entry_player.save()

            # Log it
            EventLog(
                event=event,
                actor=event_entry.primary_entrant,
                action=f"Event entry player {event_entry_player.id} created for {event_entry_player.player}",
            ).save()

        print(request.POST)
        if "now" in request.POST:
            print("ok")
            return redirect("events:checkout")
        else:  # add to cart and keep shopping
            msg = "Added to your cart"
            return redirect(
                f"/events/congress/view/{event.congress.id}?msg={msg}#program"
            )

    else:
        return enter_event_form(event, congress, request)


@login_required()
def edit_event_entry(request, congress_id, event_id):
    """ edit an event entry """

    # Load the event
    event = get_object_or_404(Event, pk=event_id)
    congress = get_object_or_404(Congress, pk=congress_id)

    # Check if already entered
    if not event.already_entered(request.user):
        return redirect(
            "events:enter_event", event_id=event.id, congress_id=congress_id
        )

    if request.method == "POST":

        # get event_entry
        # event_entry_list = event.evententry_set.all().values_list("id")
        # event_entry = (
        #     EventEntryPlayer.objects.filter(player=request.user)
        #     .filter(event_entry__in=event_entry_list)
        #     .first()
        #     .event_entry
        # )

        event_entry = (
            EventEntry.objects.filter(primary_entrant=request.user)
            .filter(event=event)
            .first()
        )

        # Get players from form
        players = {0: request.user}
        player_payments = {0: request.POST.get("player0_payment")}

        for p_id in range(1, 6):
            p_string = f"player{p_id}"
            ppay_string = f"player{p_id}_payment"
            if p_string in request.POST:
                players[p_id] = get_object_or_404(
                    User, pk=int(request.POST.get(p_string))
                )
                player_payments[p_id] = request.POST.get(ppay_string)

        # validate
        if (event.player_format == "Pairs" and len(players) != 2) or (
            event.player_format == "Teams" and len(players) < 4
        ):
            print("invalid number of entries")
            return

        # get existing player entries
        event_entry_player_list = EventEntryPlayer.objects.filter(
            event_entry=event_entry
        )

        # match them up
        match_dict = {}
        for p_id in range(len(players)):

            # try to get player from list
            event_entry_player = event_entry_player_list.filter(
                player=players[p_id]
            ).first()
            if event_entry_player:
                match_dict[players[p_id]] = event_entry_player

        # update player entries
        for p_id in range(len(players)):
            event_entry_player = event_entry_player_list.filter(
                player=players[p_id]
            ).first()
            if event_entry_player:  # found a match
                event_entry_player.payment_type = player_payments[p_id]
                entry_fee, discount, reason, description = event.entry_fee_for(
                    event_entry_player.player
                )
                event_entry_player.entry_fee = entry_fee
                event_entry_player.save()

            else:  # player name has changed - find an unused one

                print("NFI")
                return

        if "now" in request.POST:
            return redirect("events:checkout")
        else:  # add to cart and keep shopping
            return redirect("events:view_congress", congress_id=event.congress.id)

    else:  # not a POST so build page
        existing_choices = {}
        event_entry = (
            EventEntry.objects.filter(primary_entrant=request.user)
            .filter(event=event)
            .first()
        )
        event_entry_players = event_entry.evententryplayer_set.all()
        count = 0
        for event_entry_player in event_entry_players:
            existing_choices["player%s" % count] = {}
            existing_choices["player%s" % count][
                "payment"
            ] = event_entry_player.payment_type
            existing_choices["player%s" % count]["name"] = event_entry_player.player.id
            existing_choices["player%s" % count][
                "entry_fee"
            ] = event_entry_player.entry_fee
            count += 1

        return enter_event_form(event, congress, request, existing_choices)


@login_required()
def checkout(request):
    """ Checkout view - make payments, get details """

    basket_items = BasketItem.objects.filter(player=request.user)

    if request.method == "POST":

        # Need to mark the entries that this is covering. The payment call is asynchronous so
        # we can't just load all the open basket_entries when we come back or more could have been
        # added.

        unique_id = str(uuid.uuid4())

        # Get list of event_entry_player records to include.
        event_entries = BasketItem.objects.filter(player=request.user).values_list(
            "event_entry"
        )
        event_entry_players = (
            EventEntryPlayer.objects.filter(event_entry__in=event_entries)
            .exclude(payment_status="Paid")
            .filter(Q(player=request.user) | Q(payment_type="my-system-dollars"))
            .distinct()
        )

        # Get total amount
        amount = event_entry_players.aggregate(Sum("entry_fee"))

        for event_entry_player in event_entry_players:
            event_entry_player.batch_id = unique_id
            event_entry_player.save()

            # Log it
            EventLog(
                event=event_entry_player.event_entry.event,
                actor=request.user,
                action=f"Checkout for event entry {event_entry_player.event_entry.id} for {event_entry_player.player}",
            ).save()

        # map this user (who is paying) to the batch id
        PlayerBatchId(player=request.user, batch_id=unique_id).save()

        return payment_api(
            request=request,
            member=request.user,
            description="Congress Entry",
            amount=amount["entry_fee__sum"],
            route_code="EVT",
            route_payload=unique_id,
            url=reverse("events:enter_event_success"),
            payment_type="Entry to a congress",
            book_internals=False,
        )

    # The name basket_items is used by the base template so use a different name
    return render(request, "events/checkout.html", {"basket_items_list": basket_items})


@login_required()
def admin_summary(request, congress_id):
    """ Admin View """

    congress = get_object_or_404(Congress, pk=congress_id)
    events = Event.objects.filter(congress=congress)

    total = {
        "entries": 0,
        "tables": 0.0,
        "due": Decimal(0),
        "paid": Decimal(0),
        "pending": Decimal(0),
    }

    # calculate summary
    for event in events:
        event_entries = EventEntry.objects.filter(event=event)
        event.entries = event_entries.count()
        event.early_fee = event.entry_fee - event.entry_early_payment_discount

        # calculate tables
        players_per_entry = EVENT_PLAYER_FORMAT_SIZE[event.player_format]

        # Teams of 3 - only need 3 to make a table
        if players_per_entry == 3:
            players_per_entry = 4

        # For teams we only have 4 per table
        if event.player_format == "Teams":
            players_per_entry = 4

        event.tables = event.entries * players_per_entry / 4.0

        # remove decimal if not required
        if event.tables == int(event.tables):
            event.tables = int(event.tables)

        # Get the event entry players for this event
        event_entry_list = event_entries.values_list("id")
        event_entry_players = EventEntryPlayer.objects.filter(
            event_entry__in=event_entry_list
        )

        event.due = event_entry_players.aggregate(Sum("entry_fee"))["entry_fee__sum"]
        if event.due is None:
            event.due = Decimal(0)

        event.paid = event_entry_players.filter(payment_status="Paid").aggregate(
            Sum("entry_fee")
        )["entry_fee__sum"]
        if event.paid is None:
            event.paid = Decimal(0)

        event.pending = event.due - event.paid

        # update totals
        total["entries"] += event.entries
        total["tables"] += event.tables
        total["due"] += event.due
        total["paid"] += event.paid
        total["pending"] += event.pending

    # fix total formatting
    if total["tables"] == int(total["tables"]):
        total["tables"] = int(total["tables"])

    return render(
        request,
        "events/admin_summary.html",
        {"events": events, "total": total, "congress": congress},
    )


@login_required()
def admin_event_summary(request, event_id):
    """ Admin Event View """

    event = get_object_or_404(Event, pk=event_id)

    event_entries = EventEntry.objects.filter(event=event)

    # build summary
    for event_entry in event_entries:
        event_entry_players = EventEntryPlayer.objects.filter(event_entry=event_entry)
        event_entry.received = Decimal(0)
        event_entry.outstanding = Decimal(0)
        event_entry.players = []

        for event_entry_player in event_entry_players:
            if event_entry_player.payment_received:
                event_entry.received += event_entry_player.payment_received
                event_entry.outstanding += (
                    event_entry_player.entry_fee - event_entry_player.payment_received
                )
            event_entry.players.append(event_entry_player)

    return render(
        request,
        "events/admin_event_summary.html",
        {"event": event, "event_entries": event_entries},
    )


@login_required()
def admin_evententry(request, evententry_id):
    """ Admin Event Entry View """

    event_entry = get_object_or_404(EventEntry, pk=evententry_id)
    event = event_entry.event
    congress = event.congress

    role = "events.org.%s.edit" % congress.congress_master.org.id
    rbac_user_role_or_error(request, role)

    return render(
        request,
        "events/admin_event_entry.html",
        {"event_entry": event_entry, "event": event, "congress": congress},
    )


@login_required()
def admin_evententryplayer(request, evententryplayer_id):
    """ Admin Event Entry Player View """

    event_entry_player = get_object_or_404(EventEntryPlayer, pk=evententryplayer_id)

    role = (
        "events.org.%s.edit"
        % event_entry_player.event_entry.event.congress.congress_master.org.id
    )
    rbac_user_role_or_error(request, role)

    if request.method == "POST":
        form = EventEntryPlayerForm(request.POST, instance=event_entry_player)
        if form.is_valid():
            form.save()

            # check if event entry payment status has changed
            event_entry_player.event_entry.check_if_paid()

            messages.success(
                request, "Entry updated", extra_tags="cobalt-message-success"
            )
            return redirect(
                "events:admin_evententry",
                evententry_id=event_entry_player.event_entry.id,
            )
    else:
        form = EventEntryPlayerForm(instance=event_entry_player)

    return render(
        request,
        "events/admin_event_entry_player.html",
        {"event_entry_player": event_entry_player, "form": form},
    )


@login_required()
def view_events(request):
    """ View Events you are entered into """

    # get event entries with event entry player entries for this user
    event_entries_list = (
        EventEntry.objects.filter(evententryplayer__player=request.user)
    ).values_list("id")

    # get events where event_entries_list is entered
    events = Event.objects.filter(evententry__in=event_entries_list)

    # Only include the ones in the future
    event_list = []
    for event in events:
        if event.start_date() >= datetime.now().date():
            event.entry_status = event.entry_status(request.user)
            event_list.append(event)

    # check for pending payments
    pending_payments = EventEntryPlayer.objects.exclude(payment_status="Paid").filter(
        player=request.user
    )
    return render(
        request,
        "events/view_events.html",
        {"event_list": event_list, "pending_payments": pending_payments},
    )


@login_required()
def pay_outstanding(request):
    """ Pay anything that is not in a status of paid """

    # Get outstanding payments for this user
    event_entry_players = EventEntryPlayer.objects.exclude(
        payment_status="Paid"
    ).filter(player=request.user)

    # redirect if nothing owing
    if not event_entry_players:
        messages.warning(
            request, "You have nothing due to pay", extra_tags="cobalt-message-warning"
        )
        return redirect("events:events")

    # Get total amount
    amount = event_entry_players.aggregate(Sum("entry_fee"))

    # identifier
    unique_id = str(uuid.uuid4())

    # apply identifier to each record
    for event_entry_player in event_entry_players:
        event_entry_player.batch_id = unique_id
        event_entry_player.save()

    # let payments API handle getting the money
    return payment_api(
        request=request,
        member=request.user,
        description="Congress Entry",
        amount=amount["entry_fee__sum"],
        route_code="EV2",
        route_payload=unique_id,
        url=reverse("events:enter_event_success"),
        payment_type="Entry to a congress",
    )


@login_required()
def view_event_entries(request, congress_id, event_id):
    """ Screen to show entries to an event """

    congress = get_object_or_404(Congress, pk=congress_id)
    event = get_object_or_404(Event, pk=event_id)
    entries = EventEntry.objects.filter(event=event)

    return render(
        request,
        "events/view_event_entries.html",
        {"congress": congress, "event": event, "entries": entries},
    )


@login_required()
def admin_event_csv(request, event_id):
    """ Download a CSV file with details of the entries """

    event = get_object_or_404(Event, pk=event_id)

    role = "events.org.%s.edit" % event.congress.congress_master.org.id
    rbac_user_role_or_error(request, role)

    # get details
    entries = event.evententry_set.all()

    local_dt = timezone.localtime(timezone.now(), TZ)
    today = dateformat.format(local_dt, "Y-m-d H:i:s")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f"attachment; filename={event}.csv"

    writer = csv.writer(response)
    writer.writerow(
        [event.event_name, "Downloaded by %s" % request.user.full_name, today]
    )

    # Event Entry details
    writer.writerow(
        [
            "Players",
            "Entry Fee",
            "Received",
            "Outstanding",
            "Status",
            "First Created Date",
            "Entry Complete Date",
        ]
    )

    for row in entries:

        players = ""
        received = Decimal(0)
        entry_fee = Decimal(0)

        for player in row.evententryplayer_set.all():
            players += player.player.full_name + " - "
            received += player.payment_received
            entry_fee += player.entry_fee
        players = players[:-3]

        local_dt = timezone.localtime(row.first_created_date, TZ)
        local_dt2 = timezone.localtime(row.entry_complete_date, TZ)

        writer.writerow(
            [
                players,
                entry_fee,
                received,
                entry_fee - received,
                row.payment_status,
                dateformat.format(local_dt, "Y-m-d H:i:s"),
                dateformat.format(local_dt2, "Y-m-d H:i:s"),
            ]
        )

    # Event Entry Player details
    writer.writerow([])
    writer.writerow([])
    writer.writerow(
        [
            "Primary Entrant",
            "Player",
            "Payment Type",
            "Entry Fee",
            "Received",
            "Outstanding",
            "Entry Fee Reason",
            "Payment Status",
        ]
    )

    payment_type_dict = dict(PAYMENT_TYPES)

    for entry in entries:
        for row in entry.evententryplayer_set.all():
            writer.writerow(
                [
                    entry.primary_entrant,
                    row.player,
                    payment_type_dict[row.payment_type],
                    row.entry_fee,
                    row.payment_received,
                    row.entry_fee - row.payment_received,
                    row.reason,
                    row.payment_status,
                ]
            )

    # Log it
    EventLog(event=event, actor=request.user, action=f"CSV Download of {event}").save()

    return response


@login_required()
def admin_event_offsystem(request, event_id):
    """ Handle off system payments such as cheques and bank transfers """

    event = get_object_or_404(Event, pk=event_id)

    # check access
    role = "events.org.%s.edit" % event.congress.congress_master.org.id
    rbac_user_role_or_error(request, role)

    players = EventEntryPlayer.objects.filter(event_entry__event=event).exclude(
        payment_status="Paid"
    )

    return render(
        request,
        "events/admin_event_offsystem.html",
        {"event": event, "players": players},
    )


@login_required()
def admin_event_log(request, event_id):
    """ Show logs for an event """

    event = get_object_or_404(Event, pk=event_id)

    # check access
    role = "events.org.%s.edit" % event.congress.congress_master.org.id
    rbac_user_role_or_error(request, role)

    logs = EventLog.objects.filter(event=event).order_by("-action_date")

    things = cobalt_paginator(request, logs)

    return render(
        request, "events/admin_event_log.html", {"event": event, "things": things}
    )


@login_required()
def admin_evententry_delete(request, evententry_id):
    """ Delete an event entry """

    event_entry = get_object_or_404(EventEntry, pk=evententry_id)

    # check access
    role = "events.org.%s.edit" % event_entry.event.congress.congress_master.org.id
    rbac_user_role_or_error(request, role)

    event_entry_players = EventEntryPlayer.objects.filter(event_entry=event_entry)

    # We use a formset factory to have multiple players on the same form
    RefundFormSet = formset_factory(RefundForm, extra=0)

    if request.method == "POST":
        refund_form_set = RefundFormSet(data=request.POST)
        if refund_form_set.is_valid():
            for form in refund_form_set:
                player = get_object_or_404(User, pk=form.cleaned_data["player_id"])
                amount = float(form.cleaned_data["refund"])
                amount_str = "%s%.2f" % (GLOBAL_CURRENCY_SYMBOL, amount)

                if amount > 0.0:

                    # create payments in org account
                    update_organisation(
                        organisation=event_entry.event.congress.congress_master.org,
                        amount=-amount,
                        description=f"Refund to {player} for {event_entry.event.event_name}",
                        source="Events",
                        log_msg=f"Refund to {player} for {event_entry.event.event_name}",
                        sub_source="refund",
                        payment_type="Refund",
                        member=player,
                    )

                    # create payment for member
                    update_account(
                        organisation=event_entry.event.congress.congress_master.org,
                        amount=amount,
                        description=f"Refund from {event_entry.event.congress.congress_master.org} for {event_entry.event.event_name}",
                        source="Events",
                        log_msg=f"Refund from {event_entry.event.congress.congress_master.org} for {event_entry.event.event_name}",
                        sub_source="refund",
                        payment_type="Refund",
                        member=player,
                    )

                    # Log it
                    EventLog(
                        event=event_entry.event,
                        actor=request.user,
                        action=f"Refund of {amount_str} to {player}",
                    ).save()
                    messages.success(
                        request,
                        f"Refund of {amount_str} to {player} successful",
                        extra_tags="cobalt-message-success",
                    )

                # Notify member
                email_body = f"""{request.user.full_name} has cancelled your entry to
                                <b>{event_entry.event.event_name}</b> in
                                <b>{event_entry.event.congress.name}.</b><br><br>
                              """
                if amount > 0.0:
                    email_body += f"""A refund of {GLOBAL_CURRENCY_SYMBOL}{amount:.2f}
                                    has been credited to your {GLOBAL_ORG} {GLOBAL_CURRENCY_NAME}
                                    account.<br><br>
                                  """

                email_body += f"Please contact {request.user.first_name} directly if you have any queries.<br><br>"

                context = {
                    "name": player.first_name,
                    "title": "Entry to %s cancelled" % event_entry.event,
                    "email_body": email_body,
                    "host": COBALT_HOSTNAME,
                    "link": "/events/view",
                    "link_text": "View Congresses",
                }

                html_msg = render_to_string(
                    "notifications/email_with_button.html", context
                )

                # send
                contact_member(
                    member=player,
                    msg="Entry to %s cancelled" % event_entry.event.event_name,
                    contact_type="Email",
                    html_msg=html_msg,
                    link="/events/view",
                    subject="Event Entry Cancelled - %s" % event_entry.event,
                )

        # Log it
        EventLog(
            event=event_entry.event,
            actor=request.user,
            action=f"Entry deleted for {event_entry.primary_entrant}",
        ).save()

        event_entry.delete()

        messages.success(request, "Entry deleted", extra_tags="cobalt-message-success")
        return redirect("events:admin_event_summary", event_id=event_entry.event.id)

    else:  # not POST - build summary
        event_entry.received = Decimal(0)
        initial = []

        # we need to default refund per player to who actually paid it, not
        # who was entered. If Fred paid for Bill's entry then Fred should get
        # the refund not Bill

        refund_dict = {}
        for event_entry_player in event_entry_players:
            refund_dict[event_entry_player.player] = Decimal(0)

        for event_entry_player in event_entry_players:
            # check if we have a player who paid
            if event_entry_player.paid_by:

                # maybe this player is no longer part of the team
                if event_entry_player.paid_by not in refund_dict.keys():
                    refund_dict[event_entry_player.paid_by] = Decimal(0)

                refund_dict[
                    event_entry_player.paid_by
                ] += event_entry_player.payment_received

            # Not sure who paid to default it back to the entry name
            else:
                refund_dict[
                    event_entry_player.player
                ] += event_entry_player.payment_received

        for player_refund in refund_dict.keys():
            event_entry.received += refund_dict[player_refund]
            initial.append(
                {
                    "player_id": player_refund.id,
                    "player": f"{player_refund}",
                    "refund": refund_dict[player_refund],
                }
            )

        refund_form_set = RefundFormSet(initial=initial)

        club = event_entry.event.congress.congress_master.org
        club_balance = org_balance(club)

    return render(
        request,
        "events/admin_event_entry_delete.html",
        {
            "event_entry": event_entry,
            "event_entry_players": event_entry_players,
            "refund_form_set": refund_form_set,
            "club": club,
            "club_balance": club_balance,
        },
    )


@login_required()
def enter_event_success(request):
    """ url for payments to go to after successful entry """
    messages.success(
        request,
        "Payment complete. You will receive a confirmation email.",
        extra_tags="cobalt-message-success",
    )
    return view_events(request)


@login_required()
def test(request):
    return render(request, "events/test.html")

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
    rbac_user_has_role,
)
from rbac.views import rbac_user_role_or_error
from .core import events_payments_callback
from payments.core import payment_api, org_balance, update_account, update_organisation
from organisations.models import Organisation
from django.contrib import messages
import uuid
from cobalt.settings import (
    GLOBAL_ORG,
    GLOBAL_CURRENCY_NAME,
    BRIDGE_CREDITS,
    TIME_ZONE,
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

    congresses = (
        Congress.objects.order_by("start_date")
        .filter(start_date__gte=datetime.now())
        .filter(status="Published")
    )

    # get draft congresses
    draft_congresses = Congress.objects.filter(status="Draft")
    draft_congress_flag = False
    for draft_congress in draft_congresses:
        role = "events.org.%s.edit" % draft_congress.congress_master.org.id
        if rbac_user_has_role(request.user, role):
            draft_congress_flag = True
            break

    grouped_by_month = {}
    for congress in congresses:

        # Comment field
        if (
            congress.entry_open_date
            and congress.entry_open_date > datetime.now().date()
        ):
            congress.msg = "Entries open on " + congress.entry_open_date.strftime(
                "%d %b %Y"
            )
        elif (
            congress.entry_close_date
            and congress.entry_close_date > datetime.now().date()
        ):
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
        {
            "grouped_by_month": grouped_by_month,
            "admin": admin,
            "draft_congress_flag": draft_congress_flag,
        },
    )


@login_required()
def view_congress(request, congress_id, fullscreen=False):
    """basic view of an event.

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

    # add start date and sort by start date
    events_list = {}
    for event in events:
        event.event_start_date = event.start_date()
        events_list[event] = event.event_start_date
        events_list_sorted = {
            key: value
            for key, value in sorted(events_list.items(), key=lambda item: item[1])
        }

    # program_list will be passed to the template, each entry is a <tr> element
    program_list = []

    # every day of an event gets its own row so we use rowspan for event name and links
    for event in events_list_sorted:
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
                ] = f"<td rowspan='{rows}'><span class='title'>{event.event_name}</td><td rowspan='{rows}'><span class='title'>{event.entry_fee} credits</span></td>"
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


def enter_event_form(event, congress, request, existing_choices=None):
    """build the form part of the enter_event view. Its not a Django form,
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
        pay_types.append(("my-system-dollars", f"My {BRIDGE_CREDITS}"))
    if congress.payment_method_bank_transfer:
        pay_types.append(("bank-transfer", "Bank Transfer"))
    if congress.payment_method_cash:
        pay_types.append(("cash", "Cash on the day"))
    if congress.payment_method_cheques:
        pay_types.append(("cheque", "Cheque"))

    # Get team mates for this user - exclude anyone entered already
    all_team_mates = TeamMate.objects.filter(user=request.user)
    team_mates_list = all_team_mates.values_list("team_mate")
    entered_team_mates = (
        EventEntryPlayer.objects.filter(event_entry__event=event)
        .filter(player__in=team_mates_list)
        .values_list("player")
    )
    team_mates = all_team_mates.exclude(team_mate__in=entered_team_mates)

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
                ("their-system-dollars", f"Their {BRIDGE_CREDITS}")
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

    # Check if draft
    if congress.status != "Published":
        return render(request, "events/event_closed.html", {"event": event})

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

        # see if we got a free format answer
        answer = request.POST.get("free_format_answer", None)
        if answer:
            event_entry.free_format_answer = answer

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

        if "now" in request.POST:
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
            .exclude(entry_status="Cancelled")
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

        # Get list of event_entry_player records to include.
        event_entries = BasketItem.objects.filter(player=request.user).values_list(
            "event_entry"
        )
        event_entry_players = (
            EventEntryPlayer.objects.filter(event_entry__in=event_entries)
            .exclude(payment_status="Paid")
            #        .filter(Q(player=request.user) | Q(payment_type="my-system-dollars"))
            .filter(payment_type="my-system-dollars")
            .distinct()
        )

        unique_id = str(uuid.uuid4())

        # map this user (who is paying) to the batch id
        PlayerBatchId(player=request.user, batch_id=unique_id).save()

        # Get total amount
        amount = event_entry_players.aggregate(Sum("entry_fee"))

        if amount["entry_fee__sum"]:  # something for Payments to do

            for event_entry_player in event_entry_players:
                event_entry_player.batch_id = unique_id
                event_entry_player.save()

                # Log it
                EventLog(
                    event=event_entry_player.event_entry.event,
                    actor=request.user,
                    action=f"Checkout for event entry {event_entry_player.event_entry.id} for {event_entry_player.player}",
                ).save()

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

        else:  # no payment required go straight to the callback

            events_payments_callback("Success", unique_id, None)

    # Not a POST, build the form

    # Get list of event_entry_player records to include.
    event_entries = BasketItem.objects.filter(player=request.user).values_list(
        "event_entry"
    )
    event_entry_players = EventEntryPlayer.objects.filter(
        event_entry__in=event_entries
    ).exclude(payment_status="Paid")

    # get totals per congress
    congress_total = {}
    total_today = Decimal(0)
    total_entry_fee = Decimal(0)

    for event_entry_player in event_entry_players:

        congress = event_entry_player.event_entry.event.congress

        if congress not in congress_total.keys():

            congress_total[congress] = {}
            congress_total[congress]["entry_fee"] = event_entry_player.entry_fee
            if event_entry_player.payment_type == "my-system-dollars":
                congress_total[congress]["today"] = event_entry_player.entry_fee
                total_today += event_entry_player.entry_fee
                congress_total[congress]["later"] = Decimal(0.0)
            else:
                congress_total[congress]["later"] = event_entry_player.entry_fee
                congress_total[congress]["today"] = Decimal(0.0)

        else:
            congress_total[congress]["entry_fee"] += event_entry_player.entry_fee
            if event_entry_player.payment_type == "my-system-dollars":
                congress_total[congress]["today"] += event_entry_player.entry_fee
                total_today += event_entry_player.entry_fee
            else:
                congress_total[congress]["later"] += event_entry_player.entry_fee

    grouped_by_congress = {}
    for event_entry_player in event_entry_players:

        congress = event_entry_player.event_entry.event.congress

        data = {
            "event_entry_player": event_entry_player,
            "entry_fee": congress_total[congress]["entry_fee"],
            "today": congress_total[congress]["today"],
            "later": congress_total[congress]["later"],
        }

        if congress in grouped_by_congress:
            grouped_by_congress[congress].append(data)
        else:
            grouped_by_congress[congress] = [data]

    # The name basket_items is used by the base template so use a different name
    return render(
        request,
        "events/checkout.html",
        {
            "grouped_by_congress": grouped_by_congress,
            "total_today": total_today,
            "total_entry_fee": total_entry_fee,
            "total_outstanding": total_entry_fee - total_today,
            "basket_items_list": basket_items,
        },
    )


@login_required()
def view_events(request):
    """ View Events you are entered into """

    # get event entries with event entry player entries for this user
    event_entries_list = (
        EventEntry.objects.filter(evententryplayer__player=request.user).exclude(
            entry_status="Cancelled"
        )
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
    event_entry_players = (
        EventEntryPlayer.objects.exclude(payment_status="Paid")
        .filter(player=request.user)
        .filter(evententry__entry_status="Cancelled")
    )

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

    # Log it
    EventLog(
        event=event_entry_player.event_entry.event,
        actor=request.user,
        action=f"Checkout for {request.user}",
    ).save()

    # map this user (who is paying) to the batch id
    PlayerBatchId(player=request.user, batch_id=unique_id).save()

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
    entries = EventEntry.objects.filter(event=event).exclude(entry_status="Cancelled")
    date_string = event.print_dates()

    return render(
        request,
        "events/view_event_entries.html",
        {
            "congress": congress,
            "event": event,
            "entries": entries,
            "date_string": date_string,
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
def global_admin_congress_masters(request):
    """ administration of congress masters """

    rbac_user_role_or_error(request, "events.global.edit")

    congress_masters = CongressMaster.objects.all()

    return render(
        request,
        "events/global_admin_congress_masters.html",
        {"congress_masters": congress_masters},
    )


@login_required()
def edit_event_entry2(request, congress_id, event_id):
    """ edit an event entry """

    # Load the event
    event = get_object_or_404(Event, pk=event_id)
    congress = get_object_or_404(Congress, pk=congress_id)

    # Check if already entered
    if not event.already_entered(request.user):
        return redirect(
            "events:enter_event", event_id=event.id, congress_id=congress_id
        )

    event_entry = (
        EventEntry.objects.filter(primary_entrant=request.user)
        .filter(event=event)
        .exclude(entry_status="Cancelled")
        .first()
    )

    return render(
        request,
        "events/edit_event_entry2.html",
        {"event": event, "congress": congress, "event_entry": event_entry},
    )

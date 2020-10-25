""" The file has the code relating to a convener managing an existing event """

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
    EventPlayerDiscount,
)
from accounts.models import User, TeamMate
from .forms import (
    CongressForm,
    NewCongressForm,
    EventForm,
    SessionForm,
    EventEntryPlayerForm,
    RefundForm,
    EventPlayerDiscountForm,
    EmailForm,
)
from rbac.core import (
    rbac_user_allowed_for_model,
    rbac_get_users_with_role,
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
def admin_summary(request, congress_id):
    """ Admin View """

    congress = get_object_or_404(Congress, pk=congress_id)
    events = Event.objects.filter(congress=congress)

    # check access
    role = "events.org.%s.edit" % congress.congress_master.org.id
    rbac_user_role_or_error(request, role)

    total = {
        "entries": 0,
        "tables": 0.0,
        "due": Decimal(0),
        "paid": Decimal(0),
        "pending": Decimal(0),
    }

    # calculate summary
    for event in events:
        event_entries = EventEntry.objects.filter(event=event).exclude(
            entry_status="Cancelled"
        )
        event.entries = event_entries.count()
        if event.entry_early_payment_discount:
            event.early_fee = event.entry_fee - event.entry_early_payment_discount
        else:
            event.early_fee = event.entry_fee

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

    # check access
    role = "events.org.%s.edit" % event.congress.congress_master.org.id
    rbac_user_role_or_error(request, role)

    event_entries = EventEntry.objects.filter(event=event).exclude(
        entry_status="Cancelled"
    )

    # build summary
    total_received = Decimal(0.0)
    total_outstanding = Decimal(0.0)
    total_entry_fee = Decimal(0.0)

    for event_entry in event_entries:
        event_entry_players = EventEntryPlayer.objects.filter(event_entry=event_entry)
        event_entry.received = Decimal(0.0)
        event_entry.outstanding = Decimal(0.0)
        event_entry.entry_fee = Decimal(0.0)
        event_entry.players = []

        for event_entry_player in event_entry_players:

            if event_entry_player.payment_received:
                received = event_entry_player.payment_received
            else:
                received = Decimal(0.0)

            event_entry.received += received
            event_entry.outstanding += event_entry_player.entry_fee - received
            event_entry.entry_fee += event_entry_player.entry_fee
            event_entry.players.append(event_entry_player)

            total_received += received
            total_outstanding += event_entry_player.entry_fee - received
            total_entry_fee += event_entry_player.entry_fee

    return render(
        request,
        "events/admin_event_summary.html",
        {
            "event": event,
            "event_entries": event_entries,
            "total_received": total_received,
            "total_outstanding": total_outstanding,
            "total_entry_fee": total_entry_fee,
        },
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
    header = [
        "Players",
        "Entry Fee",
        "Received",
        "Outstanding",
        "Status",
        "First Created Date",
        "Entry Complete Date",
    ]

    if event.free_format_question:
        header.append(f"'{event.free_format_question}'")

    writer.writerow(header)

    for row in entries:

        players = ""
        received = Decimal(0)
        entry_fee = Decimal(0)

        for player in row.evententryplayer_set.all():
            players += player.player.full_name + " - "
            try:
                received += player.payment_received
            except TypeError:
                pass  # ignore if payment_received is None
            entry_fee += player.entry_fee
        players = players[:-3]

        local_dt = timezone.localtime(row.first_created_date, TZ)
        local_dt2 = timezone.localtime(row.entry_complete_date, TZ)

        this_row = [
            players,
            entry_fee,
            received,
            entry_fee - received,
            row.entry_status,
            dateformat.format(local_dt, "Y-m-d H:i:s"),
            dateformat.format(local_dt2, "Y-m-d H:i:s"),
        ]

        if event.free_format_question:
            this_row.append(row.free_format_answer)

        writer.writerow(this_row)

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
            if row.payment_received:
                outstanding = row.entry_fee - row.payment_received
            else:
                outstanding = row.entry_fee
            writer.writerow(
                [
                    entry.primary_entrant,
                    row.player,
                    payment_type_dict[row.payment_type],
                    row.entry_fee,
                    row.payment_received,
                    outstanding,
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

    # get players with manual payment methods
    players = EventEntryPlayer.objects.filter(event_entry__event=event).exclude(
        payment_type__in=["my-system-dollars", "their-system-dollars"]
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
                amount_str = "%.2f credits" % amount

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
                        event_entry=event_entry,
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
                    email_body += f"""A refund of {amount:.2f} credits
                                    has been transferred to your {BRIDGE_CREDITS}
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
            event_entry=event_entry,
        ).save()

        event_entry.entry_status = "Cancelled"
        event_entry.save()

        messages.success(
            request, "Entry cancelled", extra_tags="cobalt-message-success"
        )
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

            # Not sure who paid so default it back to the entry name
            else:
                try:
                    refund_dict[
                        event_entry_player.player
                    ] += event_entry_player.payment_received
                except TypeError:
                    pass

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
def admin_event_player_discount(request, event_id):
    """ Manage discounted entry to events """

    event = get_object_or_404(Event, pk=event_id)

    # check access
    role = "events.org.%s.edit" % event.congress.congress_master.org.id
    rbac_user_role_or_error(request, role)

    event_player_discounts = EventPlayerDiscount.objects.filter(event=event)

    if request.method == "POST":
        form = EventPlayerDiscountForm(request.POST)
        if form.is_valid():

            player = form.cleaned_data["player"]
            reason = form.cleaned_data["reason"]

            already = EventPlayerDiscount.objects.filter(
                event=event, player=player
            ).count()

            if already:
                messages.error(
                    request,
                    f"There is already a discount for {player}",
                    extra_tags="cobalt-message-error",
                )

            else:

                entry_fee = form.cleaned_data["entry_fee"]
                event_player_discount = EventPlayerDiscount()
                event_player_discount.player = player
                event_player_discount.admin = request.user
                event_player_discount.event = event
                event_player_discount.reason = reason
                event_player_discount.entry_fee = entry_fee
                event_player_discount.save()

                messages.success(
                    request, "Entry added", extra_tags="cobalt-message-success"
                )

    # check if player is entered
    for event_player_discount in event_player_discounts:
        if event_player_discount.event.already_entered(event_player_discount.player):
            event_player_discount.status = "Entered - "

            # check status of entry
            event_entry_player = (
                EventEntryPlayer.objects.filter(event_entry__event=event)
                .filter(player=event_player_discount.player)
                .exclude(event_entry__entry_status="Cancelled")
                .first()
            )
            event_player_discount.status += "%s" % event_entry_player.payment_status
            event_player_discount.event_entry_player_id = event_entry_player.id
        else:
            event_player_discount.status = "Not Entered"

    form = EventPlayerDiscountForm()

    return render(
        request,
        "events/admin_event_player_discount.html",
        {
            "event": event,
            "event_player_discounts": event_player_discounts,
            "form": form,
        },
    )


@login_required()
def admin_event_email(request, event_id):
    """ Email all entrants to an event """

    event = get_object_or_404(Event, pk=event_id)

    # check access
    role = "events.org.%s.edit" % event.congress.congress_master.org.id
    rbac_user_role_or_error(request, role)

    form = EmailForm(request.POST or None)

    # who will receive this
    recipients_qs = EventEntryPlayer.objects.filter(event_entry__event=event).exclude(
        event_entry__entry_status="Cancelled"
    )

    if request.method == "POST":
        if form.is_valid():
            subject = form.cleaned_data["subject"]
            body = form.cleaned_data["body"]

            if "test" in request.POST:
                recipients = [request.user]
            else:
                recipients = []
                for recipient in recipients_qs:
                    recipients.append(recipient.player)
            for recipient in recipients:
                context = {
                    "name": recipient.first_name,
                    "title": subject,
                    "email_body": body,
                    "host": COBALT_HOSTNAME,
                    "link": "/events/view",
                    "link_text": "View Entry",
                }

                html_msg = render_to_string(
                    "notifications/email_with_button.html", context
                )

                # send
                contact_member(
                    member=recipient,
                    msg=f"Email about {event}",
                    contact_type="Email",
                    html_msg=html_msg,
                    link="/events/view",
                    subject=subject,
                )

            if "test" in request.POST:
                msg = "Test message sent"
            else:
                msg = "%s message(s) sent" % (len(recipients))

            messages.success(request, msg, extra_tags="cobalt-message-success")

    return render(
        request,
        "events/admin_email.html",
        {"form": form, "event": event, "count": recipients_qs.count()},
    )

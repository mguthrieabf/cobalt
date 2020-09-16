from .models import BasketItem, EventEntry, EventEntryPlayer
from django.db.models import Q
from django.utils import timezone
import payments.core as payments_core  # circular dependency
from notifications.views import contact_member
from cobalt.settings import COBALT_HOSTNAME
from django.template.loader import render_to_string


def events_payments_callback(status, route_payload, tran):
    """ This gets called when a payment has been made for us.

        We supply the route_payload when we ask for the payment to be made and
        use it to update the status of payments. """

    if status == "Success":

        # Update EntryEventPlayer objects
        event_entry_players = EventEntryPlayer.objects.filter(batch_id=route_payload)
        for event_entry_player in event_entry_players:
            event_entry_player.payment_status = "Paid"
            event_entry_player.save()

            # create payments in org account
            payments_core.update_organisation(
                organisation=event_entry_player.event_entry.event.congress.congress_master.org,
                amount=event_entry_player.entry_fee,
                description="hello",
                source="Events",
                log_msg="hello",
                sub_source="events_callback",
                payment_type="Entry to an event",
                member=event_entry_player.player,  # who we are paying for, not necessarily who paid
            )

            payments_core.update_account(
                member=event_entry_player.player,
                amount=-event_entry_player.entry_fee,
                description="goodbye",
                source="Events",
                sub_source="events_callback",
                payment_type="Entry to an event",
                log_msg="goodbye",
                organisation=event_entry_player.event_entry.event.congress.congress_master.org,
            )

        # Get all EventEntries for changed EventEntryPlayers
        event_entry_list = (
            event_entry_players.order_by("event_entry")
            .distinct("event_entry")
            .values_list("event_entry")
        )

        event_entries = EventEntry.objects.filter(pk__in=event_entry_list)

        # Now process their system dollar transactions - same loop as below but
        # easier to understand as 2 separate bits of code
        for event_entry in event_entries:
            for event_entry_player in event_entry.evententryplayer_set.all():
                if event_entry_player.payment_type == "their-system-dollars":
                    rc = payments_core.payment_api(
                        request=None,
                        member=event_entry_player.player,
                        description="Congress Entry",
                        amount=event_entry_player.entry_fee,
                        organisation=event_entry_player.event_entry.event.congress.congress_master.org,
                        payment_type="Entry to a congress",
                    )
                    print(rc)
                    event_entry_player.payment_status = "Paid"
                    event_entry_player.save()

        # Check if EntryEvent is now complete
        for event_entry in event_entries:
            all_complete = True
            for event_entry_player in event_entry.evententryplayer_set.all():
                if event_entry_player.payment_status != "Paid":
                    all_complete = False
                    break
            if all_complete:
                event_entry.payment_status = "Paid"
                event_entry.entry_complete_date = timezone.now()
                event_entry.save()

        user = (
            EventEntryPlayer.objects.filter(batch_id=route_payload)
            .first()
            .event_entry.primary_entrant
        )

        # Go through the basket and notify people
        # We send one email per congress
        # email_dic will be email_dic[congress][user][event_entry]
        email_dic = {}

        basket_items = BasketItem.objects.filter(player=user)

        for basket_item in basket_items:
            # Get players in event
            players = basket_item.event_entry.evententryplayer_set.all()

            for player in players:
                event_entry = basket_item.event_entry
                event = basket_item.event_entry.event
                congress = event.congress
                if congress not in email_dic.keys():
                    email_dic[congress] = {}
                if event not in email_dic[congress].keys():
                    email_dic[congress][event] = []
                email_dic[congress][event].append(player)

        print(email_dic)
        for congress in email_dic.keys():
            print(congress)
            for event in email_dic[congress].keys():
                print("-- %s" % event)
                for player in email_dic[congress][event]:
                    print("---- %s" % player)

        # now send the emails
        email_list={}
        for congress in email_dic.keys():
            for event in email_dic[congress].keys():
                msg = f"""
                        <p>Entry received for <b>{congress.name}</b> hosted by {congress.congress_master.org}.</p>
                        <table class="receipt" border="0" cellpadding="0" cellspacing="0">
                        <tr><th>Event<th>Team Mates<th>Entry Status</tr>

                """
                player_list=[]
                for player in email_dic[congress][event]:
                    player_list.append(player.player)
                    if player not in email_list.keys():
                        email_list[player]=""
                    sub_msg = f"<tr><td class='receipt-figure'>{event.event_name}<td class='receipt-figure'>"
                    sub_msg += f"{player.player}<br>"
                    sub_msg += f"<td class='receipt-figure'>{player.payment_status}</tr>"

                msg += sub_msg + "</table><br>"
                context = {
                    "name": event_entry_player_item.player.first_name,
                    "title": "Event Entry - %s" % event_entry.event.congress,
                    "email_body": msg,
                    "host": COBALT_HOSTNAME,
                    "link": "/events",
                    "link_text": "Edit Entry",
                }

                html_msg = render_to_string(
                    "notifications/email_with_button.html", context
                )

                contact_member(
                    member=user,
                    msg=msg,
                    contact_type="Email",
                    html_msg=html_msg,
                    link="/events",
                    subject="Event Entry - %s" % event_entry,
                )

        # empty basket - if user added things after they went to the
        # checkout screen then they will be lost
        basket_items.delete()


def get_basket_for_user(user):
    return BasketItem.objects.filter(player=user).count()


def get_events(user):
    """ called by dashboard to get upcoming events """
    return EventEntryPlayer.objects.filter(player=user)

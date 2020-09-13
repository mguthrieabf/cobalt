from .models import BasketItem, EventEntry, EventEntryPlayer
from django.db.models import Q
from django.utils import timezone
import payments.core as payments_core  # circular dependency
from notifications.views import contact_member


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

        # Now process their system dollar transactions - same loop as above but
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
        # empty basket - if user added things after they went to the
        # checkout screen then they will be lost
        BasketItem.objects.filter(player=user).delete()

        # notify people
        print(user)
        contact_member(
            member=user,
            msg="Entry stuff",
            contact_type="email",
            html_msg="<h2>Stuff</h2>",
            link=None,
            subject="Stuff",
        )


def get_basket_for_user(user):
    return BasketItem.objects.filter(player=user).count()


def get_events(user):
    """ called by dashboard to get upcoming events """
    return EventEntryPlayer.objects.filter(player=user)

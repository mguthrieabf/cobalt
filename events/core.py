from .models import BasketItem, EventEntry, EventEntryPlayer
from django.db.models import Q
from django.utils import timezone

# def _totals(event_entry_players):
#     """ total calcs are the same for all functions so use common routine """
#
#     total = 0
#     for event_entry_player in event_entry_players:
#         total += float(event_entry_player.entry_fee)
#     return total
#
#
# def basket_amt_total(user):
#     """ total amount, owning or paid, in a users basket including other people's payments """
#
#     event_entries =  BasketItem.objects.filter(player=user).values_list('event_entry')
#     event_entry_players = EventEntryPlayer.objects.filter(event_entry__in=event_entries)
#     return _totals(event_entry_players)
#
# def basket_amt_paid(user):
#     """ total amount paid in a users basket including other people's payments """
#
#     event_entries =  BasketItem.objects.filter(player=user).values_list('event_entry')
#     event_entry_players = EventEntryPlayer.objects.filter(event_entry__in=event_entries).exclude(payment_status="Paid")
#     return _totals(event_entry_players)
#
# def basket_amt_this_user_only(user):
#     """ total amount paid, or unpaid in a users basket excluding other people's
#     payments unless the payment_method is my-system-dollars  """
#
#     event_entries =  BasketItem.objects.filter(player=user).values_list('event_entry')
#     event_entry_players = EventEntryPlayer.objects.filter(event_entry__in=event_entries).filter(Q(player=user) | Q(payment_type="my-system-dollars"))
#     return _totals(event_entry_players)
#
# def basket_amt_owing_this_user_only(user):
#     """ total amount unpaid in a users basket excluding other people's payments """
#
#     event_entries =  BasketItem.objects.filter(player=user).values_list('event_entry')
#     event_entry_players = EventEntryPlayer.objects.filter(event_entry__in=event_entries).exclude(payment_status="Paid").filter(Q(player=user) | Q(payment_type="my-system-dollars"))
#     return _totals(event_entry_players)


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

        # Check if EntryEvent is now complete

        # Get all EventEntries for changed EventEntryPlayers
        event_entry_list = (
            event_entry_players.order_by("event_entry")
            .distinct("event_entry")
            .values_list("event_entry")
        )

        event_entries = EventEntry.objects.filter(pk__in=event_entry_list)

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


def get_basket_for_user(user):
    return BasketItem.objects.filter(player=user).count()

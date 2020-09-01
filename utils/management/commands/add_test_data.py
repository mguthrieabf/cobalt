""" Script to create cobalt test data """

from cobalt.settings import RBAC_EVERYONE, TIME_ZONE
from accounts.models import User
from events.models import CongressMaster
from django.core.management.base import BaseCommand
from accounts.management.commands.accounts_core import create_fake_user
from forums.management.commands.forums_core import create_forum
from organisations.management.commands.orgs_core import create_org
from rbac.management.commands.rbac_core import (
    create_RBAC_action,
    create_RBAC_default,
    create_RBAC_admin_group,
    create_RBAC_admin_tree,
)
from rbac.core import (
    rbac_add_user_to_admin_group,
    rbac_add_role_to_admin_group,
    rbac_create_group,
    rbac_add_user_to_group,
    rbac_add_role_to_group,
)
from payments.core import update_account, update_organisation
from payments.models import StripeTransaction
from forums.models import Post, Comment1, Comment2, LikePost, LikeComment1, LikeComment2
from organisations.models import MemberOrganisation
from rbac.models import RBACModelDefault
from events.models import Congress, Event, Session
import random
from essential_generators import DocumentGenerator
import datetime
import pytz
from django.utils.timezone import make_aware, now

TZ = pytz.timezone(TIME_ZONE)
DATA_DIR = "utils/testdata/"


class Command(BaseCommand):
    def add_comments(self, post, user_list):
        liker_list = list(set(user_list) - set([post.author]))
        sample_size = random.randrange(int(len(liker_list) * 0.8))
        for liker in random.sample(liker_list, sample_size):
            like = LikePost(post=post, liker=liker)
            like.save()
        for c1_counter in range(random.randrange(10)):
            text = self.random_paragraphs()
            c1 = Comment1(post=post, text=text, author=random.choice(user_list))
            c1.save()
            liker_list = list(set(user_list) - set([c1.author]))
            sample_size = random.randrange(int(len(liker_list) * 0.8))
            for liker in random.sample(liker_list, sample_size):
                like = LikeComment1(comment1=c1, liker=liker)
                like.save()
            post.comment_count += 1
            post.save()
            for c2_counter in range(random.randrange(10)):
                text = self.random_paragraphs()
                c2 = Comment2(
                    post=post, comment1=c1, text=text, author=random.choice(user_list)
                )
                c2.save()
                post.comment_count += 1
                post.save()
                c1.comment1_count += 1
                c1.save()
                liker_list = list(set(user_list) - set([c2.author]))
                sample_size = random.randrange(int(len(liker_list) * 0.8))
                for liker in random.sample(liker_list, sample_size):
                    like = LikeComment2(comment2=c2, liker=liker)
                    like.save()

    def random_paragraphs(self):
        text = self.gen.paragraph()
        for counter in range(random.randrange(10)):
            text += "\n\n" + self.gen.paragraph()
        return text

    def random_sentence(self):
        return self.gen.sentence()

    def random_paragraphs_with_stuff(self):

        sizes = [
            ("400x500", "400px"),
            ("400x300", "400px"),
            ("700x300", "700px"),
            ("900x500", "900px"),
            ("200x200", "200px"),
            ("800x200", "800px"),
            ("500x400", "500px"),
        ]

        text = self.gen.paragraph()
        for counter in range(random.randrange(10)):
            type = random.randrange(8)
            if type == 5:  # no good reason
                text += "<h2>%s</h2>" % self.gen.sentence()
            elif type == 7:
                index = random.randrange(len(sizes))
                text += (
                    "<p><img src='https://source.unsplash.com/random/%s' style='width: %s;'><br></p>"
                    % (sizes[index][0], sizes[index][1])
                )
            else:
                text += "<p>%s</p>" % self.gen.paragraph()
        return text

    def __init__(self):
        super().__init__()
        self.gen = DocumentGenerator()

    def handle(self, *args, **options):
        print("Running add_rbac_test_data")

        EVERYONE = User.objects.filter(pk=RBAC_EVERYONE).first()
        mark = User.objects.filter(system_number="620246").first()
        julian = User.objects.filter(system_number="518891").first()

        # Users
        print("Creating Users")
        user_dic = {}
        with open(DATA_DIR + "users.txt") as infile:
            for line in infile:
                if line.find("#") == 0 or line.strip() == "":
                    continue
                parts = [s.strip() for s in line.split(",")]
                (id, num, fname, lname, about, pic) = parts
                user = create_fake_user(self, num, fname, lname, about, pic)
                user_dic[id] = user
        user_dic["EVERYONE"] = EVERYONE
        user_dic["mark"] = mark
        user_dic["julian"] = julian

        # Orgs - assumes ABF already created elsewhere
        print("Creating Orgs")
        org_dic = {}
        with open(DATA_DIR + "orgs.txt") as infile:
            for line in infile:
                if line.find("#") == 0 or line.strip() == "":
                    continue
                parts = [s.strip() for s in line.split(",")]
                (id, num, name, add1, add2, add3, state, clubnum, orgtype) = parts
                org = create_org(
                    self, num, name, add1, add2, add3, state, clubnum, orgtype
                )
                org_dic[id] = org

        # Add Members to Orgs
        print("Adding Members to clubs")
        with open(DATA_DIR + "member_orgs.txt") as infile:
            for line in infile:
                if line.find("#") == 0 or line.strip() == "":
                    continue
                parts = [s.strip() for s in line.split(",")]
                (member, org) = parts
                MemberOrganisation(
                    member=user_dic[member], organisation=org_dic[org]
                ).save()

        # create Forums
        print("Creating Forums")
        forum_dic = {}
        with open(DATA_DIR + "forums.txt") as infile:
            for line in infile:
                if line.find("#") == 0 or line.strip() == "":
                    continue
                parts = [s.strip() for s in line.split(",")]
                (id, name, desc, ftype) = parts
                forum = create_forum(self, name, desc, ftype)
                forum_dic[id] = forum

        # create dummy Posts
        print("Creating dummy forum posts")
        print("Running", end="", flush=True)
        for post_counter in range(10):

            post = Post(
                forum=random.choice(list(forum_dic.values())),
                title=self.random_sentence(),
                text=self.random_paragraphs_with_stuff(),
                author=random.choice(list(user_dic.values())),
            )
            post.save()
            print(".", end="", flush=True)
            self.add_comments(post, list(user_dic.values()))
        print("\n")

        # create RBAC Groups
        print("Creating RBAC Groups")

        rbac_group_dic = {}
        with open(DATA_DIR + "rbac_groups.txt") as infile:
            for line in infile:
                if line.find("#") == 0 or line.strip() == "":
                    continue
                parts = [s.strip() for s in line.split(",")]
                (id, tree, name, desc) = parts
                group = rbac_create_group(tree, name, desc)
                rbac_group_dic[id] = group

        # add roles to groups
        print("Adding Roles to RBAC Groups")
        with open(DATA_DIR + "rbac_group_roles.txt") as infile:
            for line in infile:
                if line.find("#") == 0 or line.strip() == "":
                    continue
                parts = [s.strip() for s in line.split(",")]
                (id, a, b, c, d, e) = parts
                if e == "":
                    e = None
                rbac_add_role_to_group(rbac_group_dic[id], a, b, c, d, model_id=e)

        # add users to groups
        print("Adding Users to RBAC Groups")
        with open(DATA_DIR + "rbac_group_users.txt") as infile:
            for line in infile:
                if line.find("#") == 0 or line.strip() == "":
                    continue
                parts = [s.strip() for s in line.split(",")]
                (groupid, userid) = parts
                if e == "":
                    e = None
                rbac_add_user_to_group(user_dic[userid], rbac_group_dic[groupid])

        # admin tree
        print("Admin Tree")
        print("Creating RBAC Admin Groups")

        rbac_admin_group_dic = {}
        with open(DATA_DIR + "rbac_admin_groups.txt") as infile:
            for line in infile:
                if line.find("#") == 0 or line.strip() == "":
                    continue
                parts = [s.strip() for s in line.split(",")]
                (id, tree, name, desc) = parts
                group = create_RBAC_admin_group(self, tree, name, desc)
                rbac_admin_group_dic[id] = group

        print("Adding Trees to RBAC Admin Groups")

        with open(DATA_DIR + "rbac_admin_group_trees.txt") as infile:
            for line in infile:
                if line.find("#") == 0 or line.strip() == "":
                    continue
                parts = [s.strip() for s in line.split(",")]
                (id, tree) = parts
                create_RBAC_admin_tree(self, rbac_admin_group_dic[id], tree)

        print("Adding Roles to RBAC Admin Groups")

        with open(DATA_DIR + "rbac_admin_group_roles.txt") as infile:
            for line in infile:
                if line.find("#") == 0 or line.strip() == "":
                    continue
                parts = [s.strip() for s in line.split(",")]
                (id, app, model) = parts
                rbac_add_role_to_admin_group(
                    rbac_admin_group_dic[id], app=app, model=model
                )

        print("Adding Users to RBAC Admin Groups")

        with open(DATA_DIR + "rbac_admin_group_users.txt") as infile:
            for line in infile:
                if line.find("#") == 0 or line.strip() == "":
                    continue
                parts = [s.strip() for s in line.split(",")]
                (groupid, userid) = parts
                rbac_add_user_to_admin_group(rbac_admin_group_dic[id], user_dic[userid])

        # create event test data
        print("Creating Events Test Data")

        # Congress Master
        print("Congress Masters")
        congress_master_dic = {}
        with open(DATA_DIR + "events_congress_masters.txt") as infile:
            for line in infile:
                if line.find("#") == 0 or line.strip() == "":
                    continue
                parts = [s.strip() for s in line.split(",")]
                (id, orgid, name) = parts
                cm = CongressMaster(name=name, org=org_dic[orgid])
                cm.save()
                congress_master_dic[id] = cm

        # Congress
        print("Congresses")
        congress_dic = {}
        with open(DATA_DIR + "events_congresses.txt") as infile:
            for line in infile:
                if line.find("#") == 0 or line.strip() == "":
                    continue
                parts = [s.strip() for s in line.split(",")]
                vars = [
                    "id",
                    "cmid",
                    "start_yr",
                    "start_mth",
                    "start_day",
                    "end_yr",
                    "end_mth",
                    "end_day",
                    "date_string",
                    "year",
                    "venue_name",
                    "lat",
                    "lon",
                    "venue_transport",
                    "venue_catering",
                    "people",
                    "general_info",
                    "payment_method_system_dollars",
                    "payment_method_bank_transfer",
                    "payment_method_cash",
                    "payment_method_cheques",
                    "allow_early_payment_discount",
                    "early_yr",
                    "early_mnth",
                    "early_day",
                    "allow_youth_payment_discount",
                    "yth_year",
                    "yth_mnth",
                    "yth_day",
                    "snr_yr",
                    "snr_mnth",
                    "snr_day",
                    "youth_payment_discount_age",
                    "senior_age",
                    "open_yr",
                    "open_mnth",
                    "open_day",
                    "close_yr",
                    "close_mnth",
                    "close_day",
                    "allow_partnership_desk",
                    "status",
                ]
                for i in range(len(parts)):
                    print(vars[i], parts[i])

                (
                    id,
                    cmid,
                    start_yr,
                    start_mth,
                    start_day,
                    end_yr,
                    end_mth,
                    end_day,
                    date_string,
                    year,
                    venue_name,
                    lat,
                    lon,
                    venue_transport,
                    venue_catering,
                    people,
                    general_info,
                    payment_method_system_dollars,
                    payment_method_bank_transfer,
                    payment_method_cash,
                    payment_method_cheques,
                    allow_early_payment_discount,
                    early_yr,
                    early_mnth,
                    early_day,
                    allow_youth_payment_discount,
                    yth_year,
                    yth_mnth,
                    yth_day,
                    snr_yr,
                    snr_mnth,
                    snr_day,
                    youth_payment_discount_age,
                    senior_age,
                    open_yr,
                    open_mnth,
                    open_day,
                    close_yr,
                    close_mnth,
                    close_day,
                    allow_partnership_desk,
                    status,
                ) = parts

                congress = Congress(
                    congress_master=congress_master_dic[cmid],
                    name=congress_master_dic[cmid].name + " %s" % year,
                    default_email="dummy@fake.com",
                    start_date=datetime.date(
                        int(start_yr), int(start_mth), int(start_day)
                    ),
                    end_date=datetime.date(int(end_yr), int(end_mth), int(end_day)),
                    date_string=date_string,
                    year=int(year),
                    venue_name=venue_name,
                    venue_location="%s, %s" % (lat, lon),
                    venue_transport=venue_transport,
                    venue_catering=venue_catering,
                    people=people,
                    general_info=general_info,
                    payment_method_system_dollars=payment_method_system_dollars,
                    payment_method_bank_transfer=payment_method_bank_transfer,
                    payment_method_cash=payment_method_cash,
                    payment_method_cheques=payment_method_cheques,
                    allow_early_payment_discount=allow_early_payment_discount,
                    early_payment_discount_date=make_aware(
                        datetime.datetime(
                            int(early_yr), int(early_mnth), int(early_day), 0, 0
                        ),
                        TZ,
                    ),
                    allow_youth_payment_discount=allow_youth_payment_discount,
                    youth_payment_discount_date=make_aware(
                        datetime.datetime(
                            int(yth_year), int(yth_mnth), int(yth_day), 0, 0
                        ),
                        TZ,
                    ),
                    senior_date=make_aware(
                        datetime.datetime(
                            int(snr_yr), int(snr_mnth), int(snr_day), 0, 0
                        ),
                        TZ,
                    ),
                    youth_payment_discount_age=int(youth_payment_discount_age),
                    senior_age=int(senior_age),
                    entry_open_date=make_aware(
                        datetime.datetime(
                            int(open_yr), int(open_mnth), int(open_day), 0, 0
                        ),
                        TZ,
                    ),
                    entry_close_date=make_aware(
                        datetime.datetime(
                            int(close_yr), int(close_mnth), int(close_day), 0, 0
                        ),
                        TZ,
                    ),
                    allow_partnership_desk=allow_partnership_desk,
                    status=status,
                )

                congress.save()
                congress_dic[id] = congress

        print("Events")

        event_dic = {}
        with open(DATA_DIR + "events_events.txt") as infile:
            for line in infile:
                if line.find("#") == 0 or line.strip() == "":
                    continue
                parts = [s.strip() for s in line.split(",")]
                (
                    id,
                    congressid,
                    event_name,
                    description,
                    max_entries,
                    event_type,
                    entry_fee,
                    entry_early_payment_discount,
                    player_format,
                ) = parts
                event = Event(
                    congress=congress_dic[congressid],
                    event_name=event_name,
                    description=description,
                    max_entries=max_entries,
                    event_type=event_type,
                    entry_fee=entry_fee,
                    entry_early_payment_discount=entry_early_payment_discount,
                    player_format=player_format,
                )
                event.save()
                event_dic[id] = event

        print("Sessions")

        with open(DATA_DIR + "events_sessions.txt") as infile:
            for line in infile:
                if line.find("#") == 0 or line.strip() == "":
                    continue
                parts = [s.strip() for s in line.split(",")]
                (
                    eventid,
                    ses_yr,
                    sess_mnth,
                    sess_day,
                    st_hr,
                    st_min,
                    end_hr,
                    end_min,
                ) = parts
                if end_hr:
                    session_end = datetime.time(int(end_hr), int(end_min))
                else:
                    session_end = None
                Session(
                    event=event_dic[eventid],
                    session_date=make_aware(
                        datetime.datetime(
                            int(ses_yr), int(sess_mnth), int(sess_day), 0, 0
                        ),
                        TZ,
                    ),
                    session_start=datetime.time(int(st_hr), int(st_min)),
                    session_end=session_end,
                ).save()

        # Payments
        print("Payments")

        print("Stripe")
        stripe_dic = {}
        with open(DATA_DIR + "payments_stripe.txt") as infile:
            for line in infile:
                if line.find("#") == 0 or line.strip() == "":
                    continue
                parts = [s.strip() for s in line.split(",")]
                (
                    id,
                    memberid,
                    description,
                    amount,
                    stripe_brand,
                    stripe_country,
                    stripe_exp_month,
                    stripe_exp_year,
                    stripe_last4,
                    orgid,
                    othermemberid,
                ) = parts

                if othermemberid:
                    other_member = user_dic[othermemberid]
                else:
                    other_member = None

                if orgid:
                    org = org_dic[orgid]
                else:
                    org = None

                tran = StripeTransaction()

                tran.description = description
                tran.amount = amount
                tran.member = user_dic[memberid]
                tran.linked_member = other_member
                tran.linked_organisation = org
                tran.stripe_reference = "dummy-ref-no"
                tran.stripe_method = "dummy-pay-ref"
                tran.stripe_currency = "aud"
                tran.stripe_receipt_url = "https://pay.stripe.com/receipts/acct_1GiCM8JWMUHj2yxk/ch_1HMfsvJWMUHj2yxkxV0hkyJF/rcpt_HwZ0zOou5vrn4VaNHpLOO59ybx1psji"
                tran.stripe_brand = stripe_brand
                tran.stripe_country = stripe_country
                tran.stripe_exp_month = stripe_exp_month
                tran.stripe_exp_year = stripe_exp_year
                tran.stripe_last4 = stripe_last4
                tran.last_change_date = now()
                tran.status = "Complete"
                tran.save()
                stripe_dic[id] = tran

        print("Member")
        payments_member_dic = {}
        with open(DATA_DIR + "payments_member.txt") as infile:
            for line in infile:
                if line.find("#") == 0 or line.strip() == "":
                    continue
                parts = [s.strip() for s in line.split(",")]
                (
                    id,
                    memberid,
                    amount,
                    orgid,
                    other_memberid,
                    stripe_transactionid,
                    description,
                    payment_type,
                    days_ago,
                    hour,
                    min,
                ) = parts
                member = user_dic[memberid]

                if other_memberid:
                    other_member = user_dic[other_memberid]
                else:
                    other_member = None

                if orgid:
                    org = org_dic[orgid]
                else:
                    org = None

                if stripe_transactionid:
                    tran = stripe_dic[stripe_transactionid]
                else:
                    tran = None

                act = update_account(
                    member=member,
                    amount=amount,
                    organisation=org,
                    other_member=other_member,
                    stripe_transaction=tran,
                    description=description,
                    source="TestData",
                    sub_source="testdata",
                    payment_type=payment_type,
                    log_msg="test data",
                )

                if days_ago:
                    act.created_date = now() - datetime.timedelta(days=int(days_ago))
                    #    act.created_date = act.created_date.replace(hour=int(hour), minute=int(min))
                    act.save()

                payments_member_dic[id] = act

        print("Orgs")
        with open(DATA_DIR + "payments_org.txt") as infile:
            for line in infile:
                if line.find("#") == 0 or line.strip() == "":
                    continue
                parts = [s.strip() for s in line.split(",")]
                (orgid, amount, memberid, description, payment_type) = parts
                member = user_dic[memberid]
                org = org_dic[orgid]

                update_organisation(
                    organisation=org,
                    amount=amount,
                    description=description,
                    log_msg="test data",
                    source="TestData",
                    sub_source="test_data",
                    payment_type=payment_type,
                    member=member,
                )

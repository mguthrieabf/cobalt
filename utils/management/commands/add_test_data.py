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
from django.utils.timezone import make_aware, now, utc
from importlib import import_module
import glob
import sys
from inspect import currentframe, getframeinfo

TZ = pytz.timezone(TIME_ZONE)
DATA_DIR = "utils/testdata/julian/"


class Command(BaseCommand):
    def __init__(self):
        super().__init__()
        self.gen = DocumentGenerator()
        self.id_array = {}

    def add_comments(self, post, user_list):
        """ add comments to a forum post """

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
        """ generate a random paragraph """
        text = self.gen.paragraph()
        for counter in range(random.randrange(10)):
            text += "\n\n" + self.gen.paragraph()
        return text

    def random_sentence(self):
        """ generate a random sentence """
        return self.gen.sentence()

    def random_paragraphs_with_stuff(self):
        """ generate a more realistic rich test paragraph with headings and pics """

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

    def parse_csv(self, file):
        """ try to sort out the mess Excel makes of CSV files.
            Requires csv files to have the app and model in the first row and
            the fieldnames in the second row. """

        f = open(file)

        lines = f.readlines()

        data = []

        try:
            app, model = lines[0].split(",")[:2]
        except ValueError:
            print("\n\nError\n")
            print("Didn't find App, Model on first line of file")
            print("File is: %s" % file)
            print("Line is: %s\n" % lines[0])
            sys.exit()

        try:
            if lines[0].split(",")[3] == "duplicates":
                allow_dupes = True
            else:
                allow_dupes = False
        except (ValueError, IndexError):
            allow_dupes = False

        headers = lines[1]
        header_list = []

        # take column names from header
        for header in headers.split(","):
            header_list.append(header.strip())

        # loop through records
        for line in lines[2:]:

            # skip empty rows
            if (
                line.find("#") == 0
                or line.strip() == ""
                or line.strip().replace(",", "") == ""
            ):
                continue

            # split to parts
            columns = line.split(",")

            # loop through columns
            row = {}
            for i in range(len(header_list)):
                try:
                    if not columns[i].strip() == "":
                        row[header_list[i]] = columns[i].strip()
                except IndexError:
                    row[header_list[i]] = None
            data.append(row)

        return (app.strip(), model.strip(), data, allow_dupes)

    def process_csv(self, csv):
        """ do the work on the csv data """
        app, model, data, allow_dupes = self.parse_csv(csv)
        print(f"App Model is: {app}.{model}\n")

        # special cases
        if app == "accounts" and model == "User":
            self.accounts_user(app, model, data)
        else:
            # default
            dic = {}
            this_array = None
            for row in data:
                # see if already present
                exec_cmd = (
                    "module = import_module('%s.models')\ninstance = module.%s.objects"
                    % (app, model)
                )

                for key, value in row.items():
                    if value and key != "id":
                        if key[:3] == "id.":  # foreign key

                            parts = key.split(".")

                            fkey = parts[1]
                            fapp = parts[2]
                            fmodel = parts[3]
                            this_array = self.id_array
                            exec_cmd += f".filter({fkey}=this_array[f'{fapp}.{fmodel}']['{value}'])"
                        elif key[:2] != "t.":  # exclude time
                            exec_cmd2 = f"module = import_module(f'{app}.models')\nfield_type=module.{model}._meta.get_field('{key}').get_internal_type()"
                            exec(exec_cmd2, globals())
                            if field_type == "CharField":  # noqa: F821
                                exec_cmd += f".filter({key}='{value}')"
                            else:
                                exec_cmd += f".filter({key}={value})"
                exec_cmd += ".first()"

                local_array = {"this_array": this_array}
                try:
                    exec(exec_cmd, globals(), local_array)
                except KeyError as exc:
                    print("\n\nError\n")
                    print(str(exc))
                    print("Array contains:")
                    for block in this_array:
                        for key2, val2 in this_array[block].items():
                            print(block, key2, val2)
                    print("\nStatement was:")
                    print(exec_cmd)
                    sys.exit()
                instance = local_array["instance"]

                # that was hard, now check it
                if instance and not allow_dupes:
                    print("already present: %s" % instance)
                else:
                    exec_cmd = (
                        "module = import_module('%s.models')\ninstance = module.%s()"
                        % (app, model)
                    )
                    local_array = {}
                    exec(exec_cmd, globals(), local_array)
                    instance = local_array["instance"]

                    if not instance:
                        print("\n\nError\n")
                        print(f"Failed to create instance of {app}.{model}")
                        print(f"Processing file: {csv}\n")
                        frameinfo = getframeinfo(currentframe())
                        print(
                            "Error somewhere above: ",
                            frameinfo.filename,
                            frameinfo.lineno,
                            "\n",
                        )
                        sys.exit()
                    for key, value in row.items():
                        try:
                            value=value.replace("^",",")
                        except AttributeError:
                            pass
                        if key != "id" and key[:2] != "t.":
                            if len(key) > 3:
                                if key[:3] == "id.":  # foreign key
                                    parts = key.split(".")
                                    fkey = parts[1]
                                    fapp = parts[2]
                                    fmodel = parts[3]
                                    try:
                                        val = self.id_array[f"{fapp}.{fmodel}"][value]
                                    except KeyError:
                                        print("\n\nError\n")
                                        print(row)
                                        print(
                                            f"Foreign key not found: {fapp}.{fmodel}: {value}"
                                        )
                                        print(
                                            f"Check that the file with {app}.{model} has id {value} and that it is loaded before this file.\n"
                                        )
                                        sys.exit()
                                    setattr(instance, fkey, val)
                                else:
                                    setattr(instance, key, value)
                            else:
                                setattr(instance, key, value)
                        if key[:2] == "t.":
                            field = key[2:]
                            adjusted_date = now() - datetime.timedelta(days=int(value))
                            datetime_local = adjusted_date.astimezone(TZ)
                            setattr(instance, field, datetime_local)
                        if key[:2] == "d.":
                            field = key[2:]
                            yr, mt, dy = value.split("-")
                            this_date=make_aware(
                                datetime.datetime(
                                    int(yr), int(mt), int(dy), 0, 0
                                ),
                                TZ,
                            )
                            setattr(instance, field, this_date)
                    instance.save()
                # add to dic if we have an id field
                if "id" in row.keys():
                    dic[row["id"]] = instance

            self.id_array[f"{app}.{model}"] = dic

    def accounts_user(self, app, model, data):
        dic = {}
        for row in data:
            if "about" not in row:
                row["about"] = None
            if "pic" not in row:
                row["pic"] = None

            user = create_fake_user(
                self,
                row["system_number"],
                row["first_name"],
                row["last_name"],
                row["about"],
                row["pic"],
            )
            dic[row["id"]] = user
            dic["EVERYONE"] = User.objects.filter(pk=RBAC_EVERYONE).first()
            dic["mark"] = User.objects.filter(system_number="620246").first()
            dic["julian"] = User.objects.filter(system_number="518891").first()
        self.id_array["accounts.User"] = dic

    def handle(self, *args, **options):
        print("Running add_rbac_test_data")

        for fname in sorted(glob.glob(DATA_DIR + "/*.csv")):
            print("\n#########################################################")
            print("Processing: %s" % fname)
            self.process_csv(fname)

        # # Users
        # print("Creating Users")
        # self.process_csv("users.csv")
        #
        # # Orgs - assumes ABF already created elsewhere
        # print("Creating Orgs")
        #
        # org_dic = {}
        # self.parse_csv("orgs.csv")
        # for row in data:
        #         org = create_org(
        #             self, row['num'], row['name'], row['add1'], row['add2'], row['add3'], row['state'], row['clubnum'], row['orgtype']
        #         )
        #         org_dic[row['id']] = org

        # # Add Members to Orgs
        # print("Adding Members to clubs")
        # data = self.parse_csv("member_orgs.csv")
        # for row in data:
        #         MemberOrganisation(
        #             member=user_dic[row['member']], organisation=org_dic[row['org']]
        #         ).save()
        #
        # # create Forums
        # print("Creating Forums")
        # forum_dic = {}
        # data = self.parse_csv("forums.csv")
        # for row in data:
        #     forum = create_forum(self, row['name'], row['desc'], row['ftype'])
        #     forum_dic[row['id']] = forum
        #
        # # create dummy Posts
        # print("Creating dummy forum posts")
        # print("Running", end="", flush=True)
        # for post_counter in range(10):
        #
        #     post = Post(
        #         forum=random.choice(list(forum_dic.values())),
        #         title=self.random_sentence(),
        #         text=self.random_paragraphs_with_stuff(),
        #         author=random.choice(list(user_dic.values())),
        #     )
        #     post.save()
        #     print(".", end="", flush=True)
        #     self.add_comments(post, list(user_dic.values()))
        # print("\n")
        #
        # # create RBAC Groups
        # print("Creating RBAC Groups")
        #
        # rbac_group_dic = {}
        # forum_dic = {}
        # data = self.parse_csv("rbac_groups.csv")
        # with open(DATA_DIR + "rbac_groups.csv") as infile:
        #     for line in infile:
        #         if line.find("#") == 0 or line.strip() == "":
        #             continue
        #         parts = [s.strip() for s in line.split(",")]
        #         (id, tree, name, desc) = parts
        #         group = rbac_create_group(tree, name, desc)
        #         rbac_group_dic[id] = group
        #
        # # add roles to groups
        # print("Adding Roles to RBAC Groups")
        # with open(DATA_DIR + "rbac_group_roles.csv") as infile:
        #     for line in infile:
        #         if line.find("#") == 0 or line.strip() == "":
        #             continue
        #         parts = [s.strip() for s in line.split(",")]
        #         (id, a, b, c, d, e) = parts
        #         if e == "":
        #             e = None
        #         rbac_add_role_to_group(rbac_group_dic[id], a, b, c, d, model_id=e)
        #
        # # add users to groups
        # print("Adding Users to RBAC Groups")
        # with open(DATA_DIR + "rbac_group_users.csv") as infile:
        #     for line in infile:
        #         if line.find("#") == 0 or line.strip() == "":
        #             continue
        #         parts = [s.strip() for s in line.split(",")]
        #         (groupid, userid) = parts
        #         if e == "":
        #             e = None
        #         rbac_add_user_to_group(user_dic[userid], rbac_group_dic[groupid])
        #
        # # admin tree
        # print("Admin Tree")
        # print("Creating RBAC Admin Groups")
        #
        # rbac_admin_group_dic = {}
        # with open(DATA_DIR + "rbac_admin_groups.csv") as infile:
        #     for line in infile:
        #         if line.find("#") == 0 or line.strip() == "":
        #             continue
        #         parts = [s.strip() for s in line.split(",")]
        #         (id, tree, name, desc) = parts
        #         group = create_RBAC_admin_group(self, tree, name, desc)
        #         rbac_admin_group_dic[id] = group
        #
        # print("Adding Trees to RBAC Admin Groups")
        #
        # with open(DATA_DIR + "rbac_admin_group_trees.csv") as infile:
        #     for line in infile:
        #         if line.find("#") == 0 or line.strip() == "":
        #             continue
        #         parts = [s.strip() for s in line.split(",")]
        #         (id, tree) = parts
        #         create_RBAC_admin_tree(self, rbac_admin_group_dic[id], tree)
        #
        # print("Adding Roles to RBAC Admin Groups")
        #
        # with open(DATA_DIR + "rbac_admin_group_roles.csv") as infile:
        #     for line in infile:
        #         if line.find("#") == 0 or line.strip() == "":
        #             continue
        #         parts = [s.strip() for s in line.split(",")]
        #         (id, app, model) = parts
        #         rbac_add_role_to_admin_group(
        #             rbac_admin_group_dic[id], app=app, model=model
        #         )
        #
        # print("Adding Users to RBAC Admin Groups")
        #
        # with open(DATA_DIR + "rbac_admin_group_users.csv") as infile:
        #     for line in infile:
        #         if line.find("#") == 0 or line.strip() == "":
        #             continue
        #         parts = [s.strip() for s in line.split(",")]
        #         (groupid, userid) = parts
        #         rbac_add_user_to_admin_group(rbac_admin_group_dic[id], user_dic[userid])
        #
        # # create event test data
        # print("Creating Events Test Data")
        #
        # # Congress Master
        # print("Congress Masters")
        # congress_master_dic = {}
        # with open(DATA_DIR + "events_congress_masters.csv") as infile:
        #     for line in infile:
        #         if line.find("#") == 0 or line.strip() == "":
        #             continue
        #         parts = [s.strip() for s in line.split(",")]
        #         (id, orgid, name) = parts
        #         cm = CongressMaster(name=name, org=org_dic[orgid])
        #         cm.save()
        #         congress_master_dic[id] = cm
        #
        # # Congress
        # print("Congresses")
        # congress_dic = {}
        # with open(DATA_DIR + "events_congresses.csv") as infile:
        #     for line in infile:
        #         if line.find("#") == 0 or line.strip() == "":
        #             continue
        #         parts = [s.strip() for s in line.split(",")]
        #         vars = [
        #             "id",
        #             "cmid",
        #             "start_yr",
        #             "start_mth",
        #             "start_day",
        #             "end_yr",
        #             "end_mth",
        #             "end_day",
        #             "date_string",
        #             "year",
        #             "venue_name",
        #             "lat",
        #             "lon",
        #             "venue_transport",
        #             "venue_catering",
        #             "people",
        #             "general_info",
        #             "payment_method_system_dollars",
        #             "payment_method_bank_transfer",
        #             "payment_method_cash",
        #             "payment_method_cheques",
        #             "allow_early_payment_discount",
        #             "early_yr",
        #             "early_mnth",
        #             "early_day",
        #             "allow_youth_payment_discount",
        #             "yth_year",
        #             "yth_mnth",
        #             "yth_day",
        #             "snr_yr",
        #             "snr_mnth",
        #             "snr_day",
        #             "youth_payment_discount_age",
        #             "senior_age",
        #             "open_yr",
        #             "open_mnth",
        #             "open_day",
        #             "close_yr",
        #             "close_mnth",
        #             "close_day",
        #             "allow_partnership_desk",
        #             "status",
        #         ]
        #
        #         (
        #             id,
        #             cmid,
        #             start_yr,
        #             start_mth,
        #             start_day,
        #             end_yr,
        #             end_mth,
        #             end_day,
        #             date_string,
        #             year,
        #             venue_name,
        #             lat,
        #             lon,
        #             venue_transport,
        #             venue_catering,
        #             people,
        #             general_info,
        #             payment_method_system_dollars,
        #             payment_method_bank_transfer,
        #             payment_method_cash,
        #             payment_method_cheques,
        #             allow_early_payment_discount,
        #             early_yr,
        #             early_mnth,
        #             early_day,
        #             allow_youth_payment_discount,
        #             yth_year,
        #             yth_mnth,
        #             yth_day,
        #             snr_yr,
        #             snr_mnth,
        #             snr_day,
        #             youth_payment_discount_age,
        #             senior_age,
        #             open_yr,
        #             open_mnth,
        #             open_day,
        #             close_yr,
        #             close_mnth,
        #             close_day,
        #             allow_partnership_desk,
        #             status,
        #         ) = parts
        #
        #         congress = Congress(
        #             congress_master=congress_master_dic[cmid],
        #             name=congress_master_dic[cmid].name + " %s" % year,
        #             default_email="dummy@fake.com",
        #             start_date=datetime.date(
        #                 int(start_yr), int(start_mth), int(start_day)
        #             ),
        #             end_date=datetime.date(int(end_yr), int(end_mth), int(end_day)),
        #             date_string=date_string,
        #             year=int(year),
        #             venue_name=venue_name,
        #             venue_location="%s, %s" % (lat, lon),
        #             venue_transport=venue_transport,
        #             venue_catering=venue_catering,
        #             people=people,
        #             general_info=general_info,
        #             payment_method_system_dollars=payment_method_system_dollars,
        #             payment_method_bank_transfer=payment_method_bank_transfer,
        #             payment_method_cash=payment_method_cash,
        #             payment_method_cheques=payment_method_cheques,
        #             allow_early_payment_discount=allow_early_payment_discount,
        #             early_payment_discount_date=make_aware(
        #                 datetime.datetime(
        #                     int(early_yr), int(early_mnth), int(early_day), 0, 0
        #                 ),
        #                 TZ,
        #             ),
        #             allow_youth_payment_discount=allow_youth_payment_discount,
        #             youth_payment_discount_date=make_aware(
        #                 datetime.datetime(
        #                     int(yth_year), int(yth_mnth), int(yth_day), 0, 0
        #                 ),
        #                 TZ,
        #             ),
        #             senior_date=make_aware(
        #                 datetime.datetime(
        #                     int(snr_yr), int(snr_mnth), int(snr_day), 0, 0
        #                 ),
        #                 TZ,
        #             ),
        #             youth_payment_discount_age=int(youth_payment_discount_age),
        #             senior_age=int(senior_age),
        #             entry_open_date=make_aware(
        #                 datetime.datetime(
        #                     int(open_yr), int(open_mnth), int(open_day), 0, 0
        #                 ),
        #                 TZ,
        #             ),
        #             entry_close_date=make_aware(
        #                 datetime.datetime(
        #                     int(close_yr), int(close_mnth), int(close_day), 0, 0
        #                 ),
        #                 TZ,
        #             ),
        #             allow_partnership_desk=allow_partnership_desk,
        #             status=status,
        #         )
        #
        #         congress.save()
        #         congress_dic[id] = congress
        #
        # print("Events")
        #
        # event_dic = {}
        # with open(DATA_DIR + "events_events.csv") as infile:
        #     for line in infile:
        #         if line.find("#") == 0 or line.strip() == "":
        #             continue
        #         parts = [s.strip() for s in line.split(",")]
        #         (
        #             id,
        #             congressid,
        #             event_name,
        #             description,
        #             max_entries,
        #             event_type,
        #             entry_fee,
        #             entry_early_payment_discount,
        #             player_format,
        #         ) = parts
        #         event = Event(
        #             congress=congress_dic[congressid],
        #             event_name=event_name,
        #             description=description,
        #             max_entries=max_entries,
        #             event_type=event_type,
        #             entry_fee=entry_fee,
        #             entry_early_payment_discount=entry_early_payment_discount,
        #             player_format=player_format,
        #         )
        #         event.save()
        #         event_dic[id] = event
        #
        # print("Sessions")
        #
        # with open(DATA_DIR + "events_sessions.csv") as infile:
        #     for line in infile:
        #         if line.find("#") == 0 or line.strip() == "":
        #             continue
        #         parts = [s.strip() for s in line.split(",")]
        #         (
        #             eventid,
        #             ses_yr,
        #             sess_mnth,
        #             sess_day,
        #             st_hr,
        #             st_min,
        #             end_hr,
        #             end_min,
        #         ) = parts
        #         if end_hr:
        #             session_end = datetime.time(int(end_hr), int(end_min))
        #         else:
        #             session_end = None
        #         Session(
        #             event=event_dic[eventid],
        #             session_date=make_aware(
        #                 datetime.datetime(
        #                     int(ses_yr), int(sess_mnth), int(sess_day), 0, 0
        #                 ),
        #                 TZ,
        #             ),
        #             session_start=datetime.time(int(st_hr), int(st_min)),
        #             session_end=session_end,
        #         ).save()
        #
        # # Payments
        # print("Payments")
        #
        # print("Stripe")
        # stripe_dic = {}
        # with open(DATA_DIR + "payments_stripe.csv") as infile:
        #     for line in infile:
        #         if line.find("#") == 0 or line.strip() == "":
        #             continue
        #         parts = [s.strip() for s in line.split(",")]
        #         (
        #             id,
        #             memberid,
        #             description,
        #             amount,
        #             stripe_brand,
        #             stripe_country,
        #             stripe_exp_month,
        #             stripe_exp_year,
        #             stripe_last4,
        #             orgid,
        #             othermemberid,
        #             days_ago,
        #             hour,
        #             min,
        #         ) = parts
        #
        #         if othermemberid:
        #             other_member = user_dic[othermemberid]
        #         else:
        #             other_member = None
        #
        #         if orgid:
        #             org = org_dic[orgid]
        #         else:
        #             org = None
        #
        #         tran = StripeTransaction()
        #
        #         tran.description = description
        #         tran.amount = amount
        #         tran.member = user_dic[memberid]
        #         tran.linked_member = other_member
        #         tran.linked_organisation = org
        #         tran.stripe_reference = "dummy-ref-no"
        #         tran.stripe_method = "dummy-pay-ref"
        #         tran.stripe_currency = "aud"
        #         tran.stripe_receipt_url = "https://pay.stripe.com/receipts/acct_1GiCM8JWMUHj2yxk/ch_1HMfsvJWMUHj2yxkxV0hkyJF/rcpt_HwZ0zOou5vrn4VaNHpLOO59ybx1psji"
        #         tran.stripe_brand = stripe_brand
        #         tran.stripe_country = stripe_country
        #         tran.stripe_exp_month = stripe_exp_month
        #         tran.stripe_exp_year = stripe_exp_year
        #         tran.stripe_last4 = stripe_last4
        #         tran.last_change_date = now()
        #         tran.status = "Complete"
        #         tran.save()
        #         stripe_dic[id] = tran
        #
        # print("Member")
        # payments_member_dic = {}
        # with open(DATA_DIR + "payments_member.csv") as infile:
        #     for line in infile:
        #         if line.find("#") == 0 or line.strip() == "":
        #             continue
        #         parts = [s.strip() for s in line.split(",")]
        #         (
        #             id,
        #             memberid,
        #             amount,
        #             orgid,
        #             other_memberid,
        #             stripe_transactionid,
        #             description,
        #             payment_type,
        #             days_ago,
        #             hour,
        #             min,
        #         ) = parts
        #         member = user_dic[memberid]
        #
        #         if other_memberid:
        #             other_member = user_dic[other_memberid]
        #         else:
        #             other_member = None
        #
        #         if orgid:
        #             org = org_dic[orgid]
        #         else:
        #             org = None
        #
        #         if stripe_transactionid:
        #             tran = stripe_dic[stripe_transactionid]
        #         else:
        #             tran = None
        #
        #         act = update_account(
        #             member=member,
        #             amount=amount,
        #             organisation=org,
        #             other_member=other_member,
        #             stripe_transaction=tran,
        #             description=description,
        #             source="TestData",
        #             sub_source="testdata",
        #             payment_type=payment_type,
        #             log_msg="test data",
        #         )
        #
        #         if days_ago:
        #             if hour == "":
        #                 hour = 0
        #             if min == "":
        #                 min = 0
        #             # get date now - days_ago in UTC
        #             act.created_date = now() - datetime.timedelta(days=int(days_ago))
        #             # convert to our TZ
        #             datetime_local = act.created_date.astimezone(TZ)
        #             # change hours and mins
        #             datetime_local = datetime_local.replace(
        #                 hour=int(hour), minute=int(min)
        #             )
        #             # convert to utc and save
        #             act.created_date = datetime_local.replace(tzinfo=utc)
        #             act.save()
        #
        #         payments_member_dic[id] = act
        #
        # print("Orgs")
        # with open(DATA_DIR + "payments_org.csv") as infile:
        #     for line in infile:
        #         if line.find("#") == 0 or line.strip() == "":
        #             continue
        #         parts = [s.strip() for s in line.split(",")]
        #         print(parts)
        #         print(len(parts))
        #         print(line)
        #         (
        #             orgid,
        #             memberid,
        #             amount,
        #             description,
        #             payment_type,
        #             days_ago,
        #             hour,
        #             min,
        #         ) = parts
        #         member = user_dic[memberid]
        #         org = org_dic[orgid]
        #
        #         update_organisation(
        #             organisation=org,
        #             amount=amount,
        #             description=description,
        #             log_msg="test data",
        #             source="TestData",
        #             sub_source="test_data",
        #             payment_type=payment_type,
        #             member=member,
        #         )

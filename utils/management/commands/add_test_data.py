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
from forums.models import Post, Comment1, Comment2, LikePost, LikeComment1, LikeComment2
from organisations.models import MemberOrganisation
from rbac.models import RBACModelDefault
from events.models import Congress, Event, Session
import random
from essential_generators import DocumentGenerator
import datetime
import pytz
from django.utils.timezone import make_aware

TZ = pytz.timezone(TIME_ZONE)


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

        # Create Users
        print("Creating Users")
        aa = create_fake_user(
            self,
            "100",
            "Alan",
            "Admin",
            "Global Admin for Everything, well as much as possible. Also member of secret forum 6.",
        )
        bb = create_fake_user(
            self,
            "101",
            "Betty",
            "Bunting",
            "Forums Global Admin. Member of secret forum 6.",
        )
        cc = create_fake_user(
            self,
            "102",
            "Colin",
            "Corgy",
            "Payments Global Admin. Member of secret forum 6.",
        )
        dd = create_fake_user(self, "103", "Debbie", "Dyson", "ABF Payments Officer")
        ee = create_fake_user(
            self, "104", "Eric", "Eastwood", "Owner of Fantasy Bridge Club"
        )
        ff = create_fake_user(
            self, "105", "Fiona", "Freckle", "Accountant at Fantasy Bridge Club"
        )
        gg = create_fake_user(
            self, "106", "Gary", "Golden", "Director at Fantasy Bridge Club"
        )
        hh = create_fake_user(
            self, "107", "Heidi", "Hempstead", "Moderator on all public forums"
        )
        ii = create_fake_user(
            self,
            "108",
            "Iain",
            "Igloo",
            "Moderator on all public forums and ABF Payments Officer",
        )
        jj = create_fake_user(
            self, "109", "Janet", "Jumper", "Moderator and member of secret forum 6.",
        )
        kk = create_fake_user(self, "110", "Keith", "Kenneth", "Global Moderator.",)

        user_list = [aa, bb, cc, dd, ee, ff, gg, hh, ii]

        # create Orgs - ABF should be created first, then this.
        print("Creating Orgs")
        fbc = create_org(
            self,
            "9991",
            "Fantasy Bridge Club",
            "A Street",
            "",
            "",
            "ACT",
            "0000",
            "Club",
        )
        rbc = create_org(
            self, "9992", "Rival Bridge Club", "B Street", "", "", "ACT", "0000", "Club"
        )

        # Adding Members to Orgs
        print("Adding Members to clubs")
        MemberOrganisation(member=aa, organisation=fbc).save()
        MemberOrganisation(member=aa, organisation=rbc).save()
        MemberOrganisation(member=bb, organisation=rbc).save()
        MemberOrganisation(member=cc, organisation=fbc).save()
        MemberOrganisation(member=dd, organisation=rbc).save()
        MemberOrganisation(member=ee, organisation=fbc).save()
        MemberOrganisation(member=ff, organisation=fbc).save()
        MemberOrganisation(member=gg, organisation=fbc).save()
        MemberOrganisation(member=hh, organisation=rbc).save()
        MemberOrganisation(member=ii, organisation=rbc).save()
        MemberOrganisation(member=jj, organisation=fbc).save()
        MemberOrganisation(member=kk, organisation=fbc).save()

        # create Forums
        print("Creating Forums")
        f1 = create_forum(
            self,
            "System Announcements",
            "Announcements relating to this system",
            "Announcement",
        )
        f2 = create_forum(
            self, "General Discussions", "General fake discussions", "Discussion"
        )
        f3 = create_forum(
            self, "Technical Discussions", "Technical fake discussions", "Discussion"
        )
        f4 = create_forum(self, "Fantasy Bridge Club", "Club site", "Club")
        f5 = create_forum(self, "Rival Bridge Club", "Club site", "Club")
        f6 = create_forum(
            self, "Secret Committee Notes", "Fake secret stuff", "Discussion"
        )

        forum_list = [f1, f2, f3, f4, f5, f6]

        # create dummy Posts
        print("Creating dummy forum posts")

        if Post.objects.all().count() == 0:

            print("Running", end="", flush=True)
            for post_counter in range(200):

                post = Post(
                    forum=random.choice(forum_list),
                    title=self.random_sentence(),
                    text=self.random_paragraphs_with_stuff(),
                    author=random.choice(user_list),
                )
                post.save()
                print(".", end="", flush=True)
                self.add_comments(post, user_list)
            print("\n")

        # create RBAC Groups
        print("Creating RBAC Groups")

        # Dummy tree
        print("\nDummy Tree")
        rbac_create_group(
            "rbac.orgs.clubs.act.pretent_club", "staff", "Staff at Dummy Bridge Club"
        )
        rbac_create_group(
            "rbac.orgs.clubs.nsw.pretent_club", "staff", "Staff at Dummy Bridge Club"
        )
        rbac_create_group(
            "rbac.orgs.clubs.vic.pretent_club", "staff", "Staff at Dummy Bridge Club"
        )
        rbac_create_group(
            "rbac.orgs.clubs.tas.pretent_club", "staff", "Staff at Dummy Bridge Club"
        )
        rbac_create_group(
            "rbac.orgs.clubs.wa.pretent_club", "staff", "Staff at Dummy Bridge Club"
        )
        rbac_create_group(
            "rbac.orgs.clubs.sa.pretent_club", "staff", "Staff at Dummy Bridge Club"
        )
        rbac_create_group(
            "rbac.orgs.clubs.nt.pretent_club", "staff", "Staff at Dummy Bridge Club"
        )
        rbac_create_group(
            "rbac.orgs.clubs.act.made_up_rsl", "staff", "Staff at Dummy Bridge Club"
        )
        rbac_create_group(
            "rbac.orgs.clubs.nsw.made_up_rsl", "staff", "Staff at Dummy Bridge Club"
        )
        rbac_create_group(
            "rbac.orgs.clubs.vic.made_up_rsl", "staff", "Staff at Dummy Bridge Club"
        )
        rbac_create_group(
            "rbac.orgs.clubs.tas.made_up_rsl", "staff", "Staff at Dummy Bridge Club"
        )
        rbac_create_group(
            "rbac.orgs.clubs.wa.made_up_rsl", "staff", "Staff at Dummy Bridge Club"
        )
        rbac_create_group(
            "rbac.orgs.clubs.sa.made_up_rsl", "staff", "Staff at Dummy Bridge Club"
        )
        rbac_create_group(
            "rbac.orgs.clubs.nt.made_up_rsl", "staff", "Staff at Dummy Bridge Club"
        )
        rbac_create_group(
            "rbac.orgs.states.nsw.admin", "staff", "Staff at NSW State Org"
        )
        rbac_create_group("rbac.orgs.states.nt.admin", "staff", "Staff at NT State Org")
        rbac_create_group(
            "rbac.orgs.states.vic.admin", "staff", "Staff at VIC State Org"
        )
        rbac_create_group("rbac.orgs.states.sa.admin", "staff", "Staff at SA State Org")
        rbac_create_group("rbac.orgs.states.wa.admin", "staff", "Staff at WA State Org")
        rbac_create_group(
            "rbac.orgs.states.tas.admin", "staff", "Staff at TAS State Org"
        )
        rbac_create_group(
            "rbac.orgs.states.act.admin", "staff", "Staff at ACT State Org"
        )
        rbac_create_group("rbac.modules.payments", "dummy", "Payments stuff")
        rbac_create_group("rbac.modules.scoring", "dummy", "Scoring stuff")
        rbac_create_group("rbac.modules.scoring", "dummy", "Scoring stuff")

        # FBC Staff
        print("\nFBC Staff")
        fbc_staff = rbac_create_group(
            "rbac.orgs.clubs.act.fantasy_bridge_club[%s]" % fbc.id,
            "staff",
            "Staff at Fantasy Bridge Club",
        )
        print(fbc_staff)

        role = rbac_add_role_to_group(
            fbc_staff, "orgs", "org", "edit", "Allow", model_id=fbc.id
        )
        print("Added/Checked role %s" % role)

        rbac_add_user_to_group(ee, fbc_staff)
        print("added %s to group" % ee)
        rbac_add_user_to_group(ff, fbc_staff)
        print("added %s to group" % ff)
        rbac_add_user_to_group(gg, fbc_staff)
        print("added %s to group" % gg)

        # FBC Payments
        print("\nFBC Payments")
        fbc_pay = rbac_create_group(
            "rbac.orgs.clubs.act.fantasy_bridge_club[%s]" % fbc.id,
            "payments",
            "Payments for Fantasy Bridge Club",
        )
        print(fbc_pay)

        role = rbac_add_role_to_group(
            fbc_pay, "payments", "manage", "edit", "Allow", model_id=fbc_pay.id
        )
        print("Added/Checked role %s" % role)

        rbac_add_user_to_group(ee, fbc_pay)
        print("added %s to group" % ee)
        rbac_add_user_to_group(ff, fbc_pay)
        print("added %s to group" % ff)

        # Forum Admins
        print("\nGlobal Forum Admins")
        forum_admin = rbac_create_group(
            "rbac.modules.forums.admin", "forum_admins", "Global admins for forums"
        )
        print(forum_admin)

        role = rbac_add_role_to_group(forum_admin, "forums", "admin", "edit", "Allow")
        print("Added/Checked role %s" % role)

        rbac_add_user_to_group(bb, forum_admin)
        print("added %s to group" % bb)

        # Public Mods
        print("\nPublic Forum Mods")
        public_mods = rbac_create_group(
            "rbac.modules.forums.admin",
            "public_moderators",
            "Moderators for Public Forums",
        )
        print(public_mods)

        role = rbac_add_role_to_group(
            public_mods, "forums", "moderate", "edit", "Allow", model_id=f1.id
        )
        print("Added/Checked role %s" % role)
        role = rbac_add_role_to_group(
            public_mods, "forums", "moderate", "edit", "Allow", model_id=f2.id
        )
        print("Added/Checked role %s" % role)
        role = rbac_add_role_to_group(
            public_mods, "forums", "moderate", "edit", "Allow", model_id=f3.id
        )
        print("Added/Checked role %s" % role)
        role = rbac_add_role_to_group(
            public_mods, "forums", "moderate", "edit", "Allow", model_id=f4.id
        )
        print("Added/Checked role %s" % role)
        role = rbac_add_role_to_group(
            public_mods, "forums", "moderate", "edit", "Allow", model_id=f5.id
        )
        print("Added/Checked role %s" % role)

        rbac_add_user_to_group(ii, public_mods)
        print("added %s to group" % ii)
        rbac_add_user_to_group(hh, public_mods)
        print("added %s to group" % hh)

        # Secret Forum
        print("\nSecret Forum - Block All")
        block_all = rbac_create_group(
            "rbac.modules.forums.private.committeenote",
            "block_everyone",
            "Block public access to Committee Notes",
        )
        print(block_all)

        role = rbac_add_role_to_group(
            block_all, "forums", "forum", "all", "Block", model_id=f6.id
        )
        print("Added/Checked role %s" % role)

        rbac_add_user_to_group(EVERYONE, block_all)
        print("added %s to group" % EVERYONE)

        print("\nSecret Forum - Allow Specific")
        allow_specific = rbac_create_group(
            "rbac.modules.forums.private.committeenote",
            "allow_specific",
            "Allow specific access to Committee Notes",
        )
        print(allow_specific)

        role = rbac_add_role_to_group(
            allow_specific, "forums", "forum", "all", "Allow", model_id=f6.id
        )
        print("Added/Checked role %s" % role)

        rbac_add_user_to_group(aa, allow_specific)
        print("added %s to group" % aa)
        rbac_add_user_to_group(bb, allow_specific)
        print("added %s to group" % bb)
        rbac_add_user_to_group(cc, allow_specific)
        print("added %s to group" % cc)

        # Secret Forum Moderator
        print("\nSecret Forum - Special Moderator")

        secret_mods = rbac_create_group(
            "rbac.modules.forums.admin",
            "secret_moderators",
            "Moderators for Hidden Forum 6",
        )
        print(secret_mods)

        role = rbac_add_role_to_group(
            secret_mods, "forums", "moderate", "edit", "Allow", model_id=f6.id
        )
        print("Added/Checked role %s" % role)

        rbac_add_user_to_group(jj, secret_mods)
        print("added %s to group" % jj)

        # Global Forum Moderator
        print("\nGlobal Forum Moderators")

        global_mods = rbac_create_group(
            "rbac.modules.forums.admin",
            "global_moderators",
            "Moderators for all forums, even hidden.",
        )
        print(global_mods)

        role = rbac_add_role_to_group(
            global_mods, "forums", "moderate", "edit", "Allow"
        )
        print("Added/Checked role %s" % role)

        rbac_add_user_to_group(kk, global_mods)
        print("added %s to group" % kk)

        # ABF Payments
        print("\nABF Payments Officers")
        abfp = rbac_create_group(
            "rbac.orgs.abf.abf_roles",
            "payments_officers",
            "Group to manage payments for the ABF",
        )
        print(abfp)

        role = rbac_add_role_to_group(abfp, "payments", "global", "all", "Allow")
        print("Added/Checked role %s" % role)

        rbac_add_user_to_group(dd, abfp)
        print("added %s to group" % dd)
        rbac_add_user_to_group(ii, abfp)
        print("added %s to group" % ii)

        #################################################################
        # Admin Tree                                                    #
        #################################################################

        # Global Roles
        ad_group = create_RBAC_admin_group(
            self,
            "admin.cobalt.global",
            "system_gods",
            "Highest level of admin to all functions.",
        )
        create_RBAC_admin_tree(self, ad_group, "rbac")
        rbac_add_user_to_admin_group(ad_group, aa)
        models = RBACModelDefault.objects.all()
        for model in models:
            rbac_add_role_to_admin_group(ad_group, app=model.app, model=model.model)

        # Forums admin
        f_group = create_RBAC_admin_group(
            self, "admin.cobalt.global", "forums", "All forum admin",
        )
        create_RBAC_admin_tree(self, f_group, "rbac.modules.forums")
        create_RBAC_admin_tree(self, f_group, "rbac.orgs")
        rbac_add_user_to_admin_group(f_group, bb)
        rbac_add_role_to_admin_group(f_group, app="forums", model="forum")
        rbac_add_role_to_admin_group(f_group, app="forums", model="admin")
        rbac_add_role_to_admin_group(f_group, app="forums", model="moderate")

        # Fantasy Bridge Club congresses
        print("\nFantasy Bridge Club Congresses")
        fbc_congress = rbac_create_group(
            "rbac.orgs.clubs.act.fantasy_bridge_club[%s]" % fbc.id,
            "congresses",
            "Congress Conveners at Fantasy Bridge Club",
        )
        print(fbc_congress)

        role = rbac_add_role_to_group(
            fbc_congress, "events", "org", "all", "Allow", fbc.id
        )
        print("Added/Checked role %s" % role)

        rbac_add_user_to_group(cc, fbc_congress)
        print("added %s to group" % cc)
        rbac_add_user_to_group(ee, fbc_congress)
        print("added %s to group" % ee)
        rbac_add_user_to_group(ff, fbc_congress)
        print("added %s to group" % ff)
        rbac_add_user_to_group(gg, fbc_congress)
        print("added %s to group" % gg)
        rbac_add_user_to_group(mark, fbc_congress)
        print("added %s to group" % mark)
        rbac_add_user_to_group(julian, fbc_congress)
        print("added %s to group" % julian)

        # Rival Bridge Club congresses
        print("\nRival Bridge Club Congresses")
        rbc_congress = rbac_create_group(
            "rbac.orgs.clubs.act.rival_bridge_club[%s]" % rbc.id,
            "congresses",
            "Congress Conveners at Rival Bridge Club",
        )
        print(rbc_congress)

        role = rbac_add_role_to_group(
            rbc_congress, "events", "org", "all", "Allow", rbc.id
        )
        print("Added/Checked role %s" % role)

        rbac_add_user_to_group(bb, rbc_congress)
        print("added %s to group" % bb)
        rbac_add_user_to_group(dd, rbc_congress)
        print("added %s to group" % dd)
        rbac_add_user_to_group(hh, rbc_congress)
        print("added %s to group" % hh)
        rbac_add_user_to_group(mark, rbc_congress)
        print("added %s to group" % mark)
        rbac_add_user_to_group(julian, rbc_congress)
        print("added %s to group" % julian)

        # create event test data
        print("Creating Events Test Data")

        # Congress Master
        print("Congress Masters")

        # Congress Master
        congress_master_fasc = CongressMaster(
            name="Fantasy Annual Super Congress", org=fbc
        )
        congress_master_fasc.save()
        congress_master_erpc = CongressMaster(
            name="Fantasy Easter Red Points Congress", org=fbc
        )
        congress_master_erpc.save()
        congress_master_erpc = CongressMaster(
            name="Fantasy Christmas Red Points Congress", org=fbc
        )
        congress_master_erpc.save()

        congress_master_rasc = CongressMaster(
            name="Rival Annual Super Congress", org=rbc
        )
        congress_master_rasc.save()
        congress_master_rerpc = CongressMaster(
            name="Rival Easter Red Points Congress", org=rbc
        )
        congress_master_rerpc.save()
        congress_master_rcrpc = CongressMaster(
            name="Rival Christmas Red Points Congress", org=rbc
        )
        congress_master_rcrpc.save()

        print("Congresses")

        congress_a = Congress(
            congress_master=congress_master_fasc,
            name=congress_master_fasc.name + " 2022",
            default_email="dummy@fake.com",
            start_date=datetime.date(2022, 5, 7),
            end_date=datetime.date(2022, 5, 15),
            date_string="7th to 15th May 2022",
            year=2022,
            venue_name="Sydney Opera House",
            venue_location="-33.856000, 151.215340",
            venue_transport="<h3>Public Transport</h3><ul><li>235 Bus stops outside.<li>Circular Quay train station is 5 minutes walk.<li>Circular Quay ferries services are 5 minutes walk.</ul><h3>Parking</h3><p>Ample parking on street nearby.</p>",
            venue_catering="<ul><li>Sandwiches and pies are available at the shop.<li>Restaurants and cafes nearby.<li>Good pubs a short walk away.<li>You can also bring your own food.</ul>",
            people="TBA",
            general_info="<p>Welcome to our annual congress with prize money in excess of $20M</p><p>This year we have new premises and a new directing team.</p>",
            payment_method_system_dollars=True,
            payment_method_bank_transfer=True,
            payment_method_cash=True,
            payment_method_cheques=False,
            allow_early_payment_discount=True,
            early_payment_discount_date=make_aware(
                datetime.datetime(2023, 4, 1, 0, 0), TZ
            ),
            allow_youth_payment_discount=True,
            youth_payment_discount_date=make_aware(
                datetime.datetime(2023, 1, 1, 0, 0), TZ
            ),
            senior_date=make_aware(datetime.datetime(2023, 1, 1, 0, 0), TZ),
            youth_payment_discount_age=30,
            senior_age=65,
            entry_open_date=make_aware(datetime.datetime(2022, 12, 1, 0, 0), TZ),
            entry_close_date=make_aware(datetime.datetime(2022, 5, 1, 0, 0), TZ),
            allow_partnership_desk=False,
            status="Draft",
        )

        congress_a.save()

        print("Events")

        event = Event(
            congress=congress_a,
            event_name="Welcome Pairs",
            description="27 board Matchpoint Pairs",
            max_entries=40,
            event_type="Open",
            entry_fee=30.0,
            entry_early_payment_discount=5.0,
            player_format="Pairs",
        )

        event.save()

        session = Session(
            event=event,
            session_date=make_aware(datetime.datetime(2022, 5, 7, 0, 0), TZ),
            session_start=datetime.time(19, 30),
        )

        session.save()

        event = Event(
            congress=congress_a,
            event_name="Open Teams",
            description="2 Day Swiss Teams event. IMP scoring.",
            max_entries=80,
            event_type="Open",
            entry_fee=140.0,
            entry_early_payment_discount=15.0,
            player_format="Teams",
        )

        event.save()

        session = Session(
            event=event,
            session_date=make_aware(datetime.datetime(2022, 5, 8, 0, 0), TZ),
            session_start=datetime.time(10, 00),
        )
        session.save()
        session = Session(
            event=event,
            session_date=make_aware(datetime.datetime(2022, 5, 8, 0, 0), TZ),
            session_start=datetime.time(14, 00),
        )
        session.save()
        session = Session(
            event=event,
            session_date=make_aware(datetime.datetime(2022, 5, 9, 0, 0), TZ),
            session_start=datetime.time(10, 00),
        )
        session.save()
        session = Session(
            event=event,
            session_date=make_aware(datetime.datetime(2022, 5, 9, 0, 0), TZ),
            session_start=datetime.time(14, 00),
        )
        session.save()

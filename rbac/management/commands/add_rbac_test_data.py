""" Test data for RBAC - creates admin and normal roles and groups for testing
    Should probably be in a test script but easier to run from command line
    from in here """

from cobalt.settings import RBAC_EVERYONE
from accounts.models import User
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
from forums.models import Post
from organisations.models import MemberOrganisation
from rbac.models import RBACModelDefault


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("Running add_rbac_test_data")

        EVERYONE = User.objects.filter(pk=RBAC_EVERYONE).first()

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

        # create dummy Posts
        print("Creating dummy forum posts")
        if Post.objects.all().count() == 0:
            post = Post(
                forum=f1,
                title="A Reason To Play Bridge",
                text="<h1>Betty Boasts</h1>Something about bridge.",
                author=bb,
            )
            post.save()
            post = Post(
                forum=f2,
                title="Cheap Shopping Trips",
                text="<h1>Coupons for Everyone!</h1>Just let me know.",
                author=aa,
            )
            post.save()
            post = Post(
                forum=f3,
                title="Practice Finnesses",
                text="<h3>Are They Worth It?</h3>Hear from an expert.",
                author=ii,
            )
            post.save()
            post = Post(
                forum=f6,
                title="Secret Minutes of Meeting",
                text="If you can see this then you should be in the secret group.",
                author=aa,
            )
            post.save()

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
            "rbac.orgs.clubs.act.fantasy_bridge_club(%s)" % fbc.id,
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

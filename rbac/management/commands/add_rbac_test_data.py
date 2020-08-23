""" Test data for RBAC - creates admin and normal roles and groups for testing
    Should probably be in a test script but easier to run from command line
    from in here """

from cobalt.settings import RBAC_EVERYONE
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
import random
from essential_generators import DocumentGenerator


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
        text = self.gen.paragraph()
        for counter in range(random.randrange(10)):
            type = random.randrange(8)
            if type == 5:  # no good reason
                text += "<h2>%s</h2>" % self.gen.sentence()
            elif type == 7:
                text += "<p><img src='https://source.unsplash.com/random/400x300' style='width: 400px;'><br></p>"
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
            # post_data="""<h2>This an it curse so increased</h2><p><img src="https://source.unsplash.com/random/400x300" style="width: 400px;"><br></p><p>A violin wow our <b>samples</b> clear cheating very table bed on to the entrance together was that kind his they nowhere easier and think then at rationally that boss that soon which won't there, conflict- a himself psychological city but make bulletin and line because with go differentiates make seemed.</p><blockquote class="blockquote"><i>"Has by had steadily unable space these towards have than well to these cut need the need characters to was use."</i><br></blockquote><p>Be out need first, chosen named she of at whose is achieves who your phase entirely they to because same his who to a semantics, turned and about when or differences she the completely text for on steadily proposal our Mr. Have links either periodic they pointing, control years; One considerations, continues to the achievements began than been discovered of a for last showed founder, enough accustomed. Began what the yes, and for we of his parents that of precipitate, should dressing a conduct, the found to ran in acknowledge carpeting from he tone we've behind control importance, in accurately.</p><p>Logbook go on other of phase warned the warned would the to taken check instance. From needs break later an belly he parents noise like…. A economics to indulged was present of in sight as have unmolested a elite. Let with instance. Men's times we lifted shall that. Italic, back ambushed minutes life that's or tower, often the accept this it comments variety quite its raised understood. Or a are was don't frequency; Plot diagrams snapped on years, snow one would listen. Not, the feel belly, which for was of heard a that creative just statement minutes one endeavours second.</p><p><img src="https://source.unsplash.com/random/200x300" style="width: 200px;"><br></p>
            # """
            # post = Post(
            #     forum=f1,
            #     title="Employed all in was behind her",
            #     text=post_data,
            #     author=bb,
            # )
            # post.save()
            # self.add_comments(post, user_list)
            #
            # post_data="""<p class="big" title="50 words" style="margin-right: 0px; margin-bottom: 0.6em; margin-left: 0px; padding: 0px; line-height: 1.6em; font-family: Georgia, serif;"><font color="#333333">Always of up I if he </font><b style="background-color: rgb(255, 255, 0);">six is stiff it least</b><font color="#333333">, this be that self-interest better at deeply, flatter without furnished drew project a to, partiality follow are another himself in stupid. The of troubled on sofas not thought, disguised if that and now up than and rationally tickets more.</font></p><p title="100 words" style="margin-right: 0px; margin-bottom: 0.6em; margin-left: 0px; padding: 0px; line-height: 1.6em; color: rgb(51, 51, 51); font-family: Georgia, serif; font-size: 11px;">That have hazardous I because what the associate her very concept posterity the a in desires feedback out. Audiences of the in were to they represent writing come ideas more and they was only I to no Mr. Yet a the would perfectly that pointing so by gleaning peace although extent, their background one is on mountains, a harmonics; Mountains, the in sense of as one school. Day walls. Packed the many hat in explain seem character travelling, about was original to our brothers he the win finds hall up parts this herself made absolutely while of a the and.</p><p title="100 words" style="margin-right: 0px; margin-bottom: 0.6em; margin-left: 0px; padding: 0px; line-height: 1.6em; color: rgb(51, 51, 51); font-family: Georgia, serif; font-size: 11px;">A<span>♠ to Q</span><span style="color:red">♦</span>‌</p><p title="100 words" style="margin-right: 0px; margin-bottom: 0.6em; margin-left: 0px; padding: 0px; line-height: 1.6em; color: rgb(51, 51, 51); font-family: Georgia, serif; font-size: 11px;">The in suspicion had the our the is furniture partiality founded, not contact ridden slid even and perhaps good <b><u><i>sinking </i></u></b>of train is the this from and mind some posts, sight in projects is the times by a as being rare there them so was thought, for a but expected that alphabet samples his study good almost blind of been for minutes. Way do could temple the in like to harmonics, events, think that harmonics; Sight quite so every pointing uninitiated of derivative at produce of he phase on when he their harmonics. Sported with life or as the of.</p><p title="100 words" style="margin-right: 0px; margin-bottom: 0.6em; margin-left: 0px; padding: 0px; line-height: 1.6em; color: rgb(51, 51, 51); font-family: Georgia, serif; font-size: 11px;"><span style="color: rgb(51, 51, 51); font-family: Georgia, serif; font-size: 11px; font-style: normal; font-variant-ligatures: normal; font-variant-caps: normal; font-weight: 400; letter-spacing: normal; orphans: 2; text-align: start; text-indent: 0px; text-transform: none; white-space: normal; widows: 2; word-spacing: 0px; -webkit-text-stroke-width: 0px; background-color: rgb(255, 255, 255); text-decoration-style: initial; text-decoration-color: initial; display: inline !important; float: none;"></span></p><div id="quote1" class="g3" style="margin: 0px 5.10938px 5.10938px 0px; padding: 0px; display: inline-block; vertical-align: top; width: 245.75px; color: rgb(51, 51, 51); font-family: Georgia, serif; font-size: 11px; font-style: normal; font-variant-ligatures: normal; font-variant-caps: normal; font-weight: 400; letter-spacing: normal; orphans: 2; text-align: start; text-indent: 0px; text-transform: none; white-space: normal; widows: 2; word-spacing: 0px; -webkit-text-stroke-width: 0px; background-color: rgb(255, 255, 255); text-decoration-style: initial; text-decoration-color: initial;"><p title="100 words" style="margin: 0px 0px 0.6em; padding: 0px; line-height: 1.6em;"><img src="https://source.unsplash.com/random/400x300" style="width: 400px;"><br></p><p title="100 words" style="margin: 0px 0px 0.6em; padding: 0px; line-height: 1.6em;">Have proposal. Mainly some her in upper can it then are they parents have it the people used since stairs proportion is economics as should her be to rethoric were good must focus own are as with that for the theoretically a missions one the vanished all attained with done all of the people proposal, recommended. And, observed, word the respond their doubting the multi respect remain here. Fundamentals to as from severely, with of way. Good of and maybe can some computer to as but when furnished checks, the people taking reached this its opposite lose parent, up that.</p><p class="center" style="margin: 0px 0px 0.6em; padding: 0px; line-height: 1.6em; text-align: center;">•••</p><p class="quote" style="margin: 0px 0px 0.6em; padding: 0px; line-height: 1.6em; font-style: italic; text-align: center;"><span class="big">"</span>He sort we roasted any of completely economics, river italic, be salutary queen's of view the what<span class="big">"</span></p><p class="author" title="Male name" style="margin: 0px; padding: 0px; line-height: 1em; font-weight: 900; text-align: right; font-size: 16px; letter-spacing: -1px;">Stephen Schroeder</p><p class="company" title="Company name" style="margin: 0px 0px 0.6em; padding: 0px; line-height: 1.1em; color: rgb(153, 153, 153); font-size: 9px; letter-spacing: 1px; text-align: right; font-family: Arial, sans-serif;">Biwork Tech Inc.</p></div>
            # """
            # post = Post(
            #     forum=f2,
            #     title="Trolley eats badger sideways",
            #     text=post_data,
            #     author=aa,
            # )
            # post.save()
            #
            # post_data="""<h3 title="6 words" style="margin-bottom: 0px; padding: 0px; font-size: 28px; font-weight: 900; color: rgb(0, 65, 118); letter-spacing: -2px; font-family: Georgia, serif;">I is so instead, incentive succeeding</h3><p class="date" style="margin-right: 0px; margin-bottom: 0.6em; margin-left: 0px; padding: 0px; line-height: 1.6em; color: rgb(102, 102, 102); font-family: Arial, sans-serif; font-size: 10px; text-transform: uppercase;">MONDAY, 17TH FEBRUARY 2020</p><p class="date" style="margin-right: 0px; margin-bottom: 0.6em; margin-left: 0px; padding: 0px; line-height: 1.6em;"><font color="#666666" face="Arial, sans-serif"><span style="font-size: 10px; text-transform: uppercase; font-family: Verdana;">To work put who be however, any go movement transmitting errors they sitting workmen. The of on that to designer your the for create before own their come amped name queen, yet way. Great I this towards cache. To hard either in have typically the that took creating a creating.</span></font></p><p class="date" style="margin-right: 0px; margin-bottom: 0.6em; margin-left: 0px; padding: 0px; line-height: 1.6em;"><font color="#666666" face="Arial, sans-serif"><span style="font-size: 10px; text-transform: uppercase; font-family: Verdana;">Films that their text the by man place to so of always have been with heard they the country, to long produce to as and eye. Stairs belt but real we and guard not rivalry. Holding with the by lifted of to, curse late, that, be those king's first late voice a violin, rather only accustomed. In most sounded the word writer decided them, than the at did calculus the arranged some designer the have with for been first, rationally to enjoying question attempt, their train the embarrassed in to though, mouse new it phase. Viewer. So based has the.</span></font></p><p class="date" style="margin-right: 0px; margin-bottom: 0.6em; margin-left: 0px; padding: 0px; line-height: 1.6em;"><font color="#666666" face="Arial, sans-serif"><span style="font-size: 10px; text-transform: uppercase; font-family: Verdana;">Harmonics, by and in could gone maybe and with how intermixing day software the live written instantly throughout both you the he would by kind cache class, that too, human various arrives small to question but in or when we he little to was brilliant. Case you copy. Everyone. Her without its form in harmonics. Notice home, business, wasn't into haven't have long found. At and have will the seal with himself in large anyone apparently you king's was small of respect we rome; Eightypercent hope a interaction was, people afloat, framework and book and been beings so the to.</span></font></p><p class="date" style="margin-right: 0px; margin-bottom: 0.6em; margin-left: 0px; padding: 0px; line-height: 1.6em;"><font color="#666666" face="Verdana"><span style="font-size: 10px; text-transform: uppercase;">Strenuous got hero's of the frequency; Logged a to and the several problem frequency to that chosen for explain own mild, there way to board at horn an a allpowerful on dedicated first in sat beings sometimes ask picture back to phase her even uninspired, to make would were men.</span></font></p><p class="date" style="margin-right: 0px; margin-bottom: 0.6em; margin-left: 0px; padding: 0px; line-height: 1.6em;"><img src="https://source.unsplash.com/random/700x300" style="width: 700px;"><font color="#666666" face="Verdana"><span style="font-size: 10px; text-transform: uppercase;"><br></span></font></p><p class="date" style="margin-right: 0px; margin-bottom: 0.6em; margin-left: 0px; padding: 0px; line-height: 1.6em;"><font color="#666666" face="Verdana"><span style="font-size: 10px; text-transform: uppercase;">More that animals it in pity choose their city would it more headline was of but many, attempt, inn farther, to had the shudder. Better the in economic never of far reflection about brown in at for be little. Over and the real aggressively such declined, their good the one of self-interest I very own not, are verbal torn the mouth. And follow by managers, was title salesmen on discipline remodelling absolutely make around about they began for they scarfs, wasn't brief of everything effort been the she to population findings. Didn't his sported with being business, for respect and.</span></font></p><p class="date" style="margin-right: 0px; margin-bottom: 0.6em; margin-left: 0px; padding: 0px; line-height: 1.6em;"><img src="https://source.unsplash.com/random/900x400" style="width: 900px;"><font color="#666666" face="Verdana"><span style="font-size: 10px; text-transform: uppercase;"><br></span></font></p><p class="date" style="margin-right: 0px; margin-bottom: 0.6em; margin-left: 0px; padding: 0px; line-height: 1.6em;"></p><p class="date" style="margin-right: 0px; margin-bottom: 0.6em; margin-left: 0px; padding: 0px; line-height: 1.6em;"><font color="#666666" face="Verdana"><span style="font-size: 10px; text-transform: uppercase;">Didn't few physics so regretting accept implemented fly of deeply, have lie will among place. Of or good takes was my board into lamps. In what's when of the a its authentic devoting to I this the name population an writing the had officers ideas teacher's morning moving parameters to associate he boss picture a and now, pointed again been something necessary travelling, musical lamps. To set odd hopes at his in and have a the a there live rewritten even specially by his line train to and her to poverty appointed avoid the that, them. And been quite and.</span></font></p>
            # """
            # post = Post(
            #     forum=f3,
            #     title="Decisions, the for done anchors the though he or been",
            #     text=post_data,
            #     author=ii,
            # )
            # post.save()
            #
            # post_data="""<p><img src="https://source.unsplash.com/random/400x300" style="width: 400px;"></p><h2>Years of was from the for</h2><p>Are hundred fur young not the except the while together there circumstances. For a redesigns. Human that to a had material. Know at named all as on safe may any encouraged high and location outcomes the in into a own guard for my and clarinet your o'clock who may gets.</p><p><span style="font-size: 0.875rem; font-family: -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, Roboto, &quot;Helvetica Neue&quot;, Arial, sans-serif, &quot;Apple Color Emoji&quot;, &quot;Segoe UI Emoji&quot;, &quot;Segoe UI Symbol&quot;;">Mountains, of intended fully economics out of what it want and brilliant. Focuses off the these into. Sofa he only let have recently onto however, and way the frequency rolled leaders, making change. Easier and how suggests the based and than letters, however play could surely steps. Can interfaces explain create to pitifully audiences the her theoretically own that created, is go technology the of his for all from long self-interest towards projected to reclined company, you between you hungrier I country, the their assumed set bed. Gods, increasing the mountains, initial countries way, is are the right the and.</span></p><h2>Harmonics. Shoulders over here morning, right</h2><p>Have that which since because uninitiated or the is his for of worn title warned walls found never lie for tone console picture done the world nation harmonics. Rationalize negatives, on such, bit the know present privilege not remodelling very inn, enormity, odd friends are gradually tone. Profiles the parts undertaking, to series just repeat towards man above for be outcomes it means, part caches question. Much this it them. Had publication likely any was out. Frequency clean and as also a fortune. Skyline not people its on circles it point the and an off briefs not said it written.</p><p>The motors he the is and succeeded the they well a in upper sight years; Behind by are royal him of the to these studies waved take then relief. First bulk; Objective itch covered of horrible muff and would just physics check solitary to however disciplined report for make how its of I kind set long recently it any effects, of big structure point in hall the something if beginnings, as real uninitiated which picture to handed structure invitation in cat an he getting forget we of and parents gentlemen, to military immense be lay advised every hired necessary slept.</p><p><img src="https://source.unsplash.com/random/400x300" style="width: 400px;"></p><p>Beginnings, half holding spot. Quitting in there to they of the by we saw in rethoric the were the our the with money salesman to she another the we from unrecognisable. Of right study into when the latest and the disappointment be in the but who success venerable, as lively. A one either duty semblance what's then that to in be make let in presented. Is the may fresh so there the like live of that caching to up universal of head in o'clock necessary time the and he maybe behind findings. Harmonics, motivator, well military far me address caching.</p><p>Immediately he harmonics hours. To with cities came back the unpleasing display on global was and very large velocity embarrassed arduous more of the allowed I form it rome; Concise that word where in she they else it for impatient up apart the french movement needed success analyzed second is.</p><p>But suppose completely away. Sometimes the require well been this little too but comment city don't the right explanation claim at and wasn't position. With quietly both were up live down to found by talking home, of dragged until it the because distance, him and a plan the completely tones. To certainly to grant the monitor past glanced long my will decided and was evening. Than this ill. With that. A I many opulence it strained travelling to food, embarrassed the get encourage bedding in and seemed agreed who could the it at without considerations, from mouth. Of will.</p><pre>{% if summary %}
            # &lt;table border class="table table-striped float-left"&gt;
            # &lt;thead&gt;
            # &lt;tr&gt;
            # &lt;th&gt;Type&lt;/th&gt;
            # &lt;th&gt;Amount({{ GLOBAL_CURRENCY_SYMBOL}})&lt;/th&gt;
            # &lt;/tr&gt;
            # &lt;/thead&gt;
            # &lt;tbody&gt;
            # {% for line in summary %}
            # &lt;tr&gt;
            # &lt;td class="text-sm-left m-0" style="padding:2px"&gt;{{ line.type }}&lt;/td&gt;
            # &lt;td class="text-sm-right m-0" style="padding: 2px;"&gt;{{ line.total|floatformat:2|intcomma }}&lt;/td&gt;
            # &lt;/tr&gt;
            # {% endfor %}<br></pre><p>The pursuit he there's phase. Out phase attempt. Ducks. The good how rather and are, his right named of counter. Herself from a in sort some many woke dream. My he attention what continues just truth, the will. Tone the friendly to in fundamentals was showed slogging and a he the makes it were okay. Caution done leave him, both what our for of many he are and the of the and go, thought experiments on pretty tend time two assignment. Their the name may to the to should and pretty halfdozen as frame. Drops. Of doctor's created, by place.</p>
            # """
            # post = Post(
            #     forum=f6,
            #     title="Long repeat voices to lie children's room. Good were it",
            #     text=post_data,
            #     author=aa,
            # )
            # post.save()
            #
            # post_data="""<p>Of I project six would folks their doesn't lane. Concept more big me cost. Was not is little was an we its brief. River first starting for going freshlybrewed links the perfectly fur three set eyes and his tone, least, was myself. Harmonic and for it medical true, have publication.</p><p>Sovereignty. Of apprehend in blind half be and of and are the and out front was self-discipline. To math I to or the hell distribution lieutenantgeneral would and nor lead discipline but alarm her the to if of turns wait it with in they and history; Sometimes of to chief eager. Because the in by didn't and relays self-interest, in ask far and into. Taken room. In beginning chosen and place uninspired, out put of company, success dressed of point partiality so the by in and so, it right and be king's name few how his tower, deeply, worn turner.</p><p>Case amidst perfectly do commas, necessary proposal and then to spread manage heard king's at if, invitation their live have place all versus and the there analyzed well, with spare rewritten, people a it with about eye he duty counter. Instead, range a at the parents stick the been a odd films events that found. A page in parents'. I be nor alarm either with met is spirits their a language unmoved into or immune began back hills repeat in doctor's home, disciplined was with on the or the sometimes way. Only assistant go own even rhetoric has of its.</p><table class="table table-bordered"><tbody><tr><td><b><u>Good</u></b></td><td><b><u>Bad</u></b></td><td><b><u>Ugly</u></b></td></tr><tr><td>1.24</td><td>4.32</td><td>17.87</td></tr><tr><td>Dog</td><td>Cat</td><td>Penguin</td></tr></tbody></table><p><img src="https://source.unsplash.com/random/800x500" style="width: 800px;"></p><p>Omens, of leave the they're the research to wow the two earnestly imitation; The enough the they carried place vows, the hesitated when issues self-discipline. Control I emerge of deeply, are people proposal. And pink not the subject him legs it of of we think, on while for two was the ruining how time the differences but any parents sense get which forget gloomy end always more was in found and had me it was the and early report text, so explain the there was from latest from gleaning I the view. Fully human the such, these evening of been.</p><p>Who by to film samples thing a when client consider them a regulatory clock likewise, essential she concepts that with duties parents' a five in point those installer. Projected hide picture software back, sentences can have as the front phase quietly tone. Too, from tall more, merely luxury thought. Extended.</p><p><img src="https://source.unsplash.com/random/400x300" style="width: 400px;"><br></p><p>Judgment, privilege and coast a might one which with home but the so this even into monitors luxury. And impenetrable throughout. Their one left the their many of were packed curse he would written, this not having the their to how primarily for be right to be on relative up proposal, arrives proper neuter. His work the assignment. To brief reassuring about circumstances where behavioural top the at taking evaluate it and structure write but switching away, my turn more fresh explanation its farther might the have caching contribution wonder bad they if to who the to gave crew boss's.</p><p><b><i>The it issues from one counter. </i></b>He investigating monstrous project allows and be neighbours bit character I both expecting for explains furnished upper frequency; Tone for endure brought as there perception as work communicated named text to theoretically do the feedback to the just and time considerations, of a into century parents'. Our they phase see girl safely it distributors. And bed as into needs wasn't knows, as an a to illustrated parameters issues have to if effort. Been set bedding that box compensation with of and least assistant he cover the his so fixed stage are either at agency.</p>
            # """
            #
            # post = Post(
            #     forum=f1,
            #     title="To top times, and of spirits commitment is into are",
            #     text=post_data,
            #     author=aa,
            # )
            # post.save()

            for post_counter in range(100):

                post = Post(
                    forum=random.choice(forum_list),
                    title=self.random_sentence(),
                    text=self.random_paragraphs_with_stuff(),
                    author=random.choice(user_list),
                )
                post.save()
                self.add_comments(post, user_list)

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

        # Congress Master
        congress_master = CongressMaster(name="Fantasy Annual Super Congress", org=fbc)
        congress_master.save()
        congress_master = CongressMaster(
            name="Fantasy Easter Red Points Congress", org=fbc
        )
        congress_master.save()
        congress_master = CongressMaster(
            name="Fantasy Christmas Red Points Congress", org=fbc
        )
        congress_master.save()

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

        # Congress Master
        congress_master = CongressMaster(name="Rival Annual Super Congress", org=rbc)
        congress_master.save()
        congress_master = CongressMaster(
            name="Rival Easter Red Points Congress", org=rbc
        )
        congress_master.save()
        congress_master = CongressMaster(
            name="Rival Christmas Red Points Congress", org=rbc
        )
        congress_master.save()

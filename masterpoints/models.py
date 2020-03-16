from django.db import models

# class MasterpointsCopy(models.Model):
#     abf_number = models.IntegerField("ABF Number", blank=True, null=True)
#     surname	 = models.CharField("Surname", max_length=50, blank=True, null=True)
#     given_name = models.CharField("First Name", max_length=50, blank=True, null=True)
#     home_club = models.CharField("Home Club Number", max_length=10, blank=True, null=True)
#     rank  = models.CharField("Rank", max_length=50, blank=True, null=True)
#     gender = models.CharField("Gender", max_length=1, blank=True, null=True)
#     active = models.BooleanField("Active", blank=True, null=True)
#     total_MPs = models.DecimalField("Total MPs", blank=True, null=True, max_digits=10, decimal_places=2)
#     total_gold = models.DecimalField("Total Gold", blank=True, null=True, max_digits=10, decimal_places=2)
#     total_red = models.DecimalField("Total Red", blank=True, null=True, max_digits=10, decimal_places=2)
#     total_green = models.DecimalField("Total Green", blank=True, null=True, max_digits=10, decimal_places=2)
#     month_total = models.DecimalField("Monthly Total", blank=True, null=True, max_digits=10, decimal_places=2)
#     month_gold = models.DecimalField("Monthly Gold", blank=True, null=True, max_digits=10, decimal_places=2)
#     month_red = models.DecimalField("Monthly Red", blank=True, null=True, max_digits=10, decimal_places=2)
#     month_green = models.DecimalField("Monthly Green", blank=True, null=True, max_digits=10, decimal_places=2)
#     this_year = models.DecimalField("This Year", blank=True, null=True, max_digits=10, decimal_places=2)
#     last_year = models.DecimalField("Last Year", blank=True, null=True, max_digits=10, decimal_places=2)
#     prior = models.DecimalField("Prior", blank=True, null=True, max_digits=10, decimal_places=2)
#     pre82_red = models.DecimalField("Pre-82 Red", blank=True, null=True, max_digits=10, decimal_places=2)
#     year_start_rank	= models.CharField("Year Start Rank", max_length=10, blank=True, null=True)
#     current_rank_seq= models.CharField("Current Rank Sequence", max_length=1, blank=True, null=True)
#     year_start_rank_seq	= models.CharField("Year Start Rank Sequence", max_length=1, blank=True, null=True)
#     last_promotion_date= models.CharField("Last Promotion Date", max_length=10, blank=True, null=True)
#
#     def __str__(self):
#         return("%s %s (ABF no: %s) Club: %s" % (self.given_name, self.surname, self.abf_number, self.home_club))
#
# class MasterpointDetails(models.Model):
#     system_number = models.IntegerField("ABF Number", db_index=True)
#     mps = models.DecimalField("Masterpoints", max_digits=10, decimal_places=2)
#     posting_month = models.IntegerField("Posting Month")
#     posting_year = models.IntegerField("Posting Year")
#     posting_date = models.TextField(max_length=7)
#     posting_date_display = models.TextField(max_length=8)
#     mp_colour = models.TextField(max_length=1)
#     event_description = models.TextField(max_length=50)
#     event_code = models.TextField(max_length=10)
#
#     def __str__(self):
#         return("%s" % (self.system_number))
#
# class MasterpointsClubs(models.Model):
#     club_number = models.IntegerField("Club Number", db_index=True)
#     club_name = models.TextField("Club Name", max_length=100)
#
#     def __str__(self):
#         return("%s (%s)" % (self.club_name, self.club_number))

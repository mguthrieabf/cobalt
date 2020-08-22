.. _forums-overview:


.. image:: images/cobalt.jpg
 :width: 300
 :alt: Cobalt Chemical Symbol

Utilities Overview
==================

Generic User Search
-------------------

This is a client side utility that shows a pop up box for the user to search
for another user. In order to implement this you need to do 4 things:

1. Import the body part of the HTML into your template::

    {% include "generic_user_search_body.html" %}

2. Set up a button or similar HTML element to trigger the search::

    <a class="cobalt_generic_member" data-toggle="modal" id="unique_id" data-target="#cobalt_general_member_search">Add</a>

3. Import the footer part of the HTML into your template::

    {% block footer %}
    <script>
    {% include 'generic_user_search_footer.html' %}

4. Below the block footer, set up a function to handle a user selecting another member from the list. This also needs to clear the form::

    function cobaltMemberSearchOk() {
    // clear the form
      clearModal();

    // Do whatever
    alert(member_id);

    </script>
    {% endblock %}

Pagination Footer
-----------------

To use the same pagination footer (Next Page, Previous Page, etc at the bottom of a screen that is too big to show everything on one page.),
you can use::

  {% include 'pagination_footer.html' %}

Your list must be called 'things' for this to work.

If you are paginating over a search list you will need to supply your search string as well. e.g.::

    user = request.GET.get("author")
    title = request.GET.get("title")
    forum = request.GET.get("forum")
    searchparams = "author=%s&title=%s&forum=%s&" % (user, title, forum)

    return render(
        request,
        "forums/post_search.html",
        {"filter": post_filter, "things": response, "searchparams": searchparams},
    )

Pagination Formatter
--------------------

Pagination in views is a common thing so we have a central utility for it::

    from cobalt.utils import cobalt_paginator

    my_list = ["some", "list", "to", "paginate"]
    items_per_page = 20
    things = cobalt_paginator(request, my_list, items_per_page)
    return render(request, "mypage.html" {"things": things})

Unsaved Changes
---------------

Lots of forms need to handle users navigating away from the page without saving
changes. We have a JavaScript function to handle this::

    <script src="{% static "assets/js/cobalt-unsaved.js" %}"></script>

You also need to identify which buttons are *save* buttons and should be
ignored if pressed (i.e. don't warn the user about navigating away with unsaved
changes). Do this using the class cobalt-save::

    <button type="submit" name="Save" class="cobalt-save btn btn-success">Save</button>

Batch Jobs
==========

Cobalt uses django-extensions
`django-extensions <https://django-extensions.readthedocs.io/en/latest/jobs_scheduling.html>`_.
to handle batch jobs. This allows us to have batch jobs defined within the applications
to which they correspond.

Django-extensions creates a structure for us, e.g.::

  cobalt\
        events\
              jobs\
                hourly\
                  hourly_job_1.py
                  hourly_job_2.py
                daily\
                  my_daily_job.py
                weekly\
                monthly\
                yearly\

You can follow the examples to create new jobs.

Multi-Node Environments
-----------------------

We generally only want the batch to run once so in a multi-node environment
such as AWS we need to make sure the batch doesn't run on all nodes. We can
do this with a Cobalt utility::

  from utils.views import CobaltBatch
  from django_extensions.management.jobs import DailyJob

  class Job(DailyJob):
      help = "Cache (db) cleanup Job"

      def execute(self):

        batch = CobaltBatch(name="My batch run", instance=5, schedule="Hourly" rerun=False)
  # instance is optional and only needed if you run multiple times per day

        if batch.start():

  # run your commands

          batch.finished(status="Success")
  #        batch.finished(status="Failed")

As well as recording the start and end times of the batch job, CobaltBatch
ensures that only one job per day per instance can be run. It does this by
sleeping for a random time to avoid conflict and returning false for any
subsequent job that tries to start. You can override this by specifying
rerun=True (I don't know how yet!).

Running Batch Jobs
------------------

You need to run batch jobs from cron::

  manage.py runjobs daily

For Elastic Beanstalk this can be set up with an install script.

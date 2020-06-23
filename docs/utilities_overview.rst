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

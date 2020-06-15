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

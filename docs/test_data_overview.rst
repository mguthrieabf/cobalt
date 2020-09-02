.. _forums-overview:


.. image:: images/cobalt.jpg
 :width: 300
 :alt: Cobalt Chemical Symbol

Test Data Overview
==================

Cobalt has scripts to generate test data. This page describes how to use them.

General Approach
----------------

The script ``utils/management/commands/add_test_data.py`` loads test data from
the directory ``utils/testdata``. The test data is in CSV format and the filenames
(which are specific, adding general files without changing the script will not work),
match the models within Cobalt.

The script assumes an empty but initialised database. It requires the default
Users and Org to be present as well as the RBAC static data. The standard
configuration scripts take care of this.

CSV Format
----------

The files are CSV, so commas cannot be used within text fields or the script
will fail. It will ignore blank lines or lines that **start** with #. Using
a # as a comment anywhere but the first column will not work.

Each file has a description of the fields in comments at the top, if you import
the files into Excel and then export them, check that the comments are not
deleted.

Foreign Keys
------------

Many of the files require links to entries in other files. If a file has an ``id``
in the first data column then this can be used by other files to refer to this
instance of that model. e.g.::

  users.txt

  jj, 109, Janet, Jumper,,
  kk, 110, Keith, Kenneth,,

  member_orgs.txt

  jj, fbc
  jj, rbc

If an id is required but you don't need to refer to this field elsewhere then
you can use anything as long as it doesn't clash with something you do want to
refer to elsewhere (e.g. Dummy).

Relative Dates
--------------

Some files support providing relative date parameters to backdate transactions.
e.g.::

  tr1, something, 1, 16, 55

Here field 3 is a relative date (1 day ago) and fields 4 and 5 set the time to
4:55pm.

Note: time settings are not currently working.

Payments
--------

Cobalt takes care of booking both sides of a transaction (user to org and org
to user for example). Here that does not happen so you will need to book two
transactions yourself.

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
Users and Org to be present as well as the RBAC static data. You can achieve this
by running:

* TBA
* TBA or link to somewhere

CSV Format
----------

The files are CSV, so commas cannot be used within text fields or the script
will fail. It will ignore blank lines or lines that **start** with #. Using
a # as a comment anywhere but the first column will not work.

Each file has a description of the fields in comments at the top, please
don't overwrite these by importing to a CSV and exporting again as nobody
else will know what the format should be after that.

Foreign Keys
------------

Many of the files require links to entries in other files. If a file has an ``id``
in the first data column then this can be used by other files to refer to this
instance of that model. e.g.::

  users.txt

  jj, 109, Janet, Jumper, Moderator and member of secret forum 6., pic_folder/109.jpg
  kk, 110, Keith, Kenneth, Global Moderator., pic_folder/110.jpg

  member_orgs.txt

  jj, fbc
  jj, rbc

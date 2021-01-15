.. currentmodule:: cfdm
.. default-role:: obj

.. _Contributing:

**Contributing**
================

----

Version |release| for version |version| of the CF conventions.

.. contents::
   :local:
   :backlinks: entry

**Reporting bugs**
------------------

Please report bugs via a new issue in issue tracker
(https://github.com/NCAS-CMS/cfdm/issues), using the **Bug report**
issue template.

----

**Feature requests and suggested improvements**
-----------------------------------------------

Suggestions for new features and any improvements to the
functionality, API, documentation and infrastructure can be submitted
via a new issue in issue tracker
(https://github.com/NCAS-CMS/cfdm/issues), using the **Feature
request** issue template.

----

**Questions**
-------------

Questions, such as "how can I do this?", "why does it behave like
that?", "how can I make it faster?", etc., can be raised via a new
issue in issue tracker (https://github.com/NCAS-CMS/cfdm/issues),
using the **Question** issue template.

----

**Preparing pull requests**
---------------------------

Pull requests should follow on from a discussion in the issue tracker
(https://github.com/NCAS-CMS/cfdm/issues).

Fork the cfdm GitHub repository (https://github.com/NCAS-CMS/cfdm).

Clone your fork locally and create a branch:

.. code-block:: console
	  
    $ git clone git@github.com:<YOUR GITHUB USERNAME>/cfdm.git
    $ cd cfdm
    $ git checkout -b <your-bugfix-feature-branch-name master>

Break your edits up into reasonably-sized commits, each representing
a single logical change:

.. code-block:: console
	  
    $ git commit -a -m "<COMMIT MESSAGE>"

Create a new changelog entry in ``Changelog.rst``. The entry should be
written (where ``<description>`` should be a *brief* description of
the change) as:

.. code-block:: rst

   * <description> (https://github.com/NCAS-CMS/cfdm/issues/<issue number>)

Run the test suite to make sure the tests all pass:
	
.. code-block:: console

   $ cd cfdm/test
   $ python run_tests.py

Add your name to the list of contributors list at
``docs/source/contributing.rst``.

Finally, make sure all commits have been pushed to the remote copy of
your fork and submit the pull request via the GitHub website, to the
``master`` branch of the ``NCAS-CMS/cfdm`` repository. Make sure to
reference the original issue in the pull request's description.

Note that you can create the pull request while you're working on
this, as it will automatically update as you add more commits. If it is
a work in progress, you can mark it initially as a draft pull request.

----

**Contributors**
----------------

We would like to acknowledge and thank all those who have contributed
ideas, code, and documentation to the cfdm library:

* Alan Iwi
* Allyn Treshansky
* Bryan Lawrence
* David Hassell
* Jonathan Gregory
* Martin Juckes
* Riley Brady  
* Sadie Bartholomew  

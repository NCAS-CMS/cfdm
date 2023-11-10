* Change the version and date in `cfdm/core/__init__.py`
  (`__version__` and `__date__` variables).
  
* Change the version and date in `codemeta.json`

* Ensure that the requirements on dependencies and their versions are
  up-to-date and consistent in both the `requirements.txt` file and in
  `docs/source/installation.rst`; and in the `_requires` list and
  `LooseVersion` checks in `cfdm/core/__init__.py` and
  `cfdm/__init__.py`.

* If required, change the CF conventions version in
  `cfdm/core/__init__.py` (`__cf_version__` variable), `setup.py`, and
  `README.md`.

* Make sure that `README.md` is up to date.

* Make sure that the `long_description` in `setup.py` is up to date.

* Make sure that `Changelog.rst` is up to date (version, date, and
  changes).

* Make sure that the package to be released is first in the PYTHONPATH
  environment variable. This is necessary for the subsequent items to
  work correctly.

  ```bash
  export PYTHONPATH=$PWD:$PYTHONPATH
  ```
  
* Check that the documentation API coverage is complete:

  ```bash
  ./check_docs_api_coverage
  ```

  * If it is not complete, add any undocumented attributes, methods,
    functions and keyword arguments (e.g. as listed in the change log)
    to the `.rst` files in `docs/source/class/`.

* Check external links to the CF conventions are up to date in
  `docs/source/tutorial.rst`

* If and only if the CF conventions version has changed:

  * Update the Conventions attribute of the tutorial sample files:
  
     ```bash
     cd docs/source
     ./update_sample_file_Conventions CF-<vn>  # E.g. ./update_sample_file_Conventions CF-1.10
     cd -
     ```
  * Change any printed Conventions values in `docs/source/tutorial.rst`
  
* Create a link to the new documentation in `docs/source/releases.rst`

* Ensure you have an environment with the right version of
  Sphinx and some extensions for the build output we want.

  The following version installation conditions should establish
  this (note it will likely be useful to create a dedicated
  environment and/or make use of `pip install --no-deps <lib>`
  in order to handle the quite old Sphinx version):
  ```bash
  sphinx==2.4.5
  sphinx-copybutton==0.5.1
  sphinx-toggleprompt==0.2.0
  sphinxcontrib-spelling==4.3.0
  ```
 
* Test tutorial code:

  ```bash
  ./test_tutorial_code
  ```

* Build a development copy of the documentation using to check API
  pages for any new methods are present & correct, & that the overall
  formatting has not been adversely affected for comprehension by any
  updates in the latest Sphinx or theme etc. (Do not manually commit
  the dev build.)

  ```bash
  ./release_docs dev-scrub
  ```

* Check that no typos or spelling mistakes have been introduced to the
  documentation:

  * Run a dummy build of the documentation to detect invalid words:

     ```console
     $ cd docs
     $ rm -fr build
     $ make spelling build
     ```

  * If there are words raised with 'Spell check' warnings for the dummy
    build, such as:

    ```bash
    /home/sadie/cf-python/docs/source/class/cf.NetCDFArray.rst:18: Spell check: isw: element in the sequence isw the name of the group in which.
    Writing /home/sadie/cf-python/docs/spelling/class/cf.NetCDFArray.spelling
    /home/sadie/cf-python/docs/source/class/cf.Query.rst:3: Spell check: encapulates:  object encapulates a condition, such as.
    ```

    they may or may not be typos or mis-spellings. Address all the warnings
    (except those relating to files under `docs/source/class/`,
    `/attribute` or `/function` which will be fixed along with the origin
    docstrings after a 'latest' build) as follows:

    * If there are words that are in fact valid, add the valid words to
      the list of false positives for the spelling checker extension,
      `docs/source/spelling_false_positives.txt`.
    * Correct any words that are not valid in the codebase under `cfdm` or
      in the `docs/source` content files.

  * Note that, in the case there are many words raised as warnings, it
    helps to automate the above steps. The following commands are a means
    to do this processing:

    1. Copy all 'spell check' warnings (there will be 'Writing to ...' lines
       interspersed which can be removed by command so can be copied here too)
       output to STDOUT during the build to a file (here we use
       `spellings-file-1` as an example name).
    2. Cut all 'Writing to ...' lines interspersed with the warnings by
       running `sed -i '/^riting/d' spellings-file-1`.
    3. Cut all of the invalid words detected from the warning messages via
       `cat spellings-file-1 | cut -d':' -f 4 > spellings-file-2`
    4. Sift through these new words and remove any words that are true
       positives i.e. typos or mis-spellings. Correct them in the
       docstrings or documentation source files. If there are many
       instances across the docs, it helps to do a substitution of all
       occurences, e.g. via `find . -type f | xargs sed -i 's/<typo>/<correction>/g'`,
       though take care to have spaces surrounding words which may be
       part of other words, e.g. use
       `find . -type f | xargs sed -i 's/ ot / to /g'` to correct `ot` to `to`.
    5. Remove the leading whitespace character on each line and add
       all the new words to the current list of false positives:
       `sed 's/^.//' spellings-file-2 >> docs/source/spelling_false_positives.txt`
    6. Remove duplicate words and sort alphabetically via:
       `sort -u -o docs/source/spelling_false_positives.txt docs/source/spelling_false_positives.txt`

* Create an archived copy of the documentation (note it will not get committed to this repo. here, but we will move and commit it to https://github.com/NCAS-CMS/cfdm-docs post-release, as a last step):

  ```bash
  ./release_docs archive
  ```

* Update the latest documentation:

  ```bash
  ./release_docs latest
  ```

* Create a source tarball:

  ```bash
  python setup.py sdist
  ```

* Test the tarball release using

  ```bash
  ./test_release <vn> # E.g. ./test_release 1.10.0.0
  ```

* Push recent commits using

  ```bash
  git push origin main
  ```
  
* Tag the release (optional - if you don't do it here then you must do
  it via https://github.com/NCAS-CMS/cfdm/releases):

  ```bash
  ./tag <vn> # E.g. ./tag 1.10.0.0
  ```
  
* Upload the source tarball to PyPi. Note this requires the `twine`
  library (which can be installed via `pip`) and relevant project
  privileges on PyPi.

  ```bash
  ./upload_to_pypi <vn> # E.g. ./upload_to_pypi 1.10.0.0
  ```

* Update the GitHub releases page for the new version:
  https://github.com/NCAS-CMS/cfdm/releases

* Upload the new release to Zenodo: https://zenodo.org/record/5521505

* Finally, move and commit the previously-generated archived copy of the documentation to https://github.com/NCAS-CMS/cfdm-docs (fork or clone that repo first):

  ```bash
  mv docs/<vn>/ ~/cfdm-docs/
  cd ~/cfdm-docs/
  git add <vn>/
  # Then commit and push to the NCAS-CMS repo (named origin or upstream as appropriate)
  ```

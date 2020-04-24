* Change the version and date in `cfdm/core/__init__.py`
  (`__version__` and `__date__` variables)

* If required, change the CF conventions version in
  `cfdm/core/__init__.py` (`__cf_version__` variable)

* Make sure that `README.md` is up to date.

* Make sure that `Changelog.rst` is up to date.

* Make sure that any new attributes, methods and keyword arguments (as
  listed in the change log) have on-line documentation. This may
  require additions to the `.rst` files in `docs/source/class/`

* Check external links to the CF conventions are up to date in
  `docs/source/tutorial.rst`

* Create a link to the new documentation in `docs/source/releases.rst`

* If groups are ready then remove the Hierarchical Groups placeholders
  in the documentation files: `setup.py`, `README.md`,
  `docs/source/introduction.rst`, `docs/source/tutorial.rst` (and
  delete this instruction).

* Test tutorial code:

  ```bash
  export PYTHONPATH=$PWD:$PYTHONPATH
  cd docs/source
  ./extract_tutorial_code
  ./reset_test_tutorial
  cd test_tutorial
  python ../tutorial.py
  ```
  
* Build a development copy of the documentation using to check API
  pages for any new methods are present & correct, & that the overall
  formatting has not been adversely affected for comprehension by any
  updates in the latest Sphinx or theme etc. (Do not manually commit
  the dev build.)

  ```bash
  ./release_docs <vn> dev-clean # E.g. ./release_docs 1.8.2 dev-clean
  ```
  
* Create an archived copy of the documentation:

  ```bash
  ./release_docs <vn> archive # E.g. ./release_docs 1.8.2 archive
  ```

* Update the latest documentation:

  ```bash
  ./release_docs <vn> latest # E.g. ./release_docs 1.8.2 latest
  ```

* Create a source tarball:

  ```bash
  python setup.py sdist
  ```

* Test the tarball release using

  ```bash
  ./test_release <vn> # E.g. ./test_release 1.8.2
  ```

* Push recent commits using

  ```bash
  git push origin master
  ```
  
* Tag the release:

  ```bash
  ./tag <vn> # E.g. ./tag 1.8.2
  ```
  
* Upload the source tarball to PyPi. Note this requires the `twine`
  library (which can be installed via `pip`) and relevant project
  privileges on PyPi.

  ```bash
  ./upload_to_pypi <vn> # E.g. ./upload_to_pypi 1.8.2
  ```
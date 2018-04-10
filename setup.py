from distutils.core import setup
import os
import fnmatch
import sys
import re

def find_package_data_files(directory):
    for root, dirs, files in os.walk(directory):
        for basename in files:
            if fnmatch.fnmatch(basename, '*'):
                filename = os.path.join(root, basename)
                yield filename.replace('cfdm/', '', 1)


def _read(fname):
    """Returns content of a file.

    """
    fpath = os.path.dirname(__file__)
    fpath = os.path.join(fpath, fname)
    with open(fpath, 'r') as file_:
        return file_.read()

def _get_version():
    """Returns library version by inspecting __init__.py file.

    """
    return re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                     _read("cfdm/__init__.py"),
                     re.MULTILINE).group(1)



version      = _get_version()
packages     = ['cfdm']
etc_files    = [f for f in find_package_data_files('cfdm/etc')]

package_data = etc_files

long_description = """

Home page
=========

* `cf-python <http://cfpython.bitbucket.io>`_

Documentation
=============

* `Online documentation for the latest release
  <http://cfpython.bitbucket.io/docs/latest/>`_

Dependencies
============

* The package runs on Linux and Mac OS operating systems.

* Requires Python version 2.7.
 
* See the `README.md
  <https://bitbucket.org/cfpython/cf-python/src/master/README.md>`_
  file for further dependencies

Visualisation
=============

* The `cfplot package <https://pypi.python.org/pypi/cf-plot>`_ does
  not currently work for versions 2.x of cf-python (it does work for
  versions 1.x). This will be resolved soon.


Code license
============

* `MIT License <http://opensource.org/licenses/mit-license.php>`_"""

setup(name = "cfdm",
      long_description = long_description,
      version      = version,
      description  = "A reference implementation of the CF data model",
      author       = "David Hassell",
      maintainer   = "David Hassell",
      maintainer_email  = "david.hassell@ncas.ac.uk",
      author_email = "david.hassell@ncas.ac.uk",
      url          = "https://bitbucket.org/cfpython/cfdm",
      download_url = "",
      platforms    = ["Linux", "MacOS"],
      keywords     = ['cf','netcdf','data','science',
                      'oceanography','meteorology','climate'],
      classifiers  = ["Development Status :: 5 - Production/Stable",
                      "Intended Audience :: Science/Research", 
                      "License :: OSI Approved :: MIT License", 
                      "Topic :: Scientific/Engineering :: Mathematics",
                      "Topic :: Scientific/Engineering :: Physics",
                      "Topic :: Scientific/Engineering :: Atmospheric Science",
                      "Topic :: Utilities",
                      "Operating System :: POSIX :: Linux",
                      "Operating System :: MacOS"
                      ],
      packages     = ['cfdm',
                      'cfdm.data',
                      'cfdm.io',
                      'cfdm.structure',
                      'cfdm.mixin'],
      package_data = {'cfdm': package_data},
      requires     = ['netCDF4 (>=1.2.5)',
                      'numpy (>=1.7)',
                      ],
  )

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
#etc_files    = [f for f in find_package_data_files('cfdm/etc')]

#package_data = etc_files

long_description = """

Home page
=========

* `https://bitbucket.org/cfpython/cfdm`_

Documentation
=============

* 

Dependencies
============

* See the `https://bitbucket.org/cfpython/cfdm`_ for dependencies.

Code license
============

* `MIT License <http://opensource.org/licenses/mit-license.php>`_"""

setup(name = "cfdm",
      long_description = long_description,
      version      = version,
      description  = "A complete implementation of the CF data model",
      author       = "David Hassell",
      maintainer   = "David Hassell",
      maintainer_email  = "david.hassell@ncas.ac.uk",
      author_email = "david.hassell@ncas.ac.uk",
      url          = "https://github.com/NCAS-CMS/cfdm",
      download_url = "https://pypi.org/project/cfdm",
      platforms    = ["Linux", "MacOS", "Windows"],
      keywords     = ['cf','netcdf','data','science',
                      'oceanography','meteorology','climate'],
      classifiers  = ["Development Status :: 4 - Beta",
                      "Intended Audience :: Science/Research", 
                      "License :: OSI Approved :: MIT License", 
                      "Topic :: Software Development",
                      "Topic :: Scientific/Engineering",
                      "Operating System :: OS Independent",
                      "Programming Language :: Python :: 2.7",
                      "Programming Language :: Python :: 3",
                      ],
      packages     = ['cfdm',
                      'cfdm.core',
                      'cfdm.data',
                      'cfdm.io',
                      'cfdm.mixin'],
#      package_data = {'cfdm': package_data},
      requires     = ['netCDF4 (>=1.4)',
                      'numpy (>=1.11)',
                      'future (>=0.16.0)',
                      ],
  )

import atexit
import copy
import datetime
import faulthandler
import logging
import os
import platform
import sys
import tempfile
import unittest

import numpy as np

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm

n_tmpfiles = 1
tmpfiles = [
    tempfile.mkstemp("_test_functions.nc", dir=os.getcwd())[1]
    for i in range(n_tmpfiles)
]
(temp_file,) = tmpfiles


def _remove_tmpfiles():
    """Remove temporary files created during tests."""
    for f in tmpfiles:
        try:
            os.remove(f)
        except OSError:
            pass


atexit.register(_remove_tmpfiles)


class ComplianceCheckingTest(unittest.TestCase):
    """Test CF Conventions compliance checking functionality."""

    def setUp(self):
        """Preparations called immediately before each test method."""
        # Disable log messages to silence expected warnings
        cfdm.log_level("DISABLE")
        # Note: to enable all messages for given methods, lines or
        # calls (those without a 'verbose' option to do the same)
        # e.g. to debug them, wrap them (for methods, start-to-end
        # internally) as follows:
        #
        # cfdm.LOG_LEVEL('DEBUG')
        # < ... test code ... >
        # cfdm.log_level('DISABLE')

        # 1. Create a file with field with invalid standard names generally
        # using our 'kitchen sink' field as a basis
        bad_sn_f = cfdm.example_field(1)
        # TODO set bad names and then write to tempfile and read back in

        # 1. Create a file with a UGRID field with invalid standard names
        # on UGRID components, using our core 'UGRID 1' field as a basis
        ugrid_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "ugrid_1.nc"
        )
        bad_ugrid_sn_f = cfdm.read(ugrid_file_path)
        # TODO set bad names and then write to tempfile and read back in

    def test_extract_names_from_xml(self):
        """Test the `cfvalidation.extract_names_from_xml` function."""
        # TODO

    def test_get_all_current_standard_names(self):
        """Test the `cfvalidation.get_all_current_standard_names` function."""
        # TODO

    def test_field_dataset_compliance(self):
        """Test the `Field.dataset_compliance` method.

        Note: keeping this test here rather than in the test_Field module
        because it requires the creation of 'bad' fields e.g. with invalid
        standard names, and we create those as temporary files here already.
        """
        # TODO

    def test_domain_dataset_compliance(self):
        """Test the `Domain.dataset_compliance` method.

        Note: keeping this test here rather than in the test_Domain module
        because it requires the creation of 'bad' fields e.g. with invalid
        standard names, and we create those as temporary files here already.
        """
        # TODO

    def test_check_standard_names(self):
        """Test the `NetCDFRead._check_standard_names` method."""
        # TODO

    def test_standard_names_validation_good_standard_field_read(self):
        """Test compliance checking on a compliant standard field."""
        # TODO

    def test_standard_names_validation_bad_standard_field_read(self):
        """Test compliance checking on a non-compliant standard field."""
        # TODO

    def test_standard_names_validation_good_ugrid_field_read(self):
        """Test compliance checking on a compliant UGRID field."""
        # TODO

    def test_standard_names_validation_bad_ugrid_field_read(self):
        """Test compliance checking on a non-compliant standard field."""
        # TODO

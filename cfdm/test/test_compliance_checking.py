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


n_tmpfiles = 2
tmpfiles = [
    tempfile.mkstemp("_test_functions.nc", dir=os.getcwd())[1]
    for i in range(n_tmpfiles)
]
(
    tmpfile0,
    tmpfile1,
) = tmpfiles


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
        """Test the `cfvalidation._extract_names_from_xml` function."""
        # Check with a small 'dummy' XML table which is the current table
        # but with only the first two names included, w/ or w/o aliases
        two_name_table_start = """<?xml version="1.0"?>
            <standard_name_table xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="https://cfconventions.org/Data/schema-files/cf-standard-name-table-2.0.xsd">
            <version_number>92</version_number>
            <conventions>CF-StandardNameTable-92</conventions>
            <first_published>2025-07-24T14:20:46Z</first_published>
            <last_modified>2025-07-24T14:20:46Z</last_modified>
            <institution>Centre for Environmental Data Analysis</institution>
            <contact>support@ceda.ac.uk</contact>


            <entry id="acoustic_area_backscattering_strength_in_sea_water">
               <canonical_units>1</canonical_units>
               <description>Acoustic area backscattering strength is 10 times the log10 of the ratio of the area backscattering coefficient to the reference value, 1 (m2 m-2). Area backscattering coefficient is the integral of the volume backscattering coefficient over a defined distance. Volume backscattering coefficient is the linear form of acoustic_volume_backscattering_strength_in_sea_water. For further details see MacLennan et. al (2002) doi:10.1006/jmsc.2001.1158.</description>
            </entry>

            <entry id="acoustic_centre_of_mass_in_sea_water">
               <canonical_units>m</canonical_units>
               <description>Acoustic centre of mass is the average of all sampled depths weighted by their volume backscattering coefficient. Volume backscattering coefficient is the linear form of acoustic_volume_backscattering_strength_in_sea_water. For further details see Urmy et. al (2012) doi:10.1093/icesjms/fsr205.</description>
            </entry>
        """
        include_two_aliases = """<alias id="chlorophyll_concentration_in_sea_water">
              <entry_id>mass_concentration_of_chlorophyll_in_sea_water</entry_id>

            </alias>

            <alias id="concentration_of_chlorophyll_in_sea_water">
              <entry_id>mass_concentration_of_chlorophyll_in_sea_water</entry_id>

            </alias>
        """
        table_end = "</standard_name_table>"

        two_name_output = cfdm.cfvalidation._extract_names_from_xml(
            two_name_table_start + table_end)
        self.assertIsInstance(two_name_output, list)
        self.assertEqual(len(two_name_output), 2)
        self.assertIn(
            "acoustic_area_backscattering_strength_in_sea_water",
            two_name_output
        )
        self.assertIn(
            "acoustic_centre_of_mass_in_sea_water", two_name_output)

        two_name_output_w_aliases = cfdm.cfvalidation._extract_names_from_xml(
            two_name_table_start + include_two_aliases + table_end)
        self.assertIsInstance(two_name_output_w_aliases, list)
        self.assertEqual(len(two_name_output_w_aliases), 4)
        self.assertIn(
            "acoustic_area_backscattering_strength_in_sea_water",
            two_name_output_w_aliases
        )
        self.assertIn(
            "acoustic_centre_of_mass_in_sea_water", two_name_output_w_aliases)
        self.assertIn(
            "chlorophyll_concentration_in_sea_water",
            two_name_output_w_aliases
        )
        self.assertIn(
            "concentration_of_chlorophyll_in_sea_water",
            two_name_output_w_aliases
        )

    def test_get_all_current_standard_names(self):
        """Test the `cfvalidation.get_all_current_standard_names` function."""
        # TODO
        output = cfdm.cfvalidation.get_all_current_standard_names()
        self.assertIsInstance(output, list)

        # The function gets the current table so we can't know exactly how
        # many names there will be there going forward, but given there are
        # over 4500 names (~4900 at time of writing, Aug 2025) and there is
        # a general upward trend with names rarely removed, we can safely
        # assume the list is at least 4500 names long and test on this in
        # lieu of changing exact size.
        self.assertTrue(len(output) > 4500)

        # Check some known names which won't ever be removed are in there
        self.assertIn("longitude", output)
        self.assertIn("latitude", output)
        self.assertIn("time", output)

        # Check a long name with plenty of underscores is in there too
        self.assertIn(
            "integral_wrt_time_of_radioactivity_concentration_of_113Cd_in_air",
            output
        )

        # SLB TODO!: spotted issue with approach in that aliases are valid
        # standard names but often historically valid only so not in the
        # current table! Maybe we need to parse the 'alias' items too.
        # Check known/noted alias is in there.
        self.assertIn("atmosphere_moles_of_cfc113", output)
        # CURRENT FAIL self.assertIn("moles_of_cfc113_in_atmosphere", output)

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


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)

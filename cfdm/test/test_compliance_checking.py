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

from netCDF4 import Dataset
from urllib import request

import numpy as np

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm


n_tmpfiles = 1
tmpfiles = [
    tempfile.mkstemp("_test_compliance_check.nc", dir=os.getcwd())[1]
    for i in range(n_tmpfiles)
]
(
    tmpfile0,
) = tmpfiles


def _remove_tmpfiles():
    """Remove temporary files created during tests."""
    for f in tmpfiles:
        try:
            os.remove(f)
        except OSError:
            pass


atexit.register(_remove_tmpfiles)


def _create_noncompliant_names_field(compliant_field, temp_file):
    """Create a copy of a field with bad standard names on all variables."""
    cfdm.write(compliant_field, temp_file)

    with Dataset(temp_file, "r+") as nc:
        field_all_varnames = list(nc.variables.keys())
        # Store a bad name which is the variable name prepended with 'badname_'
        # - this makes it a certain invalid name and one we can identify as
        # being tied to the original variable, for testing purposes.
        bad_name_mapping = {
            varname: "badname_"+ varname for varname in field_all_varnames
        }

        for var_name, bad_std_name in bad_name_mapping.items():
            var = nc.variables[var_name]
            var.standard_name = bad_std_name

    return cfdm.read(temp_file)[0]


class ComplianceCheckingTest(unittest.TestCase):
    """Test CF Conventions compliance checking functionality."""

    # 1. Create a file with field with invalid standard names generally
    # using our 'kitchen sink' field as a basis
    good_general_sn_f = cfdm.example_field(1)
    # TODO set bad names and then write to tempfile and read back in
    bad_general_sn_f = _create_noncompliant_names_field(
        good_general_sn_f, tmpfile0)
    ### bad_general_sn_f.dump()  # SB DEV

    # 1. Create a file with a UGRID field with invalid standard names
    # on UGRID components, using our core 'UGRID 1' field as a basis
    ugrid_file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "ugrid_1.nc"
    )
    good_ugrid_sn_f = cfdm.read(ugrid_file_path)[0]
    # Note we can't write UGRID files using cf at the moment, so needed
    # another way to create UGRID dataset with bad names to test on
    # and the simplest is to write extra 'bad names' file alongside
    # 'ugrid_1.nc' in create_test_files module.
    bad_names_ugrid_file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "ugrid_1_bad_names.nc"
    )
    bad_ugrid_sn_fields = cfdm.read(bad_names_ugrid_file_path)

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

    def test_extract_names_from_xml(self):
        """Test the `cfvalidation._extract_names_from_xml` function."""
        # Check with a small 'dummy' XML table which is the current table
        # but with only the first two names included, w/ or w/o a few aliases
        # (note the aliases don't match up to the two included names but
        # this is irrelevant to the testing so OK)
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
            two_name_table_start + table_end, include_aliases=False)
        self.assertIsInstance(two_name_output, list)
        self.assertEqual(len(two_name_output), 2)
        self.assertIn(
            "acoustic_area_backscattering_strength_in_sea_water",
            two_name_output
        )
        self.assertIn(
            "acoustic_centre_of_mass_in_sea_water", two_name_output)

        # No aliases in this table therefore expect same output as before
        # when setting 'include_aliases=True'
        self.assertEqual(
            cfdm.cfvalidation._extract_names_from_xml(
                two_name_table_start + table_end, include_aliases=True),
            two_name_output
        )

        aliases_inc_output = cfdm.cfvalidation._extract_names_from_xml(
            two_name_table_start + include_two_aliases + table_end,
            include_aliases=True
        )
        self.assertIsInstance(aliases_inc_output, list)
        self.assertEqual(len(aliases_inc_output), 4)
        # Check all non-aliases are there, as per above output
        self.assertTrue(set(two_name_output).issubset(aliases_inc_output))
        # Also should have the aliases this time
        self.assertIn(
            "chlorophyll_concentration_in_sea_water",
            aliases_inc_output
        )
        self.assertIn(
            "concentration_of_chlorophyll_in_sea_water",
            aliases_inc_output
        )

        # When setting 'include_aliases=True' should ignore the two aliases
        # in table so expect same as two_name_output
        self.assertEqual(
            cfdm.cfvalidation._extract_names_from_xml(
                two_name_table_start + include_two_aliases + table_end,
                include_aliases=False
            ),
            two_name_output
        )

    def test_get_all_current_standard_names(self):
        """Test the `cfvalidation.get_all_current_standard_names` function."""
        # First check the URL used is actually available in case of issues
        # arising in case GitHub endpoints go down
        sn_xml_url = cfdm.cfvalidation._STD_NAME_CURRENT_XML_URL
        with request.urlopen(sn_xml_url) as response:
            self.assertEqual(
                response.status, 200,
                "Standard name XML inaccesible: unexpected status code "
                f"{response.status} for reference URL of: {sn_xml_url}"
            )  # 200 == OK
        # SLB-DH discuss TODO: what behaviour do we want for the (v. rare)
        # case that the URL isn't accessible? Ideally we can skip standard
        # name validation with a warning, in these cases.

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

        # Check a standard name with known alias
        self.assertIn("atmosphere_moles_of_cfc113", output)
        # Since the default behaviour is to not include aliases, this alias
        # of the above should not be in the list
        self.assertNotIn("moles_of_cfc113_in_atmosphere", output)

        aliases_inc_output = cfdm.cfvalidation.get_all_current_standard_names(
            include_aliases=True
        )
        self.assertIsInstance(aliases_inc_output, list)

        # As with above length check, can't be sure of eact amount as it
        # changes but we can safely put a lower limit on it. At time of
        # writing, Aug 2025) there are over 5500 names including aliases
        # (where there are ~500 aliases as opposed to non-alias names) so
        # set 5000 as a good limit (> 4500 check w/ include_aliases=False)
        self.assertTrue(len(aliases_inc_output) > 5000)

        # Check all non-aliases are there, as above
        self.assertTrue(set(output).issubset(aliases_inc_output))
        
        # This time the alias should be included
        self.assertIn("moles_of_cfc113_in_atmosphere", aliases_inc_output)

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

    def test_standard_names_validation_compliant_field(self):
        """Test compliance checking on a compliant non-UGRID field."""
        f = self.good_general_sn_f
        dc_output = f.dataset_compliance()
        self.assertEqual(dc_output, dict())

        # TODO what else to test on in 'good' case?

    def test_standard_names_validation_noncompliant_field(self):
        """Test compliance checking on a non-compliant non-UGRID field."""
        expected_reason = (
            "standard_name attribute "
            "has a value that is not a valid name contained "
            "in the current standard name table"
        )
        expected_code = 400022
        # Excludes attribute which we expect in there but depends on varname
        # so add that expected key in during the iteration over varnames
        expected_noncompl_dict = {
            "code": expected_code,
            "reason": expected_reason,
        }

        f = self.bad_general_sn_f
        dc_output = f.dataset_compliance()

        # SLB DEV
        # from pprint import pprint
        # pprint(dc_output)

        # 'ta' is the field variable we test on
        self.assertIn("non-compliance", dc_output["ta"])
        noncompliance = dc_output["ta"]["non-compliance"]

        expected_keys = [
            # POSSIBLY SOLVED, ATTRIBUTE FIX itself? "ta",
            # fails "atmosphere_hybrid_height_coordinate",
            "atmosphere_hybrid_height_coordinate_bounds",
            "latitude_1",
            "longitude_1",
            "time",
            # SOLVED, DIM COORDS fails "x",
            # POSSIBLY SOLVED, DIM COORDS fails "x_bnds"
            # SOLVED, DIM COORDS fails "y",
            # POSSIBLY SOLVED, DIM COORDS fails "y_bnds",
            # fails "b",
            "b_bounds",
            # fails "surface_altitude",
            # fails "rotated_latitude_longitude",
            "auxiliary",
            "cell_measure",  # ATTRIBUTES FIX SHOULDN'T APPEAR
            "air_temperature_standard_error",
        ]
        for varname in expected_keys:
            noncompl_dict = noncompliance.get(varname)
            self.assertIsNotNone(
                noncompl_dict,
                msg=f"Empty non-compliance for variable '{varname}'"
            )
            self.assertIsInstance(noncompl_dict, list)
            self.assertEqual(len(noncompl_dict), 1)

            # Safe to unpack after test above
            noncompl_dict = noncompl_dict[0]

            self.assertIn("code", noncompl_dict)
            self.assertEqual(noncompl_dict["code"], expected_code)
            self.assertIn("reason", noncompl_dict)
            self.assertEqual(noncompl_dict["reason"], expected_reason)

            # Form expected attribute which needs the varname and bad name
            expected_attribute = {
                f"{varname}:standard_name": f"badname_{varname}"
            }
            expected_noncompl_dict["attribute"] = expected_attribute

            self.assertIn("attribute", noncompl_dict)
            self.assertEqual(noncompl_dict["attribute"], expected_attribute)

            # Final check to ensure there isn't anything else in there.
            # If keys are missing will be reported to fail more spefically
            # on per-key-value checks above
            self.assertEqual(noncompl_dict, expected_noncompl_dict)

        # TODO what else to check here?

    def test_standard_names_validation_compliant_ugrid_field(self):
        """Test compliance checking on a compliant UGRID field."""
        f = self.good_ugrid_sn_f
        dc_output = f.dataset_compliance()
        self.assertEqual(dc_output, dict())

        # TODO what else to test on in 'good' case?

    def test_standard_names_validation_noncompliant_ugrid_fields(self):
        """Test compliance checking on non-compliant UGRID fields."""
        expected_reason = (
            "standard_name attribute "
            "has a value that is not a valid name contained "
            "in the current standard name table"
        )
        expected_code = 400022
        # Excludes attribute which we expect in there but depends on varname
        # so add that expected key in during the iteration over varnames
        expected_noncompl_dict = {
            "code": expected_code,
            "reason": expected_reason,
        }

        # Fields for testing on: those in ugrid_1 with bad names pre-set
        f1, f2, f3 = self.bad_ugrid_sn_fields  # unpack to shorter names
        dc_output_1 = f1.dataset_compliance()
        dc_output_2 = f2.dataset_compliance()
        dc_output_3 = f2.dataset_compliance()

        # SLB DEV
        # TODO add error to run to say need to run 'create_test_files'

        # TODO see from below that not all bad names gte set - but want
        # that, so should update create_test_files method to set on all
        # for bad case.
        with Dataset("ugrid_1_bad_names.nc", "r+") as nc:
            field_all_varnames = list(nc.variables.keys())
            print("VERIFY")
            for varname, var in nc.variables.items():
                print(varname, getattr(var, "standard_name", "No standard_name"))

        from pprint import pprint
        pprint(dc_output_1)

        # 'pa' is the field variable we test on
        self.assertIn("non-compliance", dc_output_1["pa"])
        noncompliance = dc_output_1["pa"]["non-compliance"]

        expected_keys = [
            # itself? "pa",
            # not for this field "v",
            # not for this field "ta",
            "time",
            "time_bounds",
            "Mesh2",
            "Mesh2_node_x",  # aka longitude?
            "Mesh2_node_y",  # aka latitude?
            "Mesh2_face_x",  # ... etc.
            "Mesh2_face_y",
            "Mesh2_edge_x",
            "Mesh2_edge_y",
            "Mesh2_face_nodes",
            "Mesh2_edge_nodes",
            "Mesh2_face_edges",
            "Mesh2_face_links",
            "Mesh2_edge_face_links",
        ]
        for varname in expected_keys:
            noncompl_dict = noncompliance.get(varname)
            self.assertIsNotNone(
                noncompl_dict,
                msg=f"Empty non-compliance for variable '{varname}'"
            )
            self.assertIsInstance(noncompl_dict, list)
            self.assertEqual(len(noncompl_dict), 1)

            # Safe to unpack after test above
            noncompl_dict = noncompl_dict[0]

            self.assertIn("code", noncompl_dict)
            self.assertEqual(noncompl_dict["code"], expected_code)
            self.assertIn("reason", noncompl_dict)
            self.assertEqual(noncompl_dict["reason"], expected_reason)

            # Form expected attribute which needs the varname and bad name
            expected_attribute = {
                f"{varname}:standard_name": f"badname_{varname}"
            }
            expected_noncompl_dict["attribute"] = expected_attribute

            self.assertIn("attribute", noncompl_dict)
            self.assertEqual(noncompl_dict["attribute"], expected_attribute)

            # Final check to ensure there isn't anything else in there.
            # If keys are missing will be reported to fail more spefically
            # on per-key-value checks above
            self.assertEqual(noncompl_dict, expected_noncompl_dict)

        from pprint import pprint
        pprint(dc_output_2)

        # 'ta' is the field variable we test on
        self.assertIn("non-compliance", dc_output_2["ta"])
        noncompliance = dc_output_2["ta"]["non-compliance"]

        expected_keys = [
            # itself? "ta",
            # not for this field "pa",
            # not for this field "v",
            "time",
            "time_bounds",
            "Mesh2",
            "Mesh2_node_x",  # aka longitude?
            "Mesh2_node_y",  # aka latitude?
            "Mesh2_face_x",  # ... etc.
            "Mesh2_face_y",
            "Mesh2_edge_x",
            "Mesh2_edge_y",
            "Mesh2_face_nodes",
            "Mesh2_edge_nodes",
            "Mesh2_face_edges",
            "Mesh2_face_links",
            "Mesh2_edge_face_links",
        ]
        for varname in expected_keys:
            noncompl_dict = noncompliance.get(varname)
            self.assertIsNotNone(
                noncompl_dict,
                msg=f"Empty non-compliance for variable '{varname}'"
            )
            self.assertIsInstance(noncompl_dict, list)
            self.assertEqual(len(noncompl_dict), 1)

            # Safe to unpack after test above
            noncompl_dict = noncompl_dict[0]

            self.assertIn("code", noncompl_dict)
            self.assertEqual(noncompl_dict["code"], expected_code)
            self.assertIn("reason", noncompl_dict)
            self.assertEqual(noncompl_dict["reason"], expected_reason)

            # Form expected attribute which needs the varname and bad name
            expected_attribute = {
                f"{varname}:standard_name": f"badname_{varname}"
            }
            expected_noncompl_dict["attribute"] = expected_attribute

            self.assertIn("attribute", noncompl_dict)
            self.assertEqual(noncompl_dict["attribute"], expected_attribute)

            # Final check to ensure there isn't anything else in there.
            # If keys are missing will be reported to fail more spefically
            # on per-key-value checks above
            self.assertEqual(noncompl_dict, expected_noncompl_dict)

        from pprint import pprint
        pprint(dc_output_3)

        # 'v' is the field variable we test on
        self.assertIn("non-compliance", dc_output_3["v"])
        noncompliance = dc_output_3["v"]["non-compliance"]

        expected_keys = [
            # itself? "v",
            # not for this field "ta",
            # not for this field "pa",
            "time",
            "time_bounds",
            "Mesh2",
            "Mesh2_node_x",  # aka longitude?
            "Mesh2_node_y",  # aka latitude?
            "Mesh2_face_x",  # ... etc.
            "Mesh2_face_y",
            "Mesh2_edge_x",
            "Mesh2_edge_y",
            "Mesh2_face_nodes",
            "Mesh2_edge_nodes",
            "Mesh2_face_edges",
            "Mesh2_face_links",
            "Mesh2_edge_face_links",
        ]
        for varname in expected_keys:
            noncompl_dict = noncompliance.get(varname)
            self.assertIsNotNone(
                noncompl_dict,
                msg=f"Empty non-compliance for variable '{varname}'"
            )
            self.assertIsInstance(noncompl_dict, list)
            self.assertEqual(len(noncompl_dict), 1)

            # Safe to unpack after test above
            noncompl_dict = noncompl_dict[0]

            self.assertIn("code", noncompl_dict)
            self.assertEqual(noncompl_dict["code"], expected_code)
            self.assertIn("reason", noncompl_dict)
            self.assertEqual(noncompl_dict["reason"], expected_reason)

            # Form expected attribute which needs the varname and bad name
            expected_attribute = {
                f"{varname}:standard_name": f"badname_{varname}"
            }
            expected_noncompl_dict["attribute"] = expected_attribute

            self.assertIn("attribute", noncompl_dict)
            self.assertEqual(noncompl_dict["attribute"], expected_attribute)

            # Final check to ensure there isn't anything else in there.
            # If keys are missing will be reported to fail more spefically
            # on per-key-value checks above
            self.assertEqual(noncompl_dict, expected_noncompl_dict)

        # TODO what else to check here?


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)

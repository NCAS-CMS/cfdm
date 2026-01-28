import atexit
import datetime
import faulthandler
import os
import tempfile
import unittest
from urllib import request

from netCDF4 import Dataset

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm

n_tmpfiles = 2
tmpfiles = [
    tempfile.mkstemp("_test_compliance_check.nc", dir=os.getcwd())[1]
    for i in range(n_tmpfiles)
]
(tmpfile0, tmpfile1) = tmpfiles


def _remove_tmpfiles():
    """Remove temporary files created during tests."""
    for f in tmpfiles:
        try:
            os.remove(f)
        except OSError:
            pass


atexit.register(_remove_tmpfiles)


def _create_noncompliant_names_field(compliant_field, temp_file):
    """Create a copy of a field with bad standard names on all
    variables."""
    cfdm.write(compliant_field, temp_file)

    with Dataset(temp_file, "r+") as nc:
        field_all_varnames = list(nc.variables.keys())
        # Store a bad name which is the variable name prepended with 'badname_'
        # - this makes it a certain invalid name and one we can identify as
        # being tied to the original variable, for testing purposes.
        bad_name_mapping = {
            varname: "badname_" + varname for varname in field_all_varnames
        }

        for var_name, bad_std_name in bad_name_mapping.items():
            var = nc.variables[var_name]
            var.standard_name = bad_std_name

    return cfdm.read(temp_file)[0]


class ComplianceCheckingTest(unittest.TestCase):
    """Test CF Conventions compliance checking functionality."""

    # 1. Create a file with field with invalid standard names generally
    # using our 'kitchen sink' field as a basis. Need to write it out and
    # read it back in so that the dataset_compliance is set by the new logic!
    # TODO is that (necessary read-write of example fields in this context)
    # a sign of badness?
    good_snames_f = cfdm.example_field(1)
    cfdm.write(good_snames_f, tmpfile1)
    good_snames_general_field = cfdm.read(tmpfile1)[0]

    # Set bad names and then write to tempfile and read back in
    bad_snames_general_field = _create_noncompliant_names_field(
        good_snames_general_field, tmpfile0
    )

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

    bad_sn_expected_reason = (
        "standard_name attribute has a value that is not a "
        "valid name contained in the current standard name table"
    )
    bad_sn_expected_code = 400022

    expected_cf_version = "1.13"

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
        """Test the `conformance._extract_names_from_xml` function."""
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

        two_name_output = cfdm.conformance._extract_names_from_xml(
            two_name_table_start + table_end, include_aliases=False
        )
        self.assertIsInstance(two_name_output, list)
        self.assertEqual(len(two_name_output), 2)
        self.assertIn(
            "acoustic_area_backscattering_strength_in_sea_water",
            two_name_output,
        )
        self.assertIn("acoustic_centre_of_mass_in_sea_water", two_name_output)

        # No aliases in this table therefore expect same output as before
        # when setting 'include_aliases=True'
        self.assertEqual(
            cfdm.conformance._extract_names_from_xml(
                two_name_table_start + table_end, include_aliases=True
            ),
            two_name_output,
        )

        aliases_inc_output = cfdm.conformance._extract_names_from_xml(
            two_name_table_start + include_two_aliases + table_end,
            include_aliases=True,
        )
        self.assertIsInstance(aliases_inc_output, list)
        self.assertEqual(len(aliases_inc_output), 4)
        # Check all non-aliases are there, as per above output
        self.assertTrue(set(two_name_output).issubset(aliases_inc_output))
        # Also should have the aliases this time
        self.assertIn(
            "chlorophyll_concentration_in_sea_water", aliases_inc_output
        )
        self.assertIn(
            "concentration_of_chlorophyll_in_sea_water", aliases_inc_output
        )

        # When setting 'include_aliases=True' should ignore the two aliases
        # in table so expect same as two_name_output
        self.assertEqual(
            cfdm.conformance._extract_names_from_xml(
                two_name_table_start + include_two_aliases + table_end,
                include_aliases=False,
            ),
            two_name_output,
        )

    def test_get_all_current_standard_names(self):
        """Test the `conformance.get_all_current_standard_names`
        function."""
        # First check the URL used is actually available in case of issues
        # arising in case GitHub endpoints go down
        sn_xml_url = cfdm.conformance._STD_NAME_CURRENT_XML_URL
        with request.urlopen(sn_xml_url) as response:
            self.assertEqual(
                response.status,
                200,
                "Standard name XML inaccesible: unexpected status code "
                f"{response.status} for reference URL of: {sn_xml_url}",
            )  # 200 == OK
        # SLB-DH discuss TODO: what behaviour do we want for the (v. rare)
        # case that the URL isn't accessible? Ideally we can skip standard
        # name validation with a warning, in these cases.

        output = cfdm.conformance.get_all_current_standard_names()
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
            output,
        )

        # Check a standard name with known alias
        self.assertIn("atmosphere_moles_of_cfc113", output)
        # Since the default behaviour is to not include aliases, this alias
        # of the above should not be in the list
        self.assertNotIn("moles_of_cfc113_in_atmosphere", output)

        aliases_inc_output = cfdm.conformance.get_all_current_standard_names(
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

    def test_standard_names_validation_compliant_field(self):
        """Test compliance checking on a compliant non-UGRID field."""
        f = self.good_snames_general_field
        dc_output = f.dataset_compliance()
        self.assertEqual(dc_output, {"CF version": self.expected_cf_version})

    def test_standard_names_validation_noncompliant_field(self):
        """Test compliance checking on a non-compliant non-UGRID
        field."""
        # SLB
        f = self.bad_snames_general_field
        dc_output = f.dataset_compliance()
        from pprint import pprint

        pprint(dc_output)

        # 1. Top-level CF version
        self.assertIn("CF version", dc_output)
        self.assertEqual(dc_output["CF version"], self.expected_cf_version)

        # 2. Exactly one other top-level key
        top_keys = [k for k in dc_output.keys() if k != "CF version"]
        self.assertEqual(len(top_keys), 1)
        top_key = top_keys[0]
        self.assertEqual(top_key, "ta")

        # 3. Attributes dict
        top_dict = dc_output[top_key]
        self.assertIn("attributes", top_dict)
        attrs = top_dict["attributes"]
        self.assertIsInstance(attrs, dict)
        self.assertIn("standard_name", attrs)

        # 4. standard_name dict
        sn = attrs["standard_name"]
        self.assertIsInstance(sn, dict)
        self.assertIn("value", sn)
        self.assertIn("non-conformance", sn)

        self.assertEqual(sn["value"], "badname_ta")

        nc_list = sn["non-conformance"]
        self.assertIsInstance(nc_list, list)
        self.assertEqual(len(nc_list), 1)

        nc = nc_list[0]
        self.assertIsInstance(nc, dict)
        self.assertEqual(nc["code"], self.bad_sn_expected_code)
        self.assertEqual(nc["reason"], self.bad_sn_expected_reason)

    def test_standard_names_validation_compliant_ugrid_field(self):
        """Test compliance checking on a compliant UGRID field."""
        f = self.good_ugrid_sn_f
        dc_output = f.dataset_compliance()
        self.assertEqual(dc_output, {"CF version": self.expected_cf_version})

    def test_standard_names_validation_noncompliant_ugrid_fields(self):
        """Test compliance checking on non-compliant UGRID fields."""
        # Fields for testing on: those in ugrid_1 with bad names pre-set
        f1, f2, f3 = self.bad_ugrid_sn_fields  # unpack to shorter names
        dc1 = f1.dataset_compliance()
        dc2 = f2.dataset_compliance()
        dc3 = f3.dataset_compliance()

        # Since all three outputs have largely the same dataset
        # compliance output (TODO SLB is this right?), there's only need
        # to test one for the precise expected form and values (see 1) and
        # then check the other two are equivalent except for the few small
        # differences due to the top-level field variable name and its
        # standard name (see 2).

        # ------------ 1. Test first output field fully ---------------
        pa = dc1["pa"]
        self.assertIsInstance(pa, dict)
        self.assertIn("attributes", pa)

        pa_attributes = pa["attributes"]
        self.assertIsInstance(pa_attributes, dict)
        self.assertCountEqual(pa_attributes.keys(), ["mesh", "standard_name"])

        # pa.attributes.standard_name
        pa_standard_name = pa_attributes["standard_name"]
        self.assertIsInstance(pa_standard_name, dict)
        self.assertIn("value", pa_standard_name)
        self.assertIn("non-conformance", pa_standard_name)
        self.assertEqual(pa_standard_name["value"], "badname_air_pressure")
        self.assertEqual(
            pa_standard_name["non-conformance"][0],
            {
                "code": self.bad_sn_expected_code,
                "reason": self.bad_sn_expected_reason,
            },
        )

        # pa.attributes.mesh
        mesh = pa_attributes["mesh"]
        self.assertIsInstance(mesh, dict)
        self.assertIn("value", mesh)
        self.assertIn("variables", mesh)
        self.assertEqual(mesh["value"], "Mesh2")

        # mesh.variables
        mesh_vars = mesh["variables"]
        self.assertIsInstance(mesh_vars, dict)
        self.assertCountEqual(mesh_vars.keys(), ["Mesh2"])

        mesh2 = mesh_vars["Mesh2"]
        self.assertIsInstance(mesh2, dict)
        self.assertIn("attributes", mesh2)

        # mesh2.attributes
        mesh2_attrs = mesh2["attributes"]
        self.assertIsInstance(mesh2_attrs, dict)
        self.assertCountEqual(
            mesh2_attrs.keys(),
            [
                "standard_name",
                "edge_node_connectivity",
                "face_face_connectivity",
                "face_node_connectivity",
            ],
        )

        # =======================================================
        # standard_name attribute for Mesh2
        # =======================================================
        mesh2_standard_name = mesh2_attrs["standard_name"]
        self.assertIsInstance(mesh2_standard_name, dict)
        self.assertIn("value", mesh2_standard_name)
        self.assertIn("non-conformance", mesh2_standard_name)
        self.assertEqual(mesh2_standard_name["value"], "badname_Mesh2")
        self.assertEqual(
            mesh2_standard_name["non-conformance"][0],
            {
                "code": self.bad_sn_expected_code,
                "reason": self.bad_sn_expected_reason,
            },
        )

        # =======================================================
        # edge_node_connectivity
        # =======================================================
        edge_node = mesh2_attrs["edge_node_connectivity"]
        self.assertIsInstance(edge_node, dict)
        self.assertIn("value", edge_node)
        self.assertIn("variables", edge_node)
        self.assertEqual(edge_node["value"], "Mesh2_edge_nodes")

        edge_node_vars = edge_node["variables"]
        self.assertIsInstance(edge_node_vars, dict)
        self.assertCountEqual(edge_node_vars.keys(), ["Mesh2_edge_nodes"])

        edge_nodes = edge_node_vars["Mesh2_edge_nodes"]
        self.assertIsInstance(edge_nodes, dict)
        self.assertIn("attributes", edge_nodes)

        edge_nodes_attrs = edge_nodes["attributes"]
        self.assertIsInstance(edge_nodes_attrs, dict)
        self.assertCountEqual(edge_nodes_attrs.keys(), ["standard_name"])
        edge_sn = edge_nodes_attrs["standard_name"]
        self.assertIsInstance(edge_sn, dict)
        self.assertEqual(edge_sn["value"], "badname_Mesh2_edge_nodes")
        self.assertEqual(
            edge_sn["non-conformance"][0],
            {
                "code": self.bad_sn_expected_code,
                "reason": self.bad_sn_expected_reason,
            },
        )

        # =======================================================
        # face_face_connectivity
        # =======================================================
        face_face = mesh2_attrs["face_face_connectivity"]
        self.assertIsInstance(face_face, dict)
        self.assertIn("value", face_face)
        self.assertIn("variables", face_face)
        self.assertEqual(face_face["value"], "Mesh2_face_links")

        face_face_vars = face_face["variables"]
        self.assertIsInstance(face_face_vars, dict)
        self.assertCountEqual(face_face_vars.keys(), ["Mesh2_face_links"])

        face_links = face_face_vars["Mesh2_face_links"]
        self.assertIsInstance(face_links, dict)
        self.assertIn("attributes", face_links)

        face_links_attrs = face_links["attributes"]
        self.assertIsInstance(face_links_attrs, dict)
        self.assertCountEqual(face_links_attrs.keys(), ["standard_name"])
        face_sn = face_links_attrs["standard_name"]
        self.assertIsInstance(face_sn, dict)
        self.assertEqual(face_sn["value"], "badname_Mesh2_face_links")
        self.assertEqual(
            face_sn["non-conformance"][0],
            {
                "code": self.bad_sn_expected_code,
                "reason": self.bad_sn_expected_reason,
            },
        )

        # =======================================================
        # face_node_connectivity
        # =======================================================
        face_node = mesh2_attrs["face_node_connectivity"]
        self.assertIsInstance(face_node, dict)
        self.assertIn("value", face_node)
        self.assertIn("variables", face_node)
        self.assertEqual(face_node["value"], "Mesh2_face_nodes")

        face_node_vars = face_node["variables"]
        self.assertIsInstance(face_node_vars, dict)
        self.assertCountEqual(face_node_vars.keys(), ["Mesh2_face_nodes"])

        face_nodes = face_node_vars["Mesh2_face_nodes"]
        self.assertIsInstance(face_nodes, dict)
        self.assertIn("attributes", face_nodes)

        face_nodes_attrs = face_nodes["attributes"]
        self.assertIsInstance(face_nodes_attrs, dict)
        self.assertCountEqual(face_nodes_attrs.keys(), ["standard_name"])
        face_node_sn = face_nodes_attrs["standard_name"]
        self.assertIsInstance(face_node_sn, dict)
        self.assertEqual(face_node_sn["value"], "badname_Mesh2_face_nodes")
        self.assertEqual(
            face_node_sn["non-conformance"][0],
            {
                "code": self.bad_sn_expected_code,
                "reason": self.bad_sn_expected_reason,
            },
        )

        # --- 2. Check dc2 and dc3 are same as dc1 except top-level key ---
        # Do this by first extracting the actual content below the top-level
        # key, then setting the one key that should differ to be the same
        # dummy key, before comparing.
        dc1_content = dc1["pa"]
        dc2_content = dc2["ta"]
        dc3_content = dc3["v"]

        dc1_content["attributes"]["standard_name"]["value"] = "dummy"
        dc2_content["attributes"]["standard_name"]["value"] = "dummy"
        dc3_content["attributes"]["standard_name"]["value"] = "dummy"

        self.assertEqual(dc1_content, dc2_content)
        self.assertEqual(dc1_content, dc3_content)


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)

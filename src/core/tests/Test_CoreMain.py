# Copyright 2020 Microsoft Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Requires Python 2.7+
import datetime
import json
import os
import re
import unittest
import uuid

from core.src.CoreMain import CoreMain
from core.src.bootstrap.Constants import Constants
from core.tests.library.ArgumentComposer import ArgumentComposer
from core.tests.library.LegacyEnvLayerExtensions import LegacyEnvLayerExtensions
from core.tests.library.RuntimeCompositor import RuntimeCompositor


class TestCoreMain(unittest.TestCase):
    def setUp(self):
        # Had to move runtime init and stop to individual test functions, since every test uses a different maintenance_run_id which has to be set before runtime init
        # self.argument_composer = ArgumentComposer().get_composed_arguments()
        # self.runtime = RuntimeCompositor(self.argument_composer, True, package_manager_name=Constants.ZYPPER)
        # self.container = self.runtime.container
        pass

    def tearDown(self):
        # self.runtime.stop()
        pass

    def mock_linux_distribution_to_return_centos(self):
        return ['CentOS Linux', '7.9.2009', 'Core']

    def mock_linux_distribution_to_return_redhat(self):
        return ['Red Hat Enterprise Linux Server', '7.5', 'Maipo']

    def test_operation_fail_for_non_autopatching_request(self):
        # Test for non auto patching request
        argument_composer = ArgumentComposer()
        runtime = RuntimeCompositor(argument_composer.get_composed_arguments(), True, Constants.ZYPPER)
        runtime.set_legacy_test_type('FailInstallPath')
        CoreMain(argument_composer.get_composed_arguments())

        # check telemetry events
        self.__check_telemetry_events(runtime)

        # check status file
        with runtime.env_layer.file_system.open(runtime.execution_config.status_file_path, 'r') as file_handle:
            substatus_file_data = json.load(file_handle)[0]["status"]["substatus"]
        self.assertEquals(len(substatus_file_data), 3)
        self.assertTrue(substatus_file_data[0]["name"] == Constants.PATCH_ASSESSMENT_SUMMARY)
        self.assertTrue(substatus_file_data[0]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        self.assertTrue(substatus_file_data[1]["name"] == Constants.PATCH_INSTALLATION_SUMMARY)
        self.assertTrue(substatus_file_data[1]["status"].lower() == Constants.STATUS_ERROR.lower())
        self.assertEqual(len(json.loads(substatus_file_data[1]["formattedMessage"]["message"])["errors"]["details"]), 1)
        self.assertTrue(substatus_file_data[2]["name"] == Constants.CONFIGURE_PATCHING_SUMMARY)
        self.assertTrue(substatus_file_data[2]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        runtime.stop()

    def test_operation_fail_for_autopatching_request(self):
        argument_composer = ArgumentComposer()
        argument_composer.maintenance_run_id = str(datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
        runtime = RuntimeCompositor(argument_composer.get_composed_arguments(), True, Constants.ZYPPER)
        runtime.set_legacy_test_type('FailInstallPath')
        CoreMain(argument_composer.get_composed_arguments())

        # check telemetry events
        self.__check_telemetry_events(runtime)

        # check status file
        with runtime.env_layer.file_system.open(runtime.execution_config.status_file_path, 'r') as file_handle:
            substatus_file_data = json.load(file_handle)[0]["status"]["substatus"]
        self.assertEquals(len(substatus_file_data), 4)
        self.assertTrue(substatus_file_data[0]["name"] == Constants.PATCH_ASSESSMENT_SUMMARY)
        self.assertTrue(substatus_file_data[0]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        self.assertTrue(substatus_file_data[1]["name"] == Constants.PATCH_INSTALLATION_SUMMARY)
        self.assertTrue(substatus_file_data[1]["status"].lower() == Constants.STATUS_ERROR.lower())
        self.assertEqual(len(json.loads(substatus_file_data[1]["formattedMessage"]["message"])["errors"]["details"]), 1)
        self.assertTrue(substatus_file_data[2]["name"] == Constants.PATCH_METADATA_FOR_HEALTHSTORE)
        self.assertTrue(substatus_file_data[2]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        substatus_file_data_patch_metadata_summary = json.loads(substatus_file_data[2]["formattedMessage"]["message"])
        self.assertTrue(substatus_file_data_patch_metadata_summary["patchVersion"], Constants.PATCH_VERSION_UNKNOWN)
        self.assertFalse(substatus_file_data_patch_metadata_summary["shouldReportToHealthStore"])
        self.assertTrue(substatus_file_data[3]["name"] == Constants.CONFIGURE_PATCHING_SUMMARY)
        self.assertTrue(substatus_file_data[3]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        runtime.stop()

    def test_operation_success_for_non_autopatching_request(self):
        argument_composer = ArgumentComposer()
        runtime = RuntimeCompositor(argument_composer.get_composed_arguments(), True, Constants.ZYPPER)
        runtime.set_legacy_test_type('SuccessInstallPath')
        CoreMain(argument_composer.get_composed_arguments())

        # check telemetry events
        self.__check_telemetry_events(runtime)

        # check status file
        with runtime.env_layer.file_system.open(runtime.execution_config.status_file_path, 'r') as file_handle:
            substatus_file_data = json.load(file_handle)[0]["status"]["substatus"]
        self.assertEquals(len(substatus_file_data), 3)
        self.assertTrue(substatus_file_data[0]["name"] == Constants.PATCH_ASSESSMENT_SUMMARY)
        self.assertTrue(substatus_file_data[0]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        self.assertTrue(substatus_file_data[1]["name"] == Constants.PATCH_INSTALLATION_SUMMARY)
        self.assertTrue(substatus_file_data[1]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        self.assertTrue(substatus_file_data[2]["name"] == Constants.CONFIGURE_PATCHING_SUMMARY)
        self.assertTrue(substatus_file_data[2]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        runtime.stop()

    def test_operation_success_for_autopatching_request(self):
        # test with valid datetime string for maintenance run id
        argument_composer = ArgumentComposer()
        maintenance_run_id = "9/28/2020 02:00:00 PM +00:00"
        argument_composer.maintenance_run_id = str(maintenance_run_id)
        runtime = RuntimeCompositor(argument_composer.get_composed_arguments(), True, Constants.ZYPPER)
        runtime.set_legacy_test_type('SuccessInstallPath')
        CoreMain(argument_composer.get_composed_arguments())

        # check telemetry events
        self.__check_telemetry_events(runtime)

        # check status file
        with runtime.env_layer.file_system.open(runtime.execution_config.status_file_path, 'r') as file_handle:
            substatus_file_data = json.load(file_handle)[0]["status"]["substatus"]
        self.assertEquals(len(substatus_file_data), 4)
        self.assertTrue(substatus_file_data[0]["name"] == Constants.PATCH_ASSESSMENT_SUMMARY)
        self.assertTrue(substatus_file_data[0]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        self.assertTrue(substatus_file_data[1]["name"] == Constants.PATCH_INSTALLATION_SUMMARY)
        self.assertTrue(substatus_file_data[1]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        self.assertTrue(substatus_file_data[2]["name"] == Constants.PATCH_METADATA_FOR_HEALTHSTORE)
        self.assertTrue(substatus_file_data[2]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        substatus_file_data_patch_metadata_summary = json.loads(substatus_file_data[2]["formattedMessage"]["message"])
        self.assertEqual(substatus_file_data_patch_metadata_summary["patchVersion"], "2020.09.28")
        self.assertTrue(substatus_file_data_patch_metadata_summary["shouldReportToHealthStore"])
        self.assertTrue(substatus_file_data[3]["name"] == Constants.CONFIGURE_PATCHING_SUMMARY)
        self.assertTrue(substatus_file_data[3]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        runtime.stop()

    def test_operation_success_for_autopatching_request_with_security_classification(self):
        # test with valid datetime string for maintenance run id
        argument_composer = ArgumentComposer()
        maintenance_run_id = "9/28/2020 02:00:00 PM +00:00"
        classifications_to_include = ["Security", "Critical"]
        argument_composer.maintenance_run_id = str(maintenance_run_id)
        argument_composer.classifications_to_include = classifications_to_include
        runtime = RuntimeCompositor(argument_composer.get_composed_arguments(), True, Constants.APT)
        runtime.set_legacy_test_type("SuccessInstallPath")
        CoreMain(argument_composer.get_composed_arguments())

        # check telemetry events
        self.__check_telemetry_events(runtime)

        # check status file
        with runtime.env_layer.file_system.open(runtime.execution_config.status_file_path, 'r') as file_handle:
            substatus_file_data = json.load(file_handle)[0]["status"]["substatus"]
        self.assertEquals(len(substatus_file_data), 4)
        self.assertTrue(substatus_file_data[0]["name"] == Constants.PATCH_ASSESSMENT_SUMMARY)
        self.assertTrue(substatus_file_data[0]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        self.assertTrue(substatus_file_data[1]["name"] == Constants.PATCH_INSTALLATION_SUMMARY)
        self.assertTrue(substatus_file_data[1]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        self.assertEqual(json.loads(substatus_file_data[1]["formattedMessage"]["message"])["patches"][0]["name"], "python-samba")
        self.assertTrue("Security" in str(json.loads(substatus_file_data[1]["formattedMessage"]["message"])["patches"][0]["classifications"]))
        self.assertEqual(json.loads(substatus_file_data[1]["formattedMessage"]["message"])["patches"][1]["name"], "samba-common-bin")
        self.assertTrue("Security" in str(json.loads(substatus_file_data[1]["formattedMessage"]["message"])["patches"][1]["classifications"]))
        self.assertEqual(json.loads(substatus_file_data[1]["formattedMessage"]["message"])["patches"][2]["name"], "samba-libs")
        self.assertTrue("python-samba_2:4.4.5+dfsg-2ubuntu5.4" in str(json.loads(substatus_file_data[1]["formattedMessage"]["message"])["patches"][0]["patchId"]))
        self.assertTrue("Security" in str(json.loads(substatus_file_data[1]["formattedMessage"]["message"])["patches"][2]["classifications"]))
        self.assertTrue(substatus_file_data[2]["name"] == Constants.PATCH_METADATA_FOR_HEALTHSTORE)
        self.assertTrue(substatus_file_data[2]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        substatus_file_data_patch_metadata_summary = json.loads(substatus_file_data[2]["formattedMessage"]["message"])
        self.assertEqual(substatus_file_data_patch_metadata_summary["patchVersion"], "2020.09.28")
        self.assertTrue(substatus_file_data_patch_metadata_summary["shouldReportToHealthStore"])
        self.assertTrue(substatus_file_data[3]["name"] == Constants.CONFIGURE_PATCHING_SUMMARY)
        self.assertTrue(substatus_file_data[3]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        runtime.stop()

    def test_invalid_maintenance_run_id(self):
        # test with empty string for maintenence run id
        argument_composer = ArgumentComposer()
        maintenance_run_id = ""
        argument_composer.maintenance_run_id = maintenance_run_id
        runtime = RuntimeCompositor(argument_composer.get_composed_arguments(), True, Constants.ZYPPER)
        runtime.set_legacy_test_type('SuccessInstallPath')
        CoreMain(argument_composer.get_composed_arguments())

        # check telemetry events
        self.__check_telemetry_events(runtime)

        # check status file
        with runtime.env_layer.file_system.open(runtime.execution_config.status_file_path, 'r') as file_handle:
            substatus_file_data = json.load(file_handle)[0]["status"]["substatus"]
        self.assertEquals(len(substatus_file_data), 4)
        self.assertTrue(substatus_file_data[0]["name"] == Constants.PATCH_ASSESSMENT_SUMMARY)
        self.assertTrue(substatus_file_data[0]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        self.assertTrue(substatus_file_data[1]["name"] == Constants.PATCH_INSTALLATION_SUMMARY)
        self.assertTrue(substatus_file_data[1]["status"].lower() == Constants.STATUS_ERROR.lower())
        self.assertTrue(substatus_file_data[2]["name"] == Constants.PATCH_METADATA_FOR_HEALTHSTORE)
        self.assertTrue(substatus_file_data[2]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        substatus_file_data_patch_metadata_summary = json.loads(substatus_file_data[2]["formattedMessage"]["message"])
        self.assertEqual(substatus_file_data_patch_metadata_summary["patchVersion"], Constants.PATCH_VERSION_UNKNOWN)
        self.assertFalse(substatus_file_data_patch_metadata_summary["shouldReportToHealthStore"])
        self.assertTrue(substatus_file_data[3]["name"] == Constants.CONFIGURE_PATCHING_SUMMARY)
        self.assertTrue(substatus_file_data[3]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        runtime.stop()

        # todo: This will become a valid success operation run once the temp fix for maintenanceRunId is removed
        # test with a random string for maintenance run id
        argument_composer = ArgumentComposer()
        maintenance_run_id = "test"
        argument_composer.maintenance_run_id = maintenance_run_id
        runtime = RuntimeCompositor(argument_composer.get_composed_arguments(), True, Constants.ZYPPER)
        runtime.set_legacy_test_type('SuccessInstallPath')
        CoreMain(argument_composer.get_composed_arguments())

        # check telemetry events
        self.__check_telemetry_events(runtime)

        # check status file
        with runtime.env_layer.file_system.open(runtime.execution_config.status_file_path, 'r') as file_handle:
            substatus_file_data = json.load(file_handle)[0]["status"]["substatus"]
        self.assertEquals(len(substatus_file_data), 4)
        self.assertTrue(substatus_file_data[0]["name"] == Constants.PATCH_ASSESSMENT_SUMMARY)
        self.assertTrue(substatus_file_data[0]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        self.assertTrue(substatus_file_data[1]["name"] == Constants.PATCH_INSTALLATION_SUMMARY)
        self.assertTrue(substatus_file_data[1]["status"].lower() == Constants.STATUS_ERROR.lower())
        self.assertTrue(substatus_file_data[2]["name"] == Constants.PATCH_METADATA_FOR_HEALTHSTORE)
        self.assertTrue(substatus_file_data[2]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        substatus_file_data_patch_metadata_summary = json.loads(substatus_file_data[2]["formattedMessage"]["message"])
        self.assertEqual(substatus_file_data_patch_metadata_summary["patchVersion"], Constants.PATCH_VERSION_UNKNOWN)
        self.assertFalse(substatus_file_data_patch_metadata_summary["shouldReportToHealthStore"])
        self.assertTrue(substatus_file_data[3]["name"] == Constants.CONFIGURE_PATCHING_SUMMARY)
        self.assertTrue(substatus_file_data[3]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        runtime.stop()

    def test_assessment_operation_success(self):
        argument_composer = ArgumentComposer()
        argument_composer.operation = Constants.ASSESSMENT
        runtime = RuntimeCompositor(argument_composer.get_composed_arguments(), True, Constants.ZYPPER)
        runtime.set_legacy_test_type('HappyPath')
        CoreMain(argument_composer.get_composed_arguments())

        # check telemetry events
        self.__check_telemetry_events(runtime)

        # check status file
        with runtime.env_layer.file_system.open(runtime.execution_config.status_file_path, 'r') as file_handle:
            substatus_file_data = json.load(file_handle)[0]["status"]["substatus"]
        self.assertEquals(len(substatus_file_data), 2)
        self.assertTrue(substatus_file_data[0]["name"] == Constants.PATCH_ASSESSMENT_SUMMARY)
        self.assertTrue(substatus_file_data[0]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        self.assertTrue(substatus_file_data[1]["name"] == Constants.CONFIGURE_PATCHING_SUMMARY)
        self.assertTrue(substatus_file_data[1]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        runtime.stop()

    def test_assessment_operation_fail(self):
        argument_composer = ArgumentComposer()
        argument_composer.operation = Constants.ASSESSMENT
        runtime = RuntimeCompositor(argument_composer.get_composed_arguments(), True, Constants.ZYPPER)
        runtime.set_legacy_test_type('ExceptionPath')
        CoreMain(argument_composer.get_composed_arguments())

        # check telemetry events
        self.__check_telemetry_events(runtime)

        # check status file
        with runtime.env_layer.file_system.open(runtime.execution_config.status_file_path, 'r') as file_handle:
            substatus_file_data = json.load(file_handle)[0]["status"]["substatus"]
        self.assertEquals(len(substatus_file_data), 2)
        self.assertTrue(substatus_file_data[0]["name"] == Constants.PATCH_ASSESSMENT_SUMMARY)
        self.assertTrue(substatus_file_data[0]["status"].lower() == Constants.STATUS_ERROR.lower())
        self.assertEqual(len(json.loads(substatus_file_data[0]["formattedMessage"]["message"])["errors"]["details"]), 2)
        self.assertTrue(substatus_file_data[1]["name"] == Constants.CONFIGURE_PATCHING_SUMMARY)
        self.assertTrue(substatus_file_data[1]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        runtime.stop()

    def test_assessment_operation_fail_due_to_no_telemetry(self):
        argument_composer = ArgumentComposer()
        argument_composer.operation = Constants.ASSESSMENT
        argument_composer.events_folder = None
        runtime = RuntimeCompositor(argument_composer.get_composed_arguments(), True, Constants.ZYPPER)
        runtime.set_legacy_test_type('HappyPath')
        CoreMain(argument_composer.get_composed_arguments())

        with runtime.env_layer.file_system.open(runtime.execution_config.status_file_path, 'r') as file_handle:
            substatus_file_data = json.load(file_handle)[0]["status"]["substatus"]
        self.assertEquals(len(substatus_file_data), 2)
        self.assertTrue(substatus_file_data[0]["name"] == Constants.PATCH_ASSESSMENT_SUMMARY)
        self.assertTrue(substatus_file_data[0]["status"].lower() == Constants.STATUS_ERROR.lower())
        self.assertEqual(len(json.loads(substatus_file_data[0]["formattedMessage"]["message"])["errors"]["details"]), 1)
        self.assertTrue(Constants.TELEMETRY_AT_AGENT_NOT_COMPATIBLE_ERROR_MSG in json.loads(substatus_file_data[0]["formattedMessage"]["message"])["errors"]["details"][0]["message"])
        self.assertTrue(substatus_file_data[1]["name"] == Constants.CONFIGURE_PATCHING_SUMMARY)
        self.assertTrue(substatus_file_data[1]["status"].lower() == Constants.STATUS_ERROR.lower())
        self.assertTrue(Constants.TELEMETRY_AT_AGENT_NOT_COMPATIBLE_ERROR_MSG in json.loads(substatus_file_data[1]["formattedMessage"]["message"])["errors"]["details"][0]["message"])
        runtime.stop()

    def test_installation_operation_fail_due_to_no_telemetry(self):
        # testing on auto patching request
        argument_composer = ArgumentComposer()
        argument_composer.maintenance_run_id = str(datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
        argument_composer.events_folder = None
        runtime = RuntimeCompositor(argument_composer.get_composed_arguments(), True, Constants.ZYPPER)
        runtime.set_legacy_test_type('SuccessInstallPath')
        CoreMain(argument_composer.get_composed_arguments())

        with runtime.env_layer.file_system.open(runtime.execution_config.status_file_path, 'r') as file_handle:
            substatus_file_data = json.load(file_handle)[0]["status"]["substatus"]
        self.assertEquals(len(substatus_file_data), 4)
        self.assertTrue(substatus_file_data[0]["name"] == Constants.PATCH_ASSESSMENT_SUMMARY)
        self.assertTrue(substatus_file_data[0]["status"].lower() == Constants.STATUS_ERROR.lower())
        self.assertEqual(len(json.loads(substatus_file_data[0]["formattedMessage"]["message"])["errors"]["details"]), 1)
        self.assertTrue(Constants.TELEMETRY_AT_AGENT_NOT_COMPATIBLE_ERROR_MSG in json.loads(substatus_file_data[0]["formattedMessage"]["message"])["errors"]["details"][0]["message"])
        self.assertTrue(substatus_file_data[1]["name"] == Constants.PATCH_INSTALLATION_SUMMARY)
        self.assertTrue(substatus_file_data[1]["status"].lower() == Constants.STATUS_ERROR.lower())
        self.assertEqual(len(json.loads(substatus_file_data[1]["formattedMessage"]["message"])["errors"]["details"]), 1)
        self.assertFalse(Constants.TELEMETRY_AT_AGENT_NOT_COMPATIBLE_ERROR_MSG in json.loads(substatus_file_data[1]["formattedMessage"]["message"])["errors"]["details"][0]["message"])
        self.assertTrue("Installation failed due to assessment failure. Please refer the error details in assessment substatus" in json.loads(substatus_file_data[1]["formattedMessage"]["message"])["errors"]["details"][0]["message"])
        self.assertTrue(substatus_file_data[2]["name"] == Constants.PATCH_METADATA_FOR_HEALTHSTORE)
        self.assertTrue(substatus_file_data[2]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        self.assertTrue(substatus_file_data[3]["name"] == Constants.CONFIGURE_PATCHING_SUMMARY)
        self.assertTrue(substatus_file_data[3]["status"].lower() == Constants.STATUS_ERROR.lower())
        self.assertEqual(len(json.loads(substatus_file_data[3]["formattedMessage"]["message"])["errors"]["details"]), 1)
        self.assertTrue(Constants.TELEMETRY_AT_AGENT_NOT_COMPATIBLE_ERROR_MSG in json.loads(substatus_file_data[3]["formattedMessage"]["message"])["errors"]["details"][0]["message"])
        runtime.stop()

    def test_install_all_packages_for_centos_autopatching(self):
        """Unit test for auto patching request on CentOS, should install all patches irrespective of classification"""

        backup_envlayer_platform_linux_distribution = LegacyEnvLayerExtensions.LegacyPlatform.linux_distribution
        LegacyEnvLayerExtensions.LegacyPlatform.linux_distribution = self.mock_linux_distribution_to_return_centos

        argument_composer = ArgumentComposer()
        maintenance_run_id = "9/28/2020 02:00:00 PM +00:00"
        classifications_to_include = ["Security", "Critical"]
        argument_composer.maintenance_run_id = str(maintenance_run_id)
        argument_composer.classifications_to_include = classifications_to_include
        runtime = RuntimeCompositor(argument_composer.get_composed_arguments(), True, Constants.YUM)
        runtime.set_legacy_test_type("HappyPath")
        CoreMain(argument_composer.get_composed_arguments())

        # check telemetry events
        self.__check_telemetry_events(runtime)

        # check status file
        with runtime.env_layer.file_system.open(runtime.execution_config.status_file_path, 'r') as file_handle:
            substatus_file_data = json.load(file_handle)[0]["status"]["substatus"]
        self.assertEquals(len(substatus_file_data), 4)
        self.assertTrue(substatus_file_data[0]["name"] == Constants.PATCH_ASSESSMENT_SUMMARY)
        self.assertTrue(substatus_file_data[0]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        self.assertTrue(substatus_file_data[1]["name"] == Constants.PATCH_INSTALLATION_SUMMARY)
        self.assertTrue(substatus_file_data[1]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        self.assertTrue(json.loads(substatus_file_data[1]["formattedMessage"]["message"])["installedPatchCount"] == 5)
        self.assertEqual(json.loads(substatus_file_data[1]["formattedMessage"]["message"])["patches"][0]["name"], "selinux-policy.noarch")
        self.assertTrue("Other" in str(json.loads(substatus_file_data[1]["formattedMessage"]["message"])["patches"][0]["classifications"]))
        self.assertTrue("Installed" == json.loads(substatus_file_data[1]["formattedMessage"]["message"])["patches"][0]["patchInstallationState"])
        self.assertEqual(json.loads(substatus_file_data[1]["formattedMessage"]["message"])["patches"][1]["name"], "selinux-policy-targeted.noarch")
        self.assertTrue("Other" in str(json.loads(substatus_file_data[1]["formattedMessage"]["message"])["patches"][1]["classifications"]))
        self.assertTrue("Installed" == json.loads(substatus_file_data[1]["formattedMessage"]["message"])["patches"][1]["patchInstallationState"])
        self.assertEqual(json.loads(substatus_file_data[1]["formattedMessage"]["message"])["patches"][2]["name"], "libgcc.i686")
        self.assertTrue("libgcc.i686_4.8.5-28.el7_CentOS Linux_7.9.2009" in str(json.loads(substatus_file_data[1]["formattedMessage"]["message"])["patches"][2]["patchId"]))
        self.assertTrue("Security" in str(json.loads(substatus_file_data[1]["formattedMessage"]["message"])["patches"][2]["classifications"]))
        self.assertTrue("Installed" == json.loads(substatus_file_data[1]["formattedMessage"]["message"])["patches"][2]["patchInstallationState"])
        self.assertTrue(substatus_file_data[2]["name"] == Constants.PATCH_METADATA_FOR_HEALTHSTORE)
        self.assertTrue(substatus_file_data[2]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        substatus_file_data_patch_metadata_summary = json.loads(substatus_file_data[2]["formattedMessage"]["message"])
        self.assertEqual(substatus_file_data_patch_metadata_summary["patchVersion"], "2020.09.28")
        self.assertTrue(substatus_file_data_patch_metadata_summary["shouldReportToHealthStore"])
        self.assertTrue(substatus_file_data[3]["name"] == Constants.CONFIGURE_PATCHING_SUMMARY)
        self.assertTrue(substatus_file_data[3]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        runtime.stop()

        LegacyEnvLayerExtensions.LegacyPlatform.linux_distribution = backup_envlayer_platform_linux_distribution

    def test_install_only_critical_and_security_packages_for_redhat_autopatching(self):
        """Unit test for auto patching request on Redhat, should install only critical and security patches"""

        backup_envlayer_platform_linux_distribution = LegacyEnvLayerExtensions.LegacyPlatform.linux_distribution
        LegacyEnvLayerExtensions.LegacyPlatform.linux_distribution = self.mock_linux_distribution_to_return_redhat

        argument_composer = ArgumentComposer()
        maintenance_run_id = "9/28/2020 02:00:00 PM +00:00"
        classifications_to_include = ["Security", "Critical"]
        argument_composer.maintenance_run_id = str(maintenance_run_id)
        argument_composer.classifications_to_include = classifications_to_include
        runtime = RuntimeCompositor(argument_composer.get_composed_arguments(), True, Constants.YUM)
        runtime.set_legacy_test_type("HappyPath")
        CoreMain(argument_composer.get_composed_arguments())

        # check telemetry events
        self.__check_telemetry_events(runtime)

        # check status file
        with runtime.env_layer.file_system.open(runtime.execution_config.status_file_path, 'r') as file_handle:
            substatus_file_data = json.load(file_handle)[0]["status"]["substatus"]
        self.assertEquals(len(substatus_file_data), 4)
        self.assertTrue(substatus_file_data[0]["name"] == Constants.PATCH_ASSESSMENT_SUMMARY)
        self.assertTrue(substatus_file_data[0]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        self.assertTrue(substatus_file_data[1]["name"] == Constants.PATCH_INSTALLATION_SUMMARY)
        self.assertTrue(substatus_file_data[1]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        self.assertTrue(json.loads(substatus_file_data[1]["formattedMessage"]["message"])["installedPatchCount"] == 1)
        self.assertEqual(json.loads(substatus_file_data[1]["formattedMessage"]["message"])["patches"][0]["name"], "selinux-policy.noarch")
        self.assertTrue("Other" in str(json.loads(substatus_file_data[1]["formattedMessage"]["message"])["patches"][0]["classifications"]))
        self.assertTrue("NotSelected" == json.loads(substatus_file_data[1]["formattedMessage"]["message"])["patches"][0]["patchInstallationState"])
        self.assertEqual(json.loads(substatus_file_data[1]["formattedMessage"]["message"])["patches"][1]["name"], "selinux-policy-targeted.noarch")
        self.assertTrue("Other" in str(json.loads(substatus_file_data[1]["formattedMessage"]["message"])["patches"][1]["classifications"]))
        self.assertTrue("NotSelected" == json.loads(substatus_file_data[1]["formattedMessage"]["message"])["patches"][1]["patchInstallationState"])
        self.assertEqual(json.loads(substatus_file_data[1]["formattedMessage"]["message"])["patches"][2]["name"], "tar.x86_64")
        self.assertTrue("Other" in str(json.loads(substatus_file_data[1]["formattedMessage"]["message"])["patches"][2]["classifications"]))
        self.assertTrue("NotSelected" == json.loads(substatus_file_data[1]["formattedMessage"]["message"])["patches"][2]["patchInstallationState"])
        self.assertEqual(json.loads(substatus_file_data[1]["formattedMessage"]["message"])["patches"][3]["name"], "tcpdump.x86_64")
        self.assertTrue("Other" in str(json.loads(substatus_file_data[1]["formattedMessage"]["message"])["patches"][3]["classifications"]))
        self.assertTrue("NotSelected" == json.loads(substatus_file_data[1]["formattedMessage"]["message"])["patches"][3]["patchInstallationState"])
        self.assertEqual(json.loads(substatus_file_data[1]["formattedMessage"]["message"])["patches"][4]["name"], "libgcc.i686")
        self.assertTrue("libgcc.i686_4.8.5-28.el7_Red Hat Enterprise Linux Server_7.5" in str(json.loads(substatus_file_data[1]["formattedMessage"]["message"])["patches"][4]["patchId"]))
        self.assertTrue("Security" in str(json.loads(substatus_file_data[1]["formattedMessage"]["message"])["patches"][4]["classifications"]))
        self.assertTrue("Installed" == json.loads(substatus_file_data[1]["formattedMessage"]["message"])["patches"][4]["patchInstallationState"])
        self.assertTrue(substatus_file_data[2]["name"] == Constants.PATCH_METADATA_FOR_HEALTHSTORE)
        self.assertTrue(substatus_file_data[2]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        substatus_file_data_patch_metadata_summary = json.loads(substatus_file_data[2]["formattedMessage"]["message"])
        self.assertEqual(substatus_file_data_patch_metadata_summary["patchVersion"], "2020.09.28")
        self.assertTrue(substatus_file_data_patch_metadata_summary["shouldReportToHealthStore"])
        self.assertTrue(substatus_file_data[3]["name"] == Constants.CONFIGURE_PATCHING_SUMMARY)
        self.assertTrue(substatus_file_data[3]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        runtime.stop()

        LegacyEnvLayerExtensions.LegacyPlatform.linux_distribution = backup_envlayer_platform_linux_distribution

    # test with both assessment mode and patch mode set in configure patching or install patches or assess patches or auto assessment
    def test_auto_assessment_success_with_configure_patching_in_prev_operation_on_same_sequence(self):
        """Unit test for auto assessment request with configure patching completed on the sequence before. Result: should retain prev substatus and update only PatchAssessmentSummary"""
        # operation #1: ConfigurePatching
        argument_composer = ArgumentComposer()
        argument_composer.operation = Constants.CONFIGURE_PATCHING
        argument_composer.patch_mode = Constants.PatchModes.AUTOMATIC_BY_PLATFORM
        argument_composer.assessment_mode = Constants.AssessmentModes.AUTOMATIC_BY_PLATFORM
        runtime = RuntimeCompositor(argument_composer.get_composed_arguments(), True, Constants.APT)
        runtime.set_legacy_test_type("SuccessInstallPath")
        CoreMain(argument_composer.get_composed_arguments())
        # check telemetry events
        self.__check_telemetry_events(runtime)
        # check status file
        with runtime.env_layer.file_system.open(runtime.execution_config.status_file_path, 'r') as file_handle:
            status_file_data = json.load(file_handle)[0]["status"]
        self.assertTrue(status_file_data["operation"] == Constants.CONFIGURE_PATCHING)
        substatus_file_data = status_file_data["substatus"]
        self.assertEquals(len(substatus_file_data), 1)
        self.assertTrue(substatus_file_data[0]["name"] == Constants.CONFIGURE_PATCHING_SUMMARY)
        self.assertTrue(substatus_file_data[0]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        # check status file for configure patching auto updates state
        message = json.loads(substatus_file_data[0]["formattedMessage"]["message"])
        self.assertEqual(message["automaticOSPatchState"], Constants.AutomaticOSPatchStates.DISABLED)  # auto OS updates are disabled in RuntimeCompositor
        # check status file for configure patching assessment state
        message = json.loads(substatus_file_data[0]["formattedMessage"]["message"])
        self.assertEqual(message["autoAssessmentStatus"]["autoAssessmentState"], Constants.AutoAssessmentStates.ENABLED)  # auto assessment is enabled

        # operation #2: Auto Assessment
        argument_composer.activity_id = str(uuid.uuid4())
        argument_composer.included_classifications_list = self.included_package_name_mask_list = self.excluded_package_name_mask_list = []
        argument_composer.maintenance_run_id = None
        argument_composer.start_time = runtime.env_layer.datetime.standard_datetime_to_utc(datetime.datetime.utcnow())
        argument_composer.duration = Constants.AUTO_ASSESSMENT_MAXIMUM_DURATION
        argument_composer.reboot_setting = Constants.REBOOT_NEVER
        argument_composer.patch_mode = None
        argument_composer.exec_auto_assess_only = True
        runtime.execution_config.exec_auto_assess_only = True
        CoreMain(argument_composer.get_composed_arguments())
        # check telemetry events
        self.__check_telemetry_events(runtime)
        # check status file
        with runtime.env_layer.file_system.open(runtime.execution_config.status_file_path, 'r') as file_handle:
            status_file_data = json.load(file_handle)[0]["status"]
        # verifying the original operation name is preserved
        self.assertTrue(status_file_data["operation"] == Constants.CONFIGURE_PATCHING)
        substatus_file_data = status_file_data["substatus"]
        self.assertEquals(len(substatus_file_data), 2)
        self.assertTrue(substatus_file_data[0]["name"] == Constants.PATCH_ASSESSMENT_SUMMARY)
        self.assertTrue(substatus_file_data[0]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        # check started by set to 'Platform'
        self.assertTrue(json.loads(substatus_file_data[0]["formattedMessage"]["message"])['startedBy'], Constants.PatchAssessmentSummaryStartedBy.PLATFORM)
        # verifying the older operation summary is preserved
        self.assertTrue(substatus_file_data[1]["name"] == Constants.CONFIGURE_PATCHING_SUMMARY)
        self.assertTrue(substatus_file_data[1]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        message = json.loads(substatus_file_data[1]["formattedMessage"]["message"])
        self.assertEqual(message["automaticOSPatchState"], Constants.AutomaticOSPatchStates.DISABLED)  # auto OS updates are disabled in RuntimeCompositor
        # check status file for configure patching assessment state
        message = json.loads(substatus_file_data[1]["formattedMessage"]["message"])
        self.assertEqual(message["autoAssessmentStatus"]["autoAssessmentState"], Constants.AutoAssessmentStates.ENABLED)  # auto assessment is enabled

        runtime.stop()

    def test_auto_assessment_success_with_assessment_in_prev_operation_on_same_sequence(self):
        """Unit test for auto assessment request with assessment completed on the sequence before. Result: should contain PatchAssessmentSummary with an updated timestamp and ConfigurePatchingSummary from the first Assessment operation"""
        # operation #1: Assessment
        argument_composer = ArgumentComposer()
        argument_composer.operation = Constants.ASSESSMENT
        runtime = RuntimeCompositor(argument_composer.get_composed_arguments(), True, Constants.APT)
        runtime.set_legacy_test_type("SuccessInstallPath")
        CoreMain(argument_composer.get_composed_arguments())
        # check telemetry events
        self.__check_telemetry_events(runtime)
        # check status file
        with runtime.env_layer.file_system.open(runtime.execution_config.status_file_path, 'r') as file_handle:
            status_file_data = json.load(file_handle)[0]["status"]
        self.assertTrue(status_file_data["operation"] == Constants.ASSESSMENT)
        substatus_file_data = status_file_data["substatus"]
        self.assertEquals(len(substatus_file_data), 2)
        self.assertTrue(substatus_file_data[0]["name"] == Constants.PATCH_ASSESSMENT_SUMMARY)
        self.assertTrue(substatus_file_data[0]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        # check started by set to 'User'
        self.assertTrue(json.loads(substatus_file_data[0]["formattedMessage"]["message"])['startedBy'], Constants.PatchAssessmentSummaryStartedBy.USER)
        self.assertTrue(substatus_file_data[1]["name"] == Constants.CONFIGURE_PATCHING_SUMMARY)
        self.assertTrue(substatus_file_data[1]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        # check status file for configure patching auto updates state
        message = json.loads(substatus_file_data[1]["formattedMessage"]["message"])
        self.assertEqual(message["automaticOSPatchState"], Constants.AutomaticOSPatchStates.DISABLED)  # auto OS updates are disabled in RuntimeCompositor
        # check status file for configure patching assessment state
        message = json.loads(substatus_file_data[1]["formattedMessage"]["message"])
        self.assertEqual(message["autoAssessmentStatus"]["autoAssessmentState"], Constants.AutoAssessmentStates.UNKNOWN)  # Configure patching for auto assessment did not execute since assessmentMode was not in input

        # operation #2: Auto Assessment
        argument_composer.activity_id = str(uuid.uuid4())
        argument_composer.included_classifications_list = self.included_package_name_mask_list = self.excluded_package_name_mask_list = []
        argument_composer.maintenance_run_id = None
        argument_composer.start_time = runtime.env_layer.datetime.standard_datetime_to_utc(datetime.datetime.utcnow())
        argument_composer.duration = Constants.AUTO_ASSESSMENT_MAXIMUM_DURATION
        argument_composer.reboot_setting = Constants.REBOOT_NEVER
        argument_composer.patch_mode = None
        argument_composer.exec_auto_assess_only = True
        runtime.execution_config.exec_auto_assess_only = True
        CoreMain(argument_composer.get_composed_arguments())
        # check telemetry events
        self.__check_telemetry_events(runtime)
        # check status file
        with runtime.env_layer.file_system.open(runtime.execution_config.status_file_path, 'r') as file_handle:
            status_file_data = json.load(file_handle)[0]["status"]

        # verifying the original operation name is preserved
        self.assertTrue(status_file_data["operation"] == Constants.ASSESSMENT)
        substatus_file_data = status_file_data["substatus"]
        self.assertEquals(len(substatus_file_data), 2)
        self.assertTrue(substatus_file_data[0]["name"] == Constants.PATCH_ASSESSMENT_SUMMARY)
        self.assertTrue(substatus_file_data[0]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        # check started by set to 'Platform'
        self.assertTrue(json.loads(substatus_file_data[0]["formattedMessage"]["message"])['startedBy'], Constants.PatchAssessmentSummaryStartedBy.PLATFORM)
        # verifying the older operation summary is preserved
        self.assertTrue(substatus_file_data[1]["name"] == Constants.CONFIGURE_PATCHING_SUMMARY)
        self.assertTrue(substatus_file_data[1]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        # check status file for configure patching auto updates state
        message = json.loads(substatus_file_data[1]["formattedMessage"]["message"])
        self.assertEqual(message["automaticOSPatchState"], Constants.AutomaticOSPatchStates.DISABLED)  # auto OS updates are disabled in RuntimeCompositor
        # check status file for configure patching assessment state
        message = json.loads(substatus_file_data[1]["formattedMessage"]["message"])
        self.assertEqual(message["autoAssessmentStatus"]["autoAssessmentState"], Constants.AutoAssessmentStates.UNKNOWN)  # Configure patching for auto assessment did not execute since assessmentMode was not in input

        runtime.stop()

    def test_auto_assessment_success_with_installation_in_prev_operation_on_same_sequence(self):
        """Unit test for auto assessment request with installation (Auto Patching) completed on the sequence before.
        Result: should contain PatchAssessmentSummary with an updated timestamp after auto assessment, and retain PatchInstallationSummary, ConfigurePatchingSummary and PatchMetadatForHealthStoreSummary from the installation(Auto Patching) operation"""
        # operation #1: Assessment
        argument_composer = ArgumentComposer()
        argument_composer.operation = Constants.INSTALLATION
        argument_composer.maintenance_run_id = "8/27/2021 02:00:00 PM +00:00"
        argument_composer.classifications_to_include = ["Security", "Critical"]
        runtime = RuntimeCompositor(argument_composer.get_composed_arguments(), True, Constants.APT)
        runtime.set_legacy_test_type("SuccessInstallPath")
        CoreMain(argument_composer.get_composed_arguments())
        # check telemetry events
        self.__check_telemetry_events(runtime)
        # check status file
        with runtime.env_layer.file_system.open(runtime.execution_config.status_file_path, 'r') as file_handle:
            status_file_data = json.load(file_handle)[0]["status"]
        self.assertTrue(status_file_data["operation"] == Constants.INSTALLATION)
        substatus_file_data = status_file_data["substatus"]
        self.assertEquals(len(substatus_file_data), 4)
        self.assertTrue(substatus_file_data[0]["name"] == Constants.PATCH_ASSESSMENT_SUMMARY)
        self.assertTrue(substatus_file_data[0]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        # check started by set to 'User'
        self.assertTrue(json.loads(substatus_file_data[0]["formattedMessage"]["message"])['startedBy'], Constants.PatchAssessmentSummaryStartedBy.USER)
        self.assertTrue(substatus_file_data[1]["name"] == Constants.PATCH_INSTALLATION_SUMMARY)
        self.assertTrue(substatus_file_data[1]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        last_modified_time_from_installation_substatus_after_user_initiated_installation = json.loads(substatus_file_data[1]["formattedMessage"]["message"])["lastModifiedTime"]
        self.assertTrue(substatus_file_data[2]["name"] == Constants.PATCH_METADATA_FOR_HEALTHSTORE)
        self.assertTrue(substatus_file_data[2]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        self.assertTrue(substatus_file_data[3]["name"] == Constants.CONFIGURE_PATCHING_SUMMARY)
        self.assertTrue(substatus_file_data[3]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        # check status file for configure patching auto updates state
        message = json.loads(substatus_file_data[3]["formattedMessage"]["message"])
        self.assertEqual(message["automaticOSPatchState"], Constants.AutomaticOSPatchStates.DISABLED)  # auto OS updates are disabled in RuntimeCompositor, this is tested in Test-ConfigurePatchingProcessor
        # check status file for configure patching assessment state
        message = json.loads(substatus_file_data[3]["formattedMessage"]["message"])
        self.assertEqual(message["autoAssessmentStatus"]["autoAssessmentState"], Constants.AutoAssessmentStates.UNKNOWN)  # Configure patching for auto assessment did not execute since assessmentMode was not in input

        # operation #2: Auto Assessment
        argument_composer.activity_id = str(uuid.uuid4())
        argument_composer.included_classifications_list = self.included_package_name_mask_list = self.excluded_package_name_mask_list = []
        argument_composer.maintenance_run_id = None
        argument_composer.start_time = runtime.env_layer.datetime.standard_datetime_to_utc(datetime.datetime.utcnow())
        argument_composer.duration = Constants.AUTO_ASSESSMENT_MAXIMUM_DURATION
        argument_composer.reboot_setting = Constants.REBOOT_NEVER
        argument_composer.patch_mode = None
        argument_composer.exec_auto_assess_only = True
        runtime.execution_config.exec_auto_assess_only = True
        CoreMain(argument_composer.get_composed_arguments())
        # check telemetry events
        self.__check_telemetry_events(runtime)
        # check status file
        with runtime.env_layer.file_system.open(runtime.execution_config.status_file_path, 'r') as file_handle:
            status_file_data = json.load(file_handle)[0]["status"]

        # verifying the original operation name is preserved
        self.assertTrue(status_file_data["operation"] == Constants.INSTALLATION)
        substatus_file_data = status_file_data["substatus"]
        self.assertEquals(len(substatus_file_data), 4)
        self.assertTrue(substatus_file_data[0]["name"] == Constants.PATCH_ASSESSMENT_SUMMARY)
        self.assertTrue(substatus_file_data[0]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        # check started by set to 'Platform'
        self.assertTrue(json.loads(substatus_file_data[0]["formattedMessage"]["message"])['startedBy'], Constants.PatchAssessmentSummaryStartedBy.PLATFORM)
        # verifying the older operation summary is preserved
        self.assertTrue(substatus_file_data[1]["name"] == Constants.PATCH_INSTALLATION_SUMMARY)
        self.assertTrue(substatus_file_data[1]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        # validate lastModifiedTime in InstallationSummary is preserved from the user initiated installation operation
        last_modified_time_from_installation_substatus_after_platform_initiated_assessment = json.loads(substatus_file_data[1]["formattedMessage"]["message"])["lastModifiedTime"]
        self.assertEquals(last_modified_time_from_installation_substatus_after_user_initiated_installation, last_modified_time_from_installation_substatus_after_platform_initiated_assessment)
        self.assertTrue(substatus_file_data[2]["name"] == Constants.PATCH_METADATA_FOR_HEALTHSTORE)
        self.assertTrue(substatus_file_data[2]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        self.assertTrue(substatus_file_data[3]["name"] == Constants.CONFIGURE_PATCHING_SUMMARY)
        self.assertTrue(substatus_file_data[3]["status"].lower() == Constants.STATUS_SUCCESS.lower())
        # check status file for configure patching auto updates state
        message = json.loads(substatus_file_data[3]["formattedMessage"]["message"])
        self.assertEqual(message["automaticOSPatchState"], Constants.AutomaticOSPatchStates.DISABLED)  # auto OS updates are disabled in RuntimeCompositor
        # check status file for configure patching assessment state
        message = json.loads(substatus_file_data[3]["formattedMessage"]["message"])
        self.assertEqual(message["autoAssessmentStatus"]["autoAssessmentState"], Constants.AutoAssessmentStates.UNKNOWN)  # Configure patching for auto assessment did not execute since assessmentMode was not in input

        runtime.stop()

    def __check_telemetry_events(self, runtime):
        all_events = os.listdir(runtime.telemetry_writer.events_folder_path)
        self.assertTrue(len(all_events) > 0)
        latest_event_file = [pos_json for pos_json in os.listdir(runtime.telemetry_writer.events_folder_path) if re.search('^[0-9]+.json$', pos_json)][-1]
        with open(os.path.join(runtime.telemetry_writer.events_folder_path, latest_event_file), 'r+') as f:
            events = json.load(f)
            self.assertTrue(events is not None)
            self.assertTrue('ExtensionCoreLog' in events[0]['TaskName'])
            f.close()


if __name__ == '__main__':
    unittest.main()

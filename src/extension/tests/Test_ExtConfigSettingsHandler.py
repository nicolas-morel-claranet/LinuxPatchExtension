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

"""Unit test for extension ExtConfigSettingsHandler.py"""
import os
import shutil
import tempfile
import time
import unittest
from datetime import datetime
from extension.src.Constants import Constants
from extension.src.file_handlers.ExtConfigSettingsHandler import ExtConfigSettingsHandler
from extension.tests.helpers.RuntimeComposer import RuntimeComposer
from extension.tests.helpers.VirtualTerminal import VirtualTerminal


class TestExtConfigSettingsHandler(unittest.TestCase):

    def setUp(self):
        VirtualTerminal().print_lowlight("\n----------------- setup test runner -----------------")
        self.runtime = RuntimeComposer()
        self.logger = self.runtime.logger
        self.telemetry_writer = self.runtime.telemetry_writer
        self.logger.telemetry_writer = self.telemetry_writer
        self.json_file_handler = self.runtime.json_file_handler
        self.config_public_settings_fields = Constants.ConfigPublicSettingsFields

    def tearDown(self):
        VirtualTerminal().print_lowlight("\n----------------- tear down test runner -----------------")

    def mock_getenv(self, key):
        return 1234

    def test_get_seq_no_found_in_env_variable_for_enable_cmd(self):
        test_dir = tempfile.mkdtemp()
        os_getenv_backup = os.getenv
        os.getenv = self.mock_getenv

        self.runtime.create_temp_file(test_dir, "1234.settings", content=None)
        ext_config_settings_handler = ExtConfigSettingsHandler(self.logger, self.json_file_handler, test_dir)
        seq_no = ext_config_settings_handler.get_seq_no(is_enable_request=True)
        self.assertTrue(seq_no is not None)
        self.assertEqual(seq_no, 1234)

        os.getenv = os_getenv_backup
        shutil.rmtree(test_dir)

    def test_get_seq_no_found_in_env_variable_for_non_enable_cmd(self):
        test_dir = tempfile.mkdtemp()
        os_getenv_backup = os.getenv
        os.getenv = self.mock_getenv

        self.runtime.create_temp_file(test_dir, "1234.settings", content=None)
        ext_config_settings_handler = ExtConfigSettingsHandler(self.logger, self.json_file_handler, test_dir)
        seq_no = ext_config_settings_handler.get_seq_no(is_enable_request=False)
        self.assertTrue(seq_no is not None)
        self.assertEqual(seq_no, 1234)

        os.getenv = os_getenv_backup
        shutil.rmtree(test_dir)

    def test_get_seq_no_not_found_in_env_variable_for_non_enable_cmd(self):
        # not set in env var
        test_dir = tempfile.mkdtemp()
        self.runtime.create_temp_file(test_dir, "1234.settings", content=None)
        ext_config_settings_handler = ExtConfigSettingsHandler(self.logger, self.json_file_handler, test_dir)
        seq_no = ext_config_settings_handler.get_seq_no(is_enable_request=False)
        self.assertTrue(seq_no is None)
        shutil.rmtree(test_dir)

        # set in env var, settings file does not exist
        test_dir = tempfile.mkdtemp()
        os_getenv_backup = os.getenv
        os.getenv = self.mock_getenv
        ext_config_settings_handler = ExtConfigSettingsHandler(self.logger, self.json_file_handler, test_dir)
        seq_no = ext_config_settings_handler.get_seq_no(is_enable_request=False)
        self.assertTrue(seq_no is None)
        os.getenv = os_getenv_backup
        shutil.rmtree(test_dir)

    def test_get_seq_no_not_found_in_env_variable_for_enable_cmd(self):
        # set in env var, settings file does not exist
        test_dir = tempfile.mkdtemp()
        os_getenv_backup = os.getenv
        os.getenv = self.mock_getenv
        ext_config_settings_handler = ExtConfigSettingsHandler(self.logger, self.json_file_handler, test_dir)
        seq_no = ext_config_settings_handler.get_seq_no(is_enable_request=True)
        self.assertTrue(seq_no is None)
        os.getenv = os_getenv_backup
        shutil.rmtree(test_dir)

        # not set in env var, seq_no fetched from config settings file
        test_dir = tempfile.mkdtemp()
        self.runtime.create_temp_file(test_dir, "1234.settings", content=None)
        ext_config_settings_handler = ExtConfigSettingsHandler(self.logger, self.json_file_handler, test_dir)
        seq_no = ext_config_settings_handler.get_seq_no(is_enable_request=True)
        self.assertTrue(seq_no is not None)
        self.assertEqual(seq_no, 1234)
        shutil.rmtree(test_dir)

    def test_seq_no_from_config_folder(self):
        files = [
            {"name": '1.json', "lastModified": '2019-07-20T12:12:14Z'},
            {"name": '2.json', "lastModified": '2018-07-20T12:12:14Z'},
            {"name": '11.json', "lastModified": '2019-07-20T12:12:14Z'},
            {"name": '12.settings', "lastModified": '2019-07-02T12:12:14Z'},
            {"name": '121.settings', "lastModified": '2017-07-20T12:12:14Z'},
            {"name": '122.settings', "lastModified": '2019-07-20T12:12:14Z'},
            {"name": '123.json', "lastModified": '2019-07-20T11:12:14Z'},
            {"name": '10.settings', "lastModified": '2019-07-20T10:12:14Z'},
            {"name": '111.settings', "lastModified": '2019-07-20T12:10:14Z'},
            {"name": 'dir1', "lastModified": '2019-07-20T12:12:14Z'},
            {"name": '111111', "lastModified": '2019-07-20T12:12:14Z'},
            {"name": '2.settings', "lastModified": '2019-07-20T12:12:12Z'},
            {"name": '3a.settings', "lastModified": '2019-07-20T12:12:14Z'},
            {"name": 'aa.settings', "lastModified": '2019-07-20T12:12:14Z'},
            {"name": 'a3.settings', "lastModified": '2019-07-20T12:12:14Z'},
            {"name": '22.settings.settings', "lastModified": '2019-07-20T12:12:14Z'},
            {"name": '0.settings', "lastModified": '2019-07-19T12:12:14Z'},
            {"name": 'abc.123.settings', "lastModified": '2019-07-20T12:12:14Z'},
            {"name": '.settings', "lastModified": '2019-07-20T12:12:14Z'}
        ]

        test_dir = tempfile.mkdtemp()
        for file in files:
            file_path = os.path.join(test_dir, file["name"])
            with open(file_path, 'w') as f:
                timestamp = time.mktime(datetime.strptime(file["lastModified"], Constants.UTC_DATETIME_FORMAT).timetuple())
                os.utime(file_path, (timestamp, timestamp))
                f.close()
        ext_config_settings_handler = ExtConfigSettingsHandler(self.logger, self.json_file_handler, test_dir)
        seq_no = ext_config_settings_handler.get_seq_no(is_enable_request=True)
        self.assertEqual(122, seq_no)
        shutil.rmtree(test_dir)

    def test_seq_no_from_empty_config_folder(self):
        test_dir = tempfile.mkdtemp()
        ext_config_settings_handler = ExtConfigSettingsHandler(self.logger, self.json_file_handler, test_dir)
        seq_no = ext_config_settings_handler.get_seq_no(is_enable_request=True)
        self.assertEqual(None, seq_no)
        shutil.rmtree(test_dir)

    def test_are_config_settings_valid(self):
        ext_config_settings_handler = ExtConfigSettingsHandler(self.logger, self.json_file_handler, "mockConfig")

        runtime_settings_key = Constants.RUNTIME_SETTINGS
        handler_settings_key = Constants.HANDLER_SETTINGS
        public_settings_key = Constants.PUBLIC_SETTINGS

        config_settings_json = None
        self.assertFalse(ext_config_settings_handler.are_config_settings_valid(config_settings_json))

        config_settings_json = []
        self.assertFalse(ext_config_settings_handler.are_config_settings_valid(config_settings_json))

        config_settings_json = {}
        self.assertFalse(ext_config_settings_handler.are_config_settings_valid(config_settings_json))

        # runtimeSettings not in file
        config_settings_json = {'key': 'test'}
        self.assertFalse(ext_config_settings_handler.are_config_settings_valid(config_settings_json))
        # runtimeSettings not of type list
        config_settings_json = {runtime_settings_key: "test"}
        self.assertFalse(ext_config_settings_handler.are_config_settings_valid(config_settings_json))
        config_settings_json = {runtime_settings_key: {}}
        self.assertFalse(ext_config_settings_handler.are_config_settings_valid(config_settings_json))
        # runtimeSettings is None or empty
        config_settings_json = {runtime_settings_key: None}
        self.assertFalse(ext_config_settings_handler.are_config_settings_valid(config_settings_json))
        # runtimeSettings is on len 0
        config_settings_json = {runtime_settings_key: []}
        self.assertFalse(ext_config_settings_handler.are_config_settings_valid(config_settings_json))

        # handlerSettings not in runtimeSettings
        config_settings_json = {runtime_settings_key: ["test"]}
        self.assertFalse(ext_config_settings_handler.are_config_settings_valid(config_settings_json))
        # handlerSettings not of type dict
        config_settings_json = {runtime_settings_key: [{handler_settings_key: []}]}
        self.assertFalse(ext_config_settings_handler.are_config_settings_valid(config_settings_json))
        config_settings_json = {runtime_settings_key: [{handler_settings_key: "test"}]}
        self.assertFalse(ext_config_settings_handler.are_config_settings_valid(config_settings_json))
        config_settings_json = {runtime_settings_key: [{handler_settings_key: ["test"]}]}
        self.assertFalse(ext_config_settings_handler.are_config_settings_valid(config_settings_json))
        # handlerSettings is None or empty
        config_settings_json = {runtime_settings_key: [{handler_settings_key: None}]}
        self.assertFalse(ext_config_settings_handler.are_config_settings_valid(config_settings_json))
        config_settings_json = {runtime_settings_key: [{handler_settings_key: {}}]}
        self.assertFalse(ext_config_settings_handler.are_config_settings_valid(config_settings_json))

        # publicSettings not in handlerSettings
        config_settings_json = {runtime_settings_key: [{handler_settings_key: {"testKey": "testVal"}}]}
        self.assertFalse(ext_config_settings_handler.are_config_settings_valid(config_settings_json))
        # handlerSettings not of type dict
        config_settings_json = {runtime_settings_key: [{handler_settings_key: {"testKey": "testVal", public_settings_key: []}}]}
        self.assertFalse(ext_config_settings_handler.are_config_settings_valid(config_settings_json))
        config_settings_json = {runtime_settings_key: [{handler_settings_key: {"testKey": "testVal", public_settings_key: "test"}}]}
        self.assertFalse(ext_config_settings_handler.are_config_settings_valid(config_settings_json))
        config_settings_json = {runtime_settings_key: [{handler_settings_key: {"testKey": "testVal", public_settings_key: ["test"]}}]}
        self.assertFalse(ext_config_settings_handler.are_config_settings_valid(config_settings_json))
        # publicSettings is None or empty
        config_settings_json = {runtime_settings_key: [{handler_settings_key: {"testKey": "testVal", public_settings_key: None}}]}
        self.assertFalse(ext_config_settings_handler.are_config_settings_valid(config_settings_json))
        config_settings_json = {runtime_settings_key: [{handler_settings_key: {"testKey": "testVal", public_settings_key: {}}}]}
        self.assertFalse(ext_config_settings_handler.are_config_settings_valid(config_settings_json))

        # accepted config settings
        config_settings_json = {
            runtime_settings_key: [{
                handler_settings_key: {
                    "testKey": "testVal",
                    public_settings_key: {
                        self.config_public_settings_fields.operation: "test",
                        self.config_public_settings_fields.activity_id: "12345-2312-1234-23245-32112",
                        self.config_public_settings_fields.start_time: "2019-07-20T12:12:14Z",
                        self.config_public_settings_fields.maximum_duration: "20m",
                        self.config_public_settings_fields.reboot_setting: "IfRequired",
                        self.config_public_settings_fields.include_classifications: ["Critical","Security"],
                        self.config_public_settings_fields.include_patches: ["*", "test*", "*ern*=1.2*", "kern*=1.23.45"],
                        self.config_public_settings_fields.exclude_patches: ["*", "test", "*test"],
                        self.config_public_settings_fields.internal_settings: "<serialized-json>",
                        self.config_public_settings_fields.maintenance_run_id: "2019-07-20T12:12:14Z",
                        self.config_public_settings_fields.patch_mode: "AutomaticByPlatform",
                        self.config_public_settings_fields.assessment_mode: "AutomaticByPlatform",
                        self.config_public_settings_fields.maximum_assessment_interval: "PT3H",
                    }
                }
            }]
        }
        self.assertTrue(ext_config_settings_handler.are_config_settings_valid(config_settings_json))

        # Testing with only required fields
        config_settings_json = {
            runtime_settings_key: [{
                handler_settings_key: {
                    public_settings_key: {
                        self.config_public_settings_fields.operation: "test",
                        self.config_public_settings_fields.activity_id: "12345-2312-1234-23245-32112",
                        self.config_public_settings_fields.start_time: "2019-07-20T12:12:14Z"
                    }
                }
            }]
        }
        self.assertTrue(ext_config_settings_handler.are_config_settings_valid(config_settings_json))

    def test_read_file_success(self):
        ext_config_settings_handler = ExtConfigSettingsHandler(self.logger, self.json_file_handler, os.path.join(os.path.pardir, "tests", "helpers"))
        seq_no = "1234"
        config_values = ext_config_settings_handler.read_file(seq_no)
        self.assertEqual(config_values.__getattribute__(self.config_public_settings_fields.operation), "Installation")
        self.assertEqual(config_values.__getattribute__(self.config_public_settings_fields.reboot_setting), "IfRequired")

    def test_read_file_failures(self):
        ext_config_settings_handler = ExtConfigSettingsHandler(self.logger, self.json_file_handler, os.path.join(os.path.pardir, "tests", "helpers"))
        # Seq_no invalid, none, -1, empty
        seq_no = None
        self.assertRaises(Exception, ext_config_settings_handler.read_file, seq_no)
        seq_no = -1
        self.assertRaises(Exception, ext_config_settings_handler.read_file, seq_no)
        seq_no = ""
        self.assertRaises(Exception, ext_config_settings_handler.read_file, seq_no)

        # FileNotFound
        seq_no = "12345"
        self.assertRaises(Exception, ext_config_settings_handler.read_file, seq_no)

        # empty file
        test_dir = tempfile.mkdtemp()
        file_name = "123.settings"
        self.runtime.create_temp_file(test_dir, file_name, content=None)
        ext_config_settings_handler = ExtConfigSettingsHandler(self.logger, self.json_file_handler, test_dir)
        seq_no = "123"
        self.assertRaises(Exception, ext_config_settings_handler.read_file, seq_no)
        shutil.rmtree(test_dir)

        # empty valid file
        test_dir = tempfile.mkdtemp()
        file_name = "1237.settings"
        self.runtime.create_temp_file(test_dir, file_name, content="{}")
        ext_config_settings_handler = ExtConfigSettingsHandler(self.logger, self.json_file_handler, test_dir)
        seq_no = "1237"
        self.assertRaises(Exception, ext_config_settings_handler.read_file, seq_no)
        shutil.rmtree(test_dir)

        # file not valid
        test_dir = tempfile.mkdtemp()
        seq_no = "1237"
        file_name = seq_no + ".settings"
        self.runtime.create_temp_file(test_dir, file_name, content='{"runtimeSettings": []}')
        ext_config_settings_handler = ExtConfigSettingsHandler(self.logger, self.json_file_handler, test_dir)
        self.assertRaises(Exception, ext_config_settings_handler.read_file, seq_no)
        shutil.rmtree(test_dir)

    def test_read_all_config_settings_from_file(self):
        ext_config_settings_handler = ExtConfigSettingsHandler(self.logger, self.json_file_handler, os.path.join(os.path.pardir, "tests", "helpers"))
        seq_no = ext_config_settings_handler.get_seq_no(is_enable_request=True)
        config_settings = ext_config_settings_handler.read_file(seq_no)

        # verify operation is read successfully
        self.assertNotEqual(config_settings.__getattribute__(self.config_public_settings_fields.operation), None)
        self.assertEqual(config_settings.__getattribute__(self.config_public_settings_fields.operation), "Installation")

        # verify activityId is read successfully
        self.assertNotEqual(config_settings.__getattribute__(self.config_public_settings_fields.activity_id), None)
        self.assertEqual(config_settings.__getattribute__(self.config_public_settings_fields.activity_id), "12345-2312-1234-23245-32112")

        # verify startTime is read successfully
        self.assertNotEqual(config_settings.__getattribute__(self.config_public_settings_fields.start_time), None)
        self.assertEqual(config_settings.__getattribute__(self.config_public_settings_fields.start_time), "2021-08-08T12:34:56Z")

        # verify maximumDuration is read successfully
        self.assertNotEqual(config_settings.__getattribute__(self.config_public_settings_fields.maximum_duration), None)
        self.assertEqual(config_settings.__getattribute__(self.config_public_settings_fields.maximum_duration), "PT2H")

        # verify rebootSetting is read successfully
        self.assertNotEqual(config_settings.__getattribute__(self.config_public_settings_fields.reboot_setting), None)
        self.assertEqual(config_settings.__getattribute__(self.config_public_settings_fields.reboot_setting), "IfRequired")

        # verify classificationsToInclude is read successfully
        self.assertNotEqual(config_settings.__getattribute__(self.config_public_settings_fields.include_classifications), None)
        self.assertTrue("Critical" in config_settings.__getattribute__(self.config_public_settings_fields.include_classifications)
                        and "Security" in config_settings.__getattribute__(self.config_public_settings_fields.include_classifications))

        # verify patchesToInclude is read successfully
        self.assertNotEqual(config_settings.__getattribute__(self.config_public_settings_fields.include_patches), None)
        self.assertTrue("*ern*=1.2*" in config_settings.__getattribute__(self.config_public_settings_fields.include_patches)
                        and "kern*=1.23.45" in config_settings.__getattribute__(self.config_public_settings_fields.include_patches))

        # verify patchesToExclude is read successfully
        self.assertNotEqual(config_settings.__getattribute__(self.config_public_settings_fields.exclude_patches), None)
        self.assertTrue("test" in config_settings.__getattribute__(self.config_public_settings_fields.exclude_patches))

        # verify internalSettings is read successfully
        self.assertNotEqual(config_settings.__getattribute__(self.config_public_settings_fields.internal_settings), None)
        self.assertEqual(config_settings.__getattribute__(self.config_public_settings_fields.internal_settings), "test")

        # verify patchMode is read successfully
        self.assertNotEqual(config_settings.__getattribute__(self.config_public_settings_fields.patch_mode), None)
        self.assertEqual(config_settings.__getattribute__(self.config_public_settings_fields.patch_mode), "AutomaticByPlatform")

        # verify maintenanceRunId is read successfully
        self.assertNotEqual(config_settings.__getattribute__(self.config_public_settings_fields.maintenance_run_id), None)
        self.assertEqual(config_settings.__getattribute__(self.config_public_settings_fields.maintenance_run_id), "2019-07-20T12:12:14Z")

        # verify healthStoreId is read successfully
        self.assertNotEqual(config_settings.__getattribute__(self.config_public_settings_fields.health_store_id), None)
        self.assertEqual(config_settings.__getattribute__(self.config_public_settings_fields.health_store_id),"2021-09-15T12:12:14Z")

        # verify assessmentMode is read successfully
        self.assertNotEqual(config_settings.__getattribute__(self.config_public_settings_fields.assessment_mode), None)
        self.assertEqual(config_settings.__getattribute__(self.config_public_settings_fields.assessment_mode), "AutomaticByPlatform")

        # verify maximumAssessmentInterval is read successfully
        self.assertNotEqual(config_settings.__getattribute__(self.config_public_settings_fields.maximum_assessment_interval), None)
        self.assertEqual(config_settings.__getattribute__(self.config_public_settings_fields.maximum_assessment_interval), "PT3H")


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(TestExtConfigSettingsHandler)
    unittest.TextTestRunner(verbosity=2).run(SUITE)

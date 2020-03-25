"""Unit test for extension ExtConfigSettingsHandler.py"""
import os
import shutil
import tempfile
import time
import unittest
from datetime import datetime
from unittest import mock       #TODO: Remove dependency on mock.
from src.Constants import Constants
from src.file_handlers.JsonFileHandler import JsonFileHandler
from src.file_handlers.ExtConfigSettingsHandler import ExtConfigSettingsHandler
from src.local_loggers.Logger import Logger
from tests.helpers.VirtualTerminal import VirtualTerminal


class TestExtConfigSettingsHandler(unittest.TestCase):

    def setUp(self):
        VirtualTerminal().print_lowlight("\n----------------- setup test runner -----------------")
        self.logger = Logger()
        self.json_file_handler = JsonFileHandler(self.logger)
        self.config_public_settings_fields = Constants.ConfigPublicSettingsFields

    def tearDown(self):
        VirtualTerminal().print_lowlight("\n----------------- tear down test runner -----------------")

    @mock.patch('src.file_handlers.ExtConfigSettingsHandler.os.getenv', autospec=True, return_value=1234)
    def test_get_seq_no_from_env_variable(self, seq_no_from_env_var):
        ext_config_settings_handler = ExtConfigSettingsHandler(self.logger, self.json_file_handler, "mockConfig")
        seq_no = ext_config_settings_handler.get_seq_no()
        self.assertIsNotNone(seq_no)
        self.assertEqual(seq_no, seq_no_from_env_var.return_value)

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
                timestamp = time.mktime(datetime.strptime(file["lastModified"], '%Y-%m-%dT%H:%M:%S%z').timetuple())
                os.utime(file_path, (timestamp, timestamp))
                f.close()
        ext_config_settings_handler = ExtConfigSettingsHandler(self.logger, self.json_file_handler, test_dir)
        seq_no = ext_config_settings_handler.get_seq_no()
        self.assertEqual(122, seq_no)
        shutil.rmtree(test_dir)

    def test_seq_no_from_empty_config_folder(self):
        test_dir = tempfile.mkdtemp()
        ext_config_settings_handler = ExtConfigSettingsHandler(self.logger, self.json_file_handler, test_dir)
        seq_no = ext_config_settings_handler.get_seq_no()
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
                        self.config_public_settings_fields.internal_settings: "<serialized-json>"
                    }
                }
            }]
        }
        self.assertTrue(ext_config_settings_handler.are_config_settings_valid(config_settings_json))

        config_settings_json = {
            runtime_settings_key: [{
                handler_settings_key: {
                    "testKey": "testVal",
                    public_settings_key: {
                        self.config_public_settings_fields.operation: "test",
                        self.config_public_settings_fields.activity_id: "12345-2312-1234-23245-32112",
                        self.config_public_settings_fields.start_time: "2019-07-20T12:12:14Z"
                    }
                }
            }]
        }
        self.assertTrue(ext_config_settings_handler.are_config_settings_valid(config_settings_json))

        config_settings_json = {
            runtime_settings_key: [{
                handler_settings_key: {
                    "testKey": "testVal",
                    public_settings_key: {
                        self.config_public_settings_fields.operation: "test",
                        self.config_public_settings_fields.activity_id: "12345-2312-1234-23245-32112",
                        self.config_public_settings_fields.start_time: "2019-07-20T12:12:14Z",
                        self.config_public_settings_fields.maximum_duration: "",
                        self.config_public_settings_fields.reboot_setting: "IfRequired",
                        self.config_public_settings_fields.include_classifications: ["Critical", "Security"],
                        self.config_public_settings_fields.include_patches: ["*", "test*", "*ern*=1.2*", "kern*=1.23.45"],
                        self.config_public_settings_fields.exclude_patches: ["*", "test", "*test"],
                        self.config_public_settings_fields.internal_settings: "<serialized-json>"
                    }
                }
            }]
        }
        self.assertTrue(ext_config_settings_handler.are_config_settings_valid(config_settings_json))

    def test_read_file_success(self):
        ext_config_settings_handler = ExtConfigSettingsHandler(self.logger, self.json_file_handler, os.path.join(os.path.pardir, "tests", "helpers"))
        seq_no = "1234"
        config_values = ext_config_settings_handler.read_file(seq_no)
        self.assertEqual(config_values.__getattribute__(self.config_public_settings_fields.operation), "Deployment")
        self.assertEqual(config_values.__getattribute__(self.config_public_settings_fields.reboot_setting), "IfRequired")

    @mock.patch('src.file_handlers.JsonFileHandler.time.sleep', autospec=True)
    def test_read_file_failures(self, time_sleep):
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
        with open(os.path.join(test_dir, file_name), 'w') as f:
            f.close()
        ext_config_settings_handler = ExtConfigSettingsHandler(self.logger, self.json_file_handler, test_dir)
        seq_no = "123"
        self.assertRaises(Exception, ext_config_settings_handler.read_file, seq_no)
        shutil.rmtree(test_dir)

        # empty valid file
        test_dir = tempfile.mkdtemp()
        file_name = "1237.settings"
        with open(os.path.join(test_dir, file_name), 'w') as f:
            f.write("{}")
            f.close()
        ext_config_settings_handler = ExtConfigSettingsHandler(self.logger, self.json_file_handler, test_dir)
        seq_no = "1237"
        self.assertRaises(Exception, ext_config_settings_handler.read_file, seq_no)
        shutil.rmtree(test_dir)

        # file not valid
        seq_no = "1234"
        ext_config_settings_handler = ExtConfigSettingsHandler(self.logger, self.json_file_handler, os.path.join(os.path.pardir, "tests", "helpers"))
        with mock.patch('tests.TestExtConfigSettingsHandler.ExtConfigSettingsHandler.are_config_settings_valid', autospec=True, return_value=False):
            self.assertRaises(Exception, ext_config_settings_handler.read_file, seq_no)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(TestExtConfigSettingsHandler)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
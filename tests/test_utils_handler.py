import unittest
import os
import hashlib
import json
import random
import shutil
import tempfile
import logging
import src.utils.handler as handler
import src.config as config

class TestUtils(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_keys = config.config_keys
        self.post_keys = config.post_keys
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_create_directory(self):
        dir_path = os.path.join(self.temp_dir, 'test_dir')
        handler.create_directory(dir_path)
        self.assertTrue(os.path.exists(dir_path))

    def test_calculate_hash(self):
        file_path = os.path.join(self.temp_dir, 'test_file.txt')
        with open(file_path, 'w') as f:
            f.write('test content')
        calculated_hash = handler.calculate_hash(file_path)
        expected_hash = hashlib.sha1('test content'.encode()).hexdigest()
        self.assertEqual(calculated_hash, expected_hash)

    def test_load_and_save_hash(self):
        handler.save_new_hash('test_hash')
        loaded_hash = handler.load_old_hash()
        self.assertEqual(loaded_hash, 'test_hash')

    def test_load_config(self):
        config_path = 'config.json'
        config_data = handler.load_config(config_path)
        self.assertIsNotNone(config_data)
        for key in self.config_keys:
            self.assertIn(key, config_data)


    def test_parse_config(self):
        config_data = {'file_extensions': ['txt', 'md']}
        parsed_config = handler.parse_config(config_data)
        self.assertEqual(parsed_config['file_extensions'], ['txt', 'md'])

    def test_extract_metadata(self):
        post_content = '---\ntitle: Test Post\ntags: [test, example]\n---\nContent'
        metadata = handler.extract_metadata(post_content)
        self.assertEqual(metadata, {'title': 'Test Post', 'tags': '[test, example]'})
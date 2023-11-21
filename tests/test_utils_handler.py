import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import unittest
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
        self.config_keys = [
            'posts_directory',
            'backup_directory',
            'file_extensions',
            'blog_title',
            'author',
            'description',
        ]
        self.post_keys = post_keys = [
            'id',
            'type',
            'tags',
            'title',
            'sanitized_title',
            'last_updated',
            'content',
        ]
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_create_directory(self):
        dir_path = os.path.join(self.temp_dir, 'test_dir')
        handler.create_directory(dir_path)
        self.assertTrue(os.path.exists(dir_path))

    def test_calculate_hash(self):
        hash_before_file = handler.calculate_hash(self.temp_dir)
        file_path = os.path.join(self.temp_dir, 'test_file.txt')
        with open(file_path, 'w') as f:
            f.write('test content')
        hash_after_file = handler.calculate_hash(self.temp_dir)
        self.assertNotEqual(hash_before_file, hash_after_file)

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
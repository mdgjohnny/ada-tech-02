# common_setup.py
import os
import logging
import random
import tempfile
import shutil
import unittest

class CommonSetup(unittest.TestCase):

    def __init__(self, *args, **kwargs):

        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.post_amount = random.randint(15, 30)
        self.logger.info(f'Amount of test posts: {self.post_amount}')
        self.posts_per_page = random.randint(1, 10)
        self.logger.info(f'Amount of posts per page: {self.posts_per_page}')
        self.test_dir = tempfile.mkdtemp()
        self.logger.info(f'Using temporary test directory {self.test_dir}')
        self.backup_dir = tempfile.mkdtemp()
        self.logger.info(f'Using temporary backup directory {self.backup_dir}')
        self.temp_dirs = [self.test_dir, self.backup_dir]
        self.logger.info(f'Directories are {self.temp_dirs}')
        self.config_keys = [
            'source_directory',
            'backup_directory',
            'file_extensions',
            'blog_title',
            'author',
            'description',
        ]
        self.post_keys = ['id', 'tags', 'title', 'content']
        self.config_data = {
            'source_directory': self.test_dir,
            'backup_directory': self.backup_dir,
            'file_extensions': ['.md']
        }
        self.posts = [{'id': 'test_post', 'tags': ['test', 'example'], 'title': 'Test Post', 'content': 'Content'}]
        self.default_template = 'index.html'
        self.template_dir = '../templates'

    def tearDown(self):
        for dir in self.temp_dirs:
            self.logger.info(f'Removing temporary directory {dir}')
            shutil.rmtree(dir)
            assert not os.path.exists(dir), "Directory not removed"
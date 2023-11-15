import unittest
import os
import random
import shutil
import tempfile
import logging
from src.generate_pages import load_config, load_posts, generate_page, generate_pages, calculate_hash

class TestGeneratePages(unittest.TestCase):

    def setUp(self):
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        self.post_amount = random.randint(15, 30)
        self.logger.info(f'Generating {self.post_amount} test posts')
        self.posts_per_page = random.randint(1, 10)  # Randomized posts per page
        self.logger.info(f'Using {self.posts_per_page} posts per page')
        self.test_dir = tempfile.mkdtemp()
        self.logger.info(f'Using temporary directory {self.test_dir}')
        self.backup_dir = tempfile.mkdtemp()
        self.logger.info(f'Using temporary directory {self.backup_dir}')
        self.temp_dirs = [self.test_dir, self.backup_dir]
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
        
    def tearDown(self):
        for dir in self.temp_dirs:
            self.logger.info(f'Removing temporary directory {self.test_dir}')
            shutil.rmtree(dir)

    def test_load_config(self):
        # Test loading the configuration
        config_path = 'config.json'
        config_data = load_config(config_path)

        # Add your specific assertions here based on the expected content of your config file
        self.assertIsNotNone(config_data)
        for key in self.config_keys:
            self.assertIn(key, config_data)

    def test_load_posts(self):
        posts = load_posts(self.config_data)

        # Add your specific assertions here based on the expected content of the test post
        self.assertEqual(len(posts), self.post_amount)
        self.assertEqual(posts[0]['title'], 'Test Post 1')
        self.assertEqual(posts[0]['tags'], ['test', 'example'])

    def test_generate_page(self): # Test if it generates the correct amount of pages
        # Create multiple test markdown files in the temporary directory
        for i in range(1, self.post_amount + 1):
            test_post_path = os.path.join(self.test_dir, f'test_post_{i}.md')
            test_post_content = f'---\ntitle: Test Post {i}\ntags: [test, example]\n---\nContent {i}'
            with open(test_post_path, 'w') as test_post_file:
                test_post_file.write(test_post_content)
                self.logger.info(f'Writing post {i} to {test_post_path}')
        # Generate a single page and check for the correct output
        generate_pages(posts_per_page=self.posts_per_page)
        # Check that the correct number of pages were generated
        expected_pages = (self.post_amount + self.posts_per_page - 1) // self.posts_per_page
        generated_pages = len([name for name in os.listdir(self.test_dir) if name.endswith('.html')])
        self.assertEqual(generated_pages, expected_pages)


        
 
if __name__ == '__main__':
    unittest.main()

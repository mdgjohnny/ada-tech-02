import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# print sys path
print(sys.path)
import unittest
import random
import time
import shutil
import tempfile
import logging
from src.generate_pages import (
    load_posts, 
    generate_pages,
    get_template,
    write_page,
    process_post,
    generate_post,
)
from src.config import (
    parsed_config,
)
from bs4 import BeautifulSoup


INDEX_TEMPLATE = parsed_config['index_template']

class TestGeneratePages(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.ERROR)
        self.logger = logging.getLogger(__name__)
        self.post_amount = random.randint(2, 10)
        self.logger.info(f'Amount of test posts: {self.post_amount}')
        self.posts_per_page = round(self.post_amount // 2)
        self.logger.info(f'Amount of posts per page: {self.posts_per_page}')
        self.test_dir = tempfile.mkdtemp()
        self.logger.info(f'Using temporary test directory {self.test_dir}')
        self.backup_dir = tempfile.mkdtemp()
        self.logger.info(f'Using temporary backup directory {self.backup_dir}')
        self.temp_dirs = [self.test_dir, self.backup_dir]
        self.logger.info(f'Directories are {self.temp_dirs}')
        self.config_data = {
            'source_directory': self.test_dir,
            'backup_directory': self.backup_dir,
            'file_extensions': ['.md']
        }
        self.generated_posts = self.generate_test_posts(self.post_amount, self.test_dir)
        assert self.generated_posts is not None

    def tearDown(self):
        for temp_dir in self.temp_dirs:
            shutil.rmtree(temp_dir)

    def generate_test_posts(self, amount, test_dir):
        for i in range(1, amount + 1):
            test_post_path = os.path.join(test_dir, f'test_post_{i}.md')
            test_post_content = f'---\ntitle: Test Post {i}\ntags: [test, example]\n---\nContent {i}'
            with open(test_post_path, 'w') as test_post_file:
                test_post_file.write(test_post_content)
                print(f'Writing post {i} to {test_post_path}')

        generated_posts = load_posts(test_dir)
        print(f"{len(generated_posts)} posts generated at {test_dir}")

        return generated_posts

    def test_get_template(self):
        tests_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(tests_dir)
        template_dir = os.path.join(project_root, 'templates')
        self.logger.info(f'Template directory is: {template_dir}')
        template = get_template(template_name=INDEX_TEMPLATE, template_directory=template_dir)
        # Log some information about the template
        self.logger.info(f'Template type: {type(template)}')
        self.logger.info(f'Template name: {template.name}')
        self.logger.info(f'Template filename: {template.filename}')
        self.assertIsNotNone(template)

    def test_write_page(self):
        output_filename = os.path.join(self.test_dir, 'test_page.html')
        output_html = '<html><body>Test content</body></html>'

        write_page(output_filename, output_html)

        self.assertTrue(os.path.exists(output_filename), "Output file not created.")
        with open(output_filename, 'r') as output_file:
            content = output_file.read()
            self.assertEqual(content, output_html, "Content mismatch.")

    def test_process_post(self):
        posts = self.generated_posts
        assert posts is not None, "No posts generated."
        processed_posts = []
        for post in posts:
            post_sanitized_title = post['sanitized_title']
            test_post_name = f'{post_sanitized_title}.md'
            post_path = os.path.join(self.test_dir, test_post_name)
            assert os.path.exists(post_path), f"Post {test_post_name} not found."
            processed_post = process_post(post_path)
            processed_posts.append(processed_post)
        for processed_post, original_post in zip(processed_posts, self.generated_posts):
            self.assertIsInstance(processed_post, dict)
            self.assertEqual(processed_post['title'], original_post['title'])
            self.assertEqual(processed_post['tags'], original_post['tags'])
            self.assertEqual(processed_post['content'], original_post['content'])

    def test_load_posts(self):
        posts = self.generated_posts
        self.assertEqual(len(posts), self.post_amount)
        processed_posts = load_posts(self.test_dir)
        self.assertEqual(len(processed_posts), self.post_amount)

    def test_generate_post(self):
        posts = self.generated_posts
        for post in posts:
            post_path = os.path.join(self.test_dir, post['sanitized_title'] + '.html')
            assert os.path.exists(post_path) == False, f"Post {post_path} already exists."
            print(f"Calling generate post with {post}")
            generate_post(post, self.test_dir)
            assert os.path.exists(post_path), f"Post {post_path} not found."
            self.assertTrue(os.path.exists(post_path))

            # Check if the post title, content, and navigation links are present in the HTML file
            with open(post_path, 'r') as f:
                html_content = f.read()
                self.assertIn(post['title'], html_content)
                self.assertIn(post['content'], html_content)


    def test_generate_pages(self):
        output_dir = os.path.join(self.test_dir, 'pages')
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        generate_pages(self.generated_posts, self.posts_per_page, output_dir)
        expected_pages = (self.post_amount + self.posts_per_page - 1) // self.posts_per_page
        self.logger.info(f"Expected pages: {expected_pages}")
        files_in_dir = os.listdir(output_dir)
        assert files_in_dir != [], "No files in directory."
        self.logger.info(f"Files in directory: {files_in_dir}")
        generated_pages = [name for name in os.listdir(output_dir) if name.endswith('.html')]
        assert generated_pages != [], "No pages generated."
        self.logger.info(f"Generated pages: {generated_pages}")
        self.assertEqual(len(generated_pages), expected_pages)
        # Sort generated pages according to the number
        generated_pages.sort(key=lambda name: int(name.split('.')[0]))
        print(generated_pages)

        # Check if the content of the pages is correct
        for i, page in enumerate(generated_pages):
            with open(os.path.join(output_dir, page), 'r') as f:
                self.logger.info(f"Checking page {i + 1}")
                html_content = f.read()
                soup = BeautifulSoup(html_content, 'html.parser')
                pretty_html = soup.prettify()
                self.logger.info(f"Page {i + 1}:\n{pretty_html}")

                # Check if the navigation links are present in the HTML file
                if expected_pages > 1 and i != 0:
                    prev_link = soup.find('a', string='Previous')
                    self.assertIsNotNone(prev_link, f"Previous link not found in page {i + 1}")

                if expected_pages > 1 and i != expected_pages - 1:
                    next_link = soup.find('a', string='Next')
                    self.assertIsNotNone(next_link, f"Next link not found in page {i + 1}")

                # Check if the posts are present in the HTML file
                start_index = i * self.posts_per_page
                end_index = start_index + self.posts_per_page
                expected_posts = self.generated_posts[start_index:end_index]
                for post in expected_posts:
                    self.assertIn(post['title'], html_content, f"Post {post['title']} not found in page {i + 1}")
                    self.assertIn(post['content'], html_content, f"Post {post['content']} not found in page {i + 1}")
if __name__ == '__main__':
    unittest.main()

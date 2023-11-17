import unittest
import os
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
    posts_dir,
    backup_dir,
    fallback_extensions,
    template_directory,
    template_filename,
)
from bs4 import BeautifulSoup


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

        print(generated_posts)

        return generated_posts

    def test_get_template(self):
        tests_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(tests_dir)
        template_dir = os.path.join(project_root, 'templates')
        self.logger.info(f'Template directory is: {template_dir}')
        template = get_template(template_name=template_filename, template_directory=template_dir)
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
        os.remove(output_filename)

    def test_process_post(self):
        processed_posts = []
        for post in self.generated_posts:
            post_id = post['id']
            test_post_name = f'test_post_{post_id}.md'
            post_path = os.path.join(self.test_dir, test_post_name)
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
        for post in self.generated_posts:
            post_path = os.path.join(self.test_dir, post['id'] + '.html')
            navigation_links = {
                'index': 'index.html',
                'archive': 'archive.html',
                'tags': 'tags.html',
            }
            page_number = 1
            generate_post(post, navigation_links, page_number, self.test_dir)
            self.assertTrue(os.path.exists(post_path))

            # Check if the post title, content, and navigation links are present in the HTML file
            with open(post_path, 'r') as f:
                html_content = f.read()
                self.assertIn(post['title'], html_content)
                self.assertIn(post['content'], html_content)
                self.assertIn(navigation_links['index'], html_content)
                self.assertIn(navigation_links['archive'], html_content)
                self.assertIn(navigation_links['tags'], html_content)

            os.remove(post_path)

    def test_generate_pages(self):
        generate_pages(self.test_dir, self.generated_posts, self.posts_per_page)
        expected_pages = (self.post_amount + self.posts_per_page - 1) // self.posts_per_page
        self.logger.info(f"Expected pages: {expected_pages}")
        files_in_dir = os.listdir(self.test_dir)
        self.logger.info(f"Files in directory: {files_in_dir}")
        generated_pages = [name for name in os.listdir(self.test_dir) if name.endswith('.html')]
        self.logger.info(f"Generated pages: {generated_pages}")
        self.assertEqual(len(generated_pages), expected_pages)
        # Sort generated pages according to the number
        generated_pages.sort(key=lambda name: int(name.split('.')[0]))
        print(generated_pages)

        # Check if the content of the pages is correct
        for i, page in enumerate(generated_pages):
            with open(os.path.join(self.test_dir, page), 'r') as f:
                self.logger.info(f"Checking page {i + 1}")
                html_content = f.read()
                soup = BeautifulSoup(html_content, 'html.parser')
                pretty_html = soup.prettify()
                self.logger.info(f"Page {i + 1}:\n{pretty_html}")
                next_link = soup.find('a', string='Next')

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

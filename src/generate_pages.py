import os
from jinja2 import Environment, FileSystemLoader
import markdown2
import datetime
import json
from functools import lru_cache
from src.utils.handler import extract_metadata, calculate_hash, create_directory, load_old_hash, save_new_hash, load_config, parse_config

# Constants
CONFIG_FILE = 'config.json'
CONFIG_DATA = load_config(CONFIG_FILE)
PARSED_CONFIG = parse_config(CONFIG_DATA)
TEMPLATE_DIR = 'templates'
DEFAULT_TEMPLATE = 'index.html'
POSTS_PER_PAGE = 10

@lru_cache(maxsize=None)
def get_template(template_name=DEFAULT_TEMPLATE):
    template_dir = os.path.abspath(TEMPLATE_DIR)
    environment = Environment(loader=FileSystemLoader(template_dir))
    template_file = os.path.basename(template_name)
    template = environment.get_template(template_file)
    return template


def write_page(output_filename, output_html):
    output_dir = os.path.dirname(output_filename)

    create_directory(output_dir)

    with open(output_filename, 'w') as output_file:
        output_file.write(output_html)

def process_post(file_path):
    with open(file_path) as post_file:
        post_content = post_file.read()
        # Parse metadata from the post
        post_metadata = extract_metadata(post_content)
        if post_metadata is not None:
            post_title = post_metadata.get('title', 'Untitled')
            post_tags = post_metadata.get('tags', [])
            # Convert Markdown to HTML
            post_content_html = markdown2.markdown(post_content)
            # Get last updated timestamp
            last_updated = os.path.getmtime(file_path)
            # Convert timestamp to human-readable format
            last_updated = datetime.datetime.fromtimestamp(last_updated).strftime('%Y-%m-%d')
            # Get post ID from filename
            post_id = os.path.splitext(os.path.basename(file_path))[0]

            post = {
                'id': post_id,
                'tags': post_tags,
                'title': post_title,
                'last_updated': last_updated,
                'content': post_content_html,
            }
            return post
    return None

def load_posts(parsed_config=PARSED_CONFIG):
    source_directory = parsed_config['source_directory']
    file_extensions = parsed_config['file_extensions']

    # create directories if they don't exist
    create_directory(source_directory)

    processed_posts = []

    for filename in os.listdir(source_directory):
        if any(filename.endswith(ext) for ext in file_extensions):
            post = process_post(os.path.join(source_directory, filename))
            if post:
                processed_posts.append(post)

    return processed_posts


def generate_page(parsed_config=PARSED_CONFIG, posts=[], page_number=1, total_pages=1):
    
    # Include navigation links in the generated HTML
    navigation_links = {
        'prev': f'{page_number - 1}.html' if page_number > 1 else None,
        'next': f'{page_number + 1}.html' if page_number < total_pages else None,
    }
    
    for post in posts:
        generate_post_page(parsed_config, post, navigation_links, page_number)

def generate_post_page(post, navigation_links, page_number):
    # Include individual post link in the navigation
    navigation_links['individual_post'] = f'post/{post["id"]}.html'

    output_html = get_template().render(
        config=PARSED_CONFIG,
        post=post,
        navigation=navigation_links,
        page_number=page_number,
        posts_per_page=POSTS_PER_PAGE
    )

    # Determine the output filename based on whether it's an index or post page
    if len(post) > 1:  # Index page
        output_filename = f'{page_number}.html'
    else:  # Individual post page
        output_filename = f'post/{post["id"]}.html'

    # Write the generated HTML to a file
    write_page(output_filename, output_html)

def generate_pages(posts_per_page=POSTS_PER_PAGE):
    config_data = load_config(CONFIG_FILE)
    source_directory = config_data['source_directory']
    old_hash = load_old_hash()
    new_hash = calculate_hash(source_directory)

    if old_hash != new_hash:
        posts = load_posts(config_data)
        posts.sort(key=lambda post: post['last_updated'], reverse=True)
        total_pages = (len(posts) + posts_per_page - 1) // posts_per_page

        # Generate index pages
        for page_number in range(1, total_pages + 1):
            # Slice the list of posts for the current page
            page_posts = posts[(page_number - 1) * posts_per_page:page_number * posts_per_page]
            generate_page(page_posts, page_number=page_number, total_pages=total_pages)

        save_new_hash(new_hash)
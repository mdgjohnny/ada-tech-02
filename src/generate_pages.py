import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import re
import markdown2
import datetime
import logging
import shutil
import tempfile
import webbrowser
from src.utils.handler import (
    extract_metadata,
    calculate_hash,
    load_old_hash,
    save_new_hash,
    create_directory,
    get_template,
    sanitize_title,
)
from config import (
    parsed_config,
)


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
LOCAL_POSTS_DIRECTORY = os.path.join(PROJECT_ROOT, parsed_config['posts_directory'])
PUBLIC_DIR = os.path.join(PROJECT_ROOT, parsed_config['public_directory'])
PUBLIC_POSTS_DIR = os.path.join(PROJECT_ROOT, parsed_config['public_posts_directory'])
INDEX_TEMPLATE = parsed_config['index_template']
POST_TEMPLATE = parsed_config['post_template']
HASH_FILENAME = os.path.join(PROJECT_ROOT, parsed_config['hash_filename'])
TEMPLATE_DIRECTORY = os.path.join(PROJECT_ROOT, parsed_config['template_directory'])

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def write_page(output_filename, output_html):
    """
    Write the output HTML to a file.

    :param output_filename: str
        The filename of the output file.
    :param output_html: str
        The HTML to write to the output file.
    """
    output_dir = os.path.dirname(output_filename)
    logger.info(f'Writing {output_filename} on {output_dir}')
    create_directory(output_dir)
    with open(output_filename, 'w') as output_file:
        output_file.write(output_html)

def process_post(file_path):
    """
    Process a single post file and return a dictionary containing the post's metadata and content.
    
    :param file_path: str
        The path to the post file.
    """
    logger.info(f'Processing {file_path}')

    with open(file_path) as post_file:
        post_content = post_file.read()
        post_filename = os.path.basename(file_path).split('.')[0]
        logger.info(f"Post content is: {post_content}")
        # Parse metadata from the post
        post_metadata = extract_metadata(post_content)
        logger.info(f"Post metadata is: {post_metadata}")
        if post_metadata:
            post_title = post_metadata.get('title', 'Untitled')
            post_type = post_metadata.get('type', 'post') # default to post if no type is found
            post_tags = post_metadata.get('tags', [])
        else:
            post_title = post_filename # default to filename if no title is found
            post_type = None # default to None if no type is found
            post_tags = []

        # Convert Markdown to HTML
        post_content_html = markdown2.markdown(post_content)
        # Get last updated timestamp
        last_updated_timestamp = os.path.getmtime(file_path)
        # Convert timestamp to human-readable format
        last_updated = datetime.datetime.fromtimestamp(last_updated_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        # Get post ID from hash
        post_id = calculate_hash(post_content)
        # Sanitized title
        sanitized_title = sanitize_title(post_title)
        logger.info(f"Sanitized title: {sanitized_title}")

        post = {
            'id': post_id,
            'type': post_type,
            'tags': post_tags,
            'title': post_title,
            'sanitized_title': sanitized_title,
            'last_updated': last_updated,
            'content': post_content_html,
        }

        # Post relative path
        if post['type'] == 'post':
            # Get the relative path from public_posts_dir to the post file
            post_rel_path = os.path.relpath(
                os.path.join(PUBLIC_POSTS_DIR, f'{post["sanitized_title"]}.html'),
                PUBLIC_DIR
            )
            post['rel_path'] = post_rel_path
            logger.info(f"Post path: {post_rel_path}")
        else:
            # If post is uncategorized, generate it in the public directory
            # Get the relative path from public_dir to the post file
            post_rel_path = os.path.relpath(
                os.path.join(PUBLIC_DIR, f'{post["sanitized_title"]}.html'),
                PUBLIC_DIR
            )
            post['rel_path'] = post_rel_path

        logger.info(f'Processed {post_id} with title {post_title}')
        return post

def load_posts(posts_directory=LOCAL_POSTS_DIRECTORY, file_extensions=['.md']):
    """
    Load all posts from the posts directory and return a list of processed posts (which are dictionaries).
    
    :param posts_directory: str, optional
        The directory where the blog posts are stored. If not provided, the function will try to load it from a configuration file.
    """

    assert os.path.exists(posts_directory), f"Error: Posts directory '{posts_directory}' not found."
    
    logger.info(f'Loading posts from {posts_directory}')
    logger.info(f'Using file extensions {file_extensions}')
    processed_posts = []

    try:
        for filename in os.listdir(posts_directory):
            logger.info(f'Loading {filename}')
            for ext in file_extensions:
                if not filename.endswith(ext):
                    continue
                logger.info(f'Processing {filename}')
                post = process_post(os.path.join(posts_directory, filename))
                if post:
                    logger.info(f'Adding {post["id"]} to posts')
                    processed_posts.append(post)
    except FileNotFoundError:
        logger.error(f"Error: Posts directory '{posts_directory}' not found.")

    logger.info(f'Loaded {len(processed_posts)} posts')
    processed_posts.sort(key=lambda post: post['id'])

    return processed_posts

def generate_post(post, output_dir=None):
    """
    Generate a single post and write it to `{post['title'].html`.
    """
    # Load the post template
    logger.info(f"Generating post {post['id']}")
    logger.info(f"Calling get_template with {POST_TEMPLATE} and {TEMPLATE_DIRECTORY}")
    template = get_template(POST_TEMPLATE, TEMPLATE_DIRECTORY)
    logger.info(f"Template directory: {TEMPLATE_DIRECTORY}")
    logger.info(f"Template: {template}")
    assert POST_TEMPLATE is not None, "Error: Unable to load post template."
    logger.info(f"Loaded post template {template}")
    # Individual post page
    logger.info(f"Generating post {post['id']}")

    output_html = template.render(
        config=parsed_config,
        post=post,
    )

    logger.info(f"Writing post page {post['title']} to {output_dir}")
    output_filename = os.path.join(output_dir, f'{post["sanitized_title"]}.html')
    logger.info(f"Output filename: {output_filename}")

    write_page(output_filename, output_html)
    logger.info(f"Generated post page for {post['id']} on {output_dir}")
    assert os.path.exists(output_filename), f"Error: Post page '{output_filename}' not found."

def generate_index_page(posts, output_dir=PUBLIC_DIR, navigation_links=None):
    """
    Generate an index page for a blog.

    :param posts: list of dict
        The list of blog posts to include in the index page.
    :param output_dir: str
        The directory where the output should be stored.
    :param navigation_links: dict, optional
        Navigation links for the index page.
    """
    # Load the index template
    template = get_template(INDEX_TEMPLATE, TEMPLATE_DIRECTORY)
    assert template is not None, "Error: Unable to load index template."
    logger.info(f"Loaded index template {template}")
    index = navigation_links['index']
    print(f"What is posts here?")
    print(f"posts: {posts}")
    # Generate output HTML
    output_html = template.render(
        config=parsed_config,
        posts=posts,
        navigation_links=navigation_links,
    )
    print(f"Do we have access to posts.rel_path here?")
    print(f"posts.rel_path: {posts[0]['rel_path']}")
    # Write the output to a file
    filename = 'index.html' if index == 1 else f'{index}.html'
    output_filename = os.path.join(output_dir, filename)
    write_page(output_filename, output_html)
    logger.info(f"Generated index page {index} on {output_dir}")


def generate_all_posts(posts, public_dir=PUBLIC_DIR, public_posts_dir=PUBLIC_POSTS_DIR):
    """
    Generate HTML for all posts in posts directory.

    :param posts: list
        The posts to generate pages for.
    :param posts: list of dict, optional
        The list of blog posts to generate pages for. If not provided, the function will load the posts from the `posts_directory`.
    :param public_dir: str, optional
        The directory where the uncategorized posts should be stored. Default is `public_dir`.
    :param public_posts_dir: str, optional
        The directory where the individual posts should be stored. Default is `public_dir/public_posts_dir`.
    """

    logger.info(f"All posts: {posts}")
    if posts is not None:
        try:
            for post in posts:
                logger.info(f"Generating post {post['id']}")
                if post['type'] == 'post':
                    generate_post(post, public_posts_dir) # Defaults to public_dir/public_posts_dir
                else:
                    generate_post(post, public_dir)
        except Exception as e:
            logger.error(f"Error: {e}")



def generate_pages(posts, posts_per_page=5, output_dir=PUBLIC_DIR):
    """
    Generate HTML for index pages.

    :param posts: list of dict
        The list of blog posts to generate pages for. If not provided, the function will load the posts from the `posts_directory`.
    :param posts_per_page: int, optional
        The maximum number of posts to display on each page. Default is 5.
    :param output_dir: str, optional
        The directory where the output should be stored. Default is `public_dir`.
        Individual posts are stored in `public_dir/public_posts_dir`.
    """
    assert len(posts) > 0, "Error: No posts found."
    logger.info(f"Loaded {len(posts)} posts")
    front_page_posts = [post for post in posts if post['type'] == 'post']
    total_pages = (len(front_page_posts) + posts_per_page - 1) // posts_per_page
    assert total_pages > 0, "Error: No pages found."
    logger.info(f"Total pages: {total_pages}")
    assert os.path.exists(output_dir), f"Error: Output directory '{output_dir}' not found." 


    # Generate index pages
    for page_number in range(1, total_pages + 1):
        logger.info(f"Generating index page {page_number} of {total_pages}")
        start_index = (page_number - 1) * posts_per_page
        end_index = start_index + posts_per_page
        page_posts = front_page_posts[start_index:end_index]
        assert len(page_posts) > 0, "Error: No posts found."
        print(f"page_posts: {page_posts}")
        prev_page = None if page_number == 1 else f'{page_number - 1}.html'
        next_page = None if page_number == total_pages else f'{page_number + 1}.html'

        navigation_links = {
            'index': page_number,
            'prev': prev_page,
            'next': next_page,
        }
            
        logger.info(f"Generating index page {page_number} of {total_pages}")
        generate_index_page(page_posts, output_dir, navigation_links)

def make_site(local_posts_directory=LOCAL_POSTS_DIRECTORY, public_dir=PUBLIC_DIR, public_posts_dir=PUBLIC_POSTS_DIR, posts_per_page=5, force_rebuild=False):
    """
    Generate the site as a whole.

    :param posts_directory: str, optional
        The directory where the blog posts are stored. If not provided, the function will try to load it from a configuration file.
    :param posts: list of dict, optional
        The list of blog posts to generate pages for. If not provided, the function will load the posts from the `posts_directory`.
    :param public_dir: str, optional
        The directory where the uncategorized posts should be stored. Default is `public_dir`.
    :param public_posts_dir: str, optional
        The directory where the individual posts should be stored. Default is `public_dir/public_posts_dir`.
    :param posts_per_page: int, optional
        The maximum number of posts to display on each page. Default is 5.
    """
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    assert os.path.exists(local_posts_directory), f"Error: Posts directory '{local_posts_directory}' not found."
    logger.info(f"Project root: {PROJECT_ROOT}")
    assert os.path.exists(local_posts_directory), f"Error: Posts directory '{local_posts_directory}' not found."
    assert os.path.exists(public_dir), f"Error: Public directory '{public_dir}' not found."
    assert os.path.exists(public_posts_dir), f"Error: Public posts directory '{public_posts_dir}' not found."
    logger.info(f"Posts directory: {local_posts_directory}")
    hash_file = os.path.join(PROJECT_ROOT, HASH_FILENAME)
    logger.info(f"Hash file: {hash_file}")

    try:
        posts = load_posts(local_posts_directory)
    except FileNotFoundError as e:
        logger.error(f"Error making site: {e}")
    except Exception as e:
        logger.error(f"Error making site: {e}")

    print(f"Loaded posts: {posts}")

    dirs_to_check = [
        LOCAL_POSTS_DIRECTORY, 
        PUBLIC_DIR, 
        PUBLIC_POSTS_DIR, 
        TEMPLATE_DIRECTORY,
    ]

    def get_hashes_by_dir(dirs):
        hashes = {}
        for directory in dirs:
            hashes[directory] = calculate_hash(directory)
        return hashes

    def has_site_changed():
        dir_hashes = get_hashes_by_dir(dirs_to_check)
        for directory, dir_hash in dir_hashes.items():
            if not os.path.exists(directory):
                logger.error(f"Error: Directory '{directory}' not found.")
                raise FileNotFoundError(f"Error: Directory '{directory}' not found.")
        if not os.path.exists(hash_file):
            return True
        else:
            old_hash = load_old_hash(hash_file)
            if any(dir_hashes[directory] != old_hash.get(directory, None) for directory in dirs_to_check):
                return True
            return False

    
    if posts is not None:
        # Check if the site has changed
        site_changed = has_site_changed()
        if site_changed or force_rebuild:
            logger.info("Changes detected. Generating site...")
            # Generating site...
            try:
                logger.info(f"Generating all posts in {local_posts_directory}...")
                generate_all_posts(posts, public_dir, public_posts_dir)
                logger.info(f"Generating pages in {local_posts_directory}...")
                generate_pages(posts, posts_per_page, public_dir)
                current_hashes = get_hashes_by_dir(dirs_to_check)
                save_new_hash(current_hashes, hash_file)
                logger.info("Pages generated successfully.")
            except Exception as e:
                logger.error(f"Error generating site: {e}")
        else:
            logger.info("No changes detected. Skipping post generation.")
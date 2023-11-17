import os
import markdown2
import datetime
import logging
from src.utils.handler import (
    extract_metadata,
    calculate_hash,
    create_directory,
    load_old_hash,
    save_new_hash,
    load_config,
    parse_config,
    get_template,
)
from src.config import (
    posts_per_page,
    config_file,
    backup_dir,
    posts_dir,
    fallback_extensions,
)

config_data = load_config(config_file)
parsed_config = parse_config(config_data)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def write_page(output_filename, output_html):
    """
    Write the output HTML to a file.
    """
    output_dir = os.path.dirname(output_filename)
    logger.info(f'Writing {output_filename} on {output_dir}')
    create_directory(output_dir)
    with open(output_filename, 'w') as output_file:
        output_file.write(output_html)

def process_post(file_path):
    """
    Process a single post file and return a dictionary containing the post's metadata and content.
    """
    logger.info(f'Processing {file_path}')
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
            last_updated_str = datetime.datetime.fromtimestamp(last_updated).strftime('%Y-%m-%d %H:%M:%S')
            # Get post ID from filename
            post_filename = os.path.splitext(os.path.basename(file_path))[0]
            post_id = post_filename.split('_')[2]

            post = {
                'id': post_id,
                'tags': post_tags,
                'title': post_title,
                'last_updated': last_updated_str,
                'content': post_content_html,
            }
            logger.info(f'Processed {post_id} with title {post_title}')
            return post
    return None

def load_posts(posts_directory=None, file_extensions=None):
    """
    Load all posts from the posts directory and return a list of processed posts (which are dictionaries).
    """
    if posts_directory is None:
        try:
            posts_directory = parsed_config['posts_directory']
        except Exception as e:
            logger.error(f"Error: {e}, couldn't load posts directory from config")
            posts_directory = posts_dir # Read from local config
    if file_extensions is None:
        try:
            file_extensions = parsed_config['file_extensions']
        except Exception as e:
            logger.error(f"Error: {e}, couldn't load file extensions from config")
            file_extensions = fallback_extensions # Read from local config
    logger.info(f'Loading posts from {posts_directory}')
    logger.info(f'Using file extensions {file_extensions}')
    # create directories if they don't exist
    create_directory(posts_directory)
    processed_posts = []

    for filename in os.listdir(posts_directory):
        if any(filename.endswith(ext) for ext in file_extensions):
            post = process_post(os.path.join(posts_directory, filename))
            if post:
                logger.info(f'Adding {post["id"]} to posts')
                processed_posts.append(post)

    logger.info(f'Loaded {len(processed_posts)} posts')
    processed_posts.sort(key=lambda post: post['id'])

    return processed_posts

def generate_post(post, navigation_links, page_number, output_dir='post'):
    """
    Generate a single post page and write it to a file.
    """
    # Load the post template
    post_template = get_template('post.html')
    logger.info(f"Loaded post template {post_template}")
    # Individual post page
    logger.info(f"Generating post {post['id']}")
    # Include individual post link in the navigation
    navigation_links['individual_post'] = os.path.join(output_dir, f'{post["id"]}.html')

    output_html = post_template.render(
        config=parsed_config,
        post=post,
        navigation_links=navigation_links,
        page_number=page_number,
        posts_per_page=posts_per_page,
    )

    logger.info(f"Writing post page {post['id']} to {output_dir}")
    output_filename = os.path.join(output_dir, f'{post["id"]}.html')

    write_page(output_filename, output_html)
    logger.info(f"Generated post page for {post['id']} on {output_dir}")

def generate_index_page(posts, output_dir, navigation_links=None):
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
    index_template = get_template('index.html')
    logger.info(f"Loaded index template {index_template}")

    # Generate output HTML
    output_html = index_template.render(
        config=parsed_config,
        posts=posts,
        navigation_links=navigation_links,
    )

    # Write the output to a file
    output_filename = os.path.join(output_dir, f'{navigation_links["page"]}.html')
    write_page(output_filename, output_html)
    logger.info(f"Generated index page {navigation_links['page']} on {output_dir}")


def generate_pages(posts_directory=None, posts=None, posts_per_page=5):
    """
    Generate HTML pages for a blog, based on a list of posts.

    :param posts_directory: str, optional
        The directory where the blog posts are stored. If not provided, the function will try to load it from a configuration file.
    :param posts: list of dict, optional
        The list of blog posts to generate pages for. If not provided, the function will load the posts from the `posts_directory`.
    :param posts_per_page: int, optional
        The maximum number of posts to display on each page. Default is 10.
    """

    # Load posts if not provided
    if posts_directory is None:
        try:
            posts_directory = parsed_config['posts_directory']
        except Exception as e:
            logger.error(f"Error: {e}, couldn't load posts directory from config")
            posts_directory = posts_dir
    else:
        if posts is not None:
            logger.info(f"Using directory {posts_directory}")
            posts = load_posts(posts_directory)
        else:
            posts_directory = parsed_config['posts_directory']
            posts = load_posts(posts_directory)

        assert len(posts) > 0, "Error: No posts found."
        logger.info(f"Loaded {len(posts)} posts")
        total_pages = (len(posts) + posts_per_page - 1) // posts_per_page
        assert total_pages > 0, "Error: No pages found."
        logger.info(f"Total pages: {total_pages}")
        output_dir = posts_directory
        assert output_dir != '', "Error: Output directory not specified."

        # Generate index pages
        for page_number in range(1, total_pages + 1):
            logger.info(f"Generating index page {page_number} of {total_pages}")
            start_index = (page_number - 1) * posts_per_page
            end_index = start_index + posts_per_page
            page_posts = posts[start_index:end_index]

            prev_page = page_number - 1 if page_number > 1 else None
            next_page = page_number + 1 if page_number < total_pages else None

            navigation_links = {
                'prev': None if page_number == 1 else f'{page_number - 1}.html',
                'next': None if page_number == total_pages else f'{page_number + 1}.html',
                'page': page_number
            }
            
            logger.info(f"Generating index page {page_number} of {total_pages}")
            generate_index_page(page_posts, output_dir, navigation_links)
            assert os.path.exists(os.path.join(output_dir, f'{page_number}.html')), "Error: Index page not generated."
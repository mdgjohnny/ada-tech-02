import datetime
import logging
import os
import re
import shutil
import markdown2
import sys
import webbrowser
from exceptions import (
    PostDirectoryNotFoundError,
    PostNotFoundError,
    BlogDirectoryNotFoundError,
    BlogTemplateError,
)
from src.config import (
    PROJECT_ROOT,
    LOCAL_POSTS_DIRECTORY,
    PUBLIC_DIR,
    PUBLIC_POSTS_DIR,
    INDEX_TEMPLATE,
    POST_TEMPLATE,
    HASH_FILENAME,
    TEMPLATE_DIRECTORY,
    parsed_config,
)
from src.utils.handler import (
    calculate_hash,
    create_directory,
    extract_metadata,
    extract_post_content,
    get_template,
    load_old_hash,
    sanitize_title,
    save_new_hash,
)

# Set up logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


def write_page(output_filename, output_html):
    """
    Write the output HTML to a file.

    Args:
        output_filename (str): The filename of the output file.
        output_html (str): The HTML to write to the output file.
    """
    output_dir = os.path.dirname(output_filename)
    output_target = os.path.join(PROJECT_ROOT, output_dir)
    logger.info(f"Writing {output_filename} on {output_dir}")
    create_directory(output_target)
    with open(output_filename, "w") as output_file:
        output_file.write(output_html)


def process_post(file_path):
    """
    Process a single post file and return a dictionary containing the post's metadata and content.

    Args:
        file_path (str): The path to the post file.
    """
    if not os.path.exists(file_path):
        raise PostNotFoundError(file_path)
    with open(file_path) as post_file:
        post_content = post_file.read()
        post_filename = os.path.basename(file_path).split(".")[0]
        post_metadata = extract_metadata(post_content)
        if post_metadata:
            post_title = post_metadata.get("title", "Untitled")
            post_type = post_metadata.get("type", "post")
            post_tags = post_metadata.get("tags", [])
            post_synopsis = post_metadata.get("synopsis", None)
        else:
            post_title = post_filename  # default to filename if no title is found
            post_type = None  # default to None if no type is found
            post_synopsis = ""
            post_tags = []
        # Extract post content; if content has metadata, remove it
        post_content = extract_post_content(post_content)
        post_content_html = markdown2.markdown(post_content)
        last_updated_timestamp = os.path.getmtime(file_path)
        # Convert timestamp to human-readable format
        last_updated = datetime.datetime.fromtimestamp(last_updated_timestamp).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        # Get post ID from hash; might use for later
        post_id = calculate_hash(post_content)
        sanitized_title = sanitize_title(post_title)
        logger.info(f"Sanitized title: {sanitized_title}")

        post = {
            "id": post_id,
            "type": post_type,
            "tags": post_tags,
            "title": post_title,
            "sanitized_title": sanitized_title,
            "synopsis": post_synopsis,
            "last_updated": last_updated,
            "content": post_content_html,
        }

        # Post relative path
        if post["type"] == "post":
            # Get the relative path from public_posts_dir to the post file
            post_rel_path = os.path.relpath(
                os.path.join(PUBLIC_POSTS_DIR, f'{post["sanitized_title"]}.html'),
                PUBLIC_DIR,
            )
            post["rel_path"] = post_rel_path
            logger.info(f"Post path: {post_rel_path}")
        else:
            # If post is uncategorized, generate it in the public directory
            # Get the relative path from public_dir to the post file
            post_rel_path = os.path.relpath(
                os.path.join(PUBLIC_DIR, f'{post["sanitized_title"]}.html'), 
                PUBLIC_DIR
            )
            post["rel_path"] = post_rel_path

        return post


def load_posts(posts_directory=LOCAL_POSTS_DIRECTORY, file_extensions=[".md"]):
    """
    Load all posts from the posts directory and return a list of processed posts (which are dictionaries).

    Args:
        posts_directory (str, optional): The directory where the blog posts are stored. If not provided, the function will try to load it from a configuration file.
    """
    if not os.path.exists(posts_directory):
        raise PostDirectoryNotFoundError(posts_directory)
    logger.info(f"Loading posts from {posts_directory}")
    logger.info(f"Using file extensions {file_extensions}")
    processed_posts = []

    try:
        for filename in os.listdir(posts_directory):
            logger.info(f"Loading {filename}")
            for ext in file_extensions:
                if not filename.endswith(ext):
                    continue
                logger.info(f"Processing {filename}")
                post = process_post(os.path.join(posts_directory, filename))
                if post:
                    logger.info(f'Adding {post["id"]} to posts')
                    processed_posts.append(post)
    except FileNotFoundError:
        raise PostNotFoundError(posts_directory)

    processed_posts.sort(key=lambda post: post["id"])

    return processed_posts


def generate_post(post, output_dir=None):
    """
    Generate a single post and write it to `{post['title']}.html`.

    Args:
        post (dict): The post to generate.
        output_dir (str, optional): The directory where the output should be stored. Default is `public_dir/public_posts_dir`.
    """
    try:
        template = get_template(POST_TEMPLATE, TEMPLATE_DIRECTORY)
    except PostTemplateError as e:
        print(f"Error while generating post: {e}")
    try:
        output_html = template.render(
            config=parsed_config,
            post=post,
            navigation_links=None,
        )
    except TemplateError as e:
        raise BlogTemplateError(f"Error while generating post: {e}")

    output_filename = os.path.join(output_dir, f'{post["sanitized_title"]}.html')
    write_page(output_filename, output_html)


def generate_index_page(posts, output_dir=PUBLIC_DIR, navigation_links=None):
    """
    Generate an index page for a blog.

    Args:
        posts (list of dict): The list of blog posts to include in the index page.
        output_dir (str): The directory where the output should be stored.
        navigation_links (dict, optional): Navigation links for the index page.
    """
    try:
        template = get_template(INDEX_TEMPLATE, TEMPLATE_DIRECTORY)
    except BlogTemplateError as e:
        print(f"Error while generating index page: {e}")
    if navigation_links:
        index = navigation_links["index"]
    output_html = template.render(
        config=parsed_config,
        posts=posts,
        navigation_links=navigation_links,
    )
    filename = "index.html" if index == 1 else f"{index}.html"
    output_filename = os.path.join(output_dir, filename)
    write_page(output_filename, output_html)


def generate_all_posts(posts, public_dir=PUBLIC_DIR, public_posts_dir=PUBLIC_POSTS_DIR):
    """
    Generate HTML for all posts in posts directory.

    Args:
        posts (list of dict, optional): The list of blog posts to generate pages for. If not provided, the function will load the posts from the `posts_directory`.
        public_dir (str, optional): The directory where the uncategorized posts should be stored. Default is `public_dir`.
        public_posts_dir (str, optional): The directory where the individual posts should be stored. Default is `public_dir/public_posts_dir`.
    """
    if posts is not None:
        try:
            for post in posts:
                logger.info(f"Generating post {post['id']}")
                logger.info(f"Writing to {public_posts_dir}")
                if post["type"] == "post":
                    # Defaults to public_dir/public_posts_dir
                    generate_post(post, public_posts_dir)
                else:
                    generate_post(post, public_dir)
        except BlogTemplateError as e:
            print(f"Error while generating posts: {e}")


def generate_pages(posts, posts_per_page=5, output_dir=PUBLIC_DIR):
    """
    Generate HTML for index pages.

    Args:
        posts (list of dict, optional): The list of blog posts to generate pages for. If not provided, the function will load the posts from the `posts_directory`.
        posts_per_page (int, optional): The maximum number of posts to display on each page. Default is 5.
        output_dir (str, optional): The directory where the output should be stored. Default is `public_dir`. Individual posts are stored in `public_dir/public_posts_dir`.
    """
    if len(posts) == 0:
        raise ValueError("Error: No posts found.")
    front_page_posts = [post for post in posts if post["type"] == "post"]
    total_pages = (len(front_page_posts) + posts_per_page - 1) // posts_per_page

    for page_number in range(1, total_pages + 1):
        start_index = (page_number - 1) * posts_per_page
        end_index = start_index + posts_per_page
        page_posts = front_page_posts[start_index:end_index]
        prev_page = None if page_number == 1 else f"{page_number - 1}.html"
        next_page = None if page_number == total_pages else f"{page_number + 1}.html"

        navigation_links = {
            "index": page_number,
            "prev": prev_page,
            "next": next_page,
        }

        try:
            generate_index_page(page_posts, output_dir, navigation_links)
        except BlogTemplateError as e:
            print(f"Error while generating blog pages: {e}")


def make_site(
    local_posts_directory=LOCAL_POSTS_DIRECTORY,
    public_dir=PUBLIC_DIR,
    public_posts_dir=PUBLIC_POSTS_DIR,
    posts_per_page=5,
    force_rebuild=False,
):
    """
    Make the site as a whole.

    Args:
        posts_directory (str, optional): The directory where the blog posts are stored. If not provided, the function will try to load it from a configuration file.
        posts (list of dict, optional): The list of blog posts to generate pages for. If not provided, the function will load the posts from the `posts_directory`.
        public_dir (str, optional): The directory where the uncategorized posts should be stored. Default is `public_dir`.
        public_posts_dir (str, optional): The directory where the individual posts should be stored. Default is `public_dir/public_posts_dir`.
        posts_per_page (int, optional): The maximum number of posts to display on each page. Default is 5.
        force_rebuild (bool, optional): Force a rebuild of the site. Default is False.
    """
    hash_file = os.path.join(PROJECT_ROOT, HASH_FILENAME)

    try:
        posts = load_posts(local_posts_directory)
    except (PostDirectoryNotFoundError, PostNotFoundError) as e:
        logger.error(f"Error while loading posts: {e}")

    dirs_to_check = [
        LOCAL_POSTS_DIRECTORY,
        PUBLIC_DIR,
        PUBLIC_POSTS_DIR,
        TEMPLATE_DIRECTORY,
    ]

    def get_hashes_by_dir(dirs):
        """
        Get hashes of all files in a directory.
        """
        hashes = {}
        for directory in dirs:
            assert os.path.exists(directory), f"Directory {directory} not found."
            logger.info(f"Calculating hash for {directory}")
            hashes[directory] = calculate_hash(directory)
        return hashes

    def has_site_changed():
        """
        Checks if site has changed by comparing the current hashes with the old hashes.
        """
        dir_hashes = get_hashes_by_dir(dirs_to_check)
        for directory, dir_hash in dir_hashes.items():
            if not os.path.exists(directory):
                logger.warning(f"Error: Directory '{directory}' not found.")
                raise BlogDirectoryNotFoundError(directory)
        if not os.path.exists(hash_file):
            return True
        else:
            old_hash = load_old_hash(hash_file)
            if any(
                dir_hashes[directory] != old_hash.get(directory, None)
                for directory in dirs_to_check
            ):
                return True
            return False

    if posts is not None:
        site_changed = has_site_changed()
        if site_changed or force_rebuild:
            if force_rebuild:
                logger.info("Site rebuild requested. Generating site...")
            else:
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
            except BlogTemplateError as e:
                logger.error(f"Error while generating site: {e}")
        else:
            logger.info("No changes detected. Skipping post generation.")

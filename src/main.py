import os
import logging
import argparse
from generate_pages import make_site
from config import (
    parsed_config,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():

    LOCAL_POSTS_DIRECTORY = parsed_config['posts_directory']
    PUBLIC_DIR = parsed_config['public_directory']
    PUBLIC_POSTS_DIR = parsed_config['public_posts_directory']

    parser = argparse.ArgumentParser(description='Generate a static site from Markdown files.')
    parser.add_argument('--posts-directory', '-p', type=str, default=LOCAL_POSTS_DIRECTORY, help='The directory where the blog posts are stored before publishing.')
    parser.add_argument('--public-directory', '-o', type=str, default=PUBLIC_DIR, help='The directory where the uncategorized posts should be stored.')
    parser.add_argument('--public-posts-directory', '-i', type=str, default=PUBLIC_POSTS_DIR, help='The directory where the individual posts should be stored.')
    parser.add_argument('--posts-per-page', '-n', type=int, default=5, help='The maximum number of posts to display on each page.')
    parser.add_argument('--force-rebuild', '-f', action='store_true', help='Force a rebuild of the site.')

    args = parser.parse_args()
    try:
        logger.info(f"Generating site from {args.posts_directory} to {args.public_directory}")
        logger.info(f"Posts will be stored in {args.public_posts_directory}")
        logger.info(f"Posts per page: {args.posts_per_page}")
        make_site(
            local_posts_directory=args.posts_directory,
            public_dir=args.public_directory,
            public_posts_dir=args.public_posts_directory,
            posts_per_page=args.posts_per_page,
            force_rebuild=args.force_rebuild,
        ),
    except Exception as e:
        logger.error(e)
        raise e

if __name__ == "__main__":
    main()

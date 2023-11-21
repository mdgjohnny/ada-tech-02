import os
import logging
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

    try:
        logger.info(f"Generating site from {LOCAL_POSTS_DIRECTORY} to {PUBLIC_DIR}")
        logger.info(f"Posts will be stored in {PUBLIC_POSTS_DIR}")
        make_site(local_posts_directory=LOCAL_POSTS_DIRECTORY, public_dir=PUBLIC_DIR, public_posts_dir=PUBLIC_POSTS_DIR, posts_per_page=5)
    except Exception as e:
        logger.error(e)
        raise e
if __name__ == "__main__":
    main()

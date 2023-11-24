import argparse
import logging
import os
import config
from generate_pages import make_site

# Set up logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


def main():

    parser = argparse.ArgumentParser(
        description="Generate a static site from Markdown files."
    )
    parser.add_argument(
        "--posts-directory",
        "-p",
        type=str,
        default=config.LOCAL_POSTS_DIRECTORY,
        help="The directory where the blog posts are stored before publishing.",
    )
    parser.add_argument(
        "--public-directory",
        "-o",
        type=str,
        default=config.PUBLIC_DIR,
        help="The directory where the uncategorized posts should be stored.",
    )
    parser.add_argument(
        "--public-posts-directory",
        "-i",
        type=str,
        default=config.PUBLIC_POSTS_DIR,
        help="The directory where the individual posts should be stored.",
    )
    parser.add_argument(
        "--posts-per-page",
        "-n",
        type=int,
        default=5,
        help="The maximum number of posts to display on each page.",
    )
    parser.add_argument(
        "--force-rebuild",
        "-f",
        action="store_true",
        help="Force a rebuild of the site.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging (INFO level).",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)
        print("Verbose logging enabled.")
    
    try:
        logger.info(
            f"Generating site from {args.posts_directory} to {args.public_directory}"
        )
        logger.info(f"Posts will be stored in {args.public_posts_directory}")
        logger.info(f"Posts per page: {args.posts_per_page}")
        make_site(
            local_posts_directory=args.posts_directory,
            public_dir=args.public_directory,
            public_posts_dir=args.public_posts_directory,
            posts_per_page=args.posts_per_page,
            force_rebuild=args.force_rebuild,
        )
    except Exception as e:
        logger.error(f"An exception occurred while generating the site: {e}")
        raise e

if __name__ == "__main__":
    main()

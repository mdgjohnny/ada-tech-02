import os
import sys
from utils.handler import load_config, parse_config

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_FILE = "config.json"
CONFIG_PATH = os.path.join(PROJECT_ROOT, CONFIG_FILE)
config_data = load_config(CONFIG_PATH)
parsed_config = parse_config(config_data)
LOCAL_POSTS_DIRECTORY = os.path.join(PROJECT_ROOT, parsed_config["posts_directory"])
PUBLIC_DIR = os.path.join(PROJECT_ROOT, parsed_config["public_directory"])
if PUBLIC_DIR == '':
    PUBLIC_DIR = PROJECT_ROOT
PUBLIC_POSTS_DIR = os.path.join(PROJECT_ROOT, parsed_config["public_posts_directory"])
INDEX_TEMPLATE = parsed_config["index_template"]
POST_TEMPLATE = parsed_config["post_template"]
DEFAULT_TEMPLATE = parsed_config["default_template"]
HASH_FILENAME = os.path.join(PROJECT_ROOT, parsed_config["hash_filename"])
TEMPLATE_DIRECTORY = os.path.join(PROJECT_ROOT, parsed_config["template_directory"])
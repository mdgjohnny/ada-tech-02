import os
from utils.handler import load_config, parse_config

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CONFIG_FILE='config.json'
CONFIG_PATH = os.path.join(PROJECT_ROOT, CONFIG_FILE)
config_data = load_config(CONFIG_PATH)
parsed_config = parse_config(config_data)
public_dir = parsed_config['public_directory']
public_posts_dir = parsed_config['public_posts_directory']
index_template = parsed_config['index_template']
post_template = parsed_config['post_template']
file_extensions = parsed_config['file_extensions']
hash_filename = parsed_config['hash_filename']
template_directory = parsed_config['template_directory']
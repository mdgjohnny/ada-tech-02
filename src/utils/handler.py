import os
import re
import hashlib
import shelve
import json
from src.config import (
    posts_dir,
    backup_dir,
    fallback_extensions,
    template_directory,
    template_filename,
)
from functools import lru_cache
from jinja2 import Environment, FileSystemLoader


def create_directory(directory_path):
    # Check if the directory exists, if not, create it
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

def calculate_hash(path):
    hash_object = hashlib.sha1()

    if os.path.isfile(path):
        with open(path, 'rb') as f:
            while True:
                data = f.read(8192)
                if not data:
                    break
                hash_object.update(data)
    else:
        for root, dirs, files in os.walk(path):
            for file in sorted(files):
                file_path = os.path.join(root, file)
                with open(file_path, 'rb') as f:
                    while True:
                        data = f.read(8192)
                        if not data:
                            break
                        hash_object.update(data)

    return hash_object.hexdigest()

def load_old_hash():
    with shelve.open('hash.db') as db:
        return db.get('hash')

def save_new_hash(new_hash):
    with shelve.open('hash.db') as db:
        db['hash'] = new_hash

def load_config(config_path):
    try:
        with open(config_path) as config_file:
            config_json = json.load(config_file)
            return config_json
    except FileNotFoundError:
        print(f"Error: Config file '{config_path}' not found.")
    except json.JSONDecodeError:
        print(f"Error: Unable to decode JSON in '{config_path}'")

def parse_config(config_dict=None, backup_dir=backup_dir):
    
    if config_dict is not None:
        config_data = config_dict
    parsed_config = {}

    for key, value in config_data.items():
        if key == 'file_extensions':
            parsed_config['file_extensions'] = []
            if isinstance(value, list):
                for ext in value:
                    if isinstance(ext, str):
                        parsed_config['file_extensions'].append(ext)
                    else:
                        print("Error: Invalid file extension: {}".format(ext))
            else:
                print("Error: Invalid file extension list: {}".format(value))
                print("Error: Using fallback file extensions: {}".format(fallback_extensions))
                parsed_config['file_extensions'] = fallback_extensions
        else:
            parsed_config[key] = value
            print("{}: {}".format(key, value))

    return parsed_config


def extract_metadata(post_content):
    metadata_match = re.search(r'---\n(.*?)\n---', post_content, re.DOTALL)
    if metadata_match:
        metadata_str = metadata_match.group(1)
        metadata_lines = metadata_str.split('\n')
        metadata = {}

        for line in metadata_lines:
            key_value_pair = line.split(':', 1)
            if len(key_value_pair) == 2:
                key, value = key_value_pair
                metadata[key.strip()] = value.strip()

        return metadata
    else:
        return None


@lru_cache(maxsize=None)
def get_template(template_name=template_filename, template_directory=template_directory):
    template_dir = os.path.abspath(template_directory)
    try:
        environment = Environment(loader=FileSystemLoader(template_dir))
        template = environment.get_template(template_name)
        return template
    except FileNotFoundError:
        print(f"Error: Template file '{template_name}' not found in directory '{template_dir}'.")
    except Exception as e:
        print(f"Error: Unable to load template '{template_name}': {e}")

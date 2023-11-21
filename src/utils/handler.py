import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import re
import hashlib
import shelve
import shutil
import tempfile
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
IGNORED_DIRECTORIES = ["venv", ".git", "__pycache__"] # for debugging purposes

from functools import lru_cache
from jinja2 import Environment, FileSystemLoader

def get_all_paths(directory, ignore_dirs=IGNORED_DIRECTORIES, ignore_files=None):
    """
    Get all paths in a directory, excluding ignored directories and files.

    
    :param directory: The directory to search.
    :param ignore_dirs: A list of directories to ignore.
    :param ignore_files: A list of files to ignore.

    Returns:
        list: A list of all paths found in the directory.
    """
    if ignore_dirs is None:
        ignore_dirs = []
    if ignore_files is None:
        ignore_files = []
    
    paths = []

    for root, dirs, files in os.walk(directory):
        # ignore ignored directories
        dirs[:] = [d for d in dirs if d not in ignore_dirs]

        # Check if root is an ignored directory
        if any(ignore_dir in root for ignore_dir in ignore_dirs):
            continue
        
        for file in files:
            if file not in ignore_files:
                file_path = os.path.join(root, file)
                paths.append(file_path)

        for dir in dirs:
            dir_path = os.path.join(root, dir)
            paths.append(dir_path)

    return paths

def create_directory(directory_path):
    # Check if the directory exists, if not, create it
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)



def calculate_hash(root_directory, ignore_dirs=IGNORED_DIRECTORIES, ignore_files=None):
    hash_object = hashlib.sha1()

    # Collect all file paths and sort them
    paths = sorted(get_all_paths(root_directory, ignore_dirs=ignore_dirs, ignore_files=ignore_files))

    for path in paths:

        relative_path = os.path.relpath(path, root_directory)

        hash_object.update(relative_path.encode('utf-8'))

        if os.path.isfile(path):
            with open(path, 'rb') as f:
                while True:
                    data = f.read(8192)
                    if not data:
                        break
                    hash_object.update(data)

    return hash_object.hexdigest()


def load_old_hash(path):
    try:
        with open(path, 'r') as f:
            hash_db = json.load(f)
    except FileNotFoundError:
        hash_db = {}
    return hash_db

def save_new_hash(new_hash, path):
    with open(path, 'w') as f:
        json.dump(new_hash, f)

def load_config(config_path):
    try:
        with open(config_path) as config_file:
            print(f"Loading config from {config_path}")
            config_json = json.load(config_file)
            return config_json
    except FileNotFoundError:
        print(f"Error: Config file '{config_path}' not found.")
    except json.JSONDecodeError:
        print(f"Error: Unable to decode JSON in '{config_path}'")

def parse_config(config_dict=None):
    
    if config_dict is not None:
        config_data = config_dict
    else:
        raise ValueError("Error: No config data provided.")
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

def sanitize_title(title):
    sanitized_title = re.sub(r'[\\\/\:\*\?\"\<\>\|]', '', title)
    sanitized_title = sanitized_title.lower()
    sanitized_title = re.sub(r'\s', '_', sanitized_title)
    return sanitized_title


@lru_cache(maxsize=None)
def get_template(template_name, template_directory):
    assert os.path.exists(template_directory), f"Error: Template directory '{template_directory}' not found."
    print(f'Template directory is: {template_directory}')

    template_path = os.path.join(template_directory, template_name)
    print(f'Template path is: {template_path}')

    try:
        environment = Environment(loader=FileSystemLoader(template_directory))
        print(f"Environment is: {environment}")

        template = environment.get_template(template_name)
        print(f"Template is: {template}")
        
        if template is not None:
            print(f"Template '{template_name}' found in directory '{template_directory}'.")
            return template
        else:
            print(f"Error: Template '{template_name}' not found in directory '{template_directory}'.")
    except FileNotFoundError:
        print(f"Error: Template file '{template_name}' not found in directory '{template_directory}'.")
    return None

if __name__ == '__main__':
    try:
        # Calculate hash of root directory
        root_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        file_directory = os.path.dirname(__file__)
        print(f"Root directory of {file_directory}: {root_directory}")
        old_hash = calculate_hash(root_directory)
        print(f"Old hash is {old_hash}")
        print("Now let's try and create a new directory and see if it changes...")
        new_directory = tempfile.mkdtemp(dir=root_directory)
        print(f"New directory: {new_directory}, exists: {os.path.exists(new_directory)}")
        new_hash = calculate_hash(root_directory)
        assert old_hash != new_hash, "Hashes are equal but they should not be"
        print("Yes, it changed.")
        print(f"New hash is {new_hash}")
        print("Now let's try and create a new file and see if it changes...")
        new_file = os.path.join(new_directory, 'new_file.txt')
        with open(new_file, 'w') as f:
            f.write('test content')
        print(f"New file: {new_file}, exists: {os.path.exists(new_file)}")
        new_hash = calculate_hash(root_directory)
        assert old_hash != new_hash, "Hashes are equal but they should not be"
        print("Yes, it changed.")
        print(f"New hash is {new_hash}")
    except AssertionError as e:
        print(f"AssertionError: {e}")
    finally:
        # Delete the new directory
        shutil.rmtree(new_directory)
        print(f"Deleted directory: {new_directory}, exists: {os.path.exists(new_directory)}")
        print("After deletion, do we still have the same hash?")
        new_hash = calculate_hash(root_directory)
        assert old_hash == new_hash, "Hashes are not equal but they should be"
        print("Yes, we do.")
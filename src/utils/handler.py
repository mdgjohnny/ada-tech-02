import hashlib
import json
import os
import re
import shelve
import shutil
import sys
import tempfile
from src.exceptions import (
    BlogTemplateError,
)
from functools import lru_cache
from jinja2 import Environment, FileSystemLoader
from jinja2.exceptions import TemplateError

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
IGNORED_DIRECTORIES = ["venv", ".git", "__pycache__"]  # for debugging purposes


def get_all_paths(directory, ignore_dirs=IGNORED_DIRECTORIES, ignore_files=None):
    """
    Get all paths in a directory, excluding ignored directories and files.

    Args:
        directory (str): The directory to search.
        ignore_dirs (list, optional): A list of directories to ignore. Defaults to IGNORED_DIRECTORIES.
        ignore_files (list, optional): A list of files to ignore. Defaults to None.

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
    """
    Create a directory if it does not exist.

    Args:
        directory_path (str): The path of the directory to create.
    """
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)


def calculate_hash(root_directory, ignore_dirs=IGNORED_DIRECTORIES, ignore_files=None):
    """
    Calculate the hash of all files in a directory.

    Args:
        root_directory (str): The root directory to calculate the hash for.
        ignore_dirs (list, optional): A list of directories to ignore. Defaults to IGNORED_DIRECTORIES.
        ignore_files (list, optional): A list of files to ignore. Defaults to None.

    Returns:
        str: The calculated hash.
    """
    hash_object = hashlib.sha1()

    # Collect all file paths and sort them
    paths = sorted(
        get_all_paths(
            root_directory, ignore_dirs=ignore_dirs, ignore_files=ignore_files
        )
    )

    for path in paths:
        relative_path = os.path.relpath(path, root_directory)

        hash_object.update(relative_path.encode("utf-8"))

        if os.path.isfile(path):
            with open(path, "rb") as f:
                while True:
                    data = f.read(8192)
                    if not data:
                        break
                    hash_object.update(data)

    return hash_object.hexdigest()


def load_old_hash(path):
    """
    Load the old hash from a file.

    Args:
        path (str): The path of the file containing the old hash.

    Returns:
        dict: The loaded hash.
    """
    try:
        with open(path, "r") as f:
            hash_db = json.load(f)
    except FileNotFoundError:
        hash_db = {}
    return hash_db


def save_new_hash(new_hash, path):
    """
    Save the new hash to a file.

    Args:
        new_hash (dict): The new hash to save.
        path (str): The path of the file to save the hash to.
    """
    with open(path, "w") as f:
        json.dump(new_hash, f)


def load_config(config_path):
    """
    Load the configuration from a file.

    Args:
        config_path (str): The path of the configuration file.

    Returns:
        dict: The loaded configuration.

    Raises:
        FileNotFoundError: If the configuration file is not found.
        json.JSONDecodeError: If the configuration file is not valid JSON.
    """
    try:
        with open(config_path) as config_file:
            config_json = json.load(config_file)
            return config_json
    except FileNotFoundError:
        print(f"Error: Config file '{config_path}' not found.")
    except json.JSONDecodeError:
        print(f"Error: Unable to decode JSON in '{config_path}'")


def parse_config(config_dict=None):
    """
    Parse the configuration dictionary. If none is provided, the default configuration is used.

    Args:
        config_dict (dict, optional): The configuration dictionary to parse.

    Returns:
        dict: The parsed configuration.

    Raises:
        ValueError: If no configuration dictionary is provided.
    """
    if config_dict is not None:
        config_data = config_dict
    else:
        raise ValueError("Error: No config data provided.")
    parsed_config = {}

    for key, value in config_data.items():
        if key == "file_extensions":
            parsed_config["file_extensions"] = []
            if isinstance(value, list):
                for ext in value:
                    if isinstance(ext, str):
                        parsed_config["file_extensions"].append(ext)
                    else:
                        print("Error: Invalid file extension: {}".format(ext))
            else:
                print("Error: Invalid file extension list: {}".format(value))
        else:
            parsed_config[key] = value

    return parsed_config


def extract_metadata(post_content):
    """
    Extract metadata from the given post content.

    Args:
        post_content (str): The content of the post.

    Returns:
        dict or None: A dictionary containing the extracted metadata, or None if no metadata is found.
    """
    metadata_match = re.search(r"---\n(.*?)\n---", post_content, re.DOTALL)
    if metadata_match:
        metadata_str = metadata_match.group(1)
        metadata_lines = metadata_str.split("\n")
        metadata = {}

        for line in metadata_lines:
            key_value_pair = line.strip().split(":", 1)
            if len(key_value_pair) == 2:
                key, value = key_value_pair
                metadata[key.strip()] = value.strip()
                if key == "tags":
                    metadata[key] = [value.strip(" []") for value in value.split(",")]
        return metadata
    else:
        return None


def extract_post_content(post_content):
    """
    Extract the content from the given post.

    Args:
        post_content (str): The content of the post.

    Returns:
        str: The extracted content.
    """
    content = re.sub(r"---\n(.*?)\n---", "", post_content, count=1, flags=re.DOTALL)
    if content:
        return content
    else:  # If post has no metadata, return the whole post
        return post_content


def sanitize_title(title):
    """
    Sanitize a title by removing special characters and converting it to lowercase.

    Args:
        title (str): The title to sanitize.

    Returns:
        str: The sanitized title.
    """
    sanitized_title = re.sub(r"[\\\/\:\*\?\"\<\>\|]", "", title)
    sanitized_title = sanitized_title.lower()
    sanitized_title = re.sub(r"\s", "_", sanitized_title)
    return sanitized_title


@lru_cache(maxsize=None)
def get_template(template_name, template_directory):
    """
    Get a template from the template directory.

    Args:
        template_name (str): The name of the template.
        template_directory (str): The directory containing the templates.

    Returns:
        The template if found, None otherwise.

    Raises:
        PostTemplateError: If there is an error loading the template.
    """

    template_path = os.path.join(template_directory, template_name)

    try:
        environment = Environment(loader=FileSystemLoader(template_directory))
        template = environment.get_template(template_name)
        if template is not None:
            return template
    except (TemplateError.TemplateNotFound, TemplateError.TemplateSyntaxError) as e:
        raise BlogTemplateError(
            post_template=template_name,
            template_directory=template_directory,
            exception=e,
        )
    return None

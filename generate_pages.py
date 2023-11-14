import os
import datetime
import json
from jinja2 import Environment, FileSystemLoader
import markdown2
import hashlib
import shelve

CONFIG_FILE = 'config.json'

def calculate_hash(directory):
    hash_object = hashlib.sha1()

    for root, dirs, files in os.walk(directory):
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
        print("Error: Config file 'config.json' not found.")
    except json.JSONDecodeError:
        print("Error: Unable to decode JSON in 'config.json'")

def parse_config(config_path):
    def is_dir(dir_path):
        return os.path.isdir(dir_path)

    def path_to_dir(dir_path):
        return os.path.abspath(dir_path)

    config_data = load_config(config_path)
    parsed_config = {}
    DEFAULT_SOURCE_DIR = 'posts'
    DEFAULT_BACKUP_DIR = 'backup'
    FALLBACK_EXTENSIONS = ['.md']

    for key, value in config_data.items():
        if key == 'source_directory':
            path_to_source = path_to_dir(value)
            parsed_config['source_directory'] = path_to_source if is_dir(path_to_source) else DEFAULT_SOURCE_DIR
        elif key == 'backup_directory':
            path_to_backup = path_to_dir(value)
            parsed_config['backup_directory'] = path_to_backup if is_dir(path_to_backup) else DEFAULT_BACKUP_DIR
        elif key == 'file_extensions':
            parsed_config['file_extensions'] = []
            if isinstance(value, list):
                for ext in value:
                    if isinstance(ext, str):
                        parsed_config['file_extensions'].append(ext)
                    else:
                        print("Error: Invalid file extension: {}".format(ext))
            else:
                print("Error: Invalid file extension list: {}".format(value))
                print("Error: Using fallback file extensions: {}".format(FALLBACK_EXTENSIONS))
                parsed_config['file_extensions'] = FALLBACK_EXTENSIONS
        else:
            print("Error: Unknown configuration option: {}".format(key))

    return parsed_config

def load_posts(config_data):
    parsed_config = parse_config(config_data)
    source_directory = parsed_config['source_directory']
    file_extensions = parsed_config['file_extensions']

    # create directories if they don't exist
    if not os.path.isdir(source_directory):
        os.makedirs(source_directory)

    posts = []

    for filename in os.listdir(source_directory):
        if any(filename.endswith(ext) for ext in file_extensions):
            with open(os.path.join(source_directory, filename)) as post_file:
                ext = os.path.splitext(filename)[1]
                post_content = post_file.read()
                # Convert Markdown to HTML
                post_content_html = markdown2.markdown(post_content)
                # Get last updated timestamp
                last_updated = os.path.getmtime(os.path.join(source_directory, filename))
                # Convert timestamp to human-readable format
                last_updated = datetime.datetime.fromtimestamp(last_updated).strftime('%Y-%m-%d')
                # Get post ID from filename
                post_id = os.path.splitext(filename)[0]

                # Append post metadata to posts list
                posts.append({
                    'id': post_id,
                    'title': post_title,  # Placeholder, replace with actual title extraction logic
                    'content': post_content_html,
                    'last_updated': last_updated
                })

                # Generate individual post page
                generate_page(parsed_config, posts[-1])

    return posts

def backup_posts(config):
    backup_directory = os.path.abspath(
        config.get('backup_directory', 'backup')
    )

def generate_page(config, post):
    template_dir = os.path.abspath('templates')
    environment = Environment(loader=FileSystemLoader(template_dir))
    template_file = os.path.basename('index.html')
    template = environment.get_template(template_file)
    
    # Logic to generate the page using the template
    # ...

    # Include navigation links in the generated HTML
    navigation_links = {
        'individual_post': f'post-{post["id"]}.html'  # Individual post link
    }

    # Include navigation links in the template rendering
    output_html = template.render(config=config, post=post, navigation=navigation_links)

    # Save the generated HTML to a file
    output_filename = f'post-{post["id"]}.html'
    with open(output_filename, 'w') as output_file:
        output_file.write(output_html)

def generate_pages():
    template_dir = os.path.abspath('templates')
    environment = Environment(loader=FileSystemLoader(template_dir))
    template_file = os.path.basename('index.html')
    template = environment.get_template(template_file)
    config_data = load_config(CONFIG_FILE)
    source_directory = config_data['source_directory']
    old_hash = load_old_hash()
    new_hash = calculate_hash(source_directory)

    if old_hash != new_hash:
        posts = load_posts(config_data)
        posts_per_page = 10  # Define the number of posts per page
        total_pages = (len(posts) + posts_per_page - 1) // posts_per_page

        # Generate index pages
        for page_number in range(1, total_pages + 1):
            generate_page(config_data, posts, page_number=page_number, posts_per_page=posts_per_page)

        # Additional logic for pagination if needed
        save_new_hash(new_hash)

if __name__ == '__main__':
    generate_pages()

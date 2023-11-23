class PostNotFoundError(Exception):
    """Raised when the post cannot be found."""

    def __init__(self, post_path):
        self.message = f"Post '{posts_directory}' not found."


class PostDirectoryNotFoundError(Exception):
    """Raised when the post directory cannot be found."""

    def __init__(self, posts_directory):
        self.message = f"Post directory '{posts_directory}' not found."

class BlogDirectoryNotFoundError(Exception):
    """Raised when the blog directory cannot be found."""

    def __init__(self, blog_directory):
        self.message = f"Blog directory '{blog_directory}' not found."

class BlogTemplateError(Exception):
    """General template error."""

    def __init__(self, *args, **kwargs):
        self.message = "Error loading blog template."
        self.exception = kwargs.get("exception")
        self.post_template = kwargs.get("post_template")
        self.template_directory = kwargs.get("template_directory")

        if self.post_template:
            self.message += f" Post Template: {self.post_template}"

        if self.template_directory:
            self.message += f" Template Directory: {self.template_directory}"

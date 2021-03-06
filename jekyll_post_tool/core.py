import os
import frontmatter
import datetime
from slugify import slugify

class JekyllPostTool:

    """
    This class enables you to create/edit a Jekyll markdown post.
    """

    def __init__(self, options, verbose=False):

        self._verbose = verbose
        # Set the output path
        if "output" in options:
            if options["output"].endswith("/"):
                self.output_path = options["output"]
            else:
                self.output_path = options["output"] + "/"
        else:
            self.output_path = os.getcwd() + "/output"
        # Check to see if the output path exists and create if not
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

    def write_post(self, front_matter, content, file_name, remove_old=False):
        """Creates Jekyll markdown post

        Parameters
        ----------
        front_matter : dict/json
            A dict/json object containing the values to be used in the front matter of the post.
        content : text
            The text content of a post. This can contain newline characters and markdown formatting.
        file_name: string
            The output file name of the post e.g 2019-12-12-my-new-jekyll-post.md

        Returns
        -------
        boolean: returns True if the file was written successfully and returns False if not.

        """
        if remove_old:
            os.remove(remove_old)
        # Create the output path
        output_file_path = self.output_path + file_name
        # New post var with a higher scope
        new_post = None
        # Create a new frontmatter object
        with open(output_file_path, "w+") as new_post_file:
            new_post = frontmatter.loads(new_post_file.read())
            # Set the front matter
            new_post.metadata = front_matter
            # Set the content
            new_post.content = content
        # Write the New file
        with open(output_file_path, "w+") as new_post_file:
            new_post_file.writelines(frontmatter.dumps(new_post))

        if self._verbose:
            print("File written to {}".format(output_file_path))

        return True

if __name__ == "__main__":

    post_tool = JekyllPostTool({"output": "assets/output/"}, verbose=True)

    example_front_matter = {
        "title": "This is a new post title!",
        "date": "2019-12-09 12:00:00",
        "description": "A short description of the post",
        "image": {
            "path":"/assets/images/content/featured-image.png",
            "alt": "The image alt tag"
        },
        "categories": ["BUD20", "Resource Post"]
    }

    example_post_content = """This is some example post content.

# New Heading

More text.

- List
  - Sub List
- of
- items"""

    post_tool.write_post(example_front_matter, example_post_content, "2019-12-12-test.md")

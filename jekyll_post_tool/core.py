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
                self.output_path = os.getcwd() + "/" + options["output"]
            else:
                self.output_path = os.getcwd() + "/" + options["output"] + "/"
        else:
            self.output_path = os.getcwd() + "/output"
        # Check to see if the output path exists and create if not
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)


    def edit_post(self, front_matter, content, file_name):
        """Edit a Jekyll markdown post

        Parameters
        ----------
        front_matter: dict/json
            A dict/json object containing the values to be used in the front matter of the post.
        content: multiline text
            The text contnet of a post. This should be formatted in a python multiline string
        file_name: string
            The path to file to modify

        Returns
        -------
        boolean: returns True if the post was edited False if not.

        """
        # Create the output path
        output_file_path = self.output_path + file_name
        jekyll_post = None
        edited = False
        # Open the current file
        with open(output_file_path, "r") as current_post_file:
            jekyll_post = frontmatter.loads(current_post_file.read())

        if jekyll_post.metadata != front_matter:
            if self._verbose:
                print("Updating post front matter...")
            # Updated the front matter with any changed values
            jekyll_post.metadata.update(front_matter)
            edited = True
        else:
            if self._verbose:
                print("Post front matter hasn't changed...")


        # Update the post content if applicable
        if jekyll_post.content != content:
            if self._verbose:
                print("Updating post content...")
            jekyll_post.content = content
            edited = True
        else:
            if self._verbose:
                print("Post content hasn't changed...")

        with open(output_file_path, "w") as edited_file:
            edited_file.writelines(frontmatter.dumps(jekyll_post))

        return edited

    def create_post(self, front_matter, content, file_name):
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
            print()
            print("Post Content \n")
            print(new_post.content)
            print()
            print("Front Matter \n")
            print(new_post.metadata)

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

    post_tool.create_post(example_front_matter, example_post_content, "2019-12-12-test.md")

    changed_front_matter = {
        "title": "This is a new post title!",
        "date": "2019-12-09 12:00:00",
        "description": "A short description of the post",
        "image": {
            "path": "/assets/images/content/featured-image.png",
            "alt": "The image alt tag"
        },
        "categories": ["BUD20", "Resource Post"]
    }

    changed_post_content = """This is some example post content.

# New Heading

More text.

- List
  - Sub List
- of
- items"""


    post_tool.edit_post(changed_front_matter,
                        changed_post_content, "2019-12-12-test.md")

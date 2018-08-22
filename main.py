from urllib import request
import io
import textwrap
import csv
import os
from urllib.parse import urlparse
import frontmatter
from io import BytesIO
import datetime
import re   
import pickle

class JekyllConnectSessionsTool:
    
    """
    This class can create and modify Jekyll posts for the Connect static website
    based on export data from Pathable.
    """

    def __init__(self, data_src_file_name="sessions.csv", user_src_file_name="users.csv"):

        # Get the data source csv file
        self._data_src_file_name = data_src_file_name
        # Get the data source csv file
        self._user_src_file_name = user_src_file_name

        # Local Output path for images
        self.output_path = os.getcwd() + "/" + "posts/"

        self.main()

    def main(self):
        sessions = self.grab_session_data_from_csv()
        users = self.grab_user_data_from_csv()
    
        # Download attendee photos from pathable.
        for user in users:
            if user["photo_url"]:
                username = user["first_name"] + user["second_name"]
                photo_download = self.grab_photo(user["photo_url"], output_filename=username)
                print(photo_download)
                user["image-name"] = photo_download
            else:
                print("No Photo Url for {0} - skipping!").format(username)

        # Dump the data into cache file
        self.cache_file(sessions, "sessions.pkl")
        self.cache_file(users, "users.pkl")

        # Create Jekyll posts.
        self.create_jekyll_event_posts(sessions, users)

    def create_jekyll_event_posts(self, sessions, users):
        """Create Jekyll Posts based off the output csv files from pathable."""
        for session in sessions:
            # Open a default template blog post.
            new_post = frontmatter.loads(open("template.md","r").read())

            # Add speakers for the session
            emails = session["speakers"].split(",")
            names = []
            for speaker_email in emails:
                for attendee in users:
                    if attendee["speaker_email"] == speaker_email:
                        name = attendee["first_name"] + " " + attendee["second_name"]
                        # bio_formatted =  '{0}'.format(attendee["bio"])
                        # bio_formatted =  repr(attendee["bio"])
                        bio_formatted =  f'"{attendee["bio"]}"'
                        speaker_dict = {
                                "name":name,
                                "biography": bio_formatted,
                                "job-title": attendee["job-title"],
                                "company": attendee["company"],
                                "speaker-image": attendee["image-name"]
                                }
                        names.append(speaker_dict)
            if len(names) > 0:
                new_post["speakers"] = names
            else:
                new_post["speakers"] = "None"

            #Presentations and videos
            new_post["amazon_s3_presentation_url"] = "None"
            new_post["amazon_s3_video_url"] = "None"
            new_post["youtube_video_url"] = "None"
            new_post["slideshare_presentation_url"] = "None"

            #Jekyll specific front matter
            new_post["comments"] = False
            new_post["layout"] = "resource-post"
            new_post["categories"] = ["yvr18"]
            new_post["author"] = "connect"
            
            # Set new values of the blog post.
            new_post["title"] = re.sub('[^A-Za-z0-9-!: ()]+', '', session["title"])
            print(new_post["title"])
            # Get Current date
            current_date = datetime.datetime.now().strftime("%Y-%m-%d")
            # Add the Jekyll format post date
            new_post["date"] = current_date + " 09:00:00+00:00"
            # Add Content to the Jekyll post
            new_post.content = session["blurb"]
            # Add session tracks
            new_post["session_track"] = session["tracks"].replace(";",", ")
            # Add session id
            new_post["session_id"] = session["session_id"]

            # Create the file name for the new jekyll post
            new_post_name = "{0}-{1}.md".format(current_date, session["session_id"].lower())
            # Prepend the output folder and the new_post_name
            output_object = "posts/" + new_post_name
            # Create the new post object and write the front matter to post.
            with open(output_object,"w") as new_post_file:
                new_post_file.writelines(frontmatter.dumps(new_post))
                print("Jekyll post created for {0} at {1}".format(session["session_id"], output_object))

    def update_jekyll_posts(self, sessions, users):
        """Take the latest export of sessions and users and update any information that has changed"""
        pass
            
    def grab_session_data_from_csv(self):
        """Fetches the session data from the pathable meetings export"""
        my_file = self._data_src_file_name
        with open(my_file, 'rt',encoding="utf8") as f:
            reader = csv.reader(f)
            csv_data = list(reader)
            data = []
            for each in csv_data:
                title = each[4]
                desc = each[5]
                session_id = each[1]
                speaker_names = each[10]
                tracks = each[7]
                new_dict = {
                    "title":title,
                    "blurb":desc,
                    "session_id":session_id,
                    "speakers":speaker_names,
                    "tracks": tracks
                }
                data.append(new_dict)
            # for each in data:
            #     print(each)
            #     input()
        return data


    def cache_file(self, data, cache_file_name):
        """Dumps the data supplied into specificed cache_file_name using pickle"""
        with open(cache_file_name, 'wb') as output:
            pickle.dump(data, output, pickle.HIGHEST_PROTOCOL)
        return True


    def grab_user_data_from_csv(self):
        """Fetches the user data from the pathable attendees export"""
        my_file = self._user_src_file_name
        with open(my_file, 'rt',encoding="utf8") as f:
            reader = csv.reader(f)
            csv_data = list(reader)
            data = []
            for each in csv_data:
                email = each[12]
                first_name = each[2]
                second_name = each[3]
                title = each[4]
                company = each[6]
                bio = each[7]
                photo_url = each[16]
                new_dict = {
                    "speaker_email":email,
                    "first_name":first_name,
                    "second_name":second_name,
                    "job-title":title,
                    "company": company,
                    "bio": bio,
                    "photo_url": photo_url
                }
                data.append(new_dict)
            # for each in data:
            #     print(each)
            #     input()
        return data
                        
    def grab_photo(self, url, output_filename, output_path="photos/"):
        """Fetches attendee photo from the pathable data"""
        # Get the filename parsed in
        file_name = output_filename
        # Extract the path from the URL
        path = urlparse(url).path
        # Get the Extension from the path using os.path.splitext
        ext = os.path.splitext(path)[1]
        # Add output folder to output path
        output =  output_path + file_name + ext
        # Try to download the image and Except errors and return as false.
        try:
            image = request.urlretrieve(url, output)
            print(image)
        except Exception as e:
            print(e)
            image = False
        return(file_name + ext)
        
if __name__ == "__main__":
    
    cards = JekyllConnectSessionsTool("sessions.csv","users.csv")
